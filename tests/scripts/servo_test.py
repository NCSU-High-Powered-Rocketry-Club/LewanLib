import time
from lewanlib.bus import ServoBus

port = "/dev/ttyAMA0"
servo_id = 1

with ServoBus(port=port, baudrate=115200, on_exit_power_off=False) as bus:
    servo = bus.get_servo(servo_id)
    current_angle = servo.pos_read()
    try:
        while True:
            current_extension = servo.pos_read()
            print(f"Current extension: {current_extension}")
            print("Up arrow for extension, down arrow for retraction")
            match str(input()):
                case "up":
                    servo.move_time_write(current_angle + 5, 1)
                    current_angle += 5
                case "down":
                    servo.move_time_write(current_angle - 5, 1)
                    current_angle -= 5
                case _:
                    print("Invalid input")
                    continue
            print(f"Current Voltage: {servo.vin_read()}")
            print(f"Current Temp: {servo.temp_read()}")
            print(f"")
    except KeyboardInterrupt:
        pass