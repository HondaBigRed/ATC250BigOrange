import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.label import Label

from config import (
    USE_GPIO,
    SIM_MODE,
    setup_gpio,
    gpio_write,
    simulate_rpm,
    simulate_speed,
    simulate_afr,
    PINS
)

# Initialize GPIO if enabled
h = setup_gpio()

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.rpm_label = Label(text="RPM: ---", font_size='30sp')
        self.speed_label = Label(text="Speed: --- km/h", font_size='30sp')
        self.afr_label = Label(text="AFR: ---", font_size='30sp')

        self.layout.add_widget(self.rpm_label)
        self.layout.add_widget(self.speed_label)
        self.layout.add_widget(self.afr_label)

        self.add_widget(self.layout)

        Clock.schedule_interval(self.update_dashboard, 0.5)

    def update_dashboard(self, dt):
        if SIM_MODE:
            rpm = simulate_rpm()
            speed = simulate_speed()
            afr = simulate_afr()
        else:
            rpm = 0      # Replace with real sensor reading
            speed = 0.0  # Replace with real sensor reading
            afr = 0.0    # Replace with real sensor reading

        self.rpm_label.text = f"RPM: {rpm}"
        self.speed_label.text = f"Speed: {speed} km/h"
        self.afr_label.text = f"AFR: {afr}"

class ControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.low_beam_button = Button(text="Toggle Low Beam", font_size='25sp')
        self.low_beam_button.bind(on_press=self.toggle_low_beam)

        self.layout.add_widget(self.low_beam_button)
        self.add_widget(self.layout)

    def toggle_low_beam(self, instance):
        gpio_write(h, PINS['low_beam'], 1)  # Replace with toggle logic later

class DashboardApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(ControlScreen(name='controls'))
        return sm

if __name__ == '__main__':
    DashboardApp().run()
