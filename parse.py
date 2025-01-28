from daren_sns_bridge import DarenSNSBridge

# sample messages
ho = '>22084200E0C6001BD314EB100D130D130D130D130D130D130D130D140D140D140D130D140D130D130D130D1300820075006404007800780078006E009D000000640127101BD30008000000010000000000230000000000000000000000000000000000000000000000D5AF\r'
dr = '~22064A85F09806FEFD14BC0058006221EF2650265000CD0CF50CF50CF60CF60CF60CF60CF60CF60CF60CF60CF60CF60CF60CF60CF60CF5009600A0008C008C0082008CD00000000002000000000003000000DC63\r'

def transform_response(message):
    m = DarenSNSBridge(None, None, None, None, b'\x08').transform_response(message.encode())
    return m

def parse_and_print_payload(message):
    # Parse the payload using the new BASEN logic
    full_len = len(message)
    if message.startswith("~"):
        payload_str = message[13:full_len - 5]  # extract payload (darren has extra byte before payload)
    else:
        payload_str = message[13:full_len - 5]  # extract ho/sns payload

    # Define field sizes from the BASEN spec starting at offset 2:6 (adjustable below)
    field_sizes = {
        "SOC": 2,
        "Pack Voltage": 2,
        "Cell Count": 1,
        "Cell Voltages": [(i * 4 + 12, i * 4 + 16) for i in range(16)],  # 16 cell voltages
        "Ambient Temp": 2,
        "Pack Avg Temp": 2,
        "MOS Temp": 2,
        "TOT_TEMPs": 1,  # Indicates the number of cell temps following
        "Cell Temps": None,  # Will be calculated dynamically
        "Pack Current": 2,
        "Pack Internal Resistance": 2,
        "SOH": 2,
        "User-defined": 1,
        "Full Charge Capacity": 2,
        "Remaining Capacity": 2,
        "Cycle Count": 2,
        "Voltage Status": 2,
        "Current Status": 2,
        "Temperature Status": 2,
        "Alarm Status": 2,
        "FET Status": 2,
        "Overvoltage Protection Status": 2,
        "Undervolt Protection Status": 2,
        "Overvoltage Alarm Status": 2,
        "Undervolt Alarm Status": 2,
        "Cell Balance State Low": 2,
        "Cell Balance State High": 2,
        "Machine Status": 1,
        "IO Status": 2,
    }

    parsed_new_payload_values = []  # Ensure it is initialized as a list
    offset = 2
    starting_offset = 0

    for field_name, size_or_offsets in field_sizes.items():
        print(offset)
        if field_name == "Cell Voltages":
            # Parse individual cell voltages
            cell_voltages = ""
            for start, end in size_or_offsets:
                cell_hex = payload_str[start:end]
                try:
                    cell_voltage = int(cell_hex, 16)
                    cell_voltages += f"{cell_voltage}"
                except ValueError:
                    cell_voltages = "Invalid"
                    break
            parsed_new_payload_values.append((f"{starting_offset}:{starting_offset + len(size_or_offsets) * 2}", field_name, cell_voltages))
            starting_offset += len(size_or_offsets) * 2
            offset += len(size_or_offsets) * 4
        elif field_name == "TOT_TEMPs":
            # Read TOT_TEMPs to determine the number of cell temps
            field_hex = payload_str[offset:offset + 2]  # 1 byte (2 hex chars)
            try:
                tot_temps = int(field_hex, 16)
                parsed_new_payload_values.append((f"{starting_offset}:{starting_offset + 1}", field_name, tot_temps))
                # Dynamically calculate offsets for Cell Temps
                field_sizes["Cell Temps"] = [(offset + i * 4 + 2, offset + i * 4 + 6) for i in range(tot_temps)]
                starting_offset += 1
                offset += 2
            except ValueError:
                parsed_new_payload_values.append((f"{starting_offset}:{starting_offset + 1}", field_name, "Invalid"))
                starting_offset += 1
                offset += 2
        elif field_name == "Cell Temps":
            # Parse individual cell temperatures
            cell_temps = ""
            for start, end in size_or_offsets:
                temp_hex = payload_str[start:end]
                try:
                    cell_temp = int(temp_hex, 16)
                    cell_temps += f"{cell_temp}"
                except ValueError:
                    cell_temps = "Invalid"
                    break
            parsed_new_payload_values.append((f"{starting_offset}:{starting_offset + len(size_or_offsets) * 2}", field_name, cell_temps))
            starting_offset += len(size_or_offsets) * 2
            offset += len(size_or_offsets) * 4
        else:
            field_hex = payload_str[offset:offset + size_or_offsets * 2]  # 2 hex chars per byte
            try:
                raw_value = int(field_hex, 16)
                parsed_new_payload_values.append((f"{starting_offset}:{starting_offset + size_or_offsets}", field_name, raw_value))
            except ValueError:
                parsed_new_payload_values.append((f"{starting_offset}:{starting_offset + size_or_offsets}", field_name, "Invalid"))
            offset += size_or_offsets * 2
            starting_offset += size_or_offsets

    # Format parsed values as "Offset: Field Name: Raw (Decimal)"
    def format_parsed_values(parsed_values):
        formatted_values = []
        for offset, field_name, raw_value in parsed_values:
            formatted_values.append(f"Offset: {offset:>8}    {field_name}: {raw_value}")
        return "\n".join(formatted_values)

    # Example usage
    formatted_output = format_parsed_values(parsed_new_payload_values)
    print(formatted_output)

