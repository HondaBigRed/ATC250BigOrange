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
        self.horn_pressed_time = None
        self.horn_sequence_event = None
        self.horn_sequence_index = 0
        self.horn_pattern = [
            (1, 1, 0.2), (0, 0, 0.15),
            (1, 1, 0.2), (0, 0, 0.15),
            (1, 0, 0.1), (0, 1, 0.1),
            (1, 1, 0.3), (0, 0, 0.2)
        ]

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
        self.horn_button.on_press = self.start_horn_press
        self.horn_button.on_release = self.end_horn_press

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

    def start_horn_press(self, *args):
        self.horn_pressed_time = time()

    def end_horn_press(self, *args):
        held_time = time() - self.horn_pressed_time if self.horn_pressed_time else 0
        self.horn_pressed_time = None
        if held_time < 1:
            self.start_horn_sequence(loop=False)
        else:
            self.start_horn_sequence(loop=True)

    def start_horn_sequence(self, loop=False):
        self.horn_sequence_index = 0
        self.horn_loop = loop
        self.horn_sequence_event = Clock.schedule_once(self.run_horn_step, 0)

    def run_horn_step(self, dt):
        if self.horn_sequence_index >= len(self.horn_pattern):
            if self.horn_loop:
                self.horn_sequence_index = 0
                Clock.schedule_once(self.run_horn_step, 0)
            else:
                self.set_horn_output(0, 0)
                return
        else:
            a, b, duration = self.horn_pattern[self.horn_sequence_index]
            self.set_horn_output(a, b)
            self.horn_sequence_index += 1
            Clock.schedule_once(self.run_horn_step, duration)

    def set_horn_output(self, horn400, horn500):
        lgpio.gpio_write(chip, pins["horn_400"], horn400)
        lgpio.gpio_write(chip, pins["horn_500"], horn500)

    def on_stop(self):
        for pin in pins.values():
            if pin is not None:
                lgpio.gpio_write(chip, pin, 0)
        lgpio.gpiochip_close(chip)

if __name__ == '__main__':
    RelayControlApp().run()
