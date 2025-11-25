import time
from lewanlib.bus import ServoBus

port = "/dev/ttyAMA0"
servo_id = 1

with ServoBus(port=port, baudrate=115200, on_exit_power_off=False) as bus:
    print("here")
    servo = bus.get_servo(servo_id)
    # Write tests
    # servo.angle_offset_adjust(5.0)
    # servo.angle_offset_write()
    # servo.angle_limit_write(10.0, 230.0)
    # servo.vin_limit_write(6.0, 12.0)
    # servo.temp_max_limit_write(75.0)
    servo.id_write(servo_id)  # Re-write same ID for test
    print("Rewrote id")
    
    # Move tests 
    servo.set_powered(True)
    # Don't wait for the full move (wait=False), but give a tiny delay for bus stability
    servo.move_time_write(100.0, 0.1, wait=True)
    time.sleep(0.05) 
    servo.move_start()
    time.sleep(0.05)
    
    servo.move_time_wait_write(11.0, 0.0)
    # servo.move_start()
    # time.sleep(0.5)
    #servo.move_stop()
    # servo.set_powered(False)

    # Read tests
    print("angle offset ", servo.angle_offset_read())
    print("angle limit ", servo.angle_limit_read())
    print("vin limit ", servo.vin_limit_read())
    print("temp max limit ", servo.temp_max_limit_read())
    print("temp read c ", servo.temp_read(units='C'))
    print(servo.temp_read(units='F'))
    print("voltage in read ", servo.vin_read())
    print("servo pos read ", servo.pos_read())
    print(servo.mode_read())

    servo.set_powered(False)
