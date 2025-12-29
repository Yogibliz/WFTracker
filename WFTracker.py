#!/usr/bin/env python3

import argparse
import json
import os
import re

from prettytable import PrettyTable

import json_fetcher
import settings

# ----------------------- Data Structures -----------------------

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


# ----------------------- Menu Definitions -----------------------

SELLABLE_ITEMS = [
    {
        "label": "Print Duplicate Primes Parts",
        "header": "----- Duplicate Prime Parts (mastered and unmastered) -----",
        "func": "print_set_of_tuples_as_table",
        "data": duplicate_prime_parts,
    },
    {
        "label": "Print Prime Parts for Mastered",
        "header": "----- Mastered Prime Parts -----",
        "func": "print_set_of_tuples_as_table",
        "data": mastered_prime_parts,
    },
]

SETS = [
    {
        "label": "Print Weapon Prime Parts as Part of Set",
        "header": "----- Prime Weapons Set Progress -----",
        "func": "print_weapon_set_progress_as_table",
        "data": weapon_parts,
    },
    {
        "label": "Prime Warframe Prime Parts as Part of Set",
        "header": "----- Prime Warframes Set Progress -----",
        "func": "print_warframe_set_progress_as_table",
        "data": warframe_parts,
    },
    {
        "label": "Prime Archwing Prime Parts as Part of Set",
        "header": "----- Prime Archwing Set Progress -----",
        "func": "print_archwing_set_progress_as_table",
        "data": archwing_parts,
    },
]

UNMASTERED_ITEMS = [
    {
        "label": "Print Unmastered Warframes & Archwings",
        "header": "----- Unmastered Warframes & Archwings -----",
        "func": "print_set_as_table",
        "data": unmastered_warframes,
    },
    {
        "label": "Print Unmastered Primary Weapons",
        "header": "----- Unmastered Primary Weapons -----",
        "func": "print_set_as_table",
        "data": unmastered_primaries,
    },
    {
        "label": "Print Unmastered Secondary Weapons",
        "header": "----- Unmastered Secondary Weapons -----",
        "func": "print_set_as_table",
        "data": unmastered_secondaries,
    },
    {
        "label": "Print Unmastered Melee Weapons",
        "header": "----- Unmastered Melee Weapons -----",
        "func": "print_set_as_table",
        "data": unmastered_melees,
    },
    {
        "label": "Print Unmastered Arch Weapons",
        "header": "----- Unmastered Arch Weapons -----",
        "func": "print_set_as_table",
        "data": unmastered_arch_weapons,
    },
    {
        "label": "Print Unmastered Amps",
        "header": "----- Unmastered Amps -----",
        "func": "print_set_as_table",
        "data": unmastered_amps,
    },
]

MASTERED_ITEMS = [
    {
        "label": "Print Mastered Warframes & Archwings",
        "header": "----- Mastered or Owned Warframes & Archwings -----",
        "func": "print_set_as_table",
        "data": mastered_or_owned_warframes,
    },
    {
        "label": "Print Mastered Primary Weapons",
        "header": "----- Mastered or Owned Primary Weapons -----",
        "func": "print_set_as_table",
        "data": mastered_or_owned_primaries,
    },
    {
        "label": "Print Mastered Secondary Weapons",
        "header": "----- Mastered or Owned Secondary Weapons -----",
        "func": "print_set_as_table",
        "data": mastered_or_owned_secondaries,
    },
    {
        "label": "Print Mastered Melee Weapons",
        "header": "----- Mastered or Owned Melee Weapons -----",
        "func": "print_set_as_table",
        "data": mastered_or_owned_melees,
    },
    {
        "label": "Print Mastered Arch Weapons",
        "header": "----- Mastered or Owned Arch Weapons -----",
        "func": "print_set_as_table",
        "data": mastered_or_owned_arch_weapons,
    },
    {
        "label": "Print Mastered Amps",
        "header": "----- Mastered or Owned Amps -----",
        "func": "print_set_as_table",
        "data": mastered_or_owned_amps,
    },
]

MENU_ITEMS = SELLABLE_ITEMS + SETS + UNMASTERED_ITEMS + MASTERED_ITEMS

# Index Breakpoints used for Main Menu splits
BP_SETS = len(SELLABLE_ITEMS)
BP_UNMASTERED = BP_SETS + len(SETS)
BP_MASTERED = BP_UNMASTERED + len(UNMASTERED_ITEMS)

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


