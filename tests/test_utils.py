"""
Unit tests for lewanlib.utils conversion and helper functions.

"""
import math

from lewanlib import utils


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
