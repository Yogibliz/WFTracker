import json
import re

import settings

# ----------------------- Load Into Caches -----------------------

# Cache for JSON data to avoid reloading
_weapon_cache = None
_warframe_cache = None
_recipe_cache = None


def _load_weapon_data():
    """Load and cache weapon data"""
    global _weapon_cache
    if _weapon_cache is None:
        with open("warframe_weapons.json", encoding="utf-8") as f:
            data = json.load(f)
            _weapon_cache = {
                weapon["uniqueName"]: weapon["name"]
                for weapon in data.get("ExportWeapons", [])
            }
    return _weapon_cache


def _load_warframe_data():
    """Load and cache warframe/archwing data"""
    global _warframe_cache
    if _warframe_cache is None:
        with open("warframe_warframes.json", encoding="utf-8") as f:
            data = json.load(f)
            _warframe_cache = {
                wf["uniqueName"]: wf["name"] for wf in data.get("ExportWarframes", [])
            }
    return _warframe_cache


def _load_recipe_data():
    """Load and cache recipe data"""
    global _recipe_cache
    if _recipe_cache is None:
        with open("warframe_recipes.json", encoding="utf-8") as f:
            data = json.load(f)
            _recipe_cache = {
                recipe["uniqueName"]: recipe for recipe in data.get("ExportRecipes", [])
            }
    return _recipe_cache


# ----------------------- Lookup and name matching -----------------------


def _lookup_weapon_part_name(item_type):
    """Look up weapon part name by finding the matching weapon and part type"""
    recipes = _load_recipe_data()
    weapons = _load_weapon_data()

    # Try to find the weapon blueprint that uses this part
    for recipe_name, recipe in recipes.items():
        if "Recipes/Weapons" in recipe_name and recipe_name.endswith("Blueprint"):
            # Check if this recipe has our item_type as an ingredient
            for ingredient in recipe.get("ingredients", []):
                if ingredient.get("ItemType") == item_type:
                    # Found the weapon that uses this part
                    # Get the weapon name from the result type
                    result_type = recipe.get("resultType")
                    if result_type in weapons:
                        weapon_name = weapons[result_type]
                        # Extract just the part name (LowerLimb, String, Grip, etc)
                        part_base_name = item_type.split("/")[-1]

                        # Remove common weapon part prefixes that are redundant with weapon name
                        # This all started with me wanting Paris Prime to show "Paris Prime Lower Limb" instead of "Paris PrimeBow Lower Limb"
                        # I swear this API sucks, I want to beg DE to rewrite the entire thing...

                        # Try to intelligently remove the weapon prefix
                        # Start by splitting on capital letters that represent part types
                        part_types = [
                            "Blade",
                            "Hilt",
                            "String",
                            "Hook",
                            "Barrel",
                            "Receiver",
                            "Stock",
                            "Link",
                            "Guard",
                            "Handle",
                            "Lower",
                            "Upper",
                            "Grip",
                            "Scope",
                            "Magazine",
                            "Ammo",
                            "Head",
                        ]

                        # Find which part type is in the name and extract from there
                        for part_type in part_types:
                            if part_type in part_base_name:
                                # Find the index of this part type and take everything from there
                                idx = part_base_name.find(part_type)
                                if idx > 0:
                                    # Extract from the part type onwards
                                    relevant_part = part_base_name[idx:]
                                    part_formatted = _format_name(relevant_part)
                                    return f"{weapon_name} {part_formatted}".strip()

                        # Fallback: just format the whole thing
                        part_formatted = _format_name(part_base_name)
                        return f"{weapon_name} {part_formatted}".strip()

    # Fallback: just format the part name
    base_name = item_type.split("/")[-1]
    return _format_name(base_name)


def _lookup_warframe_part_name(item_type):
    """Look up warframe part name by finding the matching component recipe"""
    recipes = _load_recipe_data()

    # Try to find a recipe for this part (Neuroptics, Chassis, Systems components)
    for recipe_name, recipe in recipes.items():
        if "Recipes/Warframes" in recipe_name:
            if recipe.get("resultType") == item_type:
                base_name = recipe_name.split("/")[-1]
                return _format_name(base_name)

    return None


def _lookup_archwing_part_name(item_type):
    """Look up archwing part name by finding the matching component recipe"""
    recipes = _load_recipe_data()

    # Try to find a recipe for this part
    for recipe_name, recipe in recipes.items():
        if "Archwing" in recipe_name and "Recipes" in recipe_name:
            if recipe.get("resultType") == item_type:
                base_name = recipe_name.split("/")[-1]
                return _format_name(base_name)

    return None


# ----------------------- Formatting Helpers -----------------------


def _format_name(name_str):
    """Apply consistent formatting to a name string"""
    # Split CamelCase
    formatted = re.sub(r"([a-z])([A-Z])", r"\1 \2", name_str)
    formatted = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", formatted)

    # Remove <ARCHWING> tag
    formatted = re.sub(r"<ARCHWING>\s", "", formatted)

    # Replace Helmet with Neuroptics
    formatted = re.sub(r"\sHelmet\s", " Neuroptics ", formatted)

    # Remove trailing " Component"
    formatted = re.sub(r"\s*Component$", "", formatted)

    return formatted.strip()


