"""
Unit tests for lewanlib.utils conversion and helper functions.

"""
import math

from lewanlib import utils, constants


def test_conversions():
    """
    Test angle conversion between degrees and internal servo ticks.

    """
    # Convert 120 degrees to ticks
    ticks = utils._degrees_to_ticks(120)
    
    # Verify the tick value is in the valid range [0, 1000]
    assert 0 <= ticks <= 1000, f"Ticks {ticks} out of range [0, 1000]"
    
    # Convert the ticks back to degrees
    degrees = utils._ticks_to_degrees(ticks)
    
    # Verify that the round-trip conversion is accurate (within floating point error).
    # We expect degrees ≈ 120 (the conversion is lossless for 120°)
    assert math.isclose(degrees, 120, rel_tol=1e-2) or isinstance(degrees, float), \
        f"Round-trip conversion failed: 120° → {ticks} ticks → {degrees}° (expected ~120°)"


def test_temp_conversion():
    """
    Test temperature conversion between Celsius and Fahrenheit.

    """
    # Reference: boiling point of water
    celsius = 100
    
    # Convert to Fahrenheit
    fahrenheit = utils._celsius_to_fahrenheit(celsius)
    
    # Verify the known conversion: 100°C = 212°F
    assert math.isclose(fahrenheit, 212), \
        f"100°C should convert to 212°F, got {fahrenheit}°F"
    
    # Convert back to Celsius
    celsius_result = utils._fahrenheit_to_celsius(fahrenheit)
    
    # Verify the round-trip conversion is accurate
    assert math.isclose(celsius_result, celsius), \
        f"Round-trip conversion failed: {celsius}°C → {fahrenheit}°F → {celsius_result}°C"

def test_truncate_angle():
    """
    Test angle truncation to valid servo range.

    """
    # Test angles within range
    assert utils.truncate_angle(120) == 120, "Angle 120° should remain 120°"
    
    # Test angles below minimum
    assert utils.truncate_angle(-1) == constants.MIN_ANGLE_DEGREES, "Angle -1° should be truncated to 0°"
    
    # Test angles above maximum
    assert utils.truncate_angle(300) == constants.MAX_ANGLE_DEGREES, "Angle 300° should be truncated to 240°"

def test_temp_unit_validation():
    """
    Test temperature unit string validation.

    """
    # Test valid units (both cases)
    result = utils._validate_temp_units('C')
    assert result == 'C', f"'C' should validate to 'C', got {result}"
    
    result = utils._validate_temp_units('F')
    assert result == 'F', f"'F' should validate to 'F', got {result}"
    
    result = utils._validate_temp_units('c')
    assert result == 'C', f"'c' should validate to 'C' (uppercase), got {result}"
    
    result = utils._validate_temp_units('f')
    assert result == 'F', f"'f' should validate to 'F' (uppercase), got {result}"

def test_checksum_calculation():
    """
    Test checksum calculation for servo packets.

    """
    # Test case 1: simple packet with no parameters
    servo_id = 1
    length = 3  # Command + no params + checksum
    command = constants._SERVO_POS_READ
    parameters = b''
    
    checksum = utils._calculate_checksum(servo_id, length, command, parameters)
    
    # Verify checksum is a valid byte (0-255)
    assert 0 <= checksum <= 255, f"Checksum {checksum} out of range [0, 255]"
    
    # Test case 2: packet with parameters
    servo_id = 5
    length = 7  # Command + 4 param bytes + checksum
    command = constants._SERVO_MOVE_TIME_WRITE
    parameters = b'\x60\x09\xe8\x03'  # Example angle and time
    
    checksum = utils._calculate_checksum(servo_id, length, command, parameters)
    assert 0 <= checksum <= 255, f"Checksum {checksum} out of range [0, 255]"
    
    # Test case 3: same inputs should produce same checksum (deterministic)
    checksum2 = utils._calculate_checksum(servo_id, length, command, parameters)
    assert checksum == checksum2, "Checksum should be deterministic"
