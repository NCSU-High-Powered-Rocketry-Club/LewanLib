"""
Module containing constants and packet/struct definitions for the LewanSoul servo protocol.

This module centralizes all magic numbers, protocol constants, and binary struct formats
used throughout the library. By keeping them in one place, we make the code easier to
maintain and modify if the protocol changes.

See: https://images-na.ssl-images-amazon.com/images/I/71WyZDfQwkL.pdf (LewanSoul protocol spec)
"""
import struct

# SERVO IDENTIFICATION CONSTANTS

MIN_ID = 0                    # Minimum valid servo ID
MAX_ID = 253                  # Maximum valid servo ID (254 is broadcast-only)
BROADCAST_ID = 254           # Special ID: commands sent here affect ALL servos on the bus

# SERVO MOTION RANGE

MIN_ANGLE_DEGREES = 0         # Servo range minimum: 0 degrees
MAX_ANGLE_DEGREES = 240       # Servo range maximum: 240 degrees

# PACKET STRUCTURE & HEADER

_PACKET_HEADER = b'\x55\x55'  # Magic bytes that start every packet (0x55, 0x55)

_1_SIGNED_CHAR_STRUCT = struct.Struct('<b')

_1_SIGNED_SHORT_STRUCT = struct.Struct('<h')

_1_UNSIGNED_CHAR_1_UNSIGNED_SHORT_STRUCT = struct.Struct('<bxh')

_2_UNSIGNED_SHORTS_STRUCT = struct.Struct('<HH')

# SERVO COMMAND CODES (from the LewanSoul protocol specification)

# --- MOTION COMMANDS ---
_SERVO_MOVE_TIME_WRITE = 1         # Command: Move to angle over specified time (immediate)
_SERVO_MOVE_TIME_READ = 2          # Command: Read the last angle+time set by MOVE_TIME_WRITE
_SERVO_MOVE_TIME_WAIT_WRITE = 7    # Command: Queue a move, but DON'T start it yet
_SERVO_MOVE_TIME_WAIT_READ = 8     # Command: Read the queued move (from MOVE_TIME_WAIT_WRITE)
_SERVO_MOVE_START = 11             # Command: Start executing all queued moves
_SERVO_MOVE_STOP = 12              # Command: Stop the servo immediately

# --- IDENTIFICATION COMMANDS ---
_SERVO_ID_WRITE = 13               # Command: Change this servo's ID (e.g., 1 -> 5)
_SERVO_ID_READ = 14                # Command: Read this servo's current ID

# --- ANGLE CALIBRATION COMMANDS ---

_SERVO_ANGLE_OFFSET_ADJUST = 17    # Command: Temporarily adjust the angle offset
_SERVO_ANGLE_OFFSET_WRITE = 18     # Command: Save the offset to non-volatile memory
_SERVO_ANGLE_OFFSET_READ = 19      # Command: Read the saved offset

# --- ANGLE LIMIT COMMANDS ---
_SERVO_ANGLE_LIMIT_WRITE = 20      # Command: Set min and max angles (soft limits)
_SERVO_ANGLE_LIMIT_READ = 21       # Command: Read the current angle limits

# --- VOLTAGE LIMIT COMMANDS ---
_SERVO_VIN_LIMIT_WRITE = 22        # Command: Set min and max supply voltage
_SERVO_VIN_LIMIT_READ = 23         # Command: Read the voltage limits

# --- TEMPERATURE LIMIT COMMANDS ---
_SERVO_TEMP_MAX_LIMIT_WRITE = 24   # Command: Set maximum allowed temperature
_SERVO_TEMP_MAX_LIMIT_READ = 25    # Command: Read the temperature limit

# --- SENSOR READ COMMANDS ---
_SERVO_TEMP_READ = 26              # Command: Read current servo temperature (in Celsius)
_SERVO_VIN_READ = 27               # Command: Read current input voltage (in mV)
_SERVO_POS_READ = 28               # Command: Read current servo position (in ticks)

# --- MODE COMMANDS ---
_SERVO_OR_MOTOR_MODE_WRITE = 29    # Command: Switch between servo mode and motor mode
_SERVO_OR_MOTOR_MODE_READ = 30     # Command: Read current mode and speed

# --- POWER/TORQUE COMMANDS ---
_SERVO_LOAD_OR_UNLOAD_WRITE = 31   # Command: Enable (1) or disable (0) torque
_SERVO_LOAD_OR_UNLOAD_READ = 32    # Command: Read torque enable status

# --- LED INDICATOR COMMANDS ---
_SERVO_LED_CTRL_WRITE = 33         # Command: Set LED state (on/off in normal operation)
_SERVO_LED_CTRL_READ = 34          # Command: Read LED control setting
_SERVO_LED_ERROR_WRITE = 35        # Command: Set which error types trigger the LED
_SERVO_LED_ERROR_READ = 36         # Command: Read LED error configuration
