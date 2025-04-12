
import os
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty
from kivy.core.window import Window

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

def set_gpio(pin, state):
    if GPIO:
        GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

class ImageButton(ButtonBehavior, Image):
    pass

class RelayControlScreen(FloatLayout):
    ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'icons')

    high_beams_on = BooleanProperty(False)
    low_beams_on = BooleanProperty(False)
    tail_on = BooleanProperty(False)
    haz_on = BooleanProperty(False)
    horn_on = BooleanProperty(False)
    vape_on = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = (0, 0, 0, 1)

        self.status_label = Label(text="", size_hint=(1, 0.1), pos_hint={'top': 1}, color=(1, 1, 1, 1))
        self.add_widget(self.status_label)

        self.button_layout = BoxLayout(orientation='horizontal', spacing=30, size_hint=(1, 0.9))
        self.add_widget(self.button_layout)

        self.low_beam_image = self.add_control_button("low_beam", self.toggle_low_beams)
        self.high_beam_image = self.add_control_button("high_beam", self.toggle_high_beams)
        self.tail_light_image = self.add_control_button("tail_light", self.toggle_tail_light)
        self.vape_image = self.add_control_button("vape", self.toggle_vape)
        self.haz_image = self.add_control_button("hazard", self.toggle_hazards)
        self.horn_image = self.add_control_button("horn", self.press_horn, release_fn=self.release_horn)

        self.hazard_timer = None

    def add_control_button(self, control_name, fn, release_fn=None):
        icon = self.get_icon(control_name, False)
        image = ImageButton(source=icon)
        image.bind(on_press=fn)
        if release_fn:
            image.bind(on_release=release_fn)
        self.button_layout.add_widget(image)
        return image

    def get_icon(self, control_name, state):
        path = os.path.join(RelayControlScreen.ICONS_DIR, f"{control_name}_{'on' if state else 'off'}.png")
        return path if os.path.exists(path) else os.path.join(RelayControlScreen.ICONS_DIR, 'default.png')

    def toggle_low_beams(self, instance):
        if self.haz_on:
            return
        self.low_beams_on = not self.low_beams_on
        if self.low_beams_on:
            self.high_beams_on = False
        self.update_high_low_interlock()
        self.refresh_icons()

    def toggle_high_beams(self, instance):
        if self.haz_on:
            return
        self.high_beams_on = not self.high_beams_on
        if self.high_beams_on:
            self.low_beams_on = False
        self.update_high_low_interlock()
        self.refresh_icons()

    def update_high_low_interlock(self):
        if self.low_beams_on or self.high_beams_on:
            self.tail_on = True
        else:
            self.tail_on = False

    def toggle_tail_light(self, instance):
        if self.haz_on:
            return
        self.tail_on = not self.tail_on
        self.refresh_icons()

    def toggle_vape(self, instance):
        self.vape_on = not self.vape_on
        self.refresh_icons()

    def toggle_hazards(self, instance):
        self.haz_on = not self.haz_on
        if self.haz_on:
            self.hazard_timer = Clock.schedule_interval(self.flash_hazard_lights, 0.5)
        else:
            if self.hazard_timer:
                self.hazard_timer.cancel()
            self.low_beams_on = False
            self.high_beams_on = False
            self.tail_on = False
        self.refresh_icons()

    def flash_hazard_lights(self, dt):
        self.tail_on = not self.tail_on
        self.high_beams_on = not self.high_beams_on
        self.refresh_icons()

    def press_horn(self, instance):
        self.horn_on = True
        self.refresh_icons()

    def release_horn(self, instance):
        self.horn_on = False
        self.refresh_icons()

    def refresh_icons(self):
        self.low_beam_image.source = self.get_icon("low_beam", self.low_beams_on)
        self.high_beam_image.source = self.get_icon("high_beam", self.high_beams_on)
        self.tail_light_image.source = self.get_icon("tail_light", self.tail_on)
        self.vape_image.source = self.get_icon("vape", self.vape_on)
        self.haz_image.source = self.get_icon("hazard", self.haz_on)
        self.horn_image.source = self.get_icon("horn", self.horn_on)

class RelayControlApp(App):
    def build(self):
        print(">>> DASH STARTING UP")
        return RelayControlScreen()

if __name__ == '__main__':
    RelayControlApp().run()
