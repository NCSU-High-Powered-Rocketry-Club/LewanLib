import unittest
from unittest.mock import MagicMock, patch
import struct
from lewanlib.bus import ServoBus, ServoBusError
from lewanlib import constants, utils

class TestBusReliability(unittest.TestCase):
    def test_receive_packet_with_noise(self):
        # Create a mock serial connection
        mock_serial = MagicMock()
        
        # Construct a valid packet
        servo_id = 1
        command = constants._SERVO_POS_READ
        parameters = b'\x10\x00' # Some dummy data
        
        # Calculate checksum
        length = 3 + len(parameters)
        checksum = utils._calculate_checksum(servo_id, length, command, parameters)
        
        valid_packet = bytearray()
        valid_packet.append(servo_id)
        valid_packet.append(length)
        valid_packet.append(command)
        valid_packet.extend(parameters)
        valid_packet.append(checksum)
        
        # The stream contains:
        # 1. Garbage (0xff, 0xff)
        # 2. Partial header (0x55, 0xaa) - should be rejected
        # 3. More garbage (0xff)
        # 4. Valid header (0x55, 0x55)
        # 5. Valid packet body
        
        stream_data = b'\xff\xff\x55\xaa\xff' + constants._PACKET_HEADER + valid_packet
        
        # Configure the mock to return bytes from the stream one by one (or in chunks)
        # The bus code calls read(1) or read(N).
        # We'll make a side_effect that pops bytes from the stream.
        
        stream_iter = iter(stream_data)
        
        def read_side_effect(size=1):
            result = bytearray()
            for _ in range(size):
                try:
                    result.append(next(stream_iter))
                except StopIteration:
                    break
            return bytes(result)
            
        mock_serial.read.side_effect = read_side_effect
        
        # Initialize ServoBus with the mock connection
        bus = ServoBus(serial_conn=mock_serial)
        
        # Call _receive_packet
        packet = bus._receive_packet()
        
        # Verify we got the correct packet
        self.assertEqual(packet.servo_id, servo_id)
        self.assertEqual(packet.command, command)
        self.assertEqual(packet.parameters, parameters)
        
    def test_receive_packet_timeout(self):
        # Test that it eventually times out if no header is found
        mock_serial = MagicMock()
        
        # Infinite stream of garbage (limited by the loop in code)
        # We'll provide enough garbage to hit the loop limit (now 2048, so use 3000)
        stream_data = b'\xff' * 3000
        stream_iter = iter(stream_data)
        
        def read_side_effect(size=1):
            result = bytearray()
            for _ in range(size):
                try:
                    result.append(next(stream_iter))
                except StopIteration:
                    break
            return bytes(result)
            
        mock_serial.read.side_effect = read_side_effect
        
        bus = ServoBus(serial_conn=mock_serial)
        
        with self.assertRaises(ServoBusError) as cm:
            bus._receive_packet()
        
        self.assertIn("Timed out", str(cm.exception))

    def test_receive_packet_with_heavy_noise(self):
        # Test that we can recover from heavy noise (e.g. 1000 bytes)
        mock_serial = MagicMock()
        
        servo_id = 1
        command = constants._SERVO_POS_READ
        parameters = b'\x10\x00'
        length = 3 + len(parameters)
        checksum = utils._calculate_checksum(servo_id, length, command, parameters)
        
        valid_packet = bytearray()
        valid_packet.append(servo_id)
        valid_packet.append(length)
        valid_packet.append(command)
        valid_packet.extend(parameters)
        valid_packet.append(checksum)
        
        # 1000 bytes of garbage then the packet
        stream_data = b'\xff' * 1000 + constants._PACKET_HEADER + valid_packet
        
        stream_iter = iter(stream_data)
        def read_side_effect(size=1):
            result = bytearray()
            for _ in range(size):
                try:
                    result.append(next(stream_iter))
                except StopIteration:
                    break
            return bytes(result)
        mock_serial.read.side_effect = read_side_effect
        
        bus = ServoBus(serial_conn=mock_serial)
        packet = bus._receive_packet()
        
        self.assertEqual(packet.servo_id, servo_id)

    def test_retry_logic(self):
        # Test that _send_and_receive_packet retries on failure
        mock_serial = MagicMock()
        
        servo_id = 1
        command = constants._SERVO_POS_READ
        parameters = b'\x00' # Dummy
        
        # First attempt: Timeout (empty read)
        # Second attempt: Success
        
        # Construct valid response packet
        resp_params = b'\x10\x00'
        length = 3 + len(resp_params)
        checksum = utils._calculate_checksum(servo_id, length, command, resp_params)
        valid_packet = constants._PACKET_HEADER + bytes([servo_id, length, command]) + resp_params + bytes([checksum])
        
        # Stream: 
        # 1. (Attempt 1) Read header -> Timeout (empty)
        # 2. (Attempt 2) Read header -> Valid packet
        
        # Note: _send_packet calls reset_input_buffer, then write, then read(echo).
        # We need to mock those too or ignore them.
        # _receive_packet calls read(1) repeatedly.
        
        # Let's make read return empty bytes for the first few calls (simulating timeout on first attempt)
        # Then return valid packet bytes.
        
        # We need to be careful about how many reads happen.
        # Attempt 1:
        #   _receive_packet calls read(1). Returns b''. Loop breaks. Raises ServoBusError.
        # Attempt 2:
        #   _receive_packet calls read(1). Returns 'U'. Then 'U'. Then rest of packet.
        
        stream_data = valid_packet
        stream_iter = iter(stream_data)
        
        call_count = [0]
        
        def read_side_effect(size=1):
            call_count[0] += 1
            # Fail the first attempt (say, first 5 reads return empty)
            # Wait, if read(1) returns empty, it breaks immediately in the new code.
            if call_count[0] <= 1: 
                return b''
            
            # Success on subsequent calls
            result = bytearray()
            for _ in range(size):
                try:
                    result.append(next(stream_iter))
                except StopIteration:
                    break
            return bytes(result)
            
        mock_serial.read.side_effect = read_side_effect
        
        bus = ServoBus(serial_conn=mock_serial, retry_count=3)
        
        # We need to mock write so it doesn't fail
        mock_serial.write.return_value = None
        
        response = bus._send_and_receive_packet(servo_id, command, parameters)
        
        self.assertEqual(response.servo_id, servo_id)
        self.assertEqual(response.command, command)
        # Verify that we retried (call_count > 1)
        self.assertGreater(call_count[0], 1)


if __name__ == '__main__':
    unittest.main()
