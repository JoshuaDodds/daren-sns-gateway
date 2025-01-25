import serial
import time
import threading

# Configuration
MASTER_SLAVE_PORT = "/dev/ttyUSB1"  # JC03 master-slave communication
HO01_PORT = "/dev/ttyUSB1"         # Ho01 communication
BAUD_MASTER_SLAVE = 19200
BAUD_HO01 = 9600
TIMEOUT = 1
LOG_FILE = "communication_sniff.log"

def log_message(file, source, direction, data):
    """
    Logs a message to the log file with source, direction, and timestamp.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(file, "a") as log:
        log.write(f"[{timestamp}] {source} {direction}: {data}\n")
    print(f"[{timestamp}] {source} {direction}: {data}")

def sniff_port(port, baud, source, log_file):
    """
    Sniffs traffic on a specified serial port.
    """
    try:
        with serial.Serial(port, baud, timeout=TIMEOUT) as ser:
            print(f"Listening on {port} ({source})...")
            while True:
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    log_message(log_file, source, "RX", data)
    except KeyboardInterrupt:
        print(f"Exiting {source} sniffing...")
    except Exception as e:
        print(f"Error on {source}: {e}")

def main():
    """
    Main function to start sniffing on both USB0 and USB1.
    """
    try:
        # Start sniffing on JC03 master-slave communication
        master_slave_thread = threading.Thread(
            target=sniff_port,
            args=(MASTER_SLAVE_PORT, BAUD_MASTER_SLAVE, "JC03 Message", LOG_FILE),
            daemon=True
        )

        # Start threads
        master_slave_thread.start()
        # ho01_thread.start()

        # Keep main thread alive
        print("Sniffing on USB0 (JC03) and USB1 (Ho01). Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting sniffing...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
