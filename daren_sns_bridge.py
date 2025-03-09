import sys
import subprocess
import threading
from time import sleep, time
import serial

from utils import open_serial_port, logger
from bms.sns01_485 import Daren485v2
from parse import daren_parse_and_print_payload


class DarenSNSBridge:
    def __init__(self, daren_port, sns_port, daren_baud, sns_baud, sns_addresses):
        self.daren_port = daren_port
        self.sns_port = sns_port
        self.daren_baud = daren_baud
        self.sns_baud = sns_baud
        self.sns_addresses = sns_addresses
        self.running = True

    def listen_to_daren(self):
        """Listen for messages on the Daren master port."""
        try:
            with open_serial_port(self.daren_port, self.daren_baud) as daren_ser:
                if not daren_ser or not daren_ser.is_open:
                    logger.error(f"Failed to open Daren master port {self.daren_port}.")
                    return

                daren_ser.reset_input_buffer()
                logger.info(f"Listening to Daren master on {self.daren_port} @ {self.daren_baud}...")

                last_received_time = time()  # Track last received message time
                timeout_threshold = 10  # Number of seconds to wait before assuming failure

                while self.running:
                    message = self.read_from_serial(daren_ser)

                    if message:
                        logger.debug(f"Received: {message}")
                        last_received_time = time()  # Reset timeout tracking
                        self.handle_message(message)

                    elif time() - last_received_time > timeout_threshold:
                        logger.info(f"No messages received for {timeout_threshold} seconds. Assuming connection lost.")
                        break  # Exit the loop to allow recovery

                    # Check if the port is still open (helps detect cable or network disconnects.)
                    if not daren_ser.is_open:
                        logger.error("Daren master port unexpectedly closed - most likely a physical or network connection issue.")
                        break

        except (serial.SerialException, IOError) as e:
            logger.error(f"Serial port error: {e}. Check connections.")
        except Exception as e:
            logger.error(f"Unexpected error in listen_to_daren: {e}")

    def handle_message(self, message):
        """Determine if a message is a master request or a slave reply."""
        if self.is_master_request(message):
            addr_str = message[3:5]
            addr = bytes.fromhex(addr_str.decode())
            if addr in self.sns_addresses:
                logger.debug(f"Handling master request for SNS address: {addr}")
                threading.Thread(target=self.handle_request, args=(addr,)).start()
            else:
                logger.debug(f"Master request for unhandled address: {addr}")
        else:
            logger.info(f"Received slave reply: {message}")

    @staticmethod
    def is_master_request(request):
        """Check if the message is a valid master request."""
        try:
            if not request.startswith(b'~22'):
                logger.debug(f"Ignoring non-master message: {request}")
                return False

            addr_str = request[3:5]
            addr = int(addr_str.decode(), 16)
            if 0 <= addr <= 31:
                logger.debug(f"Valid master request for address {addr}.")
                return True

            logger.debug(f"Ignoring invalid master address: {addr}.")
            return False
        except (IndexError, ValueError) as e:
            logger.error(f"Malformed request or address parsing error: {e}")
            return False

    def handle_request(self, sns_addr):
        """Forward the request to the SNS slave and respond to the master."""
        logger.debug(f"Handling request for SNS address: {sns_addr}")
        sns_response = self.query_sns_slave(sns_addr)
        if sns_response:
            logger.debug(f"Received response from SNS slave: {sns_response}")
            daren_response = self.transform_response(sns_response)
            logger.debug(f"Transformed response for Daren master: {daren_response}")
            self.send_to_daren(daren_response)
        else:
            logger.error("No response received from SNS slave.")

    def query_sns_slave(self, sns_addr):
        """Send a command to the SNS slave and return the response (ASCII) or None on failure."""
        logger.debug(f"Querying SNS slave at address {sns_addr}...")

        sns_slave = Daren485v2(self.sns_port, self.sns_baud, sns_addr)
        # command = '>22088484E00208FD1D\r' # SNS Sniffed command from an SNS Master (for some reason ignored by slave)
        command = '>220842420000FDA8\r'  # SNS service 42 command (working)
        logger.debug(f"Constructed SNS command: {command}")

        with open_serial_port(sns_slave.port, sns_slave.baud_rate) as sns_ser:
            if not sns_ser or not sns_ser.is_open:
                logger.error(f"Failed to open SNS slave port {self.sns_port}.")
                return None

            max_attempts = 1
            for attempt in range(max_attempts):
                logger.debug(f"Sending command to SNS slave (Attempt {attempt + 1})...")
                self.write_to_serial(sns_ser, command.encode())

                # Read raw bytes until we get a '\r' or timeout
                response_bytes = self.read_from_serial(sns_ser)

                if not response_bytes:
                    logger.warning(f"No response from SNS slave on attempt {attempt + 1}. Retrying...")
                    sleep(0.5)
                    continue

                logger.debug(f"Raw bytes from SNS slave: {response_bytes}")

                # Try to decode as ASCII
                try:
                    response_str = response_bytes.decode('ascii')
                except UnicodeDecodeError as e:
                    logger.warning(f"Non-ASCII data from SNS slave (attempt {attempt + 1}): {e}")
                    # We can retry
                    sleep(0.2)
                    continue

                # Now we have an ASCII string. Optionally validate format:
                if not (response_str.startswith('>') or response_str.startswith('~')):
                    logger.warning(f"Unexpected SNS response format: {response_str}")
                    # Retry or continue if you expect strictly '>' or '~'
                    sleep(0.2)
                    continue

                # If it looks okay, return the raw bytes
                logger.debug(f"Valid SNS ASCII response: {response_str}")
                return response_bytes

            # If we get here, all attempts failed.
            logger.error("Failed to communicate with SNS slave after 3 attempts.")
            return None

    def transform_response(self, sns_response):
        """
        Transform the 'Ho' (SNS) response into a shortened 'Daren' response
        with matching offsets, length, and checksum.
        """
        if not sns_response:
            logger.error("Cannot transform an empty response.")
            return None

        logger.info(sns_response)

        try:
            # 1) Parse the payload from the Ho raw message (skip first 13 bytes of header and last 5 bytes for CRC+\r).
            full_len = len(sns_response)
            ho_payload_hex = sns_response[13: full_len - 5]  # in ASCII hex
            ho_payload_str = ho_payload_hex.decode("ascii")

            if len(ho_payload_str) < 152:
                logger.info("SNS payload is shorter than expected. Not attempting partial parse.")
                return None

            # Initialize the Daren payload with the correct size (148 hex chars for the payload)
            daren_payload_list = list("08FE" + ho_payload_str[4:152])

            # Define mappings between Ho offsets and Daren offsets
            # Ho offsets correspond to where data resides in the Ho payload
            # Daren offsets correspond to where data should reside in the Daren payload
            ho_cell_voltage_offsets = [(i * 4 + 12, i * 4 + 16) for i in range(16)]  # 16 Ho cell voltages
            daren_cell_voltage_offsets = [(34 + i * 4, 34 + i * 4 + 4) for i in range(16)]  # 16 Daren cell voltages

            # Map Cell Voltages from Ho to Daren
            logger.debug("Mapping Cell Voltages:")
            for ho_range, daren_range in zip(ho_cell_voltage_offsets, daren_cell_voltage_offsets):
                ho_start, ho_end = ho_range
                daren_start, daren_end = daren_range
                ho_data = ho_payload_str[ho_start:ho_end]
                logger.debug(f"Ho Voltage {ho_data} -> Daren Offset {daren_start}:{daren_end}")
                # Replace the corresponding slice in the Daren payload
                daren_payload_list[daren_start:daren_end] = list(ho_data)

            # Define mappings for static fields
            # Daren target offsets on the left and Ho01 offsets to retrieve from on the right
            static_mappings = {
                (14, 18): (114, 118),  # SOH
                (18, 22): (124, 128),  # Remaining Capacity / SOC
                (22, 26): (120, 124),  # Installed Cap / Available Cap
                (26, 30): (120, 124),  # Installed Capacity / Available Cap
                (98, 102): (84, 88),  # MOS Temp
                (102, 118): (90, 106),  # Cell Temps
            }

            # Remap static fields
            self.remap_static_fields(daren_payload_list, ho_payload_str, static_mappings)

            # Convert the updated payload list back to a string
            daren_payload_str = "".join(daren_payload_list)

            logger.debug(f"{ho_payload_str}")
            logger.debug(f"{daren_payload_str}")
            logger.debug(f"Ho -> Daren translation complete. Chopping addr and data flag...")
            daren_payload_str = daren_payload_str[4:152]

            # repalce last 19 bytes with hardcoded alarm data and running state (currently do not know how to map this yet)
            daren_payload_str = daren_payload_str[:-29] + '00000000001000000000003000000'

            # Encode the payload to ASCII bytes
            daren_payload = daren_payload_str.encode("ascii")

            # 2) Construct the final Daren frame
            # Header is fixed: "~22084A85F09808FE" (8 bytes of SOI + header + fixed padding)
            soi = b"~"
            header_hex = b"22084A85F09808FE"
            partial_frame = soi + header_hex + daren_payload

            # Compute the checksum for the frame
            frame_checksum = DarenSNSBridge.calculate_checksum(partial_frame[1:])
            frame_cs_hex = f"{frame_checksum:04X}".encode("ascii")

            # Construct the full frame with checksum and trailing "\r"
            final_frame = partial_frame + frame_cs_hex + b"\r"

            # Log and return the final frame
            daren_parse_and_print_payload(final_frame.decode("ascii"))
            return final_frame

        except Exception as e:
            logger.error(f"Error transforming response: {e}")
            return None

    @staticmethod
    def remap_static_fields(daren_payload_list, ho_payload_str, mappings):
        """
        Remap static fields from Ho payload to Daren payload based on provided mappings.
        Args:
            daren_payload_list (list): The Daren payload represented as a mutable list of characters.
            ho_payload_str (str): The Ho payload as a string.
            mappings (dict): A dictionary defining the remapping structure where
                             key = (start_offset, end_offset) in Daren payload,
                             value = (start_offset, end_offset) in Ho payload.
        """
        logger.debug("Remapping Static Fields:")
        for daren_range, ho_range in mappings.items():
            daren_start, daren_end = daren_range
            ho_start, ho_end = ho_range
            ho_data = ho_payload_str[ho_start:ho_end]
            logger.debug(f"Ho Data {ho_data} -> Daren Offset {daren_start}:{daren_end}")
            daren_payload_list[daren_start:daren_end] = list(ho_data)

    @staticmethod
    def length_checksum(value):
        """Calculate the 12-bit length and 4-bit checksum for the LENGTH field."""
        value = value & 0x0FFF  # Mask to keep 12 bits
        n1 = value & 0xF
        n2 = (value >> 4) & 0xF
        n3 = (value >> 8) & 0xF
        chksum = ((n1 + n2 + n3) & 0xF) ^ 0xF
        chksum = chksum + 1
        return value + (chksum << 12)

    @staticmethod
    def calculate_checksum(message):
        """Calculate the checksum for a given byte message."""
        checksum = 0
        for value in message:
            checksum += value  # `value` is already an integer in a bytes object
        checksum = checksum ^ 0xFFFF
        return checksum + 1

    def send_to_daren(self, response):
        """Send the transformed response to the Daren master."""
        with open_serial_port(self.daren_port, self.daren_baud) as daren_ser:
            if not daren_ser.is_open:
                logger.error(f"Failed to open Daren master port {self.daren_port}.")
                return
            self.write_to_serial(daren_ser, response)
            logger.info(f"Response sent to Daren master for slave 8")
            logger.info(f"{response}\n")

    @staticmethod
    def read_from_serial(ser):
        """Read and assemble a complete message from the serial port."""
        try:
            buffer = b""
            while True:
                if ser.in_waiting > 0:
                    byte = ser.read(1)
                    buffer += byte
                    if byte == b"\r":  # End of frame
                        break
                else:
                    sleep(0.01)  # Small delay to allow more data to arrive
            logger.debug(f"Read complete message: {buffer}")
            return buffer if buffer else None
        except Exception as e:
            logger.error(f"Error while reading from serial port: {e}")
            subprocess.run(["killall", "-9", "socat"], check=False)
            sys.exit(1)

    @staticmethod
    def write_to_serial(ser, message):
        """Write a message to the serial port."""
        try:
            ser.flushOutput()
            ser.write(message)
            ser.flush()
            logger.debug(f"Message sent to serial port: {message} (length: {len(message)})")
        except Exception as e:
            logger.error(f"Failed to write to serial port: {e}")
            subprocess.run(["killall", "-9", "socat"], check=False)
            sys.exit(1)

    def start(self):
        """Start the bridge."""
        self.running = True
        listener_thread = threading.Thread(target=self.listen_to_daren)
        listener_thread.start()

    def stop(self):
        """Stop the bridge."""
        self.running = False
        logger.info("Stopping bridge...")


if __name__ == "__main__":
    # Configuration
    DAREN_PORT = "/dev/ttyUSB0"
    SNS_PORT = "/dev/ttyUSB1"
    DAREN_BAUD = 19200
    SNS_BAUD = 9600
    SNS_ADDRESSES = [b'\x08']  # List of SNS slave addresses to handle

    bridge = DarenSNSBridge(DAREN_PORT, SNS_PORT, DAREN_BAUD, SNS_BAUD, SNS_ADDRESSES)
    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()
        sys.exit(0)
    except Exception as e:
        print(f"Unhandled error: {e}. Exiting...")
        subprocess.run(["killall", "-9", "socat"], check=False)
        sys.exit(1)
