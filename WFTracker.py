import argparse
import json
import os
import re

from prettytable import PrettyTable

import inventory_fetcher

# Warframe API data
warframe_name = {}
archwing_name = {}
weapon_name_category = {}

# Inventory data
warframe_inventory = dict()

# Separate Mastered
mastered_or_owned_warframes = set()
mastered_or_owned_primaries = set()
mastered_or_owned_secondaries = set()
mastered_or_owned_melees = set()
mastered_or_owned_amps = set()
mastered_or_owned_arch_weapons = set()
mastered_or_owned_others = set()

# Separate Unmastered
unmastered_warframes = set()
unmastered_primaries = set()
unmastered_secondaries = set()
unmastered_melees = set()
unmastered_amps = set()
unmastered_arch_weapons = set()
unmastered_others = set()

# Sellable duplicates
duplicate_prime_parts = set()

# Sellable prime parts that's not needed
mastered_prime_parts = set()

# Tables of sets
warframe_parts = {}
archwing_parts = {}
weapon_parts = {}

# ----------------------- Fetching from API:s -----------------------


# Fetch all currently available warframes in the game
def fetch_warframes():
    with open("warframe_warframes.json", encoding="utf-8") as wf:
        json_data = json.load(wf)
        for warframe in json_data["ExportWarframes"]:
            unique_name = warframe["uniqueName"]
            if "Archwing" in unique_name:
                archwing_name[unique_name] = warframe["name"]
            else:
                warframe_name[unique_name] = warframe["name"]


# Fetch all currently available weapons in the game
def fetch_weapons():
    with open("warframe_weapons.json", encoding="utf-8") as wp:
        json_data = json.load(wp)
        for weapon in json_data["ExportWeapons"]:
            weapon_name_category[weapon["uniqueName"]] = {
                "name": weapon["name"],
                "category": weapon["productCategory"],
            }


# Fetch all Warframe Recipes in the game
def fetch_warframe_recipes():
    with open("warframe_recipes.json", encoding="utf-8") as wr:
        json_data = json.load(wr)

        for recipe in json_data["ExportRecipes"]:
            unique_name = recipe["uniqueName"]
            result_type = recipe["resultType"]

            is_warframe = result_type in warframe_name
            is_archwing = result_type in archwing_name

            if not is_warframe and not is_archwing:
                continue

            # Shared data
            bp_name = clean_name(unique_name)
            bp_count = warframe_inventory.get(unique_name, 0)
            bp_tuple = (bp_name, bp_count)

            if is_warframe:
                item_name = warframe_name[result_type]
                entry = {
                    "name": item_name,
                    "blueprint": bp_tuple,
                    "neuroptics": ("", 0),
                    "chassis": ("", 0),
                    "systems": ("", 0),
                }
            else:
                item_name = archwing_name[result_type]
                entry = {
                    "name": item_name,
                    "blueprint": bp_tuple,
                    "harness": ("", 0),
                    "wings": ("", 0),
                    "systems": ("", 0),
                }

            has_relevant_parts = False

            for ingredient in recipe.get("ingredients", []):
                type = ingredient["ItemType"]
                part_name = clean_name(type)

                if any(
                    x in part_name
                    for x in ["Neuroptics", "Chassis", "Systems", "Harness", "Wings"]
                ):
                    count = warframe_inventory.get(type, 0)
                    part_tuple = (part_name, count)

                    # Warframe
                    if is_warframe:
                        if "Neuroptics" in part_name:
                            entry["neuroptics"] = part_tuple
                            has_relevant_parts = True
                        elif "Chassis" in part_name:
                            entry["chassis"] = part_tuple
                            has_relevant_parts = True
                        elif "Systems" in part_name:
                            entry["systems"] = part_tuple
                            has_relevant_parts = True

                    # Archwing
                    elif is_archwing:
                        if "Harness" in part_name:
                            entry["harness"] = part_tuple
                            has_relevant_parts = True
                        elif "Wings" in part_name:
                            entry["wings"] = part_tuple
                            has_relevant_parts = True
                        elif "Systems" in part_name:
                            entry["systems"] = part_tuple
                            has_relevant_parts = True

            if has_relevant_parts:
                if is_warframe:
                    warframe_parts[unique_name] = entry
                elif is_archwing:
                    archwing_parts[unique_name] = entry


