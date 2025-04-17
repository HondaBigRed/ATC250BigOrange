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

        self.low_button = IconButton(str(icon_dir / "low_on.png"), str(icon_dir / "low_off.png"))
        self.high_button = IconButton(str(icon_dir / "high_on.png"), str(icon_dir / "high_off.png"))
        self.tail_button = IconButton(str(icon_dir / "tail_on.png"), str(icon_dir / "tail_off.png"))
        self.vape_button = IconButton(str(icon_dir / "vape_on.png"), str(icon_dir / "vape_off.png"))
        self.hazard_button = IconButton(str(icon_dir / "haz_on.png"), str(icon_dir / "haz_off.png"))
        self.horn_button = IconButton(str(icon_dir / "horn_on.png"), str(icon_dir / "horn_off.png"))

        layout.add_widget(self.low_button)
        layout.add_widget(self.high_button)
        layout.add_widget(self.tail_button)
        layout.add_widget(self.vape_button)
        layout.add_widget(self.hazard_button)
        layout.add_widget(self.horn_button)
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
        self.add_widget(layout)


class ATCDashApp(App):
    """
    Main application class for the ATC Dashboard.
    """
    def build(self):
        self.sm = ScreenManager(transition=SwapTransition())
        self.sm.add_widget(RelayControlScreen(name="relays"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))

        root = BoxLayout(orientation="vertical")
        toggle_btn = Button(text="Switch Screen", size_hint_y=None, height=50)
        toggle_btn.bind(on_press=self.toggle_screen)
        root.add_widget(toggle_btn)
        root.add_widget(self.sm)

        return root

    def toggle_screen(self, *args):
        self.sm.current = "dashboard" if self.sm.current == "relays" else "relays"


if __name__ == "__main__":
    ATCDashApp().run()