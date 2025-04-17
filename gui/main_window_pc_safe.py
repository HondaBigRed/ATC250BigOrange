# [Merged GUI with ScreenManager and Dashboard]
# Cleaned and improved version

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
from kivy.app import App
from kivy.config import Config
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from kivy.uix.behaviors import ButtonBehavior

# Constants
PLATFORM_LINUX = "linux"
PLATFORM_ARM = "arm"
DEBOUNCE_TIME = 0.25
FLASH_INTERVAL = 0.5

# Determine if running on Raspberry Pi
IS_PI = sys.platform.startswith(PLATFORM_LINUX) and PLATFORM_ARM in sys.platform

# GPIO Handling
if IS_PI:
    import lgpio
    chip = lgpio.gpiochip_open(0)
else:
    class MockGPIO:
        """Mock GPIO class for non-Raspberry Pi platforms."""

        def gpio_claim_output(self, *args, **kwargs):
            pass

        def gpio_write(self, *args, **kwargs):
            pass

        def gpiochip_close(self, *args, **kwargs):
            pass

    lgpio = MockGPIO()
    chip = None

# Placeholder for pins and icon directory
pins = {
    "low": None,
    "high": None,
    "tail": None,
    "vape": None,
    "hazard": None,
    "horn_400": None,
    "horn_500": None,
}
icon_dir = Path("/path/to/icons")

class GPIOHandler:
    """Helper class for managing GPIO operations."""

    def __init__(self, is_pi: bool):
        self.is_pi = is_pi
        self.chip = lgpio.gpiochip_open(0) if is_pi else None

    def set_pin_state(self, pin: int, state: bool):
        if self.is_pi and pin is not None:
            lgpio.gpio_write(self.chip, pin, 1 if state else 0)

    def cleanup(self):
        if self.is_pi and self.chip:
            lgpio.gpiochip_close(self.chip)


class IconButton(ButtonBehavior, Image):
    """
    A custom button with an image that toggles between on and off states.

    Attributes:
        on_icon (str): Path to the "on" icon.
        off_icon (str): Path to the "off" icon.
        gpio_pin (int): GPIO pin number associated with the button.
    """

    def __init__(self, on_icon: str, off_icon: str, gpio_pin: int = None, **kwargs):
        super().__init__(**kwargs)
        self.on_icon = on_icon
        self.off_icon = off_icon
        self.gpio_pin = gpio_pin
        self.state_on = False
        self.last_touch_time = 0
        self.update_icon()

    def on_release(self):
        now = Clock.get_time()
        if now - self.last_touch_time < DEBOUNCE_TIME:
            return
        self.last_touch_time = now
        self.toggle()

    def toggle(self):
        """Toggle the button state and update the icon."""
        self.state_on = not self.state_on
        self.update_icon()
        if self.gpio_pin is not None:
            lgpio.gpio_write(chip, self.gpio_pin, 1 if self.state_on else 0)

    def set_state(self, state: bool):
        """Set the button state and update the icon."""
        self.state_on = state
        self.update_icon()
        if self.gpio_pin is not None:
            lgpio.gpio_write(chip, self.gpio_pin, 1 if state else 0)

    def update_icon(self):
        """Update the icon based on the button state."""
        self.source = self.on_icon if self.state_on else self.off_icon


