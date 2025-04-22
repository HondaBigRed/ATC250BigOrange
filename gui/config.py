# config.py

# --- GENERAL SETTINGS ---
USE_GPIO = False     # Set to True when GPIO hardware is connected
SIM_MODE = True      # Enables simulated data for sensors when True

# --- GPIO PINS ---
HALL_GPIO = 5        # Wheel speed sensor
RPM_GPIO = 6         # RPM signal input (CDI pulse, etc.)
AFR_GPIO = 7         # Placeholder if using digital signal for AFR

# --- DASH RELAYS ---
PINS = {
    'low_beam': 4,
    'tail_light': 27,
    'high_beam': 26,
    'vape': 22,
    'horn_500hz': 21,
    'horn_400hz': 13
}

# --- SENSOR CONSTANTS ---
WHEEL_CIRCUMFERENCE_M = 1.5708   # Adjust for your tire size
PULSES_PER_REV = 1               # One pulse per wheel rotation

# --- UI / DASH SETTINGS ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

# --- SIMULATION SETTINGS ---
SIM_RPM_START = 1200
SIM_SPEED_START = 5.0
SIM_AFR_START = 13.8

# --- MOCK FUNCTIONS FOR SIM MODE ---
def simulate_rpm():
    import random
    return random.randint(1100, 4500)

def simulate_speed():
    import random
    return round(random.uniform(3.5, 25.0), 1)

def simulate_afr():
    import random
    return round(random.uniform(12.5, 14.7), 2)

# --- GPIO WRAPPERS ---
def setup_gpio():
    if USE_GPIO:
        import lgpio
        try:
            h = lgpio.gpiochip_open(0)
            for name, pin in PINS.items():
                lgpio.gpio_claim_output(h, pin)
            return h
        except Exception as e:
            print(f"[ERROR] Failed to initialize GPIO: {e}")
            return None
    return None

def gpio_write(h, pin, value):
    if USE_GPIO and h is not None:
        try:
            import lgpio
            lgpio.gpio_write(h, pin, value)
        except Exception as e:
            print(f"[GPIO ERROR] Pin {pin} write failed: {e}")