# Fetch all Warframe and Archwing Recipes in the game
def fetch_warframe_and_archwing_recipes():
    with open("warframe_recipes.json", encoding="utf-8") as wr:
        json_data = json.load(wr)

        for recipe in json_data["ExportRecipes"]:
            unique_name = recipe["uniqueName"]
            result_type = recipe["resultType"]

            is_warframe = result_type in warframe_name
            is_archwing = result_type in archwing_name

            if not settings.INCLUDE_NON_PRIME_WARFRAMES_IN_SETS:
                if "Prime" not in unique_name:
                    continue
            if not is_warframe and not is_archwing:
                continue

            # Blueprint
            bp_name = clean_name(unique_name)
            bp_count = warframe_inventory.get(unique_name, 0)
            bp_tuple = (bp_name, bp_count)

            progress = 1 if bp_count >= 1 else 0

            if is_warframe:
                entry = {
                    "name": warframe_name[result_type],
                    "blueprint": bp_tuple,
                    "neuroptics": ("", 0),
                    "chassis": ("", 0),
                    "systems": ("", 0),
                }
            else:
                entry = {
                    "name": clean_name(archwing_name[result_type]),
                    "blueprint": bp_tuple,
                    "harness": ("", 0),
                    "wings": ("", 0),
                    "systems": ("", 0),
                }

            for ingredient in recipe.get("ingredients", []):
                item_type = ingredient["ItemType"]
                part_name = clean_name(item_type)

                if not any(
                    x in part_name
                    for x in ["Neuroptics", "Chassis", "Systems", "Harness", "Wings"]
                ):
                    continue

                # Count both Blueprint and Component versions
                # e.g., CalibianPrimeSystemsBlueprint + CalibianPrimeSystemsComponent
                blueprint_version = item_type if item_type.endswith("Blueprint") else item_type + "Blueprint"
                component_version = item_type if not item_type.endswith("Blueprint") else item_type.replace("Blueprint", "Component")
                
                count = warframe_inventory.get(item_type, 0)
                count += warframe_inventory.get(blueprint_version, 0)
                count += warframe_inventory.get(component_version, 0)
                
                part_tuple = (part_name, count)

                if count >= 1:
                    progress += 1

                # Warframe parts
                if is_warframe:
                    if "Neuroptics" in part_name:
                        entry["neuroptics"] = part_tuple
                    elif "Chassis" in part_name:
                        entry["chassis"] = part_tuple
                    elif "Systems" in part_name:
                        entry["systems"] = part_tuple

                # Archwing parts
                else:
                    if "Harness" in part_name:
                        entry["harness"] = part_tuple
                    elif "Wings" in part_name:
                        entry["wings"] = part_tuple
                    elif "Systems" in part_name:
                        entry["systems"] = part_tuple

            if progress >= settings.WARFRAME_PROGRESS_FILTER:
                if is_warframe:
                    warframe_parts[unique_name] = entry
                else:
                    archwing_parts[unique_name] = entry


# Fetch all Weapon Recipes in the game
def fetch_weapon_recipes():
    with open("warframe_recipes.json", encoding="utf-8") as wr:
        json_data = json.load(wr)

        for recipe in json_data["ExportRecipes"]:
            unique_name = recipe["uniqueName"]
            result_type = recipe["resultType"]

            if not settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS:
                if "Prime" not in unique_name:
                    continue
            if result_type in warframe_name or result_type in archwing_name:
                continue
            if "Sentinel" in unique_name or "Sentinel" in clean_name(result_type):
                continue
            if "Weapons" not in unique_name:
                continue
            # Skip weapon part blueprints (WeaponParts recipes shouldn't end in Blueprint)
            if "WeaponParts" in unique_name and unique_name.endswith("Blueprint"):
                continue

            bp_count = warframe_inventory.get(unique_name, 0)
            blueprint = (clean_name(unique_name), bp_count)

            progress = 1 if bp_count >= 1 else 0
            owned_parts = []

            for ingredient in recipe.get("ingredients", []):
                item_type = ingredient["ItemType"]
                part_name = clean_name(item_type)

                if not settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS:
                    if "Prime" not in part_name:
                        continue

                # Count both Blueprint and Component versions
                blueprint_version = item_type if item_type.endswith("Blueprint") else item_type + "Blueprint"
                component_version = item_type if not item_type.endswith("Blueprint") else item_type.replace("Blueprint", "Component")
                
                count = warframe_inventory.get(item_type, 0)
                count += warframe_inventory.get(blueprint_version, 0)
                count += warframe_inventory.get(component_version, 0)

                if count >= 1:
                    owned_parts.append((part_name, count))
                    progress += 1

            if progress >= settings.WEAPON_PROGRESS_FILTER:
                weapon_parts[unique_name] = {
                    "name": weapon_name_category[result_type]["name"],
                    "blueprint": blueprint,
                    "parts": owned_parts,
                }