def daren_parse_and_print_payload(daren_response):
    # Extract the payload
    full_len = len(daren_response)
    daren_payload_str = daren_response[13:full_len - 5]  # Skip the first 13 bytes and last 5 bytes
    print(f"length: {len(daren_payload_str)}")

    # Define field sizes and offsets based on Daren's structure
    field_sizes = {
        "Pack Voltage": (6, 10),
        "SOH": (14, 18),
        "SOC": (18, 22),
        "Installed": (22, 26),
        "Full Charge Capacity": (26, 30),
        "Cell Voltages": [(34 + i * 4, 34 + i * 4 + 4) for i in range(16)],  # 16 cell voltages starting at offset 34
        "MOS Temp": (98, 102),
        "Cell Temps": [(102 + i * 4, 102 + i * 4 + 4) for i in range(4)],  # 4 temperatures starting at offset 102
        # todo:  "Pack Current": (132, 136),
    }

    # Parse and format fields
    parsed_fields = []
    offset = 0
    for field_name, size_or_offsets in field_sizes.items():
        if isinstance(size_or_offsets, list):  # Handle dynamic lists (e.g., Cell Voltages, Cell Temps)
            field_values = ""
            for start, end in size_or_offsets:
                field_hex = daren_payload_str[start:end]
                try:
                    field_value = int(field_hex, 16)
                    field_values += str(field_value)
                except ValueError:
                    field_values = "Invalid"
                    break
            parsed_fields.append((f"{offset}:{offset + len(size_or_offsets) * 2}", field_name, field_values))
            offset += len(size_or_offsets) * 2
        else:  # Handle fixed-size fields
            start, end = size_or_offsets
            field_hex = daren_payload_str[start:end]
            try:
                raw_value = int(field_hex, 16)
                parsed_fields.append((f"{offset}:{offset + (end - start) // 2}", field_name, raw_value))
            except ValueError:
                parsed_fields.append((f"{offset}:{offset + (end - start) // 2}", field_name, "Invalid"))
            offset += (end - start) // 2

    # Format parsed values as "Offset: Field Name: Raw (Decimal)"
    def format_parsed_values(parsed_values):
        formatted_values = []
        for offset, field_name, raw_value in parsed_values:
            formatted_values.append(f"Offset: {offset:>8}    {field_name}: {raw_value}")
        return "\n".join(formatted_values)

    # Print the formatted output
    formatted_output = format_parsed_values(parsed_fields)
    print(formatted_output)
