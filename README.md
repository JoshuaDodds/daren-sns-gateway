# Daren-SNS Bridge

## Disclaimer
This project is about as bleeding edge alpha as you can get.  As of the time of this writing (Jan 25th 2025) I am running 
it for about 8 hours in debug mode without any issues but I fully expect there will be some that will arise.  

## Overview
The **Daren-SNS Bridge** is a Python-based application designed to mediate communication between a Daren master device 
and multiple SNS slave devices using the serial/RS-485 dongles they are shipped with. It handles  both protocol translation 
and baud rate conversion. 

## How it works
 - listens for commands from the Daren system
 - queries designated SNS devices for rich telemetry data
 - extracts data and builds a valid Daren formatted dataframe from the SNS response
 - returns that response to the Daren master module. 

The bridge ensures seamless interoperability between the two systems assuming that your modules are daisy chained and 
connected via BMS-CAN to a Victron Inverter. (Other inverters could work but this is not tested, yet)

# What are Daren / SNS battery modules ?
These I have mainly seen sold by Aliexpress seller Papool, SuperBattery, possible Cernss, and maybe others but the BMS 
types I am referring to are as follows:

Daren is the DR-JC03 based BMS which was first seen in Papool batteries and can be 19200 or 9600 baud depending on version 
and possibly firmware. It has ussually 2 RJ-45 ports on the front. 

SNS refers to a newer type module shipping with three RJ-45 ports on the front (one is labeled CAN). The manufacturer 
info mentions SNS, Cerns, and Ho01.  This module by default, communicates at 9600 baud and and shares a common RS-485 
pinout now with the Daren DR-JCXX BMS types so the same USB serial adapter can be used for both types.  

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
   git clone https://github.com/JoshuaDodds/daren-sns-gateway.git
   cd daren-sns-bridge
   ```

## Configuration
Edit the configuration section in `daren_sns_bridge.py` to match your setup:
```python
DAREN_PORT = "/dev/ttyUSB1"  # Daren master port serial dongle
SNS_PORT = "/dev/ttyUSB0"    # SNS slave port serial dongle
DAREN_BAUD = 19200            # Baud rate for Daren
SNS_BAUD = 9600               # Baud rate for SNS
SNS_ADDRESSES = [b'\x08']    # SNS slave addresses
```

## Usage
1. Start the bridge:
   ```bash
   python daren_sns_bridge.py
   ```
2. The bridge will begin listening on the configured Daren port and translate messages between the Daren master and a sns slaves
3. To stop the bridge, use `Ctrl+C`.

## File Structure
```
./
├── LICENSE
├── README.md
├── __init__.py
├── battery.py
├── bms
│   ├── __init__.py
│   ├── daren_485.py
│   └── sns01_485.py
├── config.default.ini
├── daren_sns_bridge.py
├── parse.py
└── utils.py
```

## Logging
The application provides detailed logs for troubleshooting. Adjust the logging configuration in `utils/logger.py` for verbosity levels (e.g., `DEBUG`, `INFO`, `ERROR`).

## Future Improvements
- Add support for additional communication protocols (if needed)
- Expand error-handling mechanisms.
- Enable dynamic configuration through a JSON or YAML file.
- remove/refactor dbus-serial-battery methods and configurations that are not used in this project 

## Contributing
Contributions are welcome! Please submit issues or pull requests for bug fixes or feature requests.

## Credits
Many thanks to the maintainer and authors of https://github.com/mr-manuel/venus-os_dbus-serialbattery 
Without their work, this would have taken me so much more time.  Some modules and bits of pieces from that project are 
still reused in this one until refactored. 

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

