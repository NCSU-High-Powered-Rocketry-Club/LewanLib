import time
from lewanlib.bus import ServoBus
from lewanlib.gpio import GPIOPin

port = "/dev/ttyAMA0"
servo_id = 1
tx_disable = GPIOPin(20, chip_path="/dev/gpiochip0")
rx_disable = GPIOPin(16, chip_path="/dev/gpiochip0")

# Set bias as requested
# tx_disable.set_bias('pull_up')
# rx_disable.set_bias('pull_up')

with ServoBus(port=port, baudrate=115200, on_exit_power_off=False, discard_echo=False, 
              tx_disable=tx_disable, rx_disable=rx_disable) as bus:
    servo = bus.get_servo(servo_id)
    # tx_disable.off()
    # rx_disable.on()
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
    # # Don't wait for the full move (wait=False), but give a tiny delay for bus stability
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
    # tx_disable.on()
    # rx_disable.off()
    time.sleep(0.05)
    print("angle offset ", servo.angle_offset_read())
    print("angle limit ", servo.angle_limit_read())
    print("vin limit ", servo.vin_limit_read())
    print("temp max limit ", servo.temp_max_limit_read())
    print("temp read c ", servo.temp_read(units='C'))
    print(servo.temp_read(units='F'))
    print("voltage in read ", servo.vin_read())
    print("servo pos read ", servo.pos_read())
    print(servo.mode_read())

    # servo.set_powered(False)
tx_disable.close()
rx_disable.close()
