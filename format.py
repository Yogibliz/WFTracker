import json
import re

# ----------------------- Load Into Caches -----------------------

# Cache for JSON data to avoid reloading
_weapon_cache = None
_warframe_cache = None
_recipe_cache = None
_sentinel_cache = None


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


def _load_sentinel_data():
    """Load and cache sentinel data"""
    global _sentinel_cache
    if _sentinel_cache is None:
        with open("warframe_sentinels.json", encoding="utf-8") as f:
            data = json.load(f)
            _sentinel_cache = {
                sentinel["uniqueName"]: sentinel["name"]
                for sentinel in data.get("ExportSentinels", [])
            }
    return _sentinel_cache


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
                                    result = f"{weapon_name} {part_formatted}".strip()
                                    return _remove_duplicate_names(result)

                        # Fallback: just format the whole thing
                        part_formatted = _format_name(part_base_name)
                        result = f"{weapon_name} {part_formatted}".strip()
                        return _remove_duplicate_names(result)

    # Fallback: just format the part name
    base_name = item_type.split("/")[-1]
    return _remove_duplicate_names(_format_name(base_name))


def _lookup_warframe_part_name(item_type):
    """Look up warframe part name by finding the matching component recipe and warframe"""
    recipes = _load_recipe_data()
    warframes = _load_warframe_data()

    # Try to find a recipe for this part (Neuroptics, Chassis, Systems components)
    for recipe_name, recipe in recipes.items():
        if "Recipes/Warframes" in recipe_name:
            if recipe.get("resultType") == item_type:
                # Found the recipe that produces this part
                # Now find the warframe blueprint recipe that uses this part
                for bp_recipe_name, bp_recipe in recipes.items():
                    if (
                        "Recipes/Warframes" in bp_recipe_name
                        and bp_recipe_name.endswith("Blueprint")
                    ):
                        for ingredient in bp_recipe.get("ingredients", []):
                            if ingredient.get("ItemType") == item_type:
                                # Found the warframe blueprint that uses this part
                                result_type = bp_recipe.get("resultType")
                                if result_type in warframes:
                                    warframe_name = warframes[result_type]
                                    # Extract part type (Neuroptics, Chassis, Systems)
                                    part_base_name = item_type.split("/")[-1]
                                    part_formatted = _format_name(part_base_name)
                                    return f"{warframe_name} {part_formatted}".strip()

                # Fallback: just use the recipe name
                base_name = recipe_name.split("/")[-1]
                return _format_name(base_name)

    return None


def _lookup_archwing_part_name(item_type):
    """Look up archwing part name by finding the matching component recipe and archwing"""
    recipes = _load_recipe_data()
    warframes = _load_warframe_data()

    # Try to find a recipe for this part
    for recipe_name, recipe in recipes.items():
        if "Archwing" in recipe_name and "Recipes" in recipe_name:
            if recipe.get("resultType") == item_type:
                # Found the recipe that produces this part
                # Now find the archwing blueprint recipe that uses this part
                for bp_recipe_name, bp_recipe in recipes.items():
                    if (
                        "Archwing" in bp_recipe_name
                        and "Recipes" in bp_recipe_name
                        and bp_recipe_name.endswith("Blueprint")
                    ):
                        for ingredient in bp_recipe.get("ingredients", []):
                            if ingredient.get("ItemType") == item_type:
                                # Found the archwing blueprint that uses this part
                                result_type = bp_recipe.get("resultType")
                                if result_type in warframes:
                                    archwing_name = warframes[result_type]
                                    # Format the archwing name (remove <ARCHWING> tag)
                                    archwing_name = _format_name(archwing_name)
                                    # Extract part type (Wings, Chassis, Systems)
                                    part_base_name = item_type.split("/")[-1]

                                    # Remove "Prime" and "Archwing" prefixes from part name
                                    if part_base_name.startswith("PrimeArchwing"):
                                        part_base_name = part_base_name[
                                            13:
                                        ]  # Remove "PrimeArchwing"
                                    elif part_base_name.startswith("Prime"):
                                        part_base_name = part_base_name[
                                            5:
                                        ]  # Remove "Prime" otherwise give double prime *facepalm* example: "Odonata Prime Prime Harness" due to API formatting.
                                    part_formatted = _format_name(part_base_name)
                                    # Convert "Chassis" to "Harness" for archwings (they have chassis in the API, probably reused from warframes)
                                    if part_formatted == "Chassis":
                                        part_formatted = "Harness"
                                    return f"{archwing_name} {part_formatted}".strip()

                # Fallback: just use the recipe name
                base_name = recipe_name.split("/")[-1]
                return _format_name(base_name)

    return None


