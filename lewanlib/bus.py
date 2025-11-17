"""
This module contains the ServoBus class, which is the main interface for controlling
LewanSoul bus servos. It handles all low-level protocol details (packet construction,
checksum calculation, serial communication) and provides high-level commands for
moving servos, reading sensors, and configuring behavior.

The LewanSoul protocol is a master-slave protocol where your computer is the master
and the servos are slaves. The master sends commands on a single serial line (RS-485),
and each servo either executes the command (if it's addressed) or ignores it (if it's
for a different servo). Some commands also cause the servo to send a response packet.

"""
from typing import Optional, Union, Tuple, List
import time
from multiprocessing import RLock

import serial  # type: ignore

from . import constants, utils, types


class ServoBusError(Exception):
    """
    Exception raised when there's an error on the servo bus.

    """
    pass


class ServoBus:
    """
    Represents a bus of LewanSoul servos connected via a serial interface.
    Provides methods to send commands and read data from servos.
    """

    def __init__(
            self,
            port: Optional[str] = None,         # Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
            timeout: float = 1.0,               # Read timeout in seconds
            baudrate: int = 115200,             # Communication speed (HiwonderServos use 115200)
            serial_conn=None,                   # Existing serial.Serial connection to use
            on_enter_power_on: bool = False,    # Power on all servos on context enter
            on_exit_power_off: bool = True,     # Power off all servos on context exit
            discard_echo: bool = True,          # Discard echoed bytes after sending
            verify_checksum: bool = True        # Verify checksums on received packets
    ) -> None:
        
        self.on_enter_power_on = on_enter_power_on
        self.on_exit_power_off = on_exit_power_off
        self.discard_echo = discard_echo
        self.verify_checksum = verify_checksum

        # Set up the serial connection
        if serial_conn:
            # Use provided connection (don't close it on exit, since we didn't create it)
            self._serial_conn = serial_conn
            self._close_on_exit = False
        else:
            # Create a new connection
            self._serial_conn = serial.Serial(
                port=port, baudrate=baudrate, timeout=timeout)
            self._close_on_exit = True

        # RLock (recursive lock) ensures thread-safe access to the serial port.
        # Multiple threads can safely call bus methods; only one at a time will have access to the serial port.
        self._serial_conn_lock = RLock()

    def __enter__(self):
        """
        Enter the context manager ('with' statement).

        If on_enter_power_on=True, power on all servos on the bus.
        """
        if self.on_enter_power_on:
            self.set_powered(constants.BROADCAST_ID, True)  # Power all servos

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager. Power off servos and close connection.

        If on_exit_power_off=True, power off all servos.
        Always closes the serial connection (if we opened it).
        """
        try:
            if self.on_exit_power_off:
                self.set_powered(constants.BROADCAST_ID, False)
        finally:
            if self._close_on_exit:
                with self._serial_conn_lock:
                    self.serial_conn.close()

    @property
    def serial_conn(self):
        """
        Return the underlying serial.Serial connection object.
        """
        return self._serial_conn

    def _send_packet(self, servo_id: int, command: int,
                     parameters: Optional[Union[bytearray, bytes]] = None) -> None:
        """
        servo_id - Target servo ID (0-253) or broadcast ID (254).
        command - Command byte (0-255).
        parameters - Optional bytearray or bytes of parameters to include in the packet.

        Sends a packet to the specified servo over the serial connection.

        """
        # Validate inputs
        if servo_id < constants.MIN_ID or servo_id > constants.BROADCAST_ID:
            raise ValueError(
                f'servo_id must be in range [{constants.MIN_ID}, {constants.BROADCAST_ID}]; '
                f'got {servo_id}.')
        if command < 0 or command > 255:
            raise ValueError(
                f'command must be in range [0, 255]; got {command}.')

        if parameters is None:
            parameters = b''
        
        # Build the packet: [Header(2)] [ID] [Length] [Command] [Parameters...] [Checksum]
        servo_packet = bytearray(constants._PACKET_HEADER)
        servo_packet.append(servo_id)
        length = 3 + len(parameters)    # Length includes: Command + Parameters + Checksum
        servo_packet.append(length)
        servo_packet.append(command)
        if parameters:
            servo_packet.extend(parameters)

        checksum = utils._calculate_checksum(servo_id, length, command, parameters)
        servo_packet.append(checksum)

        # Send over serial, thread-safe
        with self._serial_conn_lock:
            # Clear the input buffer to remove any stale/corrupted data
            try:
                self.serial_conn.reset_input_buffer()
            except AttributeError:
                pass

            # Send the packet to the servo(s)
            self.serial_conn.write(servo_packet)

            # If using RS-485, the hardware may echo back our transmitted bytes.
            # Discard them so they don't interfere with reading the response.
            if self.discard_echo:
                self.serial_conn.read(len(servo_packet))

    def _receive_packet(self) -> types._ServoPacket:
        """
        receives a packet from the servo over the serial connection.
        Returns a _ServoPacket namedtuple with fields: (servo_id, command, parameters).
        Raises ServoBusError on checksum failure or protocol errors.

        """
        with self._serial_conn_lock:
            # Read the 2-byte synchronization header
            header = self.serial_conn.read(2)
            if header != constants._PACKET_HEADER:
                raise ServoBusError(
                    f'Expected header {repr(constants._PACKET_HEADER)}; '
                    f'received header {repr(header)}.')

            # Read ID, Length, and Command (3 bytes)
            servo_id, length, command = self.serial_conn.read(3)
            
            # Read parameters: (length - 3) bytes
            # The "length" field includes Command + Parameters + Checksum, so we subtract 3
            # to get just the parameter count.
            param_count = length - 3
            parameters = self.serial_conn.read(param_count)
            
            # Read and verify checksum (1 byte)
            checksum = self.serial_conn.read(1)[0]

        # Verify checksum to detect corruption
        if self.verify_checksum:
            actual_checksum = utils._calculate_checksum(servo_id, length, command,
                                                       parameters)
            if checksum != actual_checksum:
                raise ServoBusError(
                    f'Checksum failed for received packet! '
                    f'Received checksum = {checksum}. '
                    f'Actual checksum = {actual_checksum}.'
                )

        return types._ServoPacket(servo_id, command, parameters)

    def _send_and_receive_packet(
            self, servo_id: int,
            command: int,
            parameters: Optional[Union[bytearray, bytes]] = None
    ) -> types._ServoPacket:
        """
        servo_id - Target servo ID (0-253)
        command - Command byte (0-255)
        parameters - Optional bytearray or bytes of parameters to include in the packet

        returns the response packet from the servo after sending a command
        Raises ServoBusError on checksum failure or protocol errors

        """
        with self._serial_conn_lock:
            self._send_packet(servo_id, command, parameters=parameters)
            response = self._receive_packet()

        # Make sure received packet servo ID matches (so we got data from the right servo)
        if response.servo_id != servo_id:
            raise ServoBusError(
                f'Received packet servo ID ({response.servo_id}) does not '
                f'match sent packet servo ID ({servo_id}).'
            )

        # Make sure received packet command matches (so we got the right response)
        if response.command != command:
            raise ServoBusError(
                f'Received packet command ({response.command}) does not '
                f'match sent packet command ({command}).'
            )

        return response

    def get_servo(self, servo_id: int, name: Optional[str] = None):
        """
        servo_id - Target servo ID (0-253)
        name - Optional name for the servo (for easier identification)
        
        returns a Servo object representing the servo with the given ID.
        """
        # Local import to avoid circular imports
        from .servo import Servo

        return Servo(servo_id, self, name=name)

    # Movement Commands

    def _move_time_write(self, servo_id: int, angle_degrees: types.Real, time_s: types.Real,
                         command: int, wait: bool) -> None:
        """
        id - the servo ID
        angle_degrees - target angle in degrees
        time_s - time to move in seconds
        wait: Whether or not to wait time_s seconds after sending the command.
        command: Acceptable values are _SERVO_MOVE_TIME_WRITE, or _SERVO_MOVE_TIME_WAIT_WRITE.
        """
        if command not in {constants._SERVO_MOVE_TIME_WRITE, constants._SERVO_MOVE_TIME_WAIT_WRITE}:
            raise ValueError(
                f'Command must be either {constants._SERVO_MOVE_TIME_WRITE} or '
                f'{constants._SERVO_MOVE_TIME_WAIT_WRITE}; got {command}.')

        angle_degrees = utils.truncate_angle(angle_degrees)
        angle = utils._degrees_to_ticks(angle_degrees)

        time_s = min(max(0, time_s), 30)
        time_ms = int(round(time_s * 1000))

        params = constants._2_UNSIGNED_SHORTS_STRUCT.pack(angle, time_ms)
        self._send_packet(servo_id, command, params)

        if wait:
            time.sleep(time_s)

    def move_time_write(self, servo_id: int, angle_degrees: types.Real, time_s: types.Real,
                        wait: bool = False) -> None:
        """
        id - the servo ID
        angle_degrees - target angle in degrees
        time_s - time to move in seconds
        wait: Whether or not to wait time_s seconds after sending the command.
        """
        return self._move_time_write(servo_id, angle_degrees, time_s,
                                     constants._SERVO_MOVE_TIME_WRITE, wait)

    def move_time_wait_write(self, servo_id: int, angle_degrees: types.Real,
                             time_s: types.Real) -> None:
        """
        servo_id
        angle_degrees - target angle in degrees
        time_s - time to move in seconds
        """
        return self._move_time_write(servo_id, angle_degrees, time_s,
                                     constants._SERVO_MOVE_TIME_WAIT_WRITE, False)

    def _move_time_read(
            self, servo_id: int, command: int
    ) -> Tuple[float, float]:
        """
        servo_id:
        Returns the parameters set by the last call to move_time_write().
        """

        if command not in {constants._SERVO_MOVE_TIME_READ, constants._SERVO_MOVE_TIME_WAIT_READ}:
            raise ValueError(
                f'Command must be either {constants._SERVO_MOVE_TIME_READ} or '
                f'{constants._SERVO_MOVE_TIME_WAIT_READ}; got {command}.')

        response = self._send_and_receive_packet(servo_id, command)

        angle, time_ms = constants._2_UNSIGNED_SHORTS_STRUCT.unpack(response.parameters)

        angle_degrees = utils._ticks_to_degrees(angle)
        time_s = time_ms / 1000

        return angle_degrees, time_s

    def move_time_read(self, servo_id: int) -> Tuple[float, float]:
        """
        Read the move target and duration that was set.

        Returns Tuple of (angle_degrees, time_seconds) from the last move_time_write.
        """
        return self._move_time_read(servo_id, command=constants._SERVO_MOVE_TIME_READ)

    def move_time_wait_read(self, servo_id: int) -> Tuple[float, float]:
        """
        Read the move target and duration for a blocking move.

        Returns Tuple of (angle_degrees, time_seconds) from the last move_time_wait_write.
        """
        return self._move_time_read(
            servo_id, command=constants._SERVO_MOVE_TIME_WAIT_READ)

    def move_speed_write(self, servo_id: int, angle_degrees: types.Real,
                         speed_dps: types.Real, wait: bool = False) -> None:
        """
        servo_id
        angle_degrees - target angle in degrees
        speed_dps - speed in degrees per second

        moves to angle at a specific speed (degrees/second).
        """

        current_angle = self.pos_read(servo_id)
        error = abs(angle_degrees - current_angle)
        time_s = error / speed_dps

        self.move_time_write(servo_id, angle_degrees, time_s, wait=wait)

    def velocity_read(
            self, *servo_ids: int, period_s: types.Real = 0.1
    ) -> List[float]:
        """
        servo_ids - One or more servo IDs to read velocity from.
        period_s - Time interval over which to measure velocity (seconds).

        Estimate current velocity by sampling position twice with a delay.
        """

        measurements0 = [(time.monotonic(), self.pos_read(servo_id)) for
                         servo_id in servo_ids]
        time.sleep(period_s)
        measurements1 = [(time.monotonic(), self.pos_read(servo_id)) for
                         servo_id in servo_ids]

        velocities = []
        for measurement0, measurement1 in zip(measurements0, measurements1):
            time0, position0 = measurement0
            time1, position1 = measurement1
            velocities.append((position1 - position0) / (time1 - time0))

        return velocities

    def move_start(self, servo_id: int) -> None:
        """
        servo_id

        Start executing all queued moves (from move_time_wait_write()).
        """
        self._send_packet(servo_id, constants._SERVO_MOVE_START)

    def move_stop(self, servo_id: int) -> None:
        """
        Stop the current move (decelerate to stop).

        Args:
            servo_id: Target servo ID, or 254 for broadcast (stop all).
        """
        self._send_packet(servo_id, constants._SERVO_MOVE_STOP)


    # Identification & ID Configuration

    def id_write(self, old_id: int, new_id: int) -> None:
        """
        old_id: Current servo ID.
        new_id: New servo ID to set (0-253).

        """
        if old_id < constants.MIN_ID or old_id > constants.MAX_ID:
            raise ValueError(
                f'old_id must be in range [{constants.MIN_ID}, {constants.MAX_ID}]; got {old_id}.')
        if new_id < constants.MIN_ID or new_id > constants.MAX_ID:
            raise ValueError(
                f'new_id must be in range [{constants.MIN_ID}, {constants.MAX_ID}]; got {new_id}.')

        if new_id != old_id:
            self._send_packet(old_id, constants._SERVO_ID_WRITE, bytes((new_id,)))


    # Angle Offset & Limits

    def angle_offset_adjust(self, servo_id: int, offset_degrees: types.Real,
                            write: bool = True) -> None:
        """
        servo_id:
        offset_degrees - Offset angle in degrees (-30 to +30).
        write - If True, save the offset to permanent memory.
        """

        if offset_degrees < -30 or offset_degrees > 30:
            raise ValueError(
                f'offset_degrees must be in range [-30, 30]; '
                f'got {offset_degrees}.')

        offset = int(round(offset_degrees * 125 / 30))
        params = constants._1_SIGNED_CHAR_STRUCT.pack(offset)
        self._send_packet(servo_id, constants._SERVO_ANGLE_OFFSET_ADJUST, params)

        if write:
            self.angle_offset_write(servo_id)

    def angle_offset_write(self, servo_id: int) -> None:
        """
        Save the current angle offset to permanent memory.

        This ensures the offset persists even after the servo is powered off.

        """
        self._send_packet(servo_id, constants._SERVO_ANGLE_OFFSET_WRITE)

    def angle_offset_read(self, servo_id: int) -> float:
        """
        Read the current angle offset.

        Returns Offset angle in degrees (-30 to +30).
        """
        response = self._send_and_receive_packet(servo_id,
                                                 constants._SERVO_ANGLE_OFFSET_READ)
        offset = constants._1_SIGNED_CHAR_STRUCT.unpack(response.parameters)[0]
        return offset * 30 / 125

    def angle_limit_write(self, servo_id: int, min_angle_degrees: types.Real,
                          max_angle_degrees: types.Real) -> None:
        """
        servo_id:
        min_angle_degrees - Minimum angle limit in degrees.
        max_angle_degrees - Maximum angle limit in degrees.

        Sets angle Minimum and Maximum limits.
        returns error if min_angle_degrees >= max_angle_degrees.

        """

        min_angle_degrees = utils.truncate_angle(min_angle_degrees)
        max_angle_degrees = utils.truncate_angle(max_angle_degrees)

        min_angle = utils._degrees_to_ticks(min_angle_degrees)
        max_angle = utils._degrees_to_ticks(max_angle_degrees)

        if min_angle >= max_angle:
            raise ValueError(
                f'min_angle_degrees must be less than max_angle_degrees; got min_angle_degrees={min_angle_degrees} '
                f'(==> min_angle={min_angle}) and max_angle_degrees={max_angle_degrees} (==> max_angle={max_angle}).')

        params = constants._2_UNSIGNED_SHORTS_STRUCT.pack(min_angle, max_angle)
        self._send_packet(servo_id, constants._SERVO_ANGLE_LIMIT_WRITE, params)

    def angle_limit_read(self, servo_id: int) -> Tuple[float, float]:
        """
        Read the servo's angle limits.

        Tuple of (min_angle_degrees, max_angle_degrees).
        """
        response = self._send_and_receive_packet(servo_id,
                                                 constants._SERVO_ANGLE_LIMIT_READ)

        min_angle, max_angle = constants._2_UNSIGNED_SHORTS_STRUCT.unpack(
            response.parameters)

        min_angle_degrees = utils._ticks_to_degrees(min_angle)
        max_angle_degrees = utils._ticks_to_degrees(max_angle)

        return min_angle_degrees, max_angle_degrees


    # Voltage & Power Limits

    def vin_limit_write(self, servo_id: int, min_voltage: types.Real,
                        max_voltage: types.Real) -> None:
        """
        servo_id:
        min_voltage - Minimum input voltage in Volts.
        max_voltage - Maximum input voltage in Volts.

        Set limits on the servo's input voltage.
        returns error if min_voltage >= max_voltage.

        """

        def scrub_voltage(v: types.Real) -> int:
            # Convert to millivolts and clamp to valid range
            v = int(round(v * 1000))
            return min(max(4500, v), 12000)

        min_voltage_mv = scrub_voltage(min_voltage)
        max_voltage_mv = scrub_voltage(max_voltage)

        if min_voltage_mv > max_voltage_mv:
            raise ValueError(
                f'min_voltage must be less than max_voltage; got min_voltage={min_voltage} (==> min_voltage_mv={min_voltage_mv}) '
                f'and max_voltage={max_voltage} (==> max_voltage_mv={max_voltage_mv}).')

        params = constants._2_UNSIGNED_SHORTS_STRUCT.pack(min_voltage_mv, max_voltage_mv)
        self._send_packet(servo_id, constants._SERVO_VIN_LIMIT_WRITE, params)

    def vin_limit_read(self, servo_id: int) -> Tuple[float, float]:
        """
        Read the servo's voltage limits.

        Returns Tuple of (min_voltage_volts, max_voltage_volts).
        """
        response = self._send_and_receive_packet(servo_id,
                                                 constants._SERVO_VIN_LIMIT_READ)

        min_voltage_mv, max_voltage_mv = constants._2_UNSIGNED_SHORTS_STRUCT.unpack(
            response.parameters)
        min_voltage = min_voltage_mv / 1000
        max_voltage = max_voltage_mv / 1000

        return min_voltage, max_voltage

    # Temperature Limits & Readings

    def temp_max_limit_write(self, servo_id: int, temp: types.Real,
                             units: str = 'F') -> None:
        """
        servo_id:
        temp - Maximum temperature limit.
        units - 'C' for Celsius or 'F' for Fahrenheit.

        set the maximum temperature limit for the servo.
        returns error if temp is out of range [50°C, 100°C] or [122°F, 212°F].

        """

        units = utils._validate_temp_units(units)

        if units == 'F':
            temp = utils._fahrenheit_to_celsius(temp)

        temp = int(round(temp))
        temp = min(max(50, temp), 100)

        self._send_packet(servo_id, constants._SERVO_TEMP_MAX_LIMIT_WRITE, bytes((temp,)))

    def temp_max_limit_read(self, servo_id: int,
                            units: str = 'F') -> float:
        """
        servo_id:
        units - 'C' for Celsius or 'F' for Fahrenheit.

        returns the maximum temperature limit.
        """
        units = utils._validate_temp_units(units)

        response = self._send_and_receive_packet(servo_id,
                                                 constants._SERVO_TEMP_MAX_LIMIT_READ)

        temp = float(response.parameters[0])
        if units == 'F':
            temp = utils._celsius_to_fahrenheit(temp)

        return temp

    def temp_read(self, servo_id: int, units: str = 'F') -> float:
        """
        servo_id:
        units - 'C' for Celsius or 'F' for Fahrenheit.

        read the servo's current temperature.

        """
        units = utils._validate_temp_units(units)

        response = self._send_and_receive_packet(servo_id, constants._SERVO_TEMP_READ)

        temp = float(response.parameters[0])

        if units.upper() == 'F':
            temp = utils._celsius_to_fahrenheit(temp)

        return temp

    # Sensor Readings

    def vin_read(self, servo_id: int) -> float:
        """
        read the servo's current input voltage (in Volts).

        """
        response = self._send_and_receive_packet(servo_id, constants._SERVO_VIN_READ)

        vin_mv = constants._1_SIGNED_SHORT_STRUCT.unpack(response.parameters)[0]

        return vin_mv / 1000

    def pos_read(self, servo_id: int) -> float:
        """
        read the servo's current position (in degrees).

        """
        response = self._send_and_receive_packet(servo_id, constants._SERVO_POS_READ)

        angle = constants._1_SIGNED_SHORT_STRUCT.unpack(response.parameters)[0]

        return utils._ticks_to_degrees(angle)


    # Mode Configuration (Servo vs Motor)

    def mode_write(self, servo_id: int, mode: str,
                   speed: Optional[types.Real] = None) -> None:
        """
        servo_id:
        mode - 'servo' (hold position) or 'motor' (rotate continuously).
        speed - Speed in degrees per second (required if mode='motor').

        Set the servo's operating mode.
        speed is restricted to [-1000, 1000] degrees/second.

        """

        if mode.lower() not in {'motor', 'servo'}:
            raise ValueError(
                f'mode must be either "motor" or "servo"; got "{mode}".')

        mode = mode.lower()
        if mode == 'motor':
            if speed is None:
                raise ValueError('speed must be specified if mode is "motor".')

            speed = int(round(speed))
            speed = min(max(-1000, speed), 1000)
        else:
            speed = 0

        params = constants._1_UNSIGNED_CHAR_1_UNSIGNED_SHORT_STRUCT.pack(
            1 if mode == 'motor' else 0, speed)
        self._send_packet(servo_id, constants._SERVO_OR_MOTOR_MODE_WRITE, params)

    def mode_read(self, servo_id: int) -> Tuple[str, Optional[int]]:
        """
        servo_id:
        returns the current mode and speed setting.
        Mode is 'servo' or 'motor'.
        Speed is in degrees/second if mode is 'motor', else None.

        """
        response = self._send_and_receive_packet(servo_id,
                                                 constants._SERVO_OR_MOTOR_MODE_READ)

        mode, speed = constants._1_UNSIGNED_CHAR_1_UNSIGNED_SHORT_STRUCT.unpack(
            response.parameters)

        if mode == 0:
            mode = 'servo'
            speed = None
        elif mode == 1:
            mode = 'motor'
            speed = int(speed)
        else:
            raise ValueError(f'Received unknown mode: {mode}')

        return mode, speed

    # Power & Torque Control

    def set_powered(self, servo_id: int, powered: bool) -> None:
        """
        servo_id:

        Enable (True) or disable (False) servo torque (motor on/off).

        """
        self._send_packet(servo_id, constants._SERVO_LOAD_OR_UNLOAD_WRITE,
                          b'\x01' if powered else b'\x00')

    def is_powered(self, servo_id: int) -> bool:
        """
        servo_id:

        returns True if servo torque is currently enabled.

        """
        if servo_id < constants.MIN_ID or servo_id > constants.MAX_ID:
            raise ValueError(
                f'servo_id must be in range [{constants.MIN_ID}, {constants.MAX_ID}]; '
                f'got {servo_id}.')

        response = self._send_and_receive_packet(servo_id,
                                                 constants._SERVO_LOAD_OR_UNLOAD_READ)
        return bool(response.parameters[0])


    # LED Control & Status Indicators

    def led_ctrl_write(self, servo_id: int, state: bool) -> None:
        """
        servo_id:
        state - If True, enable the LED; if False, disable it.

        Control the LED state when there are no errors.
        """
        self._send_packet(servo_id, constants._SERVO_LED_CTRL_WRITE,
                          b'\x00' if state else b'\x01')

    def led_ctrl_read(self, servo_id: int) -> bool:
        """
        Read the servo's LED control state.

        Returns True if LED is enabled, False if disabled.
        """
        response = self._send_and_receive_packet(servo_id, constants._SERVO_LED_CTRL_READ)
        return response.parameters == b'\x00'

    def led_error_write(self, servo_id: int, stalled: bool, over_voltage: bool,
                        over_temp: bool) -> None:
        """
        servo_id:
        stalled - If True, LED will indicate stall errors.
        over_voltage - If True, LED will indicate over-voltage errors.
        over_temp - If True, LED will indicate over-temperature errors.


        Returns booleans indicating which error conditions trigger the LED.
        """
        params = (stalled << 2) | (over_voltage << 1) | over_temp
        params = bytes((params,))
        self._send_packet(servo_id, constants._SERVO_LED_ERROR_WRITE, params)

    def led_error_read(self, servo_id: int) -> Tuple[bool, bool, bool]:
        """
        Read which error conditions trigger the LED.

        Returns Tuple of (stalled, over_voltage, over_temp) booleans.
        """
        result = self._send_and_receive_packet(servo_id, constants._SERVO_LED_ERROR_READ)
        params = result.parameters[0]

        stalled = bool(params & 4)
        over_voltage = bool(params & 2)
        over_temp = bool(params & 1)

        return stalled, over_voltage, over_temp
