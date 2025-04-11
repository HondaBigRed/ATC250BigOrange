def read_cht():
    """Reads Cylinder Head Temperature."""
    # Placeholder: Replace with actual CHT reading code
    print("Placeholder: Reading CHT")  # For testing
    return 200.0  # Dummy temperature (replace later)

def read_egt():
    """Reads Exhaust Gas Temperature."""
    # Placeholder: Replace with actual EGT reading code
    print("Placeholder: Reading EGT")  # For testing
    return 600.0  # Dummy temperature (replace later)

def read_afr():
    """Reads Air-Fuel Ratio."""
    # Placeholder: Replace with actual AFR reading code
    print("Placeholder: Reading AFR")  # For testing
    return 14.7  # Dummy AFR (replace later)

def read_speed():
    """Reads Speed."""
    # Placeholder: Replace with actual speed reading code
    print("Placeholder: Reading Speed")  # For testing
    return 30.0  # Dummy speed (replace later)

# Add more functions here for other sensors as needed

if __name__ == '__main__':
    # This block of code will only run if you execute this script directly
    # (e.g., `python sensor_reader.py`)
    print("Sensor Reader Script Test")
    cht = read_cht()
    egt = read_egt()
    afr = read_afr()
    speed = read_speed()

    print(f"CHT: {cht}, EGT: {egt}, AFR: {afr}, Speed: {speed}")