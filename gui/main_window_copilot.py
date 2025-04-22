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

class RelayControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = GridLayout(cols=3, spacing=20, padding=20)

        # Add buttons with labels
        self.add_relay_button(layout, "Low Beam", "low_on.png", "low_off.png", PINS["low"])
        self.add_relay_button(layout, "High Beam", "high_on.png", "high_off.png", PINS["high"])
        self.add_relay_button(layout, "Tail Light", "tail_on.png", "tail_off.png", PINS["tail"])
        self.add_relay_button(layout, "Vape Outlet", "vape_on.png", "vape_off.png", PINS["vape"])
        self.add_relay_button(layout, "Hazards", "haz_on.png", "haz_off.png", None)
        self.add_relay_button(layout, "Horn", "horn_on.png", "horn_off.png", None)

        self.add_widget(layout)

    def add_relay_button(self, layout, label_text, on_icon, off_icon, gpio_pin):
        # Create the button
        button = IconButton(on_icon, off_icon, gpio_pin)
        label = Label(
            text=label_text,
            font_size="14sp",
            halign="center",
            valign="middle",
            size_hint=(1, 0.2),
        )

        # Add to layout
        layout.add_widget(button)
        layout.add_widget(label)

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.progressbar import ProgressBar
        from kivy.uix.gridlayout import GridLayout

        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # RPM Bar styled like TS Dash
        self.rpm_bar = ProgressBar(max=7000, value=0, size_hint_y=0.06)
        layout.add_widget(self.rpm_bar)

        # GridLayout for TS-style tiles
        tile_grid = GridLayout(cols=3, spacing=20, size_hint_y=0.9)

        def create_tile(label_text):
            box = BoxLayout(orientation='vertical', padding=10, size_hint=(1, 1))
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