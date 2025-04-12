from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.core.window import Window
import RPi.GPIO as GPIO
import os
from pathlib import Path

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# --- Button Configuration ---
BUTTON_CONFIG = [
    {"name": "low", "pin": 4, "on_icon": "low_on.png", "off_icon": "low_off.png"},
    {"name": "high", "pin": 26, "on_icon": "high_on.png", "off_icon": "high_off.png"},
    {"name": "tail", "pin": 27, "on_icon": "tail_on.png", "off_icon": "tail_off.png"},
    {"name": "vape", "pin": 22, "on_icon": "vape_on.png", "off_icon": "vape_off.png"},
    {"name": "power", "pin": None, "on_icon": "power_on.png", "off_icon": "power_off.png"},
    {"name": "hazard", "pin": None, "on_icon": "haz_on.png", "off_icon": "haz_off.png"},
]

class IconButton(ButtonBehavior, Image):
    def __init__(self, on_icon, off_icon, gpio_pin=None, **kwargs):
        super().__init__(**kwargs)
        self.on_icon = on_icon
        self.off_icon = off_icon
        self.gpio_pin = gpio_pin
        self.is_on = False
        self.source = str(self.off_icon)
        if self.gpio_pin is not None:
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            GPIO.output(self.gpio_pin, GPIO.LOW)

    def on_press(self):
        self.toggle()

    def toggle(self):
        self.is_on = not self.is_on
        self.source = str(self.on_icon if self.is_on else self.off_icon)
        if self.gpio_pin is not None:
            GPIO.output(self.gpio_pin, GPIO.HIGH if self.is_on else GPIO.LOW)

class RelayControlApp(App):
    def build(self):
        print(">>> DASH STARTING UP")
        self.icon_dir = Path(__file__).parent / "icons"

        self.buttons = {}
        self.hazard_state = False
        self.hazard_event = None

        layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)

        for config in BUTTON_CONFIG:
            on_icon = self.icon_dir / config["on_icon"]
            off_icon = self.icon_dir / config["off_icon"]
            pin = config["pin"]

            button = IconButton(on_icon=on_icon, off_icon=off_icon, gpio_pin=pin)
            self.buttons[config["name"]] = button
            layout.add_widget(button)

        # Link interdependent logic
        Clock.schedule_interval(self.update_logic, 0.1)

        return layout

    def update_logic(self, dt):
        # High/low logic (mutual exclusive)
        low = self.buttons["low"]
        high = self.buttons["high"]
        tail = self.buttons["tail"]
        hazard = self.buttons["hazard"]

        if low.is_on and high.is_on:
            high.is_on = False
            high.source = str(high.off_icon)
            GPIO.output(high.gpio_pin, GPIO.LOW)

        # Tail on if either low or high is on
        tail_should_be_on = low.is_on or high.is_on
        if tail.is_on != tail_should_be_on:
            tail.is_on = tail_should_be_on
            tail.source = str(tail.on_icon if tail_should_be_on else tail.off_icon)
            GPIO.output(tail.gpio_pin, GPIO.HIGH if tail_should_be_on else GPIO.LOW)

        # Hazard flash logic
        if hazard.is_on and self.hazard_event is None:
            self.hazard_event = Clock.schedule_interval(self.toggle_hazard_flash, 0.5)
        elif not hazard.is_on and self.hazard_event:
            self.hazard_event.cancel()
            self.hazard_event = None
            # Turn off flashing outputs
            GPIO.output(high.gpio_pin, GPIO.LOW)
            GPIO.output(tail.gpio_pin, GPIO.LOW)

    def toggle_hazard_flash(self, dt):
        high = self.buttons["high"]
        tail = self.buttons["tail"]
        # Alternate flashing
        high_state = GPIO.input(high.gpio_pin)
        new_high_state = GPIO.LOW if high_state else GPIO.HIGH
        new_tail_state = GPIO.HIGH if high_state else GPIO.LOW

        GPIO.output(high.gpio_pin, new_high_state)
        GPIO.output(tail.gpio_pin, new_tail_state)

        high.source = str(high.on_icon if new_high_state else high.off_icon)
        tail.source = str(tail.on_icon if new_tail_state else tail.off_icon)

if __name__ == '__main__':
    RelayControlApp().run()