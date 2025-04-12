import kivy
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from pathlib import Path
import lgpio
import os
from time import time

print(">>> DASH STARTING UP")

# Setup full screen window
Config.set('graphics', 'fullscreen', 'auto')
Window.clearcolor = (0, 0, 0, 1)

# Icon path
icon_dir = Path(__file__).parent / "icons"

# GPIO pin assignments
pins = {
    "low": 4,
    "high": 26,
    "tail": 27,
    "vape": 22,
    "hazards": None,
    "horn_500": 21,
    "horn_400": 13
}

# Initialize GPIO
chip = lgpio.gpiochip_open(0)
for name, pin in pins.items():
    if pin is not None:
        lgpio.gpio_claim_output(chip, pin, 0)

# Button class with touch debounce
class IconButton(ButtonBehavior, Image):
    def __init__(self, on_icon, off_icon, gpio_pin=None, **kwargs):
        super().__init__(**kwargs)
        self.on_icon = on_icon
        self.off_icon = off_icon
        self.gpio_pin = gpio_pin
        self.state_on = False
        self.last_touch_time = 0
        self.update_icon()

    def on_release(self):
        now = time()
        if now - self.last_touch_time < 0.25:
            return
        self.last_touch_time = now
        self.toggle()

    def toggle(self):
        self.state_on = not self.state_on
        self.update_icon()
        if self.gpio_pin is not None:
            lgpio.gpio_write(chip, self.gpio_pin, 1 if self.state_on else 0)

    def set_state(self, state: bool):
        self.state_on = state
        self.update_icon()
        if self.gpio_pin is not None:
            lgpio.gpio_write(chip, self.gpio_pin, 1 if state else 0)

    def update_icon(self):
        self.source = self.on_icon if self.state_on else self.off_icon

# App class
class RelayControlApp(App):
    def build(self):
        self.hazard_state = False
        self.hazard_timer = None

        layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)

        self.low_button = IconButton(
            on_icon=str(icon_dir / "low_on.png"),
            off_icon=str(icon_dir / "low_off.png"),
            gpio_pin=pins["low"]
        )

        self.high_button = IconButton(
            on_icon=str(icon_dir / "high_on.png"),
            off_icon=str(icon_dir / "high_off.png"),
            gpio_pin=pins["high"]
        )

        self.tail_button = IconButton(
            on_icon=str(icon_dir / "tail_on.png"),
            off_icon=str(icon_dir / "tail_off.png"),
            gpio_pin=pins["tail"]
        )

        self.vape_button = IconButton(
            on_icon=str(icon_dir / "vape_on.png"),
            off_icon=str(icon_dir / "vape_off.png"),
            gpio_pin=pins["vape"]
        )

        self.hazard_button = IconButton(
            on_icon=str(icon_dir / "haz_on.png"),
            off_icon=str(icon_dir / "haz_off.png"),
            gpio_pin=None
        )
        self.hazard_button.on_release = self.toggle_hazards

        self.horn_button = IconButton(
            on_icon=str(icon_dir / "horn_on.png"),
            off_icon=str(icon_dir / "horn_off.png"),
            gpio_pin=None
        )
        self.horn_button.on_press = self.press_horn
        self.horn_button.on_release = self.release_horn

        self.low_button.on_release = self.low_beam_pressed
        self.high_button.on_release = self.high_beam_pressed

        layout.add_widget(self.low_button)
        layout.add_widget(self.high_button)
        layout.add_widget(self.tail_button)
        layout.add_widget(self.vape_button)
        layout.add_widget(self.hazard_button)
        layout.add_widget(self.horn_button)

        return layout

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
            self.hazard_timer = Clock.schedule_interval(self.flash_hazards, 0.5)
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

    def on_stop(self):
        for pin in pins.values():
            if pin is not None:
                lgpio.gpio_write(chip, pin, 0)
        lgpio.gpiochip_close(chip)

if __name__ == '__main__':
    RelayControlApp().run()