# Fetch all Weapon Recipes in the game
def fetch_weapon_recipes():
    with open("warframe_recipes.json", encoding="utf-8") as wr:
        json_data = json.load(wr)

        for recipe in json_data["ExportRecipes"]:
            unique_name = recipe["uniqueName"]
            result_type = recipe["resultType"]

            if "Prime" not in unique_name:
                continue

            if result_type in warframe_name or result_type in archwing_name:
                continue

            if "Sentinels" in unique_name or "Sentinel" in clean_name(result_type):
                continue

            if "Weapons" not in unique_name:
                continue

            current_parts = []
            owned_ingredients = 0
            main_bp_owned = warframe_inventory.get(unique_name, 0)

            for ingredient in recipe.get("ingredients", []):
                type = ingredient["ItemType"]
                part_name = clean_name(type)

                if "Prime" not in part_name:
                    continue

                # If type is in inventory
                if type in warframe_inventory:
                    count = warframe_inventory.get(type, 0)
                    current_parts.append((part_name, count))
                    if count > 0:
                        owned_ingredients += 1
                else:
                    current_parts.append((part_name, 0))

            total_owned = owned_ingredients + (1 if main_bp_owned > 0 else 0)

            if total_owned >= 2:
                entry = {
                    "name": weapon_name_category[recipe["resultType"]]["name"],
                    "blueprint": (
                        clean_name(unique_name),
                        main_bp_owned,
                    ),
                    "parts": current_parts,
                }
                weapon_parts[unique_name] = entry


# Helper to fetch the inventory data.
def fetch_inventory_data():
    with open("inventory.json") as f:
        data = json.load(f)

    if "MiscItems" in data:
        for item in data["MiscItems"]:
            item_type = item.get("ItemType", "")
            lower_type = item_type.lower()

            if "prime" not in lower_type:
                continue

            if (
                "projection" in lower_type
                or "bucks" in lower_type
                or "resources" in lower_type
            ):
                continue

            warframe_inventory[item_type] = item.get("ItemCount", 0)


# ----------------------- Formatting Helpers -----------------------


# Helper to clean up uniqueName to name mapping
def clean_name(name_str):
    base_name = name_str.split("/")[-1]

    # Split CamelCase
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", base_name)
    cleaned = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", cleaned)

    # Replace Helmet with Neuroptics
    cleaned = re.sub(r"\sHelmet\s", " Neuroptics ", cleaned)

    # Remove trailing " Component"
    cleaned = re.sub(r"\s*Component$", "", cleaned)

    return cleaned.strip()


# Basic Main Menu
def main_menu():
    option = -1
    while option not in range(0, 10):
        os.system("cls" if os.name == "nt" else "clear")
        print("1. Print Unmastered Warframes")
        print("2. Print Unmastered Primary Weapons")
        print("3. Print Unmastered Secondary Weapons")
        print("4. Print Unmastered Melee Weapons")
        print("5. Print Unmastered Arch Weapons")
        print("6. Print Unmastered Amps")
        print("7. Print Duplicate Primes Parts")
        print("8. Print Prime Parts for Mastered")
        print("9. Print Weapon Prime Parts as Part of Set")
        print("0. Prime Warframe Prime Parts as Port of Set")
        option = int(input("What do you want to do? [0-9]: "))

    print_selection(option)


