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

def load_icon(path):
    return str(path) if Path(path).exists() else str(ICON_DIR / "default.png")

class IconButton(ButtonBehavior, Image):
    def __init__(self, on_icon, off_icon, gpio_pin=None, **kwargs):
        super().__init__(**kwargs)
        self.on_icon = load_icon(on_icon)
        self.off_icon = load_icon(off_icon)
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

        self.low_button = IconButton(ICON_DIR / "low_on.png", ICON_DIR / "low_off.png", gpio_pin=PINS["low"])
        self.high_button = IconButton(ICON_DIR / "high_on.png", ICON_DIR / "high_off.png", gpio_pin=PINS["high"])
        self.tail_button = IconButton(ICON_DIR / "tail_on.png", ICON_DIR / "tail_off.png", gpio_pin=PINS["tail"])
        self.vape_button = IconButton(ICON_DIR / "vape_on.png", ICON_DIR / "vape_off.png", gpio_pin=PINS["vape"])
        self.hazard_button = IconButton(ICON_DIR / "haz_on.png", ICON_DIR / "haz_off.png")
        self.horn_button = IconButton(ICON_DIR / "horn_on.png", ICON_DIR / "horn_off.png")

        self.low_button.on_press = self.low_beam_pressed
        self.high_button.on_press = self.high_beam_pressed
        self.hazard_button.on_press = self.toggle_hazards
        self.horn_button.bind(on_touch_down=self.press_horn, on_touch_up=self.release_horn)

        layout.add_widget(self.low_button)
        layout.add_widget(self.high_button)
        layout.add_widget(self.tail_button)
        layout.add_widget(self.vape_button)
        layout.add_widget(self.hazard_button)
        layout.add_widget(self.horn_button)

        self.add_widget(layout)

        self.hazard_state = False
        self.hazard_timer = None

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
            self.tail_button.set_state(False)
            self.high_button.set_state(False)

    def flash_hazards(self, dt):
        toggle = not self.high_button.state_on
        self.high_button.set_state(toggle)
        self.tail_button.set_state(not toggle)

    def press_horn(self, *args):
        self.horn_button.set_state(True)
        if PINS["horn_400"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_400"], 1)
        if PINS["horn_500"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_500"], 1)

    def release_horn(self, *args):
        self.horn_button.set_state(False)
        if PINS["horn_400"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_400"], 0)
        if PINS["horn_500"] is not None:
            lgpio.gpio_write(CHIP, PINS["horn_500"], 0)

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.uix.gridlayout import GridLayout
        from kivy.uix.widget import Widget
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        from kivy.graphics import Color, Rectangle

        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # RPM Bar styled like TS Dash
        self.rpm_bar = ProgressBar(max=7000, value=0, size_hint_y=0.06)
        layout.add_widget(self.rpm_bar)

        # GridLayout for TS-style tiles
        tile_grid = GridLayout(cols=3, spacing=20, size_hint_y=0.9)

        def create_tile(label_text):
            box = BoxLayout(orientation='vertical', padding=10, size_hint=(1, 1))
            with box.canvas.before:
                Color(0.1, 0.1, 0.1, 1)
                box.bg_rect = Rectangle(size=box.size, pos=box.pos)
                box.bind(size=lambda instance, value: setattr(box.bg_rect, 'size', value))
                box.bind(pos=lambda instance, value: setattr(box.bg_rect, 'pos', value))
            value_label = Label(text="0", font_size='36sp', bold=True, halign='center')
            title_label = Label(text=label_text, font_size='18sp', halign='center')
            value_label.bind(size=value_label.setter('text_size'))
            title_label.bind(size=title_label.setter('text_size'))
            box.add_widget(value_label)
            box.add_widget(title_label)
            return box, value_label

        self.rpm_tile, self.rpm_value = create_tile("RPM")
        self.speed_tile, self.speed_value = create_tile("Speed (MPH)")
        self.gear_tile, self.gear_value = create_tile("Gear")
        self.afr_tile, self.afr_value = create_tile("AFR")
        self.egt_tile, self.egt_value = create_tile("EGT (°C)")
        self.temp_tile, self.temp_value = create_tile("Head Temp (°C)")

        for tile in [self.rpm_tile, self.speed_tile, self.gear_tile,
                     self.afr_tile, self.egt_tile, self.temp_tile]:
            tile_grid.add_widget(tile)

        layout.add_widget(tile_grid)
        self.add_widget(layout)

    def update_dashboard(self, speed, rpm, afr, gear, head_temp):
        egt = head_temp + 300
        self.rpm_bar.value = rpm

        self.rpm_value.text = f"{rpm}"
        self.speed_value.text = f"{speed}"
        self.gear_value.text = f"{gear}"
        self.afr_value.text = f"{afr:.2f}"
        self.egt_value.text = f"{egt}"
        self.temp_value.text = f"{head_temp}"

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

    def on_touch_down(self, window, touch):
        self._touch_start_x = touch.x

    def on_touch_up(self, window, touch):
        dx = touch.x - self._touch_start_x
        if abs(dx) > 50:
            if dx > 0:
                self.switch_screen("left")
            else:
                self.switch_screen("right")

    def switch_screen(self, direction):
        if direction == "left":
            self.sm.current = "relays"
        elif direction == "right":
            self.sm.current = "dashboard"

    def poll_hall_sensor(self, dt):
        level = lgpio.gpio_read(CHIP, HALL_GPIO)
        if level == 0:
            self.pulse_count += 1

    def update_speed(self, dt):
        now = time.time()
        elapsed = now - self.last_time
        self.last_time = now
        rotations = self.pulse_count / PULSES_PER_REV
        distance_m = rotations * WHEEL_CIRCUMFERENCE_M
        speed_mps = distance_m / elapsed if elapsed else 0
        speed_mph = speed_mps * 2.23694
        self.pulse_count = 0

        self.dashboard_screen.update_dashboard(
            speed=int(speed_mph), rpm=3100, afr=14.2, gear='3', head_temp=132
        )

    def on_stop(self):
        for pin in PINS.values():
            if pin is not None:
                lgpio.gpio_write(CHIP, pin, 0)
        lgpio.gpiochip_close(CHIP)

if __name__ == '__main__':
    Window.clearcolor = (0, 0, 0, 1)
    ATCDashApp().run()
