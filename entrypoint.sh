#!/bin/bash

# Function to start socat with auto-recovery
start_socat() {
    echo "Starting socat for virtual serial devices..."
    while true; do
        # Kill any existing socat processes before restarting
        pkill socat || true

        # Start socat processes in background
        # Daren battery string
        socat -d pty,link=/dev/ttyUSB0,raw,mode=666,echo=0 tcp:192.168.1.53:4196 &
        SOCAT_PID1=$!

        # Ho2 Battery string
        socat -d pty,link=/dev/ttyUSB1,raw,mode=666,echo=0 tcp:192.168.1.52:4196 &
        SOCAT_PID2=$!

        # Wait a bit for connections to establish
        sleep 5

        # Verify socat is still running
        if ! kill -0 $SOCAT_PID1 2>/dev/null || ! kill -0 $SOCAT_PID2 2>/dev/null; then
            echo "Error: socat failed to start. Retrying in 5 seconds..."
            sleep 5
            continue
        fi

        echo "socat processes started successfully."
        break
    done
}

# Function to ensure serial devices exist
wait_for_serial_devices() {
    echo "Waiting for virtual serial devices to be available..."
    while [ ! -e /dev/ttyUSB0 ] || [ ! -e /dev/ttyUSB1 ]; do
        echo "Serial devices not available yet, retrying..."
        sleep 2
    done
    echo "Both virtual serial devices are available."
}

# Main loop to ensure socat runs and restart the Python script reliably
while true; do
    # Ensure socat is running before starting Python service
    start_socat
    wait_for_serial_devices

    echo "Starting Python service..."
    python daren_sns_bridge.py

    echo "Python script exited. Restarting after 5 seconds..."
    sleep 5
done