# Print the selected option in the main_menu
def print_selection(index):
    os.system("cls" if os.name == "nt" else "clear")
    match index:
        case 1:
            print("----- Unmastered Archwings & Warframes -----")
            print_set_as_table(unmastered_warframes)
        case 2:
            print("----- Unmastered Primary Weapons -----")
            print_set_as_table(unmastered_primaries)
        case 3:
            print("----- Unmastered Secondary Weapons -----")
            print_set_as_table(unmastered_secondaries)
        case 4:
            print("----- Unmastered Melee Weapons -----")
            print_set_as_table(unmastered_melees)
        case 5:
            print("----- Unmastered Arch Weapons -----")
            print_set_as_table(unmastered_arch_weapons)
        case 6:
            print("----- Unmastered Amps -----")
            print_set_as_table(unmastered_amps)
        case 7:
            print("----- Duplicate Prime Parts (mastered and unmastered) -----")
            print_set_of_tuples_as_table(duplicate_prime_parts)
        case 8:
            print("----- Mastered Prime Parts -----")
            print_set_of_tuples_as_table(mastered_prime_parts)
        case 9:
            print("----- Prime Weapons Set Progress -----")
            print_weapon_set_progress_as_table(weapon_parts)
        case 0:
            print("----- Prime Warframes Set Progress -----")
            print_warframe_set_progress_as_table(warframe_parts)
    go_back = ""
    while go_back != "y":
        go_back = input("Go back to menu or quit? (y/q): ").lower()
        if go_back == "q":
            exit()
    main_menu()


# Convert the set of tuples data into a printable table with item and count
def print_set_of_tuples_as_table(input_set):
    table = PrettyTable(["Item", "Count"])
    for tup in sorted(input_set):
        item = tup[0]
        count = tup[1]
        table.add_row([item, count])
    print(table)


# Convert the set into a printable table
def print_set_as_table(input_set):
    table = PrettyTable(["Item"])
    for item in sorted(input_set):
        table.add_row([item])
    print(table)


# For prime_warframe_sets.
def print_warframe_set_progress_as_table(prime_warframe_set):
    prime_warframe_table = PrettyTable(
        ["Item", "Blueprint", "Neuroptics", "Chassis", "Systems", "Progress"]
    )

    # Sort by name
    for entry in sorted(prime_warframe_set.values(), key=lambda x: x["name"]):
        progress = (
            entry["blueprint"][1]
            + entry["neuroptics"][1]
            + entry["chassis"][1]
            + entry["systems"][1]
        )

        row = [
            entry["name"],
            entry["blueprint"][1],
            entry["neuroptics"][1],
            entry["chassis"][1],
            entry["systems"][1],
            f"{progress}/4",
        ]
        prime_warframe_table.add_row(row)
    print(prime_warframe_table)


# For the prime_weapon_sets.
def print_weapon_set_progress_as_table(prime_weapon_set):
    prime_weapon_table = PrettyTable(["Item", "Parts", "Progress"])

    for entry in sorted(prime_weapon_set.values(), key=lambda x: x["name"]):
        parts_str_list = [f"Blueprint: {entry['blueprint'][1]}"]
        amount = 1
        progress = 0

        for part_name, count in entry["parts"]:
            if count >= 1:
                progress += 1
            amount += 1
            parts_str_list.append(f"{part_name}: {count}")

        progress_str = f"Progress: {progress}/{amount}"
        formatted_parts = ", ".join(parts_str_list)

        prime_weapon_table.add_row([entry["name"], formatted_parts, progress_str])
    print(prime_weapon_table)


# For archwing_sets
def print_archwing_set_progress_as_table(archwing_set):
    table = PrettyTable(["Item", "Blueprint", "Harness", "Wings", "Systems"])
    table.align["Item"] = "l"

    for entry in sorted(archwing_set.values(), key=lambda x: x["name"]):
        row = [
            entry["name"],
            entry["blueprint"][1],
            entry["harness"][1],
            entry["wings"][1],
            entry["systems"][1],
        ]
        table.add_row(row)
    print(table)


# ----------------------- Filter API-data into categories -----------------------


# Return each prime item there's a duplicate of.
def filter_duplicate_prime_parts():
    for item in warframe_inventory:
        if warframe_inventory[item] > 1:
            duplicate_prime_parts.add((clean_name(item), warframe_inventory[item]))