# Fetch the inventory data.
def fetch_inventory_data():
    with open("inventory.json") as f:
        data = json.load(f)

    # Helper function to check if an item should be included based on prime filter
    def should_include_item(item_type):
        lower_type = item_type.lower()

        # Skip projection, bucks, and resources
        if (
            "projection" in lower_type
            or "bucks" in lower_type
            or "resources" in lower_type
        ):
            return False

        # Check if it's a weapon or warframe based on the path
        is_weapon = "weapon" in lower_type
        is_warframe = "warframe" in lower_type or "archwing" in lower_type

        # Determine if this item passes the prime filter
        is_prime = "prime" in lower_type

        if is_weapon:
            # Include if: (item is prime) OR (settings allow non-prime weapons)
            return is_prime or settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS == 1
        elif is_warframe:
            # Include if: (item is prime) OR (settings allow non-prime warframes)
            return is_prime or settings.INCLUDE_NON_PRIME_WARFRAMES_IN_SETS == 1
        else:
            # For other item types, include if prime or if we're including non-primes
            return is_prime or (
                settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS == 1
                or settings.INCLUDE_NON_PRIME_WARFRAMES_IN_SETS == 1
            )

    # Import from MiscItems (old format - components as MiscItems)
    if "MiscItems" in data:
        for item in data["MiscItems"]:
            item_type = item.get("ItemType", "")
            if should_include_item(item_type):
                warframe_inventory[item_type] = item.get("ItemCount", 0)

    # Import from Recipes (new format - components as Recipes)
    if "Recipes" in data:
        for item in data["Recipes"]:
            item_type = item.get("ItemType", "")
            if should_include_item(item_type):
                warframe_inventory[item_type] = item.get("ItemCount", 0)


# Fetch everything in correct order, helper for main
def fetch_items():
    fetch_inventory_data()
    fetch_warframes()
    fetch_weapons()
    fetch_warframe_and_archwing_recipes()
    fetch_weapon_recipes()


# ----------------------- Formatting Helpers -----------------------


# Helper to format if part more than 1 or not.
def has_part(count):
    return "✓" if count >= 1 else "✗"


# Helper to clean up uniqueName to name mapping
def clean_name(name_str):
    base_name = name_str.split("/")[-1]

    # Split CamelCase
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", base_name)
    cleaned = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", cleaned)

    # Remove <ARCHWING> tag
    cleaned = re.sub(r"<ARCHWING>\s", "", cleaned)

    # Replace Helmet with Neuroptics
    cleaned = re.sub(r"\sHelmet\s", " Neuroptics ", cleaned)

    # Remove trailing " Component"
    cleaned = re.sub(r"\s*Component$", "", cleaned)

    return cleaned.strip()


# Basic Main Menu
def main_menu():
    menu = PrettyTable(["Index", "Action"])
    menu.align["Action"] = "l"
    menu.title = "----- Main Menu -----"

    for index, item in enumerate(MENU_ITEMS):
        if index == 0:
            menu.add_row(["", "--- Sellable Items ---"])

        elif index == BP_SETS:
            menu.add_row(["", ""])  # Spacer
            menu.add_row(["", "--- Sets ---"])

        elif index == BP_UNMASTERED:
            menu.add_row(["", ""])  # Spacer
            menu.add_row(["", "--- Unmastered Items ---"])

        elif index == BP_MASTERED:
            menu.add_row(["", ""])  # Spacer
            menu.add_row(["", "--- Mastered Items ---"])

        menu.add_row([index, item["label"]])

    selected_option = -1

    # Automatically calculate valid range based on list size
    while selected_option not in range(len(MENU_ITEMS)):
        os.system("cls" if os.name == "nt" else "clear")
        print(menu)

        # Unfiltered items, includes warframe weapons (e.g. Valkyr Talons), Sentinel weapons (e.g. Deconstructor) etc...
        # print(unmastered_others)
        # print(mastered_or_owned_others)

        user_input = input("What do you want to do? (q to quit): ")

        if user_input == "q":
            exit()

        try:
            selected_option = int(user_input)
        except ValueError:
            continue

    print_selection(selected_option)


# Print the selected option in the main_menu
def print_selection(index):
    os.system("cls" if os.name == "nt" else "clear")

    selection = MENU_ITEMS[index]

    func_name = selection["func"]
    if func_name in globals():
        func_to_call = globals()[func_name]
        func_to_call(selection["data"], selection["header"])
    else:
        print(f"Error: Function '{func_name}' not found.")

    go_back = ""
    while go_back != "b":
        go_back = input("Go back to menu or quit? (b/q): ").lower()
        if go_back == "q":
            exit()
    main_menu()


# Convert the set of tuples data into a printable table with item and count
def print_set_of_tuples_as_table(input_set, title):
    table = PrettyTable(["Item", "Count"])
    table.title = title
    table.sortby = "Count"
    table.reversesort = True

    for tup in input_set:
        item = tup[0]
        count = tup[1]
        table.add_row([item, count])
    print(table)


