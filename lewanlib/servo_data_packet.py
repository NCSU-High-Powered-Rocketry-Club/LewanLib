import msgspec

class ServoDataPacket(msgspec.Struct, tag=True, array_like=True):

    servo_id: int
    current_position: float
    velocity: float
    angel_offset: float
    current_temp: float
    voltage: float


