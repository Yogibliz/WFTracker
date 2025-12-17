import json
import os
import re

import requests

if os.name == "nt":
    try:
        import pymem
        import pymem.pattern
    except ImportError:
        print("Warning: pymem not installed. Windows functionality will be limited.")


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


def get_nonce_linux():
    process_name = "Warframe.x64.exe"
    pid = None

    # 1. Find the PID (Process ID)
    # We iterate over /proc
    try:
        for dirname in os.listdir("/proc"):
            if dirname.isdigit():
                try:
                    with open(f"/proc/{dirname}/cmdline", "rb") as f:
                        cmdline = f.read().decode().replace("\0", " ")
                        if process_name in cmdline:
                            pid = int(dirname)
                            break
                except (IOError, OSError):
                    continue
    except Exception as e:
        print(f"Error scanning processes: {e}")
        return None

    if pid is None:
        print(f"Could not find process: {process_name}")
        return None

    # 2. Define Pattern
    # ?accountId=
    pattern = b"\x3f\x61\x63\x63\x6f\x75\x6e\x74\x49\x64\x3d"

    try:
        maps_path = f"/proc/{pid}/maps"
        mem_path = f"/proc/{pid}/mem"

        # 3. Scan Memory Regions
        with open(maps_path, "r") as maps_file, open(mem_path, "rb", 0) as mem_file:
            for line in maps_file:
                # Parse map line: 00400000-00452000 r-xp ...
                parts = line.split()
                if not parts:
                    continue

                address_range = parts[0]
                perms = parts[1]

                # Filter: We only want readable/writable private memory (heap/stack)
                # 'rw' is standard for valid data segments in Wine/Proton
                if "rw" not in perms:
                    continue

                start_str, end_str = address_range.split("-")
                start_addr = int(start_str, 16)
                end_addr = int(end_str, 16)
                size = end_addr - start_addr

                # Skip massive empty regions or tiny fragments to save time
                # Lower bound: 2^12 (4 KiB - 1 page)
                # Upper bound: 2^28 (256 MiB - arbitrary sanity check)
                if size < 4096 or size > 268435456:
                    continue

                try:
                    mem_file.seek(start_addr)
                    # Read the chunk
                    chunk = mem_file.read(size)

                    if chunk:
                        # Search for pattern in this chunk
                        found_idx = chunk.find(pattern)

                        while found_idx != -1:
                            # 4. Offset Calculation & Extraction
                            # Found Pattern Address = start_addr + found_idx
                            # Target (Nonce) Address = Found Address + 42 bytes

                            # 11 bytes (?accountId=) + 24 bytes (ID) + 7 bytes (&nonce=)

                            nonce_start_offset = found_idx + 42

                            # Read 64 bytes (2^6) from the nonce position to ensure we capture all digits
                            # Slicing the chunk is faster than seeking/reading again
                            raw_nonce_area = chunk[
                                nonce_start_offset : nonce_start_offset + 64
                            ]

                            # raw bytes (hex) to readable text (or, well... numbers in this case)
                            decoded = raw_nonce_area.decode("utf-8", errors="ignore")

                            match = re.match(r"^\d+", decoded)
                            if match:
                                nonce = match.group(0)

                                # Extract Account ID (+11 from pattern start)
                                acc_id_start = found_idx + 11

                                # Extract the ID (24 characters long)
                                acc_id_data = chunk[acc_id_start : acc_id_start + 24]
                                acc_id = acc_id_data.decode("utf-8", errors="ignore")

                                full_auth = f"?accountId={acc_id}&nonce={nonce}" 
                                return full_auth

                            # Find next occurrence in the same chunk
                            found_idx = chunk.find(pattern, found_idx + 1)

                except (OSError, ValueError):
                    # Region might be protected or changed during read
                    continue

    except PermissionError:
        print("Permission Denied: Run with sudo/root to read process memory.")
    except Exception as e:
        print(f"Error reading memory: {e}")

    print("Failed to confirm a nonce.")
    return None


def fetch_and_save_inventory():
    # 1. Construct the URL
    base_url = str("https://api.warframe.com/api/inventory.php")
    if os.name == "nt":
        auth_string = str(get_nonce_windows())
    else:
        auth_string = str(get_nonce_linux())
    target_url = base_url + auth_string

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


    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except json.JSONDecodeError:
        print("Error: The server returned data, but it wasn't valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")
