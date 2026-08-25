import time
from lewanlib.bus import ServoBus
from sshkeyboard import listen_keyboard

# Servo setup
port = "/dev/ttyAMA0"
servo_id = 1
current_extension = 10  # starting position

# Callback for key presses
def press(key):
    global current_extension
    if key == "up":
        current_extension += 20
        servo.move_time_write(current_extension, .25, wait=False)
        print(f"Moved up to {current_extension}")
    elif key == "down":
        current_extension -= 20
        servo.move_time_write(current_extension, .25, wait=False)
        print(f"Moved down to {current_extension}")
    elif key == "q":
        print("Exiting...")
        return False  # stop listener

# Initialize servo bus
with ServoBus(port=port, baudrate=115200, on_exit_power_off=False) as bus:
    servo = bus.get_servo(servo_id)
    servo.id_write(servo_id)
    servo.set_powered(True)

    print("Use arrow keys to move servo. Press 'q' to quit.")
    listen_keyboard(on_press=press)