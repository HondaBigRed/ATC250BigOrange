import os.path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        # Speedometer
        speedometer_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)  # Adjust height as needed
        speedometer_image = Image(source=os.path.join(os.path.dirname(__file__), 'icons/speedometer.png'), size_hint_x=None, width=100)  # Adjust width as needed
        speedometer_label = Label(text='Speed: 0 MPH', size_hint_x=1.5)  # Adjust size_hint_x as needed
        speedometer_box.add_widget(speedometer_image)
        speedometer_box.add_widget(speedometer_label)
        self.add_widget(speedometer_box)

        # RPM
        rpm_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)  # Adjust height as needed
        rpm_image = Image(source=os.path.join(os.path.dirname(__file__), 'icons/rpm.png'), size_hint_x=None, width=100)  # Adjust width as needed
        rpm_label = Label(text='RPM: 0', size_hint_x=1.5)  # Adjust size_hint_x as needed
        rpm_box.add_widget(rpm_image)
        rpm_box.add_widget(rpm_label)
        self.add_widget(rpm_box)

        # Engine Temperature
        engine_temp_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)  # Adjust height as needed
        engine_temp_image = Image(source=os.path.join(os.path.dirname(__file__), 'icons/thermometer.png'), size_hint_x=None, width=100)  # Adjust width as needed
        engine_temp_label = Label(text='Engine Temp: 0 °C', size_hint_x=1.5)  # Adjust size_hint_x as needed
        engine_temp_box.add_widget(engine_temp_image)
        engine_temp_box.add_widget(engine_temp_label)
        self.add_widget(engine_temp_box)

        # Air/Fuel Ratio
        afr_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)  # Adjust height as needed
        afr_image = Image(source=os.path.join(os.path.dirname(__file__), 'icons/afr.png'), size_hint_x=None, width=100)  # Adjust width as needed
        afr_label = Label(text='AFR: 0', size_hint_x=1.5)  # Adjust size_hint_x as needed
        afr_box.add_widget(afr_image)
        afr_box.add_widget(afr_label)
        self.add_widget(afr_box)

        # Gear Indicator (Placeholder)
        gear_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)  # Adjust height as needed
        gear_image = Image(source=os.path.join(os.path.dirname(__file__), 'icons/gear.png'), size_hint_x=None, width=100)  # Adjust width as needed
        gear_label = Label(text='Gear: N', size_hint_x=1.5)  # Adjust size_hint_x as needed
        gear_box.add_widget(gear_image)
        gear_box.add_widget(gear_label)
        self.add_widget(gear_box)

        # Warning Lights (Placeholder)
        warning_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)  # Adjust height as needed
        warning_image = Image(source=os.path.join(os.path.dirname(__file__), 'icons/warning.png'), size_hint_x=None, width=100)  # Adjust width as needed
        warning_label = Label(text='Warnings: None', size_hint_x=1.5)  # Adjust size_hint_x as needed
        warning_box.add_widget(warning_image)
        warning_box.add_widget(warning_label)
        self.add_widget(warning_box)

        # Schedule the update function to run every 0.1 seconds
        Clock.schedule_interval(self.update_labels, 0.1)

        # Initialize sensor data (replace with actual sensor readings)
        self.speed = 0
        self.rpm = 0
        self.engine_temp = 0
        self.afr = 0
        self.gear = 'N'
        self.warnings = 'None'

    def update_labels(self, dt):
        # Update the labels with the latest sensor data
        self.speedometer_label.text = f'Speed: {self.speed} MPH'
        self.rpm_label.text = f'RPM: {self.rpm}'
        self.engine_temp_label.text = f'Engine Temp: {self.engine_temp} °C'
        self.afr_label.text = f'AFR: {self.afr}'
        self.gear_label.text = f'Gear: {self.gear}'
        self.warning_label.text = f'Warnings: {self.warnings}'

class MainApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    MainApp().run()