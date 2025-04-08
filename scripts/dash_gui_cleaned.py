
import tkinter as tk
from PIL import Image, ImageTk
import LGPIO as GPIO
import os

# GPIO Setup
GPIO.setmode(GPIO.BCM)
RELAY_PINS = {
    "headlight": 4,
    "high_beam": 26,
    "tail_light": 27,
    "vape": 22
}
for pin in RELAY_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# State tracking
states = {name: False for name in RELAY_PINS}
party_mode_active = False

# Toggle relay function
def toggle_output(name, button):
    global states
    pin = RELAY_PINS[name]
    states[name] = not states[name]
    GPIO.output(pin, GPIO.HIGH if states[name] else GPIO.LOW)
    update_button_visual(button, states[name])

def update_button_visual(button, active):
    button.config(bg="#00cc44" if active else "#222222")

# Party mode
def toggle_party_mode(button):
    global party_mode_active
    party_mode_active = not party_mode_active
    update_button_visual(button, party_mode_active)
    if party_mode_active:
        cycle_party_mode()

def cycle_party_mode():
    if party_mode_active:
        GPIO.output(RELAY_PINS["headlight"], GPIO.HIGH)
        GPIO.output(RELAY_PINS["high_beam"], GPIO.LOW)
        root.after(500, lambda: (
            GPIO.output(RELAY_PINS["headlight"], GPIO.LOW),
            GPIO.output(RELAY_PINS["high_beam"], GPIO.HIGH),
            root.after(500, cycle_party_mode)
        ))
    else:
        GPIO.output(RELAY_PINS["headlight"], GPIO.LOW)
        GPIO.output(RELAY_PINS["high_beam"], GPIO.LOW)

# Load icon images
def load_icon(path, size=(64, 64)):
    image = Image.open(path).resize(size, Image.ANTIALIAS)
    return ImageTk.PhotoImage(image)

# GUI setup
root = tk.Tk()
root.title("ATC250ES Dashboard")
root.attributes('-fullscreen', True)
root.configure(bg="black")

icon_dir = Path(__file__).parent / "icons"

icons = {
    "headlight": load_icon(icon_dir / "headlight.png"),
    "tail_light": load_icon(icon_dir / "taillight.png"),
    "vape": load_icon(icon_dir / "vape.png"),
    "party_mode": load_icon(icon_dir / "party_mode.png")
}

button_style = {"width": 100, "height": 100, "compound": "top", "bg": "#222222", "fg": "white"}

# Create buttons
button_frame = tk.Frame(root, bg="black")
button_frame.pack(expand=True)

buttons = {
    "headlight": tk.Button(button_frame, text="Low Beam", image=icons["headlight"],
                           command=lambda: toggle_output("headlight", buttons["headlight"]), **button_style),
    "tail_light": tk.Button(button_frame, text="Tail Light", image=icons["tail_light"],
                            command=lambda: toggle_output("tail_light", buttons["tail_light"]), **button_style),
    "vape": tk.Button(button_frame, text="Vape", image=icons["vape"],
                      command=lambda: toggle_output("vape", buttons["vape"]), **button_style),
    "party_mode": tk.Button(button_frame, text="Party Mode", image=icons["party_mode"],
                            command=lambda: toggle_party_mode(buttons["party_mode"]), **button_style)
}

# Layout in grid
buttons["headlight"].grid(row=0, column=0, padx=20, pady=20)
buttons["tail_light"].grid(row=0, column=1, padx=20, pady=20)
buttons["vape"].grid(row=0, column=2, padx=20, pady=20)
buttons["party_mode"].grid(row=0, column=3, padx=20, pady=20)

# Exit fullscreen with ESC
def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)

root.bind("<Escape>", exit_fullscreen)

# Start GUI
root.mainloop()
