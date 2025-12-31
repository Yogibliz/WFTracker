import json

import settings
from format import clean_name

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


# Fetch all Sentinel data in the game
def fetch_sentinels_and_companions(sentinel_and_companion_name):
    with open("warframe_sentinels.json", encoding="utf-8") as sf:
        json_data = json.load(sf)
        for sentinel in json_data["ExportSentinels"]:
            unique_name = sentinel["uniqueName"]
            sentinel_and_companion_name[unique_name] = sentinel["name"]


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
            bp_tuple = (bp_name, bp_count, 0)

            progress = 1 if bp_count >= 1 else 0

            if is_warframe:
                entry = {
                    "name": warframe_name[result_type],
                    "blueprint": bp_tuple,
                    "neuroptics": ("", 0, 0),
                    "chassis": ("", 0, 0),
                    "systems": ("", 0, 0),
                }
            else:
                entry = {
                    "name": clean_name(archwing_name[result_type]),
                    "blueprint": bp_tuple,
                    "harness": ("", 0, 0),
                    "wings": ("", 0, 0),
                    "systems": ("", 0, 0),
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
                if item_type.endswith("Blueprint"):
                    blueprint_version = item_type
                    component_version = item_type.replace("Blueprint", "Component")
                else:
                    blueprint_version = item_type + "Blueprint"
                    component_version = item_type
                    # Also check for base name + "Blueprint" (e.g., SystemsBlueprint for Systems Component)
                    base_blueprint = item_type.replace("Component", "Blueprint")

                bp_count = warframe_inventory.get(blueprint_version, 0)
                comp_count = warframe_inventory.get(component_version, 0)
                
                # If we didn't find ComponentBlueprint, try the base blueprint variant
                if bp_count == 0 and not item_type.endswith("Blueprint"):
                    bp_count = warframe_inventory.get(base_blueprint, 0)
                
                total_count = bp_count + comp_count

                part_tuple = (part_name, bp_count, comp_count)

                if total_count >= 1:
                    progress += 1

                # Sentinel parts
                if is_warframe:
                    if "Neuroptics" in part_name:
                        entry["neuroptics"] = part_tuple
                    elif "Chassis" in part_name:
                        entry["chassis"] = part_tuple
                    elif "Systems" in part_name:
                        entry["systems"] = part_tuple

                # Archwing parts
                else:
                    if "Harness" in part_name or "Chassis" in part_name:
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
            blueprint = (clean_name(unique_name), bp_count, 0)

            progress = 1 if bp_count >= 1 else 0
            owned_parts = []

            for ingredient in recipe.get("ingredients", []):
                item_type = ingredient["ItemType"]
                part_name = clean_name(item_type)

                if not settings.INCLUDE_NON_PRIME_WEAPONS_IN_SETS:
                    if "Prime" not in part_name:
                        continue

                # Count both Blueprint and Component versions
                if item_type.endswith("Blueprint"):
                    blueprint_version = item_type
                    component_version = item_type.replace("Blueprint", "Component")
                else:
                    blueprint_version = item_type + "Blueprint"
                    component_version = item_type
                    # Also check for base name + "Blueprint" (e.g., SystemsBlueprint for Systems Component)
                    base_blueprint = item_type.replace("Component", "Blueprint")

                bp_count = warframe_inventory.get(blueprint_version, 0)
                comp_count = warframe_inventory.get(component_version, 0)
                
                # If we didn't find ComponentBlueprint, try the base blueprint variant
                if bp_count == 0 and not item_type.endswith("Blueprint"):
                    bp_count = warframe_inventory.get(base_blueprint, 0)
                
                total_count = bp_count + comp_count

                # Include all parts, even those with 0 count
                owned_parts.append((part_name, bp_count, comp_count))
                if total_count >= 1:
                    progress += 1

            if progress >= settings.WEAPON_PROGRESS_FILTER:
                weapon_parts[unique_name] = {
                    "name": weapon_name_category[result_type]["name"],
                    "blueprint": blueprint,
                    "parts": owned_parts,
                }


# Fetch all Sentinel and Companion Recipes in the game
def fetch_sentinel_and_companion_recipes(
    sentinel_and_companion_name, warframe_inventory, sentinel_parts
):
    with open("warframe_recipes.json", encoding="utf-8") as wr:
        json_data = json.load(wr)

        for recipe in json_data["ExportRecipes"]:
            unique_name = recipe["uniqueName"]
            result_type = recipe["resultType"]

            is_sentinel = result_type in sentinel_and_companion_name

            if not settings.INCLUDE_NON_PRIME_WARFRAMES_IN_SETS:
                if "Prime" not in unique_name:
                    continue
            if not is_sentinel:
                continue
            if "Blueprint" not in unique_name:
                continue

            # Blueprint
            bp_name = clean_name(unique_name)
            bp_count = warframe_inventory.get(unique_name, 0)
            bp_tuple = (bp_name, bp_count, 0)

            progress = 1 if bp_count >= 1 else 0

            entry = {
                "name": clean_name(sentinel_and_companion_name[result_type]),
                "blueprint": bp_tuple,
                "cerebrum": ("", 0, 0),
                "carapace": ("", 0, 0),
                "systems": ("", 0, 0),
            }

            for ingredient in recipe.get("ingredients", []):
                item_type = ingredient["ItemType"]
                part_name = clean_name(item_type)

                if not any(
                    x in part_name
                    for x in [
                        "Cerebrum",
                        "Carapace",
                        "Systems",
                    ]
                ):
                    continue

                # Remove duplicate "Prime" if it appears twice
                part_name = part_name.replace("Prime Prime", "Prime")

                # Count both Blueprint and Component versions
                # Count both Blueprint and Component versions
                # Handle two cases:
                # 1. ingredient is "ComponentBlueprint" -> look for both Blueprint and Component
                # 2. ingredient is "Component" -> look for Component and ComponentBlueprint, 
                #    but also check for just "Blueprint" (e.g., SystemsBlueprint for SystemsComponent)
                if item_type.endswith("Blueprint"):
                    blueprint_version = item_type
                    component_version = item_type.replace("Blueprint", "Component")
                else:
                    # Item is a Component - try multiple blueprint variants
                    blueprint_version = item_type + "Blueprint"
                    component_version = item_type
                    # Also check for base name + "Blueprint" (e.g., SystemsBlueprint for Systems Component)
                    base_blueprint = item_type.replace("Component", "Blueprint")

                bp_count = warframe_inventory.get(blueprint_version, 0)
                comp_count = warframe_inventory.get(component_version, 0)
                
                # If we didn't find ComponentBlueprint, try the base blueprint variant
                if bp_count == 0 and not item_type.endswith("Blueprint"):
                    bp_count = warframe_inventory.get(base_blueprint, 0)
                
                total_count = bp_count + comp_count

                part_tuple = (part_name, bp_count, comp_count)

                if total_count >= 1:
                    progress += 1

                # Sentinel parts
                if "Cerebrum" in part_name:
                    entry["cerebrum"] = part_tuple
                elif "Carapace" in part_name:
                    entry["carapace"] = part_tuple
                elif "Systems" in part_name:
                    entry["systems"] = part_tuple

            if progress >= settings.WARFRAME_PROGRESS_FILTER:
                sentinel_parts[unique_name] = entry


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
    sentinel_and_companion_name,
    warframe_inventory,
    warframe_parts,
    archwing_parts,
    weapon_parts,
    sentinel_parts,
):
    fetch_inventory_data(warframe_inventory)
    fetch_warframes(warframe_name, archwing_name)
    fetch_weapons(weapon_name_category)
    fetch_sentinels_and_companions(sentinel_and_companion_name)
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
    fetch_sentinel_and_companion_recipes(
        sentinel_and_companion_name, warframe_inventory, sentinel_parts
    )