# Return a list of all prime parts of mastered items.
def filter_mastered_prime_parts():
    aggrigate_mastered_items = (
        mastered_or_owned_warframes
        | mastered_or_owned_primaries
        | mastered_or_owned_secondaries
        | mastered_or_owned_melees
        | mastered_or_owned_amps
        | mastered_or_owned_arch_weapons
        | mastered_or_owned_others
    )

    inventory_items = warframe_inventory.keys()

    for inv_item_type in inventory_items:
        for mastered_item in aggrigate_mastered_items:
            if "Prime" not in mastered_item:
                continue

            check_name = mastered_item.replace(" ", "")

            if check_name in inv_item_type:
                clean_part_name = clean_name(inv_item_type)
                mastered_prime_parts.add(
                    (clean_part_name, warframe_inventory[inv_item_type])
                )


# Get which items have been mastered thus far.
def filter_mastered_and_owned_gear():
    with open("inventory.json", encoding="utf-8") as inv:
        json_data = json.load(inv)

        # Get Mastered Item/Warframes etc
        for mastered_item in json_data["XPInfo"]:
            item_path = mastered_item["ItemType"]

            # Filter Mastered Warframes
            if item_path in warframe_name:
                mastered_or_owned_warframes.add(warframe_name[item_path])

            # Filter Mastered Weapons
            if item_path in weapon_name_category:
                weapon_data = weapon_name_category[item_path]
                name = weapon_data["name"]
                category = weapon_data["category"]

                # Amp
                if category == "OperatorAmplifiers":
                    mastered_or_owned_amps.add(name)

                # Primary
                elif category == "LongGuns":
                    mastered_or_owned_primaries.add(name)

                # Secondary
                elif category == "Pistols":
                    mastered_or_owned_secondaries.add(name)

                # Melee
                elif category == "Melee":
                    mastered_or_owned_melees.add(name)

                # Arch-Weapon
                elif category in ["SpaceGuns", "SpaceMelee"]:
                    mastered_or_owned_arch_weapons.add(name)

                # Weirdly categoriezed in API. Might set up exceptions to catch later...
                else:
                    mastered_or_owned_others.add(name)


# Filter Unmastered Warframes
def filter_unmastered_warframes():
    for _, name in warframe_name.items():
        if name not in mastered_or_owned_warframes:
            unmastered_warframes.add(name)


# Filter Unmastered Weapons
def filter_unmastered_weapons():
    for _, data in weapon_name_category.items():
        name = data["name"]
        category = data["category"]

        # Amp
        if category == "OperatorAmplifiers":
            if name not in mastered_or_owned_amps:
                unmastered_amps.add(name)

        # Primary
        elif category == "LongGuns":
            if name not in mastered_or_owned_primaries:
                unmastered_primaries.add(name)

        # Secondary
        elif category == "Pistols":
            if name not in mastered_or_owned_secondaries:
                unmastered_secondaries.add(name)

        # Melee
        elif category == "Melee":
            if name not in mastered_or_owned_melees:
                unmastered_melees.add(name)

        # Arch-Weapon
        elif category in ["SpaceGuns", "SpaceMelee"]:
            if name not in mastered_or_owned_arch_weapons:
                unmastered_arch_weapons.add(name)

        # Weirdly categoriezed in API. Might set up exceptions to catch later...
        else:
            if name not in mastered_or_owned_others:
                unmastered_others.add(name)


def filter_items():
    filter_duplicate_prime_parts()
    filter_mastered_and_owned_gear()
    filter_mastered_prime_parts()
    filter_unmastered_warframes()
    filter_unmastered_weapons()


# ----------------------------------- Main -----------------------------------

# Main command-line functionality
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-y",
        "--yes",
        help="Automatically says 'Y' to is Warframe Started question.",
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--no-fetch",
        help="Don't fetch new inventory and json files on start.",
        action="store_true",
    )
    args = parser.parse_args()

    # Check that the Warframe is started and logged in.
    if not args.yes:
        logged_in_check = "n"
        while logged_in_check != "y":
            logged_in_check = input(
                "Is Warframe Started & Are you logged in? (y/n): "
            ).lower()

    if not args.no_fetch:
        # Fetch and Filter everything
        inventory_fetcher.fetch_and_save_inventory()
    fetch_inventory_data()
    fetch_warframes()
    fetch_weapons()
    fetch_warframe_recipes()
    fetch_weapon_recipes()
    filter_items()
    main_menu()

# ----------------------------------- END OF FILE -----------------------------------