# Helper to clean up uniqueName to name mapping
def clean_name(name_str):
    """
    Convert a uniqueName to a human-readable name by matching against data files.

    Handles:
    - Weapons: matches against warframe_weapons.json
    - Warframes/Powersuits: matches against warframe_warframes.json
    - Weapon parts: extracts from recipe data
    - Warframe/Archwing parts: extracts from recipe data
    """
    lower_name = name_str.lower()

    # Try weapon match first (includes weapon parts)
    if "weapons" in lower_name:
        weapons = _load_weapon_data()
        if name_str in weapons:
            return weapons[name_str]

        # Try to find weapon blueprint and get the weapon name
        if "recipes/weapons" in lower_name and name_str.endswith("Blueprint"):
            recipes = _load_recipe_data()
            if name_str in recipes:
                result_type = recipes[name_str].get("resultType")
                if result_type in weapons:
                    return f"{weapons[result_type]} Blueprint"

        # Try to find weapon part name
        part_name = _lookup_weapon_part_name(name_str)
        if part_name:
            return part_name

    # Try warframe/archwing match
    if (
        "powersuit" in lower_name
        or "archwing" in lower_name
        or "warframe" in lower_name
    ):
        warframes = _load_warframe_data()
        if name_str in warframes:
            return _format_name(warframes[name_str])

        # Try to find warframe part name
        if "archwing" in lower_name:
            part_name = _lookup_archwing_part_name(name_str)
            if part_name:
                return part_name

        # Try to find warframe part name
        part_name = _lookup_warframe_part_name(name_str)
        if part_name:
            return part_name

    # Fallback to original formatting logic
    base_name = name_str.split("/")[-1]
    return _format_name(base_name)


# ----------------------- Fetching from API:s -----------------------


# Fetch all currently available warframes in the game
def fetch_warframes(warframe_name, archwing_name):
    with open("warframe_warframes.json", encoding="utf-8") as wf:
        json_data = json.load(wf)
        for warframe in json_data["ExportWarframes"]:
            unique_name = warframe["uniqueName"]
            if "Archwing" in unique_name:
                archwing_name[unique_name] = warframe["name"]
            else:
                warframe_name[unique_name] = warframe["name"]


# Fetch all currently available weapons in the game
def fetch_weapons(weapon_name_category):
    with open("warframe_weapons.json", encoding="utf-8") as wp:
        json_data = json.load(wp)
        for weapon in json_data["ExportWeapons"]:
            weapon_name_category[weapon["uniqueName"]] = {
                "name": weapon["name"],
                "category": weapon["productCategory"],
            }


# Fetch all Warframe and Archwing Recipes in the game
def fetch_warframe_and_archwing_recipes(
    warframe_name, archwing_name, warframe_inventory, warframe_parts, archwing_parts
):
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
                blueprint_version = (
                    item_type
                    if item_type.endswith("Blueprint")
                    else item_type + "Blueprint"
                )
                component_version = (
                    item_type
                    if not item_type.endswith("Blueprint")
                    else item_type.replace("Blueprint", "Component")
                )

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
def fetch_weapon_recipes(
    weapon_name_category, warframe_inventory, weapon_parts, warframe_name, archwing_name
):
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
                blueprint_version = (
                    item_type
                    if item_type.endswith("Blueprint")
                    else item_type + "Blueprint"
                )
                component_version = (
                    item_type
                    if not item_type.endswith("Blueprint")
                    else item_type.replace("Blueprint", "Component")
                )

                count = warframe_inventory.get(item_type, 0)
                count += warframe_inventory.get(blueprint_version, 0)
                count += warframe_inventory.get(component_version, 0)

                # Include all parts, even those with 0 count
                owned_parts.append((part_name, count))
                if count >= 1:
                    progress += 1

            if progress >= settings.WEAPON_PROGRESS_FILTER:
                weapon_parts[unique_name] = {
                    "name": weapon_name_category[result_type]["name"],
                    "blueprint": blueprint,
                    "parts": owned_parts,
                }


# Fetch the inventory data.
def fetch_inventory_data(warframe_inventory):
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

        # Skip weapon part blueprints only when prime-only mode is enabled
        # (Mainly a fix for GalariakPrime which isn't a prime weapon...)
        if "weaponparts" in lower_type and item_type.endswith("Blueprint"):
            if settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS == 0:
                return False

        # Check if it's a weapon or warframe based on the path
        is_weapon = "weapon" in lower_type
        is_warframe = "warframe" in lower_type or "archwing" in lower_type

        # Determine if this item passes the prime filter
        is_prime = "prime" in lower_type

        if is_weapon:
            return is_prime or settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS == 1
        elif is_warframe:
            return is_prime or settings.INCLUDE_NON_PRIME_WARFRAMES_IN_SETS == 1
        else:
            # For other item types, include if prime or if we're including non-primes
            return is_prime or (
                settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS == 1
                or settings.INCLUDE_NON_PRIME_WARFRAMES_IN_SETS == 1
            )

    # Import from MiscItems
    if "MiscItems" in data:
        for item in data["MiscItems"]:
            item_type = item.get("ItemType", "")
            if should_include_item(item_type):
                warframe_inventory[item_type] = item.get("ItemCount", 0)

    # Import from Recipes
    if "Recipes" in data:
        for item in data["Recipes"]:
            item_type = item.get("ItemType", "")
            if should_include_item(item_type):
                warframe_inventory[item_type] = item.get("ItemCount", 0)


# Fetch everything in correct order, helper for main
def fetch_items(
    warframe_name,
    archwing_name,
    weapon_name_category,
    warframe_inventory,
    warframe_parts,
    archwing_parts,
    weapon_parts,
):
    fetch_inventory_data(warframe_inventory)
    fetch_warframes(warframe_name, archwing_name)
    fetch_weapons(weapon_name_category)
    fetch_warframe_and_archwing_recipes(
        warframe_name, archwing_name, warframe_inventory, warframe_parts, archwing_parts
    )
    fetch_weapon_recipes(
        weapon_name_category,
        warframe_inventory,
        weapon_parts,
        warframe_name,
        archwing_name,
    )
