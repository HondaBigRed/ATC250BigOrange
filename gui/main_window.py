import os
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
    ICONS_DIR = os.path.join(os.path.dirname(__file__), 'icons')  # Class-level attribute

    low_beams_on = BooleanProperty(False)
    high_beams_on = BooleanProperty(False)
    tail_on = BooleanProperty(True)  # Initial state is ON
    haz_on = BooleanProperty(False)
    horn_on = BooleanProperty(False)
    vape_on = BooleanProperty(True)  # Initial state is ON

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
        self.low_beam_image = ImageButton(source=self.get_icon('low', self.low_beams_on), size_hint_x=None, width=100)
        self.low_beam_image.bind(on_press=self.toggle_low_beams)
        low_beam_box.add_widget(self.low_beam_image)
        relay_button_box.add_widget(low_beam_box)

        # --- High Beam Control ---
        high_beam_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.high_beams_on = BooleanProperty(False)  # Initial state is OFF
        self.high_beam_image = ImageButton(source=self.get_icon('high', self.high_beams_on), size_hint_x=None, width=100)
        self.high_beam_image.bind(on_press=self.toggle_high_beams)
        high_beam_box.add_widget(self.high_beam_image)
        relay_button_box.add_widget(high_beam_box)

        # --- Taillight Control ---
        tail_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.tail_on = BooleanProperty(True)  # Initial state is ON
        self.tail_image = ImageButton(source=self.get_icon('tail', self.tail_on), size_hint_x=None, width=100)
        self.tail_image.bind(on_press=self.toggle_tail)
        tail_box.add_widget(self.tail_image)
        relay_button_box.add_widget(tail_box)

        # --- Hazard Light Control ---
        haz_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.haz_on = BooleanProperty(False)  # Initial state is OFF
        self.haz_image = ImageButton(source=self.get_icon('haz', self.haz_on), size_hint_x=None, width=100)
        self.haz_image.bind(on_press=self.toggle_haz)
        haz_box.add_widget(self.haz_image)
        relay_button_box.add_widget(haz_box)

        # --- Horn Control ---
        horn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.horn_on = BooleanProperty(False)  # Initial state is OFF
        self.horn_image = ImageButton(source=self.get_icon('horn', self.horn_on), size_hint_x=None, width=100)
        self.horn_image.bind(on_press=self.toggle_horn)
        self.horn_image.bind(on_release=self.horn_released)
        horn_box.add_widget(self.horn_image)
        relay_button_box.add_widget(horn_box)

        # --- Vape Control ---
        vape_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.vape_on = BooleanProperty(True)  # Initial state is ON
        self.vape_image = ImageButton(source=self.get_icon('vape', self.vape_on), size_hint_x=None, width=100)
        self.vape_image.bind(on_press=self.toggle_vape)
        vape_box.add_widget(self.vape_image)
        relay_button_box.add_widget(vape_box)

        self.add_widget(relay_button_box)

        # Schedule the hazard light flashing
        self.flash_event = None  # Store the event for later unscheduling
        Clock.schedule_once(self.set_initial_icon_states, 0)  # Call after initialization

    def set_initial_icon_states(self, dt):
        self.update_all_buttons()  # Call after all widgets are created

    def get_icon(self, control_name, state):
        try:
            return os.path.join(RelayControlScreen.ICONS_DIR, f'{control_name}_{"on" if state else "off"}.png')  # Corrected
        except FileNotFoundError:
            print(f"Icon file not found for {control_name}, using default.")
            return os.path.join(RelayControlScreen.ICONS_DIR, 'default.png')  # Corrected

    def toggle_low_beams(self, instance, *args):  # Added *args
        # Placeholder: Replace with actual relay control logic
        self.low_beams_on = not self.low_beams_on
        self.low_beam_image.source = self.get_icon('low', self.low_beams_on)
        self.update_high_low_interlock()
        print(f"Toggling low beams. New state: {'ON' if self.low_beams_on else 'OFF'}")
        # Example (replace with your RPi.GPIO code):
        # if self.low_beams_on:
        #     GPIO.output(LOW_BEAM_PIN, GPIO.HIGH)
        # else:
        #     GPIO.output(LOW_BEAM_PIN, GPIO.LOW)

    def toggle_high_beams(self, instance, *args):  # Added *args
        # Placeholder: Replace with actual relay control logic
        self.high_beams_on = not self.high_beams_on
        self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
        self.update_high_low_interlock()
        print(f"Toggling high beams. New state: {'ON' if self.high_beams_on else 'OFF'}")
        # Example (replace with your RPi.GPIO code):
        # if self.high_beams_on:
        #     GPIO.output(HIGH_BEAM_PIN, GPIO.HIGH)
        # else:
        #     GPIO.output(HIGH_BEAM_PIN, GPIO.LOW)

    def update_high_low_interlock(self):
        # Ensure only one of high or low beams is on
        if self.high_beams_on and self.low_beams_on:
            if self.high_beams_on:
                self.low_beams_on = False
                self.low_beam_image.source = self.get_icon('low', self.low_beams_on)
                # Placeholder: GPIO.output(LOW_BEAM_PIN, GPIO.LOW)
            elif self.low_beams_on:
                self.high_beams_on = False
                self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
                # Placeholder: GPIO.output(HIGH_BEAM_PIN, GPIO.LOW)

    def toggle_tail(self, instance, *args):  # Added *args
        # Placeholder: Replace with actual relay control logic
        self.tail_on = not self.tail_on
        self.tail_image.source = self.get_icon('tail', self.tail_on)
        if self.haz_on:
            self.tail_image.disabled = self.tail_on  # Disable tail lights
            # Placeholder: GPIO.output(TAIL_PIN, GPIO.LOW) if self.tail_on else GPIO.output(TAIL_PIN, GPIO.HIGH)
        else:
            self.tail_image.disabled = False
            # Placeholder: GPIO.output(TAIL_PIN, GPIO.HIGH) if self.tail_on else GPIO.output(TAIL_PIN, GPIO.LOW)
        print(f"Toggling taillights. New state: {'ON' if self.tail_on else 'OFF'}")

    def toggle_haz(self, instance, *args):  # Added *args
        # Placeholder: Replace with actual relay control logic
        self.haz_on = not self.haz_on
        self.haz_image.source = self.get_icon('haz', self.haz_on)

        if self.haz_on:
            # Start flashing
            self.flash_event = Clock.schedule_interval(self.flash_hazard_lights, 0.5)  # 2Hz
            # Disable other controls
            self.low_beam_image.disabled = True
            self.high_beam_image.disabled = True
            self.tail_image.disabled = True
            self.vape_image.disabled = True
            print("Starting hazard lights")
            # Placeholder: Start hazard light flashing
        else:
            # Stop flashing
            if self.flash_event:
                Clock.unschedule(self.flash_event)
                self.flash_event = None
            # Re-enable other controls
            self.low_beam_image.disabled = False
            self.high_beam_image.disabled = False
            self.tail_image.disabled = False
            self.vape_image.disabled = False
            self.update_all_buttons()

            print("Stopping hazard lights")
            # Placeholder: Stop hazard light flashing

    def flash_hazard_lights(self, dt):
        # Placeholder: Implement hazard light flashing logic (e.g., using RPi.GPIO.output)
        # This function is called by the Clock every 0.5 seconds
        if GPIO:
            self.high_beams_on = not self.high_beams_on
            self.tail_on = not self.tail_on
            self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
            self.tail_image.source = self.get_icon('tail', self.tail_on)
            # GPIO.output(HIGH_BEAM_PIN, GPIO.HIGH) if self.high_beams_on else GPIO.output(HIGH_BEAM_PIN, GPIO.LOW)
            # GPIO.output(TAIL_PIN, GPIO.HIGH) if self.tail_on else GPIO.output(TAIL_PIN, GPIO.LOW)
            print("Flashing lights (Placeholder)")

    def toggle_horn(self, instance, *args):
        # Placeholder: Implement momentary horn control
        self.horn_on = True  # Set to true on press
        self.horn_image.source = self.get_icon('horn', self.horn_on)
        print("Horn ON (Placeholder)")
        # Placeholder: Activate horn relay

    def horn_released(self, instance, *args):
        # Placeholder: Implement momentary horn control
        self.horn_on = False  # Set to false on release
        self.horn_image.source = self.get_icon('horn', self.horn_on)
        print("Horn OFF (Placeholder)")
        # Placeholder: Deactivate horn relay

    def toggle_vape(self, instance, *args):
        # Placeholder: Replace with actual relay control logic
        self.vape_on = not self.vape_on
        self.vape_image.source = self.get_icon('vape', self.vape_on)
        print(f"Toggling vape. New state: {'ON' if self.vape_on else 'OFF'} (Placeholder)")
        # Placeholder: Replace with actual relay control logic

    def update_all_buttons(self):
        self.low_beam_image.source = self.get_icon('low', self.low_beams_on)
        self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
        self.tail_image.source = self.get_icon('tail', self.tail_on)
        self.haz_image.source = self.get_icon('haz', self.haz_on)
        self.horn_image.source = self.get_icon('horn', self.horn_on)
        self.vape_image.source = self.get_icon('vape', self.vape_on)


class MainApp(App):
    def build(self):
        return RelayControlScreen()


if __name__ == '__main__':
    GPIO = None  # Initialize GPIO to None
    try:
        MainApp().run()
    finally:
        if GPIO:
            GPIO.cleanup()  # Clean up GPIO on app exit