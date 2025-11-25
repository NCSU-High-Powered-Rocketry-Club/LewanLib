import gpiod
from gpiod.line import Direction, Value, Bias

class GPIOPin:
    """
    Helper class for controlling a GPIO pin using gpiod.
    """
    def __init__(self, pin: int, chip_path: str = "/dev/gpiochip0", initial_value: bool = False):
        self.pin = pin
        self.chip_path = chip_path
        self._direction = Direction.OUTPUT
        self._value = Value.ACTIVE if initial_value else Value.INACTIVE
        self._bias = Bias.DISABLED
        self.request = None
        self._update_request()

    def _update_request(self):
        if self.request:
            self.request.release()
        
        config = {
            self.pin: gpiod.LineSettings(
                direction=self._direction,
                output_value=self._value,
                bias=self._bias
            )
        }
        self.request = gpiod.request_lines(
            self.chip_path,
            consumer="lewanlib",
            config=config
        )

    def set_direction_output(self, initial_value: bool = False):
        """
        Set the pin direction to output.
        """
        self._direction = Direction.OUTPUT
        self._value = Value.ACTIVE if initial_value else Value.INACTIVE
        self._update_request()

    def set_bias(self, bias: str):
        """
        Set bias to 'pull_up', 'pull_down', or 'disable'.
        """
        if bias == 'pull_up':
            self._bias = Bias.PULL_UP
        elif bias == 'pull_down':
            self._bias = Bias.PULL_DOWN
        else:
            self._bias = Bias.DISABLED
        self._update_request()

    def drive_high(self):
        """
        Drive the pin high.
        """
        print(f"DEBUG: Setting pin {self.pin} HIGH")
        self._value = Value.ACTIVE
        if self.request:
            self.request.set_value(self.pin, Value.ACTIVE)
            val = self.request.get_value(self.pin)
            print(f"DEBUG: Pin {self.pin} readback: {val}")

    def drive_low(self):
        """
        Drive the pin low.
        """
        print(f"DEBUG: Setting pin {self.pin} LOW")
        self._value = Value.INACTIVE
        if self.request:
            self.request.set_value(self.pin, Value.INACTIVE)
            val = self.request.get_value(self.pin)
            print(f"DEBUG: Pin {self.pin} readback: {val}")

    def close(self):
        """
        Release the GPIO line.
        """
        if self.request:
            self.request.release()
            self.request = None
