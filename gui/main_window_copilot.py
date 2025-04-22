import os
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
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
        self.state_on = state
        self.source = self.on_icon if state else self.off_icon
        if self.gpio_pin is not None:
            lgpio.gpio_write(CHIP, self.gpio_pin, int(state))

class RelayControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)

        # Buttons for relay controls
        self.low_button = IconButton("low_on.png", "low_off.png", gpio_pin=PINS["low"])
        self.high_button = IconButton("high_on.png", "high_off.png", gpio_pin=PINS["high"])
        self.tail_button = IconButton("tail_on.png", "tail_off.png", gpio_pin=PINS["tail"])
        self.vape_button = IconButton("vape_on.png", "vape_off.png", gpio_pin=PINS["vape"])
        self.hazard_button = IconButton("haz_on.png", "haz_off.png")
        self.horn_button = IconButton("horn_on.png", "horn_off.png")

        # Add buttons to layout
        layout.add_widget(self.low_button)
        layout.add_widget(self.high_button)
        layout.add_widget(self.tail_button)
        layout.add_widget(self.vape_button)
        layout.add_widget(self.hazard_button)
        layout.add_widget(self.horn_button)

        self.add_widget(layout)

        # State and timers
        self.hazard_state = False
        self.hazard_timer = None

        # Attach logic to buttons
        self.low_button.on_press = self.low_beam_pressed
        self.high_button.on_press = self.high_beam_pressed
        self.hazard_button.on_press = self.toggle_hazards
        self.horn_button.bind(on_touch_down=self.press_horn, on_touch_up=self.release_horn)

    def low_beam_pressed(self, *args):
        if self.low_button.state_on:
            self.low_button.set_state(False)
            self.tail_button.set_state(False)
        else:
            self.low_button.set_state(True)
            self.high_button.set_state(False)
            self.tail_button.set_state(True)

    def high_beam_pressed(self, *args):
        if self.high_button.state_on:
            self.high_button.set_state(False)
            self.tail_button.set_state(False)
        else:
            self.high_button.set_state(True)
            self.low_button.set_state(False)
            self.tail_button.set_state(True)

    def toggle_hazards(self, *args):
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
        toggle = not self.high_button.state_on
        self.high_button.set_state(toggle)
        self.tail_button.set_state(not toggle)

    def press_horn(self, instance, touch):
        if not self.horn_button.collide_point(*touch.pos):
            return
        self.horn_button.set_state(True)
        if PINS["horn_400"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_400"], 1)
        if PINS["horn_500"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_500"], 1)

    def release_horn(self, instance, touch):
        if not self.horn_button.collide_point(*touch.pos):
            return
        self.horn_button.set_state(False)
        if PINS["horn_400"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_400"], 0)
        if PINS["horn_500"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_500"], 0)

class DashboardScreen(Screen):
    # Dashboard logic retained
    ...

class ATCDashApp(App):
    # Main app logic retained
    ...

if __name__ == '__main__':
    ATCDashApp().run()