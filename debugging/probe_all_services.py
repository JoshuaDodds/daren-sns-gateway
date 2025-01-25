import serial
import time

# Configuration
PORT = "/dev/ttyUSB1"
BAUD = 9600
TIMEOUT = 3
ADDRESS = "08"  # Adjust as needed for the BMS
SERVICE_START = 0xA9
SERVICE_END = 0xFF
LOG_FILE = "service_responses.log"

def create_command(addr, cid1, cid2, payload=""):
    """
    Constructs a command with optional payload.
    """
    command = ">"  # Start of command ('3E' in ASCII)
    command += "22"  # Version
    command += addr  # Address
    command += cid1  # CID1
    command += cid2  # CID2

    if payload:
        length = len(payload) // 2  # Calculate length in bytes
        length = length & 0x0FFF
        n1, n2, n3 = length & 0xF, (length >> 4) & 0xF, (length >> 8) & 0xF
        checksum_prefix = ((n1 + n2 + n3) & 0xF) ^ 0xF
        length_field = f"{length + (checksum_prefix << 12):04X}"
        command += length_field
        command += payload
    else:
        command += "0000"

    checksum = calculate_checksum(command[1:])
    command += f"{checksum:04X}"
    command += "\r"  # Add terminator
    return command


def calculate_checksum(message):
    """
    Calculates checksum for the given command string.
    """
    checksum = 0
    for char in message:
        checksum += ord(char)
    checksum ^= 0xFFFF
    return checksum + 1

def send_command(ser, command):
    """
    Sends a command to the BMS and reads the response.
    """
    try:
        command = command.encode()
        ser.write(command)
        # print(f"sent: {command}")
        time.sleep(0.5)
        response = ser.read(ser.in_waiting)
        return response.hex() if response else None
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

def brute_force_services(port, baud, address, start, end):
    """
    Iterates through service codes, logs responses, and writes to a file.
    """
    try:
        with serial.Serial(port, baud, timeout=TIMEOUT) as ser:
            if ser.is_open:
                print(f"Connected to {port} at {baud} baud.")
                with open(LOG_FILE, "w") as log_file:
                    log_file.write("Service Code\tResponse\n")
                    for service in range(start, end + 1):
                        service_hex = f"{service:02X}"
                        command = create_command(address, "42", service_hex)
                        print(f"Testing service: {service_hex} Sent: {command}")
                        response = send_command(ser, command)
                        if response:
                            print(f"Service {service_hex}: Response: {response}")
                            log_file.write(f"{service_hex}\t{response}\n")
                        else:
                            print(f"Service {service_hex}: No response")
                            log_file.write(f"{service_hex}\tNo response\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    brute_force_services(PORT, BAUD, ADDRESS, SERVICE_START, SERVICE_END)
