import json
import lzma

import requests

import inventory_fetcher

INDEX_URL = "https://origin.warframe.com/PublicExport/index_en.txt.lzma"
PUBLIC_EXPORT_BASE = "http://content.warframe.com/PublicExport/Manifest/"
OUTPUT_FOLDER = "./"


def download_index():
    resp = requests.get(INDEX_URL)
    resp.raise_for_status()

    # --- IN-Place Fix --- (Not sure if there's a better way to fix this)
    # The file header (first 13 bytes) apparently often claims the wrong size for the file.
    # Setting bytes 5-12 to 0xFF (meaning "Unknown Size")
    # forces Python to decode everything until the end of the stream.
    content = bytearray(resp.content)
    for i in range(5, 13):
        content[i] = 0xFF

    return lzma.decompress(content, format=lzma.FORMAT_ALONE).decode("utf-8")


def parse_entries(index_text):
    entries = {}
    for line in index_text.splitlines():
        line = line.strip()
        if not line or "!" not in line:
            continue
        filename, key = line.split("!", 1)
        entries[filename] = key
    return entries


def download_json(filename, key):
    url = PUBLIC_EXPORT_BASE + f"{filename}!{key}"
    r = requests.get(url)
    r.raise_for_status()
    # Return text so we can save it or parse it
    return r.text


def save_json(data_text, local_name):
    # Try to parse to ensure it's valid JSON, then save formatted
    try:
        parsed = json.loads(data_text)
        with open(local_name, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        print(f"Warning: {local_name} is not valid JSON. Saving raw text.")
        with open(local_name, "w", encoding="utf-8") as f:
            f.write(data_text)


def fetch_warframe_json_data():
    try:
        # 1. Get the index
        index_text = download_index()
        entries = parse_entries(index_text)

        # 2. Define what to fetch
        interesting_files = {
            "ExportWarframes_en.json": "warframe_warframes.json",
            "ExportWeapons_en.json": "warframe_weapons.json",
            "ExportRecipes_en.json": "warframe_recipes.json",
            "ExportSentinels_en.json": "warframe_sentinels.json",
            "ExportRelicArcane_en.json": "warframe_relic_arcanes.json",
        }

        # 3. Fetch files
        for filename, output_name in interesting_files.items():
            if filename not in entries:
                print(f"Skipping {filename} (not found in index)")
                continue

            key = entries[filename]
            try:
                raw_json_text = download_json(filename, key)
                save_json(raw_json_text, OUTPUT_FOLDER + output_name)
            except Exception as e:
                print(f"Failed to fetch {filename}: {e}")

        # 4. Fetch Warframe Inventory JSON data
        inventory_fetcher.fetch_and_save_inventory()

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
