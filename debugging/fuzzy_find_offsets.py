# sample response
response = '~22064A85F09806FF5014CA005A006222BB2650265000CD0CFF0CFF0CFF0CFF0CFF0CFE0CFE0CFF0CFF0CFF0CFF0CFF0D000CFE0CFE0CFE00A000AA00960096008C0096D00000000002000000000003000000DBB2\r'

# Removing the first 13 bytes and last 5 bytes as instructed
sampled_payload = response[13:-5]

# Function to brute force and find offsets matching expected ranges
def brute_force_parse(payload):
    matches = []
    for offset in range(0, len(payload) - 4, 2):  # Check every two hex chars (1 byte)
        # Extract 2 bytes (4 hex chars) at a time
        field_hex = payload[offset:offset + 4]
        try:
            # Convert hex to integer
            raw_value = int(field_hex, 16)
            # if 8000 <= raw_value <= 9999:  # ~6900 remaining capacity
            #     matches.append((offset, "Value", raw_value))
            # elif 100 <= raw_value <= 150:  # ~13-15°C temps
            #     matches.append((offset, "Temperature", raw_value))
            # elif 1000 <= raw_value <= 7000:
            #     matches.append((offset, "Current", raw_value))
            # elif 9700 <= raw_value <= 9900:
            #     matches.append((offset, "SOH", raw_value))
            if 85 <= offset <= 150:  # Check within a specific range
                if raw_value & (1 << 3):  # Check if bit 3 is set
                    matches.append((offset, "Machine Status (DISCH Active)", bin(raw_value)))

        except ValueError:
            continue
    return matches


# Running the brute force parser
results = brute_force_parse(sampled_payload)

# Print the results
for offset, field_name, value in results:
    print(f"Offset: {offset:2}    Field: {field_name}    Value: {value}")
