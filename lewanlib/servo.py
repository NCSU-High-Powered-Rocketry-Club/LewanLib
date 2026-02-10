"""
This module provides the Servo class, which is a convenience wrapper that remembers
a specific servo's ID and automatically includes it in all commands.

Instead of writing servo_bus.move_time_write(servo_id=1, angle=120, time=1), you can write
servo.move_time_write(120, 1).

"""
from typing import TYPE_CHECKING, Optional

# TYPE_CHECKING prevents circular imports at runtime while allowing type hints
# to work properly. Servo depends on ServoBus (for type hints), and ServoBus
# depends on Servo (in its get_servo() method).
if TYPE_CHECKING:
    from .bus import ServoBus
    from .servo_data_packet import ServoDataPacket


class Servo:
    """
    Wrapper class for a single servo on a ServoBus.
    Remembers the servo ID and bus, and delegates all commands to the bus with the ID included.

    id (int): The ID of the servo (0-253).
    bus (ServoBus): The ServoBus instance this servo is connected to.
    name (Optional[str]): An optional name for the servo for easier identification.

    """

    def __init__(self, id_: int, bus: 'ServoBus', name: Optional[str] = None) -> None:
        """
        sets up a Servo object with the given ID and bus.
        0-253 are valid IDs for servos.
        
        """
        self.id = id_
        self.bus = bus
        self.name = name

    def __str__(self) -> str:
        """
        returns string representation of the servo or 'Servo' if no name is set.
        """
        name = self.name or 'Servo'
        return f'{name} (ID {self.id})'

    # MOVEMENT COMMANDS (all delegate to self.bus with self.id prepended)

    def move_time_write(self, *args, **kwargs) -> None:
        """
        Moves servo to specified angle over given time.
        Sends command to servo immediately.
        """
        self.bus.move_time_write(self.id, *args, **kwargs)

    def move_time_wait_write(self, *args, **kwargs) -> None:
        """
        Moves servo to specified angle over given time.
        Holds and waits for seperate command (move_start()) to begin motion.
        Servo will block subsequent commands until move_start() is called.
        Can move all servos simultaneously by providing broadcast ID to move_start(254)
        """
        self.bus.move_time_wait_write(self.id, *args, **kwargs)

    def move_time_read(self) -> tuple:
        """
        Read the angle+time from the last move_time_write() command.
        """
        return self.bus.move_time_read(self.id)

    def move_time_wait_read(self) -> tuple:
        """
        Read the queued angle+time from the last move_time_wait_write() command.
        """
        return self.bus.move_time_wait_read(self.id)

    def move_speed_write(self, *args, **kwargs) -> None:
        """
        Move to angle at a specific speed (degrees/second).
        """
        self.bus.move_speed_write(self.id, *args, **kwargs)

    def velocity_read(self, *args, **kwargs) -> float:
        """
        Estimate current velocity by sampling position twice with a delay.
        """
        return self.bus.velocity_read(self.id, *args, **kwargs)[0]

    def move_start(self) -> None:
        """
        Start executing all queued moves (from move_time_wait_write()).
        """
        self.bus.move_start(self.id)

    def move_stop(self) -> None:
        """
        Stop the servo immediately (halt current motion).
        """
        self.bus.move_stop(self.id)

    # IDENTIFICATION & CONFIGURATION COMMANDS

    def id_write(self, new_id: int) -> None:
        """
        checks new_id is valid and changes the servo's ID to new_id.
        """
        self.bus.id_write(self.id, new_id)
        self.id = new_id

    def angle_offset_adjust(self, *args, **kwargs) -> None:
        """
        Adjust angle calibration offset (temporary, not saved to servo memory).
        """
        self.bus.angle_offset_adjust(self.id, *args, **kwargs)

    def angle_offset_write(self) -> None:
        """
        Save the angle offset adjustment to servo non-volatile memory.
        """
        self.bus.angle_offset_write(self.id)

    def angle_offset_read(self) -> float:
        """
        Read the servo's saved angle offset (in degrees, range ±30°).
        """
        return self.bus.angle_offset_read(self.id)

    # ANGLE & VOLTAGE LIMIT COMMANDS

    def angle_limit_write(self, *args, **kwargs) -> None:
        """
        Set minimum and maximum angles the servo is allowed to move to.
        """
        self.bus.angle_limit_write(self.id, *args, **kwargs)

    def angle_limit_read(self) -> tuple:
        """
        Read the angle limits (min_angle, max_angle) in degrees.
        """
        return self.bus.angle_limit_read(self.id)

    def vin_limit_write(self, *args, **kwargs) -> None:
        """
        Set minimum and maximum supply voltages for safe operation.
        """
        self.bus.vin_limit_write(self.id, *args, **kwargs)

    def vin_limit_read(self) -> tuple:
        """
        Read the voltage limits (min_v, max_v) in Volts.
        """
        return self.bus.vin_limit_read(self.id)

    # TEMPERATURE LIMIT & SENSOR COMMANDS

    def temp_max_limit_write(self, *args, **kwargs) -> None:
        """
        Set the maximum temperature at which the servo will operate.
        """
        return self.bus.temp_max_limit_write(self.id, *args, **kwargs)

    def temp_max_limit_read(self, *args, **kwargs) -> float:
        """
        Read the maximum temperature limit.
        """
        return self.bus.temp_max_limit_read(self.id, *args, **kwargs)

    def temp_read(self, *args, **kwargs) -> float:
        """
        Read the servo's current temperature (in Celsius or Fahrenheit).
        """
        return self.bus.temp_read(self.id, *args, **kwargs)

    def vin_read(self) -> float:
        """
        Read the servo's current input voltage (in Volts).
        """
        return self.bus.vin_read(self.id)

    def pos_read(self) -> float:
        """
        Read the servo's current position (in degrees).
        """
        return self.bus.pos_read(self.id)

    # MODE COMMANDS (servo vs. motor mode)

    def mode_write(self, *args, **kwargs) -> None:
        """
        Set servo mode: 'servo' (hold position) or 'motor' (rotate continuously).
        """
        return self.bus.mode_write(self.id, *args, **kwargs)

    def mode_read(self) -> tuple:
        """
        Read current mode and speed setting.
        """
        return self.bus.mode_read(self.id)

    # POWER/TORQUE COMMANDS

    def set_powered(self, powered: bool) -> None:
        """
        Enable (True) or disable (False) servo torque (motor on/off).
        """
        return self.bus.set_powered(self.id, powered)

    def is_powered(self) -> bool:
        """
        Check if servo torque is currently enabled.
        """
        return self.bus.is_powered(self.id)

    # LED INDICATOR COMMANDS

    def led_ctrl_write(self, *args, **kwargs) -> None:
        """
        Control the LED state when there are no errors.
        """
        return self.bus.led_ctrl_write(self.id, *args, **kwargs)

    def led_ctrl_read(self) -> bool:
        """
        Read the LED control setting.
        """
        return self.bus.led_ctrl_read(self.id)

    def led_error_write(self, *args, **kwargs) -> None:
        """
        Set which error types will trigger the LED indicator.
        """
        return self.bus.led_error_write(self.id, *args, **kwargs)

    def led_error_read(self) -> tuple:
        """
        Read which errors currently trigger the LED (stalled, over_voltage, over_temp).
        """
        return self.bus.led_error_read(self.id)

    def return_data_packet(self) -> ServoDataPacket:
        """
        Read the servo's current data packet.
        """
        return self.bus.return_data_packet(self.id)