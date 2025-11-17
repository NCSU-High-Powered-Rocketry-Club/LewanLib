# LewanLib

Library for controlling bus servos using the LewanSoul Bus Servo Communication Protocol.

**This README explains how to get the library, set up a Python environment on Windows (and other OSes), run tests, and start using the API.**

**Getting The Code**

Clone the repository:

```powershell
git clone https://github.com/NCSU-High-Powered-Rocketry-Club/LewanLib.git
cd LewanLib
```

**Supported Python versions:** 3.8 and newer (the project was developed against modern Python — use 3.10+ when possible).

**Quick Setup (recommended: use a virtualenv)**

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

macOS / Linux (bash):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

- `-e .` installs the package in editable/developer mode. The `".[dev]"` extra installs development dependencies (tests, linters, type checkers).
- If you prefer not to install dev dependencies, run `python -m pip install -e .` instead.

**Notes about `pytest` and PATH on Windows**

- If `pytest` is not found when you run `pytest` directly, it's usually because the Python `Scripts` directory (or your virtualenv's `Scripts`) isn't on your PATH. Instead of modifying PATH you can always run tests with:

```powershell
python -m pytest tests/ -q
```

- Using the virtualenv activation step above ensures the `Scripts` directory is on PATH for the current shell session.

**Run Tests**

After installing dev dependencies, run the test suite:

```powershell
python -m pytest tests/ -v
```

This repository ships small unit tests in `tests/` that validate utility functions and basic behavior.

**Quick Usage Example**

```python
from lewanlib.bus import ServoBus

with ServoBus(port='COM3', baudrate=115200) as bus:
    # Move servo 1 to 120 degrees over 1.0 seconds and wait until movement completes
    bus.move_time_write(1, 120, 1.0, wait=True)

    servo = bus.get_servo(1, name='Arm')
    print('Position (deg):', servo.pos_read())
```

See `lewanlib/bus.py` and `lewanlib/servo.py` for more detailed API documentation and examples.

**Development Tips**

- Run the type checker:

```powershell
python -m mypy lewanlib
```

- Run linters / formatters if installed:

```powershell
python -m flake8
python -m black .
```

**Hardware & Dependencies**

- Hardware: LewanSoul bus servos and a serial adapter (USB-to-TTL/RS485 as appropriate for your hardware).
- Runtime dependency: `pyserial` (installed automatically by the dev extras).

**Troubleshooting**

- If you see permission errors when accessing serial ports on Linux/macOS, ensure your user has access to the device (e.g., add to `dialout` group or use `sudo` when testing).
- If a test or command uses an absolute Python path (leftover from older workflows), prefer `python -m <module>` to avoid path issues.

**Additional Setup Docs**

For alternative setups (for example, if you don't want to use conda), see `SETUP_NO_CONDA.md` for step-by-step instructions.

**Package Layout**

- `lewanlib/constants.py` — Protocol constants and packet definitions.
- `lewanlib/types.py` — Type aliases and data structures.
- `lewanlib/utils.py` — Utility functions (conversions, checksums, etc.).
- `lewanlib/servo.py` — `Servo` convenience wrapper class.
- `lewanlib/bus.py` — `ServoBus` class (main interface to the servo bus).

**License**

See the `LICENSE` file for license details.