class RelayControlScreen(Screen):
    """
    Screen for controlling relays using IconButton widgets.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="horizontal", padding=10, spacing=10)

        self.low_button = IconButton(str(icon_dir / "low_on.png"), str(icon_dir / "low_off.png"), gpio_pin=pins["low"])
        self.high_button = IconButton(str(icon_dir / "high_on.png"), str(icon_dir / "high_off.png"), gpio_pin=pins["high"])
        self.tail_button = IconButton(str(icon_dir / "tail_on.png"), str(icon_dir / "tail_off.png"), gpio_pin=pins["tail"])
        self.vape_button = IconButton(str(icon_dir / "vape_on.png"), str(icon_dir / "vape_off.png"), gpio_pin=pins["vape"])
        self.hazard_button = IconButton(str(icon_dir / "haz_on.png"), str(icon_dir / "haz_off.png"))
        self.horn_button = IconButton(str(icon_dir / "horn_on.png"), str(icon_dir / "horn_off.png"))

        self.low_button.on_release = self.low_beam_pressed
        self.high_button.on_release = self.high_beam_pressed
        self.hazard_button.on_release = self.toggle_hazards
        self.horn_button.on_press = self.press_horn
        self.horn_button.on_release = self.release_horn

        for button in [
            self.low_button,
            self.high_button,
            self.tail_button,
            self.vape_button,
            self.hazard_button,
            self.horn_button,
        ]:
            layout.add_widget(button)

        self.add_widget(layout)

        self.hazard_state = False
        self.hazard_timer = None

    def low_beam_pressed(self, *args):
        self.low_button.set_state(True)
        self.high_button.set_state(False)
        self.tail_button.set_state(True)

    def high_beam_pressed(self, *args):
        self.high_button.set_state(True)
        self.low_button.set_state(False)
        self.tail_button.set_state(True)

    def toggle_hazards(self, *args):
        self.hazard_state = not self.hazard_state
        self.hazard_button.set_state(self.hazard_state)
        if self.hazard_state:
            self.hazard_timer = Clock.schedule_interval(self.flash_hazards, FLASH_INTERVAL)
        else:
            if self.hazard_timer:
                self.hazard_timer.cancel()
            self.tail_button.set_state(False)
            self.high_button.set_state(False)

    def flash_hazards(self, dt):
        toggle = not self.high_button.state_on
        self.high_button.set_state(toggle)
        self.tail_button.set_state(not toggle)

    def press_horn(self, *args):
        self.horn_button.set_state(True)
        lgpio.gpio_write(chip, pins["horn_400"], 1)
        lgpio.gpio_write(chip, pins["horn_500"], 1)

    def release_horn(self, *args):
        self.horn_button.set_state(False)
        lgpio.gpio_write(chip, pins["horn_400"], 0)
        lgpio.gpio_write(chip, pins["horn_500"], 0)


class DashboardScreen(Screen):
    """
    Screen for displaying live dashboard data.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Live Dashboard", font_size=24))
        self.speed_label = Label(text="Speed: 0 MPH", font_size=20)
        self.rpm_label = Label(text="RPM: 0", font_size=20)
        self.afr_label = Label(text="AFR: 14.7", font_size=20)
        self.gear_label = Label(text="Gear: N", font_size=20)
        self.temp_label = Label(text="Head Temp: 0°C", font_size=20)
        for widget in [self.speed_label, self.rpm_label, self.afr_label, self.gear_label, self.temp_label]:
            layout.add_widget(widget)
        self.add_widget(layout)

    def update_dashboard(self, speed: int, rpm: int, afr: float, gear: str, head_temp: int):
        self.speed_label.text = f"Speed: {speed} MPH"
        self.rpm_label.text = f"RPM: {rpm}"
        self.afr_label.text = f"AFR: {afr:.2f}"
        self.gear_label.text = f"Gear: {gear}"
        self.temp_label.text = f"Head Temp: {head_temp}°C"


class ATCDashApp(App):
    """
    Main application class for the ATC Dashboard.
    """

    def build(self):
        self.sm = ScreenManager(transition=SwapTransition())
        self.relay_screen = RelayControlScreen(name="relays")
        self.dashboard_screen = DashboardScreen(name="dashboard")
        self.sm.add_widget(self.relay_screen)
        self.sm.add_widget(self.dashboard_screen)

        root = BoxLayout(orientation="vertical")
        toggle_btn = Button(text="Switch Screen", size_hint_y=None, height=50)
        toggle_btn.bind(on_press=self.toggle_screen)
        root.add_widget(toggle_btn)
        root.add_widget(self.sm)

        Clock.schedule_interval(self.mock_sensor_data, 1)
        return root

    def toggle_screen(self, *args):
        self.sm.current = "dashboard" if self.sm.current == "relays" else "relays"

    def mock_sensor_data(self, dt):
        """Simulates sensor data for testing purposes."""
        speed = 25
        rpm = 3100
        afr = 14.2
        gear = "3"
        head_temp = 132
        self.dashboard_screen.update_dashboard(speed, rpm, afr, gear, head_temp)

    def on_stop(self):
        """Clean up GPIO resources on application exit."""
        for pin in pins.values():
            if pin is not None:
                lgpio.gpio_write(chip, pin, 0)
        lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    ATCDashApp().run()