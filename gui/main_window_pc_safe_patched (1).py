# [Merged GUI with ScreenManager and Dashboard]
# Fully updated and improved version

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from kivy.uix.behaviors import ButtonBehavior

# Constants
IS_PI = sys.platform.startswith("linux") and "arm" in sys.platform
ICON_DIR = Path("gui/icons")  # Path to the icons directory
DEBOUNCE_TIME = 0.25
FLASH_INTERVAL = 0.5

# GPIO Handling
if IS_PI:
    import lgpio
    chip = lgpio.gpiochip_open(0)
else:
    class MockGPIO:
        """Mock GPIO class for non-Raspberry Pi platforms."""
        def gpio_claim_output(self, *args, **kwargs): pass
        def gpio_write(self, *args, **kwargs): pass
        def gpiochip_close(self, *args, **kwargs): pass

    lgpio = MockGPIO()
    chip = None

# GPIO pin definitions
pins = {
    "low": None,
    "high": None,
    "tail": None,
    "vape": None,
    "hazard": None,
    "horn_400": None,
    "horn_500": None,
}


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
        self.on_icon = Path(on_icon)
        self.off_icon = Path(off_icon)
        self.gpio_pin = gpio_pin
        self.state_on = False
        self.last_touch_time = 0

        # Verify that the icons exist
        if not self.on_icon.exists():
            raise FileNotFoundError(f"Icon not found: {self.on_icon}")
        if not self.off_icon.exists():
            raise FileNotFoundError(f"Icon not found: {self.off_icon}")

        self.update_icon()

    def on_release(self):
        """Debounce the button touch and toggle state."""
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
        self.source = str(self.on_icon if self.state_on else self.off_icon)


class RelayControlScreen(Screen):
    """
    Screen for controlling relays using IconButton widgets.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="horizontal", padding=10, spacing=10)

        # Instantiate relay control buttons
        self.low_button = IconButton(ICON_DIR / "low_on.png", ICON_DIR / "low_off.png", gpio_pin=pins["low"])
        self.high_button = IconButton(ICON_DIR / "high_on.png", ICON_DIR / "high_off.png", gpio_pin=pins["high"])
        self.tail_button = IconButton(ICON_DIR / "tail_on.png", ICON_DIR / "tail_off.png", gpio_pin=pins["tail"])
        self.vape_button = IconButton(ICON_DIR / "vape_on.png", ICON_DIR / "vape_off.png", gpio_pin=pins["vape"])
        self.hazard_button = IconButton(ICON_DIR / "haz_on.png", ICON_DIR / "haz_off.png", gpio_pin=pins["hazard"])
        self.horn_button = IconButton(ICON_DIR / "horn_on.png", ICON_DIR / "horn_off.png", gpio_pin=pins["horn_400"])

        # Add buttons to layout
        for button in [
            self.low_button, self.high_button, self.tail_button,
            self.vape_button, self.hazard_button, self.horn_button
        ]:
            layout.add_widget(button)

        self.add_widget(layout)


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
        self.temp_label = Label(text="Head Temp: 0°C", font_size=20)
        self.gear_label = Label(text="Gear: N", font_size=20)
        self.afr_label = Label(text="AFR: 14.7", font_size=20)

        # Add labels to layout
        for widget in [self.speed_label, self.rpm_label, self.temp_label, self.gear_label, self.afr_label]:
            layout.add_widget(widget)

        self.add_widget(layout)

    def update_dashboard(self, speed, rpm, head_temp, gear, afr):
        """Update dashboard data."""
        self.speed_label.text = f"Speed: {speed} MPH"
        self.rpm_label.text = f"RPM: {rpm}"
        self.temp_label.text = f"Head Temp: {head_temp}°C"
        self.gear_label.text = f"Gear: {gear}"
        self.afr_label.text = f"AFR: {afr:.2f}"


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

        Clock.schedule_interval(self.mock_sensor_data, 1)  # Simulate sensor data
        return root

    def toggle_screen(self, *args):
        """Toggle between relay control and dashboard screens."""
        self.sm.current = "dashboard" if self.sm.current == "relays" else "relays"

    def mock_sensor_data(self, dt):
        """Simulate sensor data for testing."""
        self.dashboard_screen.update_dashboard(speed=25, rpm=3100, head_temp=132, gear="3", afr=14.2)

    def on_stop(self):
        """Clean up GPIO resources on application exit."""
        for pin in pins.values():
            if pin is not None:
                lgpio.gpio_write(chip, pin, 0)
        if IS_PI:
            lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    ATCDashApp().run()