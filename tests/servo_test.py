from lewanlib.bus import ServoBus

port = "/dev/ttyAMA0"
servo_id = 1

with ServoBus(port=port, baudrate=115200) as bus:
    servo = bus.get_servo(servo_id)
    # Write tests
    servo.angle_offset_adjust(5.0)
    servo.angle_offset_write()
    servo.angle_limit_write(10.0, 230.0)
    servo.vin_limit_write(6.0, 12.0)
    servo.temp_max_limit_write(75.0)
    servo.id_write(servo_id)  # Re-write same ID for test
    
    # Move tests 
    servo.set_powered(True)
    servo.move_time_write(120.0, 1.0, wait=True)
    servo.move_time_wait_write(60.0, 1.0)
    servo.move_start()
    servo.move_stop()
    servo.set_powered(False)

    # Read tests
    servo.angle_offset_read()
    servo.angle_limit_read()
    servo.vin_limit_read()
    servo.temp_max_limit_read()
    servo.temp_read(units='C')
    servo.temp_read(units='F')
    servo.vin_read()
    servo.pos_read()
    servo.mode_read()