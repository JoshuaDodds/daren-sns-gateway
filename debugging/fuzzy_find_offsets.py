import pandas as pd

def incremental_brute_force_parse(payload):
    results = []
    payload_len = len(payload)

    # Iterate through each offset
    for offset in range(0, payload_len, 2):  # Step by 2 HEX chars
        # Check 2 HEX chars (1 byte)
        if offset + 2 <= payload_len:
            try:
                value_2hex = int(payload[offset:offset + 2], 16)
                results.append((offset, f"{offset}:{offset+2}", "2-HEX (1 Byte)", value_2hex))
            except ValueError:
                results.append((offset, f"{offset}:{offset+2}", "2-HEX (1 Byte)", None))

        # Check 4 HEX chars (2 bytes)
        if offset + 4 <= payload_len:
            try:
                value_4hex = int(payload[offset:offset + 4], 16)
                results.append((offset, f"{offset}:{offset+4}", "4-HEX (2 Bytes)", value_4hex))
            except ValueError:
                results.append((offset, f"{offset}:{offset+4}", "4-HEX (2 Bytes)", None))

    # Convert results to DataFrame for display
    df = pd.DataFrame(results, columns=["Offset", "Slice", "Type", "Value"])
    return df


response = '~22064A85F09806FE0F147A002B006210BF2650265000CD0CCB0CCD0CCC0CCD0CCC0CCD0CCD0CCE0CCD0CCE0CCD0CCD0CCE0CCD0CCD0CCB0082008200780078006E0078D00000000002000000000003000000DBF1\r'
sampled_payload = response[17:-5]

# Run the function
df_results = incremental_brute_force_parse(sampled_payload)

# Enable full row display
pd.set_option('display.max_rows', None)

# Display the DataFrame
print(df_results)
