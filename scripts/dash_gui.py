
import tkinter as tk
from PIL import Image, ImageTk
import lgpio as GPIO
from pathlib import Path

# GPIO Setup
RELAY_PINS = {
    "low_beam": 4,
    "high_beam": 26,
    "tail_light": 27,
    "vape": 22
}
chip_handle = GPIO.gpiochip_open(0)
for pin in RELAY_PINS.values():
    GPIO.gpio_claim_output(chip_handle, pin)

# State tracking
states = {name: False for name in RELAY_PINS}
party_mode_active = False

# Load icon images
def load_icon(path, size=(64, 64)):
    image = Image.open(path).resize(size, Image.ANTIALIAS)
    return ImageTk.PhotoImage(image)

# GUI setup
root = tk.Tk()
root.title("ATC250ES Dashboard")
root.attributes('-fullscreen', True)
root.configure(bg="black")

# Icon path from repo root
icon_dir = Path(__file__).parent.parent / "icons"

icons = {
    "low_beam": {
        "on": load_icon(icon_dir / "low_on.png"),
        "off": load_icon(icon_dir / "low_off.png")
    },
    "high_beam": {
        "on": load_icon(icon_dir / "high_on.png"),
        "off": load_icon(icon_dir / "high_off.png")
    },
    "tail_light": {
        "on": load_icon(icon_dir / "tail_on.png"),
        "off": load_icon(icon_dir / "tail_off.png")
    },
    "vape": {
        "on": load_icon(icon_dir / "vape_on.png"),
        "off": load_icon(icon_dir / "vape_off.png")
    },
    "party_mode": {
        "on": load_icon(icon_dir / "party_on.png"),
        "off": load_icon(icon_dir / "party_off.png")
    }
}

# Toggle relay function
def toggle_output(name, button):
    global states
    pin = RELAY_PINS[name]
    states[name] = not states[name]
    GPIO.gpio_write(chip_handle, pin, 1 if states[name] else 0)
    update_button_icon(button, states[name], icons[name])

def update_button_icon(button, active, icon_pair):
    button.config(image=icon_pair["on"] if active else icon_pair["off"])

# Party mode
def toggle_party_mode(button):
    global party_mode_active
    party_mode_active = not party_mode_active
    update_button_icon(button, party_mode_active, icons["party_mode"])
    if party_mode_active:
        cycle_party_mode()

def cycle_party_mode():
    if party_mode_active:
        # Turn all lights ON
        GPIO.gpio_write(chip_handle, RELAY_PINS["low_beam"], 1)
        GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 1)
        GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 1)
        root.after(500, lambda: (
            GPIO.gpio_write(chip_handle, RELAY_PINS["low_beam"], 0),
            GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 0),
            GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 0),
            root.after(500, cycle_party_mode)
        ))
    else:
        # Turn all lights OFF
        GPIO.gpio_write(chip_handle, RELAY_PINS["low_beam"], 0)
        GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 0)
        GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 0)

# Button config
button_style = {"width": 100, "height": 100, "compound": "top", "bg": "#222222", "fg": "white"}

# Layout
button_frame = tk.Frame(root, bg="black")
button_frame.pack(expand=True)

buttons = {
    "low_beam": tk.Button(button_frame, text="Low Beam", **button_style),
    "high_beam": tk.Button(button_frame, text="High Beam", **button_style),
    "tail_light": tk.Button(button_frame, text="Tail Light", **button_style),
    "vape": tk.Button(button_frame, text="Vape", **button_style),
    "party_mode": tk.Button(button_frame, text="Party Mode", **button_style)
}

# Assign images and commands
for name in buttons:
    update_button_icon(buttons[name], False, icons[name])

buttons["low_beam"].config(command=lambda: toggle_output("low_beam", buttons["low_beam"]))
buttons["high_beam"].config(command=lambda: toggle_output("high_beam", buttons["high_beam"]))
buttons["tail_light"].config(command=lambda: toggle_output("tail_light", buttons["tail_light"]))
buttons["vape"].config(command=lambda: toggle_output("vape", buttons["vape"]))
buttons["party_mode"].config(command=lambda: toggle_party_mode(buttons["party_mode"]))

# Grid layout
buttons["low_beam"].grid(row=0, column=0, padx=20, pady=20)
buttons["high_beam"].grid(row=0, column=1, padx=20, pady=20)
buttons["tail_light"].grid(row=0, column=2, padx=20, pady=20)
buttons["vape"].grid(row=0, column=3, padx=20, pady=20)
buttons["party_mode"].grid(row=0, column=4, padx=20, pady=20)

# Exit fullscreen with ESC
def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)

root.bind("<Escape>", exit_fullscreen)

# Start GUI
root.mainloop()
