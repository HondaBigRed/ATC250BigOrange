
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
hazards_active = False

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
    "hazards": {
        "on": load_icon(icon_dir / "haz_on.png"),
        "off": load_icon(icon_dir / "haz_off.png")
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

# Hazards (replacing Party Mode)
def toggle_hazards(button):
    global hazards_active
    hazards_active = not hazards_active
    update_button_icon(button, hazards_active, icons["hazards"])
    if hazards_active:
        cycle_hazards()

def cycle_hazards():
    if hazards_active:
        # Turn all lights ON
        GPIO.gpio_write(chip_handle, RELAY_PINS["low_beam"], 1)
        GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 1)
        GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 1)
        root.after(500, lambda: (
            GPIO.gpio_write(chip_handle, RELAY_PINS["low_beam"], 0),
            GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 0),
            GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 0),
            root.after(500, cycle_hazards)
        ))
    else:
        GPIO.gpio_write(chip_handle, RELAY_PINS["low_beam"], 0)
        GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 0)
        GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 0)

# Button config with no border/hover flash
button_style = {
    "width": 100,
    "height": 100,
    "compound": "top",
    "bg": "black",
    "activebackground": "black",
    "highlightthickness": 0,
    "bd": 0
}

# Layout
button_frame = tk.Frame(root, bg="black")
button_frame.pack(expand=True)

buttons = {
    "low_beam": tk.Button(button_frame, text="Low Beam", **button_style),
    "high_beam": tk.Button(button_frame, text="High Beam", **button_style),
    "tail_light": tk.Button(button_frame, text="Tail Light", **button_style),
    "vape": tk.Button(button_frame, text="Vape", **button_style),
    "hazards": tk.Button(button_frame, text="Hazards", **button_style)
}

# Assign images and commands
for name in buttons:
    update_button_icon(buttons[name], False, icons[name])

buttons["low_beam"].config(command=lambda: toggle_output("low_beam", buttons["low_beam"]))
buttons["high_beam"].config(command=lambda: toggle_output("high_beam", buttons["high_beam"]))
buttons["tail_light"].config(command=lambda: toggle_output("tail_light", buttons["tail_light"]))
buttons["vape"].config(command=lambda: toggle_output("vape", buttons["vape"]))
buttons["hazards"].config(command=lambda: toggle_hazards(buttons["hazards"]))

# Grid layout
buttons["low_beam"].grid(row=0, column=0, padx=20, pady=20)
buttons["high_beam"].grid(row=0, column=1, padx=20, pady=20)
buttons["tail_light"].grid(row=0, column=2, padx=20, pady=20)
buttons["vape"].grid(row=0, column=3, padx=20, pady=20)
buttons["hazards"].grid(row=0, column=4, padx=20, pady=20)

# Exit fullscreen with ESC
def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)

root.bind("<Escape>", exit_fullscreen)

# Start GUI
root.mainloop()
