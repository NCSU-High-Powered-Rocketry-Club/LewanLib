"""
Unit tests for bus module

"""
from lewanlib import constants, types

def test_servo_packet_structure():
    """
    Test the _ServoPacket namedtuple structure and fields
    """
    # Create a servo packet
    servo_id = 1
    command = constants._SERVO_POS_READ
    parameters = b'\x00\x00'
    
    packet = types._ServoPacket(servo_id, command, parameters)
    
    # Verify fields are accessible and have correct values
    assert packet.servo_id == servo_id, \
        f"Packet servo_id should be {servo_id}, got {packet.servo_id}"
    assert packet.command == command, \
        f"Packet command should be {command}, got {packet.command}"
    assert packet.parameters == parameters, \
        f"Packet parameters should be {parameters}, got {packet.parameters}"
    
    # Verify it's a named tuple (has _fields)
    assert hasattr(packet, '_fields'), "Packet should be a namedtuple"
    assert 'servo_id' in packet._fields, "Packet should have servo_id field"
    assert 'command' in packet._fields, "Packet should have command field"
    assert 'parameters' in packet._fields, "Packet should have parameters field"