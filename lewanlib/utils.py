"""
Utility functions and conversions used by the library.

This module contains pure, stateless helper functions that don't depend on hardware.
They handle unit conversions, data validation, and protocol-level calculations.
These functions are easy to test and can be reused in other servo-related projects.
"""
from typing import Union

from . import constants

# Type alias: numeric values (int or float) representing angles, temps, voltages, etc.
Real = Union[float, int]


def truncate_angle(angle_degrees: Real) -> Real:
    """
    returns angle_degrees if between MIN_ANGLE_DEGREES and MAX_ANGLE_DEGREES else returns nearest limit.

    """
    return min(max(constants.MIN_ANGLE_DEGREES, angle_degrees),
               constants.MAX_ANGLE_DEGREES)


def _calculate_checksum(servo_id: int, length: int, command: int,
                        parameters: Union[bytearray, bytes]) -> int:
    """
    returns checksum byte for given packet components.

    """
    # Sum all relevant bytes
    checksum = servo_id + length + command + sum(parameters)
    # Bitwise NOT (~) gives us all bits flipped. The & 0xFF keeps only the lowest byte.
    checksum = ~checksum & 0xFF
    return checksum


def _celsius_to_fahrenheit(temp: Real) -> float:
    """
    Unit conversion from Celsius to Fahrenheit.
    """
    return (temp * 9 / 5) + 32

def _fahrenheit_to_celsius(temp: Real) -> float:
    """
    unit conversion from Fahrenheit to Celsius.
    """
    return (temp - 32) * 5 / 9


def _degrees_to_ticks(degrees: Real) -> int:
    """
    unit conversion from degrees to internal servo ticks.

    """
    return int(float(degrees * 1000 / constants.MAX_ANGLE_DEGREES))


def _ticks_to_degrees(ticks: int) -> float:
    """
    unit conversion from internal servo ticks to degrees.    

    """
    return ticks * constants.MAX_ANGLE_DEGREES / 1000


def _validate_temp_units(units: str) -> str:
    """
    checks that units is either 'C' or 'F', case-insensitive. Raises ValueError if not.
    """
    if units.upper() not in {'C', 'F'}:
        raise ValueError(f'Units must be either "C" or "F"; got "{units}".')

    return units.upper()
