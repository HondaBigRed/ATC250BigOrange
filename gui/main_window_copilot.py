import os
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.core.window import Window
from pathlib import Path
import lgpio
import time

# Constants
CHIP = lgpio.gpiochip_open(0)
ICON_DIR = Path(__file__).resolve().parent / "icons"
WHEEL_CIRCUMFERENCE_M = 1.6
PULSES_PER_REV = 1
HALL_GPIO = 17

print(">>> DASH STARTING UP")

# Setup relay output pins
PINS = {
    "low": 4,
    "high": 26,
    "tail": 27,
    "vape": 22,
    "hazards": None,
    "horn_500": 21,
    "horn_400": 13,
}

for pin in PINS.values():
    if pin is not None:
        lgpio.gpio_claim_output(CHIP, pin, 0)

class IconButton(ButtonBehavior, Image):
    def __init__(self, on_icon, off_icon, gpio_pin=None, **kwargs):
        super().__init__(**kwargs)
        self.on_icon = str(ICON_DIR / on_icon)
        self.off_icon = str(ICON_DIR / off_icon)
        self.gpio_pin = gpio_pin
        self.state_on = False
        self.source = self.off_icon
        if self.gpio_pin is not None:
            lgpio.gpio_claim_output(CHIP, self.gpio_pin, 0)

    def on_press(self):
        self.toggle()

    def toggle(self):
        self.state_on = not self.state_on
        self.source = self.on_icon if self.state_on else self.off_icon
        if self.gpio_pin is not None:
            lgpio.gpio_write(CHIP, self.gpio_pin, int(self.state_on))

    def set_state(self, state: bool):
        """Set the button state programmatically."""
        self.state_on = state
        self.source = self.on_icon if state else self.off_icon
        if self.gpio_pin is not None:
            lgpio.gpio_write(CHIP, self.gpio_pin, int(state))

class RelayControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = GridLayout(cols=3, spacing=20, padding=20)

        # Add buttons with correct logic
        self.low_button = IconButton("low_on.png", "low_off.png", PINS["low"])
        self.high_button = IconButton("high_on.png", "high_off.png", PINS["high"])
        self.tail_button = IconButton("tail_on.png", "tail_off.png", PINS["tail"])
        self.vape_button = IconButton("vape_on.png", "vape_off.png", PINS["vape"])
        self.hazard_button = IconButton("haz_on.png", "haz_off.png", None)
        self.horn_button = IconButton("horn_on.png", "horn_off.png", None)

        # Add buttons to the layout
        layout.add_widget(self.low_button)
        layout.add_widget(self.high_button)
        layout.add_widget(self.tail_button)
        layout.add_widget(self.vape_button)
        layout.add_widget(self.hazard_button)
        layout.add_widget(self.horn_button)

        self.add_widget(layout)

        # Initialize hazard state
        self.hazard_state = False
        self.hazard_timer = None

        # Attach custom logic to buttons
        self.low_button.on_press = self.low_beam_pressed
        self.high_button.on_press = self.high_beam_pressed
        self.hazard_button.on_press = self.toggle_hazards
        self.horn_button.bind(on_touch_down=self.press_horn, on_touch_up=self.release_horn)

    def low_beam_pressed(self, *args):
        """Logic for low beam button."""
        if self.low_button.state_on:
            self.low_button.set_state(False)
            self.tail_button.set_state(False)
        else:
            self.low_button.set_state(True)
            self.high_button.set_state(False)
            self.tail_button.set_state(True)

    def high_beam_pressed(self, *args):
        """Logic for high beam button."""
        if self.high_button.state_on:
            self.high_button.set_state(False)
            self.tail_button.set_state(False)
        else:
            self.high_button.set_state(True)
            self.low_button.set_state(False)
            self.tail_button.set_state(True)

    def toggle_hazards(self, *args):
        """Logic for toggling hazard lights."""
        self.hazard_state = not self.hazard_state
        self.hazard_button.set_state(self.hazard_state)
        if self.hazard_state:
            self.hazard_timer = Clock.schedule_interval(self.flash_hazards, 0.5)
        else:
            if self.hazard_timer:
                self.hazard_timer.cancel()
            self.high_button.set_state(False)
            self.tail_button.set_state(False)

    def flash_hazards(self, dt):
        """Blink hazard lights."""
        toggle = not self.high_button.state_on
        self.high_button.set_state(toggle)
        self.tail_button.set_state(not toggle)

    def press_horn(self, *args):
        """Horn press-and-hold logic."""
        if self.horn_button.state_on:  # Ensure it's only tied to the horn button
            return
        self.horn_button.set_state(True)
        if PINS["horn_400"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_400"], 1)
        if PINS["horn_500"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_500"], 1)

    def release_horn(self, *args):
        """Release horn logic."""
        self.horn_button.set_state(False)
        if PINS["horn_400"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_400"], 0)
        if PINS["horn_500"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_500"], 0)

class ATCDashApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pulse_count = 0
        self.last_time = time.time()

    def build(self):
        self.sm = ScreenManager(transition=SlideTransition())
        self.relay_screen = RelayControlScreen(name='relays')
        self.sm.add_widget(self.relay_screen)

        Window.bind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)
        self._touch_start_x = 0

        return self.sm

    def on_touch_down(self, window, touch):
        self._touch_start_x = touch.x

    def on_touch_up(self, window, touch):
        dx = touch.x - self._touch_start_x
        if abs(dx) > 50:
            if dx > 0:
                self.sm.current = "relays"

if __name__ == '__main__':
    Window.clearcolor = (0, 0, 0, 1)
    ATCDashApp().run()