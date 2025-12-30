#!/usr/bin/env python3

import argparse

import json_fetcher
from fetch import fetch_items
from filter import filter_items
from prints import main_menu

# ----------------------- Data Structures -----------------------

# Warframe API data
warframe_name = {}
archwing_name = {}
weapon_name_category = {}
sentinel_and_companion_name = {}

# Inventory data
warframe_inventory = dict()

# Separate Mastered
mastered_or_owned_warframes = set()
mastered_or_owned_primaries = set()
mastered_or_owned_secondaries = set()
mastered_or_owned_melees = set()
mastered_or_owned_amps = set()
mastered_or_owned_arch_weapons = set()
mastered_or_owned_sentinels_and_companions = set()
mastered_or_owned_others = set()

# Separate Unmastered
unmastered_warframes = set()
unmastered_primaries = set()
unmastered_secondaries = set()
unmastered_melees = set()
unmastered_amps = set()
unmastered_arch_weapons = set()
unmastered_sentinels_and_companions = set()
unmastered_others = set()

# Sellable duplicates
duplicate_prime_parts = set()

# Sellable prime parts that's not needed
mastered_prime_parts = set()

# Tables of sets
warframe_parts = {}
archwing_parts = {}
weapon_parts = {}
sentinel_parts = {}
sellable_prime_sets = {}

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
    fetch_items(
        warframe_name,
        archwing_name,
        weapon_name_category,
        sentinel_and_companion_name,
        warframe_inventory,
        warframe_parts,
        archwing_parts,
        weapon_parts,
        sentinel_parts,
    )
    filter_items(
        warframe_name,
        weapon_name_category,
        sentinel_and_companion_name,
        warframe_inventory,
        mastered_or_owned_warframes,
        mastered_or_owned_primaries,
        mastered_or_owned_secondaries,
        mastered_or_owned_melees,
        mastered_or_owned_amps,
        mastered_or_owned_arch_weapons,
        mastered_or_owned_sentinels_and_companions,
        mastered_or_owned_others,
        unmastered_warframes,
        unmastered_primaries,
        unmastered_secondaries,
        unmastered_melees,
        unmastered_amps,
        unmastered_arch_weapons,
        unmastered_sentinels_and_companions,
        unmastered_others,
        duplicate_prime_parts,
        mastered_prime_parts,
        warframe_parts,
        archwing_parts,
        weapon_parts,
        sentinel_parts,
        sellable_prime_sets,
    )

    # Create context dictionary for menu functions
    context = {
        "warframe_name": warframe_name,
        "archwing_name": archwing_name,
        "weapon_name_category": weapon_name_category,
        "warframe_inventory": warframe_inventory,
        "warframe_parts": warframe_parts,
        "archwing_parts": archwing_parts,
        "weapon_parts": weapon_parts,
        "sentinel_parts": sentinel_parts,
        "sellable_prime_sets": sellable_prime_sets,
        "mastered_or_owned_warframes": mastered_or_owned_warframes,
        "mastered_or_owned_primaries": mastered_or_owned_primaries,
        "mastered_or_owned_secondaries": mastered_or_owned_secondaries,
        "mastered_or_owned_melees": mastered_or_owned_melees,
        "mastered_or_owned_amps": mastered_or_owned_amps,
        "mastered_or_owned_arch_weapons": mastered_or_owned_arch_weapons,
        "mastered_or_owned_sentinels_and_companions": mastered_or_owned_sentinels_and_companions,
        "mastered_or_owned_others": mastered_or_owned_others,
        "unmastered_warframes": unmastered_warframes,
        "unmastered_primaries": unmastered_primaries,
        "unmastered_secondaries": unmastered_secondaries,
        "unmastered_melees": unmastered_melees,
        "unmastered_amps": unmastered_amps,
        "unmastered_arch_weapons": unmastered_arch_weapons,
        "unmastered_sentinels_and_companions": unmastered_sentinels_and_companions,
        "unmastered_others": unmastered_others,
        "duplicate_prime_parts": duplicate_prime_parts,
        "mastered_prime_parts": mastered_prime_parts,
    }

    main_menu(context)

# ----------------------------------- END OF FILE -----------------------------------