def _lookup_sentinel_part_name(item_type):
    """Look up sentinel part name by finding the matching component recipe and sentinel"""
    recipes = _load_recipe_data()
    sentinels = _load_sentinel_data()

    # Find the sentinel blueprint recipe that uses this part
    for bp_recipe_name, bp_recipe in recipes.items():
        if (
            "Sentinel" in bp_recipe_name
            and "Recipes" in bp_recipe_name
            and bp_recipe_name.endswith("Blueprint")
        ):
            for ingredient in bp_recipe.get("ingredients", []):
                if ingredient.get("ItemType") == item_type:
                    # Found the sentinel blueprint that uses this part
                    result_type = bp_recipe.get("resultType")
                    if result_type in sentinels:
                        sentinel_name = sentinels[result_type]
                        # Extract part type (Cerebrum, Carapace, Systems)
                        part_base_name = item_type.split("/")[-1]

                        # Remove "Prime" prefix from part name since it's in the sentinel name
                        if part_base_name.startswith("Prime"):
                            part_base_name = part_base_name[5:]  # Remove "Prime"

                        # Also remove the sentinel name prefix to avoid duplication
                        # e.g., "HeliosCerebrum" -> "Cerebrum" (when sentinel is "Helios Prime")
                        sentinel_base = sentinel_name.split()[
                            0
                        ]  # Get just "Helios" from "Helios Prime"
                        if part_base_name.startswith(sentinel_base):
                            part_base_name = part_base_name[len(sentinel_base) :]

                        part_formatted = _format_name(part_base_name)
                        result = f"{sentinel_name} {part_formatted}".strip()
                        return _remove_duplicate_names(result)

    return None


# ----------------------- Formatting Helpers -----------------------


def _remove_duplicate_names(text):
    """Remove duplicate name patterns like 'Bo Prime Bo Prime' -> 'Bo Prime'"""
    # First, handle "Prime Prime" -> "Prime"
    text = text.replace("Prime Prime", "Prime")

    # Then, handle weapon name duplication patterns like "Hikou Prime Hikou Stars" -> "Hikou Prime Stars"
    # and "Glaive Prime Glaive Prime Disc" -> "Glaive Prime Disc"
    # and "Bo Prime Bo Prime Ornament" -> "Bo Prime Ornament"
    words = text.split()
    if len(words) >= 3:
        cleaned_words = []
        i = 0
        while i < len(words):
            if i + 2 < len(words):
                # Check if current word matches the word after "Prime"
                # Pattern: "Name Prime Name ..."
                if words[i + 1] == "Prime" and words[i] == words[i + 2]:
                    # Found "Name Prime Name", add "Name Prime" and skip both the duplicate Name and any trailing "Prime" words
                    cleaned_words.append(words[i])
                    cleaned_words.append("Prime")
                    i += 3  # Skip "Name Prime Name"
                    # Also skip any trailing "Prime" words after the duplicate name
                    while i < len(words) and words[i] == "Prime":
                        i += 1
                    continue
            cleaned_words.append(words[i])
            i += 1
        text = " ".join(cleaned_words)

    return text


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
    - Sentinels: matches against warframe_sentinels.json
    - Sentinel parts: extracts from recipe data
    """
    lower_name = name_str.lower()

    # Try sentinel match first (before weapon match since sentinel parts can be in WeaponParts folder)
    # Try to find sentinel part name
    part_name = _lookup_sentinel_part_name(name_str)
    if part_name:
        return part_name

    # Try weapon match (includes weapon parts)
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

    # Try sentinel match by name (for direct sentinel lookups)
    if "sentinel" in lower_name:
        sentinels = _load_sentinel_data()
        if name_str in sentinels:
            return sentinels[name_str]

        # Try to find sentinel blueprint and get the sentinel name
        if "recipes/sentinel" in lower_name and name_str.endswith("Blueprint"):
            recipes = _load_recipe_data()
            if name_str in recipes:
                result_type = recipes[name_str].get("resultType")
                if result_type in sentinels:
                    return f"{sentinels[result_type]} Blueprint"

    # Try warframe/archwing match
    if (
        "powersuit" in lower_name
        or "archwing" in lower_name
        or "warframe" in lower_name
    ):
        warframes = _load_warframe_data()
        if name_str in warframes:
            return _format_name(warframes[name_str])

        # Try to find archwing blueprint and get the archwing name
        if "archwing" in lower_name and name_str.endswith("Blueprint"):
            recipes = _load_recipe_data()
            if name_str in recipes:
                result_type = recipes[name_str].get("resultType")
                if result_type in warframes:
                    archwing_name = _format_name(warframes[result_type])
                    # Convert "Chassis" to "Harness" for archwings (they have harness, not chassis)
                    if "Chassis" in name_str:
                        return f"{archwing_name} Harness Blueprint"
                    return f"{archwing_name} Blueprint"
                else:
                    # If result_type is not directly an archwing, try to find the archwing via the part
                    part_name = _lookup_archwing_part_name(result_type)
                    if part_name:
                        # part_name is like "Odonata Prime Harness", extract the archwing name
                        parts = part_name.split()
                        if len(parts) >= 2:
                            archwing_name = " ".join(
                                parts[:-1]
                            )  # Everything except the last word (the part type)
                            if "Chassis" in name_str:
                                return f"{archwing_name} Harness Blueprint"
                            return f"{archwing_name} Blueprint"

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
    result = _format_name(base_name)
    return _remove_duplicate_names(result)
