# LewanLib

Library for controlling bus servos using the [LewanSoul Bus Servo Communication Protocol](https://images-na.ssl-images-amazon.com/images/I/71WyZDfQwkL.pdf).

## Installation

Install the package with its dependencies:

```bash
pip install -e .
```

Or, to install with development dependencies (testing, type checking, linting):

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from lewanlib.bus import ServoBus

# Create a bus and connect to the servos
with ServoBus(port='COM3', baudrate=115200) as servo_bus:
    # Move servo with ID 1 to 120 degrees over 1 second
    servo_bus.move_time_write(1, 120, 1.0, wait=True)
    
    # Get a Servo object for convenience
    servo = servo_bus.get_servo(1, name="Arm")
    
    # Read the servo's current position
    position = servo.pos_read()
    print(f"{servo}: Position = {position}°")
```

## Package Structure

- `lewanlib/constants.py` — Protocol constants and packet definitions.
- `lewanlib/types.py` — Type aliases and data structures.
- `lewanlib/utils.py` — Utility functions (conversions, checksums, etc.).
- `lewanlib/servo.py` — `Servo` class (wrapper for individual servos).
- `lewanlib/bus.py` — `ServoBus` class (main interface for hardware communication).
- `temp.py` — Backwards-compatible compatibility shim (re-exports from `lewanlib`).

## Testing

Run the unit tests:

```bash
pytest tests/
```

## Hardware Requirements

- LewanSoul bus servos
- Serial connection (USB-to-RS485 adapter or similar)
- Python 3.8+

## Dependencies

- `pyserial>=3.5` — For serial communication with the servos.

## License

See LICENSE file for details.
