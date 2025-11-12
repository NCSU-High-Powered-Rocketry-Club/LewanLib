"""
Shared type definitions used throughout the lewanlib package.

This module defines type aliases and data structures that are used across
multiple modules to ensure consistency and readability.
"""
from typing import Union, NamedTuple

Real = Union[float, int]

class _ServoPacket(NamedTuple):
    """
    
    """
    servo_id: int
    command: int
    parameters: bytes
