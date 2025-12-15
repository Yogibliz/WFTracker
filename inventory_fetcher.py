import json
import os
import re

import pymem
import pymem.pattern
import requests


def get_nonce_windows():
    # Open the Process
    try:
        pm = pymem.Pymem("Warframe.x64.exe")
        print(f"Attached to process: {pm.process_id}")
    except Exception as e:
        print(f"Could not find Warframe: {e}")
        return None

    # Warframe-Api-Helper used: "3F 61 63 63 6F 75 6E 74 49 64 3D" which is ASCII for "?accountId=" (Thanks, I'll steal this!)
    raw_pattern = b"\x3f\x61\x63\x63\x6f\x75\x6e\x74\x49\x64\x3d"  # ?accountId=
    pattern = re.escape(raw_pattern)

    # Scan memory to find nonce candidates
    matches = pymem.pattern.pattern_scan_all(pm.process_handle, pattern)

    if isinstance(matches, int):
        matches = [matches]
    elif matches is None:
        matches = []

    if not matches:
        print("No patterns found.")
        return None

    for address in matches:
        try:
            # Offset Calculation (42 bytes)
            # 11 (?accountId=) + 24 (ID) + 7 (&nonce=) = 42
            # Stole from Warframe-Api-Helper (Thanks again!)
            print(address)
            nonce_address = address + 42

            # Read 64 bytes (2^6)
            chunk = pm.read_bytes(nonce_address, 64)
            decoded = chunk.decode("utf-8", errors="ignore")

            # Extract digits
            match = re.match(r"^\d+", decoded)
            if match:
                nonce = match.group(0)

                # Read Account ID
                acc_id_bytes = pm.read_bytes(address + 11, 24)
                acc_id = acc_id_bytes.decode("utf-8", errors="ignore")

                full_auth = f"?accountId={acc_id}&nonce={nonce}"

                # LOWERED THRESHOLD TO 1
                print(f"Candidate found: {full_auth}")
                return full_auth
            else:
                print(
                    f"Match found at {hex(address)}, but regex failed on data: {decoded[:10]}..."
                )

        except Exception as e:
            # Print the actual error instead of ignoring it
            print(f"Error reading at {hex(address)}: {e}")
            continue

    print("Failed to confirm a nonce.")
    return None


def fetch_and_save_inventory():
    # 1. Construct the URL
    base_url = str("https://api.warframe.com/api/inventory.php")
    if os.name == "nt":
        auth_string = str(get_nonce_windows())
    else:
        auth_string = ""  # WiP get a Linux version of get_nonce
    target_url = base_url + auth_string

    print(f"Connecting to {base_url}...")

    try:
        # 2. Execute Request
        # Set a user-agent to avoid being blocked by basic filters
        headers = {"User-Agent": "Warframe/1.0"}
        response = requests.get(target_url, headers=headers)

        # Check for HTTP errors (4xx or 5xx)
        response.raise_for_status()

        # 3. Validate JSON
        # We parse it first to ensure we didn't just download an HTML error page
        data = response.json()

        # 4. Save to Disk
        filename = "inventory.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        # 5. Report Size (Powers of 2)
        # Get size in bytes
        size_bytes = os.path.getsize(filename)
        # Convert to Kibibytes (KiB = 2^10 bytes)
        size_kib = size_bytes / 1024

        print(f"Success! Saved to {filename}")
        print(f"Data size: {size_kib:.2f} KiB")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except json.JSONDecodeError:
        print("Error: The server returned data, but it wasn't valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")
