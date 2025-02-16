#!/bin/bash

# Function to start and monitor socat processes
start_socat() {
    echo "Starting socat for virtual serial devices..."

    while true; do
        # Kill existing socat processes
        pkill socat || true

        # Start socat processes in background
        socat -d pty,link=/dev/ttyUSB0,raw,mode=666,echo=0 tcp:192.168.1.53:4196 &
        SOCAT_PID1=$!

        socat -d pty,link=/dev/ttyUSB1,raw,mode=666,echo=0 tcp:192.168.1.52:4196 &
        SOCAT_PID2=$!

        sleep 5  # Allow connections to establish

        # Verify both socat processes are running
        if ! kill -0 $SOCAT_PID1 2>/dev/null || ! kill -0 $SOCAT_PID2 2>/dev/null; then
            echo "Error: socat processes failed. Restarting..."
            sleep 5
            continue
        fi

        echo "socat processes started successfully."

        # Monitor socat processes and restart if they exit
        wait $SOCAT_PID1
        wait $SOCAT_PID2
        echo "socat process exited unexpectedly. Restarting..."
    done
}

# Function to ensure serial devices exist
wait_for_serial_devices() {
    echo "Waiting for virtual serial devices..."
    while [ ! -e /dev/ttyUSB0 ] || [ ! -e /dev/ttyUSB1 ]; do
        echo "Serial devices not available yet, retrying..."
        sleep 2
    done
    echo "Both virtual serial devices are available."
}

# Function to start Python and monitor for crashes
start_python() {
    echo "Starting Python service..."

    while true; do
        python daren_sns_bridge.py
        echo "Python script exited. Restarting in 5 seconds..."
        sleep 5
    done
}

# Cleanup function on exit
cleanup() {
    echo "Shutting down... Cleaning up socat and Python processes."
    pkill socat
    pkill python
    exit 0
}

# Trap exit signals
trap cleanup SIGTERM SIGINT

# Start socat in background
start_socat &

# Wait for virtual devices before launching Python
wait_for_serial_devices

# Start Python process in background
start_python
