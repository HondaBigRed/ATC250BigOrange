import os.path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import ButtonBehavior
#from RPi import GPIO  # Remove RPi.GPIO
from gpiozero import DigitalOutputDevice  # Import gpiozero

ICONS_DIR = os.path.join(os.path.dirname(__file__), 'icons')

class ImageButton(ButtonBehavior, Image):
    pass

class RelayControlScreen(Screen):
    low_beams_on = BooleanProperty(False)
    high_beams_on = BooleanProperty(False)
    tail_on = BooleanProperty(True)
    haz_on = BooleanProperty(False)
    horn_on = BooleanProperty(False)
    vape_on = BooleanProperty(True)

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
        self.high_beam_image = ImageButton(source=self.get_icon('high', self.high_beams_on), size_hint_x=None, width=100)
        self.high_beam_image.bind(on_press=self.toggle_high_beams)
        high_beam_box.add_widget(self.high_beam_image)
        relay_button_box.add_widget(high_beam_box)

        # --- Taillight Control ---
        tail_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.tail_image = ImageButton(source=self.get_icon('tail', self.tail_on), size_hint_x=None, width=100)
        self.tail_image.bind(on_press=self.toggle_tail)
        tail_box.add_widget(self.tail_image)
        relay_button_box.add_widget(tail_box)

        # --- Hazard Light Control ---
        haz_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.haz_image = ImageButton(source=self.get_icon('haz', self.haz_on), size_hint_x=None, width=100)
        self.haz_image.bind(on_press=self.toggle_haz)
        haz_box.add_widget(self.haz_image)
        relay_button_box.add_widget(haz_box)

        # --- Horn Control ---
        horn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.horn_on = BooleanProperty(False)
        self.horn_image = ImageButton(source=self.get_icon('horn', self.horn_on), size_hint_x=None, width=100)
        self.horn_image.bind(on_press=self.toggle_horn)
        self.horn_image.bind(on_release=self.horn_released)
        horn_box.add_widget(self.horn_image)
        relay_button_box.add_widget(horn_box)

        # --- Vape Control ---
        vape_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.vape_on = BooleanProperty(True)
        self.vape_image = ImageButton(source=self.get_icon('vape', self.vape_on), size_hint_x=None, width=100)
        self.vape_image.bind(on_press=self.toggle_vape)
        vape_box.add_widget(self.vape_image)
        relay_button_box.add_widget(vape_box)

        self.add_widget(relay_button_box)

        # Initialize GPIO devices (gpiozero)
        if GPIO:
            self.low_beam_relay = DigitalOutputDevice(LOW_BEAM_PIN, active_high=True, initial_value=False)
            self.high_beam_relay = DigitalOutputDevice(HIGH_BEAM_PIN, active_high=True, initial_value=False)
            self.tail_relay = DigitalOutputDevice(TAIL_PIN, active_high=True, initial_value=True)
            self.vape_relay = DigitalOutputDevice(VAPE_PIN, active_high=True, initial_value=True)

        # Schedule the hazard light flashing
        self.flash_event = None

    def on_kv_post(self, base_widget):
        # After all widgets are created, set initial icon states
        # Clock.schedule_once(self.set_initial_icon_states, 0) # Schedule after initialization
        pass

    def get_icon(self, control_name, state):
        try:
            return os.path.join(RelayControlScreen.ICONS_DIR, f'{control_name}_{"on" if state else "off"}.png')
        except FileNotFoundError:
            print(f"Icon file not found for {control_name}, using default.")
            return os.path.join(RelayControlScreen.ICONS_DIR, 'default.png')

    def toggle_low_beams(self, instance, *args):
        self.low_beams_on = not self.low_beams_on
        self.low_beam_image.source = self.get_icon('low', self.low_beams_on)
        self.update_high_low_interlock()
        print(f"Toggling low beams. New state: {'ON' if self.low_beams_on else 'OFF'}")
        if GPIO:
            self.low_beam_relay.value = self.low_beams_on

    def toggle_high_beams(self, instance, *args):
        self.high_beams_on = not self.high_beams_on
        self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
        self.update_high_low_interlock()
        print(f"Toggling high beams. New state: {'ON' if self.high_beams_on else 'OFF'}")
        if GPIO:
            self.high_beam_relay.value = self.high_beams_on

    def update_high_low_interlock(self):
        # Ensure only one of high or low beams is on
        if self.high_beams_on and self.low_beams_on:
            if self.high_beams_on:
                self.low_beams_on = False
                self.low_beam_image.source = self.get_icon('low', self.low_beams_on)
                if GPIO:
                    self.low_beam_relay.off()
            elif self.low_beams_on:
                self.high_beams_on = False
                self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
                if GPIO:
                    self.high_beam_relay.off()

    def toggle_tail(self, instance, *args):
        self.tail_on = not self.tail_on
        self.tail_image.source = self.get_icon('tail', self.tail_on)
        if self.haz_on:
            self.tail_image.disabled = self.tail_on
            if GPIO:
                self.tail_relay.off() if self.tail_on else self.tail_relay.on()
        else:
            self.tail_image.disabled = False
            if GPIO:
                self.tail_relay.on() if self.tail_on else self.tail_relay.off()
        print(f"Toggling taillights. New state: {'ON' if self.tail_on else 'OFF'}")

    def toggle_haz(self, instance, *args):
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

    def flash_hazard_lights(self, dt):
        # Implement hazard light flashing logic (gpiozero)
        if GPIO:
            self.high_beams_on = not self.high_beams_on
            self.tail_on = not self.tail_on
            self.high_beam_image.source = self.get_icon('high', self.high_beams_on)
            self.tail_image.source = self.get_icon('tail', self.tail_on)
            self.high_beam_relay.on() if self.high_beams_on else self.high_beam_relay.off()
            self.tail_relay.on() if self.tail_on else self.tail_relay.off()
        print("Flashing lights (Placeholder)")

    def toggle_horn(self, instance, *args):
        self.horn_on = True  # Set to true on press
        self.horn_image.source = self.get_icon('horn', self.horn_on)
        print("Horn ON (Placeholder)")
        if GPIO:
            self.horn_relay.on()  # Activate horn relay

    def horn_released(self, instance, *args):
        self.horn_on = False  # Set to false on release
        self.horn_image.source = self.get_icon('horn', self.horn_on)
        print("Horn OFF (Placeholder)")
        if GPIO:
            self.horn_relay.off()  # Deactivate horn relay

    def toggle_vape(self, instance, *args):
        self.vape_on = not self.vape_on
        self.vape_image.source = self.get_icon('vape', self.vape_on)
        print(f"Toggling vape. New state: {'ON' if self.vape_on else 'OFF'} (Placeholder)")
        if GPIO:
            self.vape_relay.on() if self.vape_on else self.vape_relay.off()

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
    if GPIO:
        GPIO.cleanup()  # Clean up GPIO on app exit
    MainApp().run()