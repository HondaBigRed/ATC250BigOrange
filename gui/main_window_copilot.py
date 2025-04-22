import os
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
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

        # Add buttons with logic
        self.low_button = self.add_relay_button(layout, "Low Beam", "low_on.png", "low_off.png", PINS["low"])
        self.high_button = self.add_relay_button(layout, "High Beam", "high_on.png", "high_off.png", PINS["high"])
        self.tail_button = self.add_relay_button(layout, "Tail Light", "tail_on.png", "tail_off.png", PINS["tail"])
        self.vape_button = self.add_relay_button(layout, "Vape Outlet", "vape_on.png", "vape_off.png", PINS["vape"])
        self.hazard_button = self.add_relay_button(layout, "Hazards", "haz_on.png", "haz_off.png", None)
        self.horn_button = self.add_relay_button(layout, "Horn", "horn_on.png", "horn_off.png", None)

        self.hazard_state = False
        self.hazard_timer = None

        # Add custom logic for specific buttons
        self.low_button.on_press = self.low_beam_pressed
        self.high_button.on_press = self.high_beam_pressed
        self.hazard_button.on_press = self.toggle_hazards
        self.horn_button.bind(on_touch_down=self.press_horn, on_touch_up=self.release_horn)

        self.add_widget(layout)

    def add_relay_button(self, layout, label_text, on_icon, off_icon, gpio_pin):
        """Helper to create and add relay buttons with labels."""
        button = IconButton(on_icon, off_icon, gpio_pin)
        label = Label(
            text=label_text,
            font_size="14sp",
            halign="center",
            valign="middle",
            size_hint=(1, 0.2),
        )
        layout.add_widget(button)
        layout.add_widget(label)
        return button

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

# ... The rest of the DashboardScreen and ATCDashApp classes remain unchanged ...

class ATCDashApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pulse_count = 0
        self.last_time = time.time()

    def build(self):
        self.sm = ScreenManager(transition=SlideTransition())
        self.relay_screen = RelayControlScreen(name='relays')
        self.dashboard_screen = DashboardScreen(name='dashboard')
        self.sm.add_widget(self.relay_screen)
        self.sm.add_widget(self.dashboard_screen)

        Window.bind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)
        self._touch_start_x = 0

        Clock.schedule_interval(self.update_speed, 1)
        Clock.schedule_interval(self.poll_hall_sensor, 0.05)

        return self.sm

    # Additional logic for screen switching and GPIO updates is unchanged...

if __name__ == '__main__':
    Window.clearcolor = (0, 0, 0, 1)
    ATCDashApp().run()