# Convert the set into a printable table
def print_set_as_table(input_set, title):
    table = PrettyTable(["Item"])
    table.title = title

    for item in sorted(input_set):
        table.add_row([item])
    print(table)


# For prime_warframe_sets.
def print_warframe_set_progress_as_table(prime_warframe_set, title):
    table = PrettyTable(
        ["Item", "Blueprint", "Neuroptics", "Chassis", "Systems", "Progress"]
    )
    table.title = title
    table.sortby = "Progress"
    table.reversesort = True

    # Sort by name
    for entry in prime_warframe_set.values():
        bp = entry["blueprint"][1]
        neu = entry["neuroptics"][1]
        cha = entry["chassis"][1]
        sys = entry["systems"][1]

        progress = sum(count >= 1 for count in (bp, neu, cha, sys))

        row = [
            entry["name"],
            has_part(bp),
            has_part(neu),
            has_part(cha),
            has_part(sys),
            f"{progress}/4",
        ]
        table.add_row(row)
    print(table)


# For archwing_sets
def print_archwing_set_progress_as_table(archwing_set, title):
    table = PrettyTable(
        ["Item", "Blueprint", "Harness", "Wings", "Systems", "Progress"]
    )
    table.title = title
    table.sortby = "Progress"
    table.reversesort = True

    for entry in archwing_set.values():
        bp = entry["blueprint"][1]
        har = entry["harness"][1]
        wing = entry["wings"][1]
        sys = entry["systems"][1]

        progress = sum(count >= 1 for count in (bp, har, wing, sys))

        row = [
            entry["name"],
            has_part(bp),
            has_part(har),
            has_part(wing),
            has_part(sys),
            f"{progress}/4",
        ]
        table.add_row(row)
    print(table)


# For the prime_weapon_sets.
def print_weapon_set_progress_as_table(prime_weapon_set, title):
    table = PrettyTable(["Item", "Parts", "Progress"])
    table.title = title
    table.sortby = "Progress"
    table.reversesort = True

    for entry in prime_weapon_set.values():
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

        table.add_row([entry["name"], formatted_parts, progress_str])
    print(table)


# ----------------------- Filter API-data into categories -----------------------


# Return each prime item there's a duplicate of.
def filter_duplicate_prime_parts():
    for item in warframe_inventory:
        # Only process Blueprint versions
        if not item.endswith("Blueprint"):
            continue
            
        blueprint_count = warframe_inventory[item]
        
        # Check if there's a Component version of this part
        component_version = item.replace("Blueprint", "Component")
        component_count = warframe_inventory.get(component_version, 0)
        
        # The part is sellable if:
        # 1. There are multiple blueprints (blueprint_count > 1), OR
        # 2. There's at least 1 blueprint AND 1 component (meaning the set is complete, so blueprint is extra)
        if blueprint_count > 1 or (blueprint_count >= 1 and component_count >= 1):
            # Count only the sellable blueprints
            sellable_count = blueprint_count
            if component_count >= 1:
                # If there's a component, we can sell all blueprints (the component means it's built)
                sellable_count = blueprint_count
            
            if sellable_count >= 1:
                duplicate_prime_parts.add((clean_name(item), sellable_count))


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
                    mastered_or_owned_arch_weapons.add(clean_name(name))

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
    for key, data in weapon_name_category.items():
        name = data["name"]
        category = data["category"]

        # Primary
        if category == "LongGuns":
            if name not in mastered_or_owned_primaries:
                unmastered_primaries.add(name)

        # Amps require the use of the key, since they're categorised as pistols for some reason.
        elif "OperatorAmplifiers" in key and "Prism" in key:
            if name not in mastered_or_owned_amps:
                unmastered_amps.add(name)

        # Special case for sirocco since it's marked as a pistol in the key,
        # and the only amp categoriesed as "OperatorAmps". (Hope they change them all to OperatorAmps...)
        elif category == "OperatorAmps":
            if name not in mastered_or_owned_amps:
                unmastered_amps.add(name)

        # Special case for Zaw weapons, since they're catagorized as pistols (Surely some day these categories will make sense.)
        elif "/Ostron/Melee" in key and "Tip" in key:
            if name not in mastered_or_owned_melees:
                unmastered_melees.add(name)

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
                unmastered_arch_weapons.add(clean_name(name))

        # Weirdly categoriezed in API. Might set up exceptions to catch later...
        else:
            if name not in mastered_or_owned_others:
                unmastered_others.add(name)


# Filter everything in correct order, helper for main
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
        json_fetcher.fetch_warframe_json_data()
    fetch_items()
    filter_items()
    main_menu()

# ----------------------------------- END OF FILE -----------------------------------
