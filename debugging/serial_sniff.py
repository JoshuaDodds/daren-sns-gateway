import serial
import time

# Configuration
serial_port = "/dev/ttyUSB0"  # Serial device
baud_rate = 19200             # Adjust based on your device

def log_serial_to_console():
    try:
        # Open the serial port
        with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
            print(f"Listening on {serial_port} at {baud_rate} baud...")
            while True:
                # Read a line of data from the serial device
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    # Print to console with timestamp
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{timestamp} - {line}")
    except serial.SerialException as e:
        print(f"Error accessing {serial_port}: {e}")
    except KeyboardInterrupt:
        print("Logging stopped by user.")


if __name__ == "__main__":
    log_serial_to_console()
