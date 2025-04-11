import os.path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import ButtonBehavior  # Import ButtonBehavior


class ImageButton(ButtonBehavior, Image):  # Create a custom ImageButton
    pass


class RelayControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        # Header
        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        header_label = Label(text="Relay Control", font_size=24)
        header_box.add_widget(header_label)
        self.add_widget(header_box)

        # Relay Control Buttons
        relay_button_box = BoxLayout(orientation='vertical', size_hint_y=None, height=400)

        # --- Low Beam Control ---
        low_beam_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.low_beams_on = BooleanProperty(False)  # Initial state is OFF
        self.low_beam_image = ImageButton(source=self.get_low_beam_icon(), size_hint_x=None, width=100)
        self.low_beam_image.bind(on_press=self.toggle_low_beams)
        low_beam_box.add_widget(self.low_beam_image)
        relay_button_box.add_widget(low_beam_box)

        # --- High Beam Control ---
        high_beam_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.high_beams_on = BooleanProperty(False)  # Initial state is OFF
        self.high_beam_image = ImageButton(source=self.get_high_beam_icon(), size_hint_x=None, width=100)
        self.high_beam_image.bind(on_press=self.toggle_high_beams)
        high_beam_box.add_widget(self.high_beam_image)
        relay_button_box.add_widget(high_beam_box)

        # --- Taillight Control ---
        tail_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.tail_on = BooleanProperty(True)  # Initial state is ON
        self.tail_image = ImageButton(source=self.get_tail_icon(), size_hint_x=None, width=100)
        self.tail_image.bind(on_press=self.toggle_tail)
        tail_box.add_widget(self.tail_image)
        relay_button_box.add_widget(tail_box)

        # --- Hazard Light Control ---
        haz_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.haz_on = BooleanProperty(False)  # Initial state is OFF
        self.haz_image = ImageButton(source=self.get_haz_icon(), size_hint_x=None, width=100)
        self.haz_image.bind(on_press=self.toggle_haz)
        haz_box.add_widget(self.haz_image)
        relay_button_box.add_widget(haz_box)

        # --- Horn Control ---
        horn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.horn_on = BooleanProperty(False)  # Initial state is OFF
        self.horn_image = ImageButton(source=self.get_horn_icon(), size_hint_x=None, width=100)
        self.horn_image.bind(on_press=self.toggle_horn)
        self.horn_image.bind(on_release=self.horn_released)
        horn_box.add_widget(self.horn_image)
        relay_button_box.add_widget(horn_box)

        # --- Vape Control ---
        vape_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.vape_on = BooleanProperty(True)  # Initial state is ON
        self.vape_image = ImageButton(source=self.get_vape_icon(), size_hint_x=None, width=100)
        self.vape_image.bind(on_press=self.toggle_vape)
        vape_box.add_widget(self.vape_image)
        relay_button_box.add_widget(vape_box)

        self.add_widget(relay_button_box)

        # Schedule the hazard light flashing
        self.flash_event = None  # Store the event for later unscheduling

    def on_kv_post(self, base_widget):
        # After all widgets are created, set initial icon states
        # Clock.schedule_once(self.set_initial_icon_states, 0) # Schedule after initialization
        pass  # Do nothing here

    def get_low_beam_icon(self):
        return os.path.join(os.path.dirname(__file__),
                            'icons/low_on.png' if self.low_beams_on else 'icons/low_off.png')

    def toggle_low_beams(self, instance, touch):  # Added touch argument
        # Placeholder: Replace with actual relay control logic
        if instance.collide_point(*touch.pos):
            self.low_beams_on = not self.low_beams_on
            self.low_beam_image.source = self.get_low_beam_icon()
            self.update_high_low_interlock()
            print(f"Toggling low beams. New state: {'ON' if self.low_beams_on else 'OFF'}")

    def get_high_beam_icon(self):
        return os.path.join(os.path.dirname(__file__),
                            'icons/high_on.png' if self.high_beams_on else 'icons/high_off.png')

    def toggle_high_beams(self, instance, touch):  # Added touch argument
        # Placeholder: Replace with actual relay control logic
        if instance.collide_point(*touch.pos):
            self.high_beams_on = not self.high_beams_on
            self.high_beam_image.source = self.get_high_beam_icon()
            self.update_high_low_interlock()
            print(f"Toggling high beams. New state: {'ON' if self.high_beams_on else 'OFF'}")

    def update_high_low_interlock(self):
        # Ensure only one of high or low beams is on
        if self.high_beams_on and self.low_beams_on:
            if self.high_beams_on:
                self.low_beams_on = False
                self.low_beam_image.source = self.get_low_beam_icon()
            elif self.low_beams_on:
                self.high_beams_on = False
                self.high_beam_image.source = self.get_high_beam_icon()

    def get_tail_icon(self):
        return os.path.join(os.path.dirname(__file__), 'icons/tail_on.png' if self.tail_on else 'icons/tail_off.png')

    def toggle_tail(self, instance, touch):  # Added touch argument
        # Placeholder: Replace with actual relay control logic
        if instance.collide_point(*touch.pos):
            self.tail_on = not self.tail_on
            self.tail_image.source = self.get_tail_icon()
            if self.haz_on:
                self.tail_image.disabled = self.tail_on  # Disable tail lights
            print(f"Toggling taillights. New state: {'ON' if self.tail_on else 'OFF'}")

    def get_haz_icon(self):
        return os.path.join(os.path.dirname(__file__),
                            'icons/haz_on.png' if self.haz_on else 'icons/haz_off.png')

    def toggle_haz(self, instance, touch):  # Added touch argument
        # Placeholder: Replace with actual relay control logic
        if instance.collide_point(*touch.pos):
            self.haz_on = not self.haz_on
            self.haz_image.source = self.get_haz_icon()

            if self.haz_on:
                # Start flashing
                self.flash_event = Clock.schedule_interval(self.flash_hazard_lights, 0.5)  # 2Hz
                # Disable other buttons
                self.low_beam_image.disabled = True
                self.high_beam_image.disabled = True
                self.tail_image.disabled = True
                self.vape_image.disabled = True
                print("Starting hazard lights")
            else:
                # Stop flashing
                if self.flash_event:
                    Clock.unschedule(self.flash_event)
                    self.flash_event = None
                # Re-enable other buttons
                self.low_beam_image.disabled = False
                self.high_beam_image.disabled = False
                self.tail_image.disabled = False
                self.vape_image.disabled = False
                print("Stopping hazard lights")

    def flash_hazard_lights(self, dt):
        # Placeholder: Implement hazard light flashing logic
        # This function is called by the Clock every 0.5 seconds
        self.high_beams_on = not self.high_beams_on
        self.tail_on = not self.tail_on
        self.high_beam_image.source = self.get_high_beam_icon()
        self.tail_image.source = self.get_tail_icon()

    def get_horn_icon(self):
        return os.path.join(os.path.dirname(__file__),
                            'icons/horn_on.png' if self.horn_on else 'icons/horn_off.png')

    def toggle_horn(self, instance, touch):  # Added touch argument
        # Placeholder: Implement momentary horn control
        if instance.collide_point(*touch.pos):
            self.horn_on = True  # Set to true on press
            self.horn_image.source = self.get_horn_icon()
            print("Horn ON")

    def horn_released(self, instance, touch):  # Added touch argument
        # Placeholder: Implement momentary horn control
        if instance.collide_point(*touch.pos):
            self.horn_on = False  # Set to false on release
            self.horn_image.source = self.get_horn_icon()
            print("Horn OFF")

    def get_vape_icon(self):
        return os.path.join(os.path.dirname(__file__),
                            'icons/vape_on.png' if self.vape_on else 'icons/vape_off.png')

    def toggle_vape(self, instance, touch):  # Added touch argument
        # Placeholder: Replace with actual relay control logic
        if instance.collide_point(*touch.pos):
            self.vape_on = not self.vape_on
            self.vape_image.source = self.get_vape_icon()
            print(f"Toggling vape. New state: {'ON' if self.vape_on else 'OFF'}")

    def update_all_buttons(self):
        self.low_beam_image.source = self.get_low_beam_icon()
        self.high_beam_image.source = self.get_high_beam_icon()
        self.tail_image.source = self.get_tail_icon()
        self.haz_image.source = self.get_haz_icon()
        self.horn_image.source = self.get_horn_icon()
        self.vape_image.source = self.get_vape_icon()

class MainApp(App):
    def build(self):
        return RelayControlScreen()

if __name__ == '__main__':
    MainApp().run()