
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
hazard_toggle = False  # For alternating logic

# Load icon images
def load_icon(path, size=(320, 320)):
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

def update_button_icon(button, active, icon_pair):
    button.config(image=icon_pair["on"] if active else icon_pair["off"])

def set_output(name, on):
    pin = RELAY_PINS[name]
    GPIO.gpio_write(chip_handle, pin, 1 if on else 0)
    states[name] = on
    update_button_icon(buttons[name], on, icons[name])

def toggle_output(name, button):
    # If turning low or high beam ON, disable the other
    if name == "low_beam":
        set_output("low_beam", not states["low_beam"])
        if states["low_beam"]:
            set_output("high_beam", False)
    elif name == "high_beam":
        set_output("high_beam", not states["high_beam"])
        if states["high_beam"]:
            set_output("low_beam", False)
    else:
        set_output(name, not states[name])

    # Auto-on tail light if low or high beam is active
    if name in ["low_beam", "high_beam"]:
        tail_should_be_on = states["low_beam"] or states["high_beam"]
        set_output("tail_light", tail_should_be_on)

# Hazards (alternate tail and high beam)
def toggle_hazards(button):
    global hazards_active
    hazards_active = not hazards_active
    update_button_icon(button, hazards_active, icons["hazards"])
    if hazards_active:
        cycle_hazards()

def cycle_hazards():
    global hazard_toggle
    if hazards_active:
        hazard_toggle = not hazard_toggle
        GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 1 if hazard_toggle else 0)
        GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 0 if hazard_toggle else 1)
        root.after(500, cycle_hazards)
    else:
        GPIO.gpio_write(chip_handle, RELAY_PINS["high_beam"], 0)
        GPIO.gpio_write(chip_handle, RELAY_PINS["tail_light"], 0)

# Button config with no borders/hover effects and increased size
button_style = {
    "width": 320,
    "height": 320,
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

# Assign icons and logic
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
