# [Merged GUI with ScreenManager and Dashboard]
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import pigpio
pi = pigpio.pi()
import time
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.config import Config
from kivy.core.window import Window
from pathlib import Path
import pigpio
import os
from time import time

print(">>> DASH STARTING UP")

Config.set('graphics', 'fullscreen', 'auto')
Window.clearcolor = (0, 0, 0, 1)

icon_dir = Path(__file__).parent / "icons"

pins = {
    "low": 4,
    "high": 26,
    "tail": 27,
    "vape": 22,
    "hazards": None,
    "horn_500": 21,
    "horn_400": 13
}

pi = pigpio.pi()
for name, pin in pins.items():
    if pin is not None:
        lgpio.gpio_claim_output(chip, pin, 0)

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

class RelayControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)

        self.low_button = IconButton(str(icon_dir / "low_on.png"), str(icon_dir / "low_off.png"), gpio_pin=pins["low"])
        self.high_button = IconButton(str(icon_dir / "high_on.png"), str(icon_dir / "high_off.png"), gpio_pin=pins["high"])
        self.tail_button = IconButton(str(icon_dir / "tail_on.png"), str(icon_dir / "tail_off.png"), gpio_pin=pins["tail"])
        self.vape_button = IconButton(str(icon_dir / "vape_on.png"), str(icon_dir / "vape_off.png"), gpio_pin=pins["vape"])
        self.hazard_button = IconButton(str(icon_dir / "haz_on.png"), str(icon_dir / "haz_off.png"))
        self.horn_button = IconButton(str(icon_dir / "horn_on.png"), str(icon_dir / "horn_off.png"))

        self.low_button.on_release = self.low_beam_pressed
        self.high_button.on_release = self.high_beam_pressed
        self.hazard_button.on_release = self.toggle_hazards
        self.horn_button.on_press = self.press_horn
        self.horn_button.on_release = self.release_horn

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


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        layout.add_widget(Label(text="Live Dashboard", font_size=24))
        self.speed_label = Label(text="Speed: 0 MPH", font_size=20)
        self.rpm_label = Label(text="RPM: 0", font_size=20)
        self.afr_label = Label(text="AFR: 14.7", font_size=20)
        self.gear_label = Label(text="Gear: N", font_size=20)
        self.temp_label = Label(text="Head Temp: 0°C", font_size=20)
        for widget in [self.speed_label, self.rpm_label, self.afr_label, self.gear_label, self.temp_label]:
            layout.add_widget(widget)
        self.add_widget(layout)

    def update_dashboard(self, speed, rpm, afr, gear, head_temp):
        self.speed_label.text = f"Speed: {speed} MPH"
        self.rpm_label.text = f"RPM: {rpm}"
        self.afr_label.text = f"AFR: {afr:.2f}"
        self.gear_label.text = f"Gear: {gear}"
        self.temp_label.text = f"Head Temp: {head_temp}°C"



# Setup GPIO for Hall Effect Sensor
HALL_GPIO = 17  # GPIO pin for Hall sensor
WHEEL_CIRCUMFERENCE_M = 1.6  # adjust as needed
PULSES_PER_REV = 1
lgpio.gpio_set_alert_func(chip, 17, on_pulse)

        chip, gpio, level, tick = a
        if level == 0:
        self.pulse_count += 1
    app = App.get_running_app()
    if level == 0:
        app.pulse_count += 1
    if level == 0:
        pulse_count += 1
    pulse_count += 1


class ATCDashApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pulse_count = 0
        self.last_time = time.time()
    def build(self):
        self.sm = ScreenManager(transition=SwapTransition())
        self.relay_screen = RelayControlScreen(name='relays')
        self.dashboard_screen = DashboardScreen(name='dashboard')
        self.sm.add_widget(self.relay_screen)
        self.sm.add_widget(self.dashboard_screen)

        root = BoxLayout(orientation='vertical')
        toggle_btn = Button(text="Switch Screen", size_hint_y=None, height=50)
        toggle_btn.bind(on_press=self.toggle_screen)
        root.add_widget(toggle_btn)
        root.add_widget(self.sm)

        Clock.schedule_interval(self.poll_hall_sensor, 0.05)
        pi.set_mode(17, pigpio.INPUT)
        pi.set_pull_up_down(17, pigpio.PUD_UP)
        pi.callback(17, pigpio.FALLING_EDGE, lambda gpio, level, tick: self.increment_pulse())
        Clock.schedule_interval(self.update_speed, 1)
        return root

    def toggle_screen(self, *args):
        self.sm.current = 'dashboard' if self.sm.current == 'relays' else 'relays'

    def increment_pulse(self):
        self.pulse_count += 1

    def update_speed(self, dt):
        now = time.time()
        elapsed = now - last_time
        last_time = now
        rotations = pulse_count / PULSES_PER_REV
        distance_m = rotations * WHEEL_CIRCUMFERENCE_M
        speed_mps = distance_m / elapsed
        speed_mph = speed_mps * 2.23694
        self.dashboard_screen.update_dashboard(
            speed=int(speed_mph), rpm=3100, afr=14.2, gear='3', head_temp=132
        )

    def mock_sensor_data(self, dt):
        speed = 25
        rpm = 3100
        afr = 14.2
        gear = "3"
        head_temp = 132
        self.dashboard_screen.update_dashboard(speed, rpm, afr, gear, head_temp)

    def on_stop(self):
        for pin in pins.values():
            if pin is not None:
                lgpio.gpio_write(chip, pin, 0)
        lgpio.gpiochip_close(chip)


if __name__ == '__main__':
    ATCDashApp().run()
