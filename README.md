# Daren-SNS Bridge

## Overview
The **Daren-SNS Bridge** is a Python-based application designed to mediate communication between a Daren master device and multiple SNS slave devices over serial ports. It listens for commands from the Daren system, forwards them to designated SNS devices, and returns the responses to the Daren master. The bridge ensures seamless interoperability between the two systems.

## Features
- Listens for commands from the Daren master.
- Routes requests to specific SNS slave devices.
- Processes SNS responses and reformats them for the Daren master.
- Built-in retries and error handling for robust communication.

## System Requirements
- Python 3.7+
- Access to serial communication ports

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/daren-sns-bridge.git
   cd daren-sns-bridge
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Edit the configuration section in `daren_sns_bridge.py` to match your setup:
```python
DAREN_PORT = "/dev/ttyUSB1"  # Daren master port
SNS_PORT = "/dev/ttyUSB0"    # SNS slave port
DAREN_BAUD = 19200            # Baud rate for Daren
SNS_BAUD = 9600               # Baud rate for SNS
SNS_ADDRESSES = [b'\x08']    # SNS slave addresses
```

## Usage
1. Start the bridge:
   ```bash
   python daren_sns_bridge.py
   ```
2. The bridge will begin listening on the configured Daren port and route messages to the SNS system as required.
3. To stop the bridge, use `Ctrl+C`.

## File Structure
- `daren_sns_bridge.py`: Main script for running the bridge.
- `utils/`: Utility modules for logging and serial port handling.
- `bms/sns01_485.py`: Module for interfacing with SNS devices.

## How It Works
1. **Listening**: The bridge listens on the Daren master port for incoming commands.
2. **Routing**: It identifies valid master requests and forwards them to the appropriate SNS slave based on the address.
3. **Transformation**: Responses from SNS slaves are processed, transformed, and sent back to the Daren master in the required format.
4. **Error Handling**: The system retries failed SNS communications and logs errors for debugging.

## Logging
The application provides detailed logs for troubleshooting. Adjust the logging configuration in `utils/logger.py` for verbosity levels (e.g., `DEBUG`, `INFO`, `ERROR`).

## Future Improvements
- Add support for additional communication protocols.
- Expand error-handling mechanisms.
- Enable dynamic configuration through a JSON or YAML file.

## Contributing
Contributions are welcome! Please submit issues or pull requests for bug fixes or feature requests.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

