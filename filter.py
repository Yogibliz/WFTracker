import json
from fetch import clean_name

# ----------------------- Filter API-data into categories -----------------------


# Return each prime item there's a duplicate of.
def filter_duplicate_prime_parts(warframe_inventory, duplicate_prime_parts):
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
def filter_mastered_prime_parts(warframe_inventory, mastered_or_owned_warframes, mastered_or_owned_primaries, mastered_or_owned_secondaries, mastered_or_owned_melees, mastered_or_owned_amps, mastered_or_owned_arch_weapons, mastered_or_owned_others, mastered_prime_parts):
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
                mastered_prime_parts.add(
                    (clean_name(inv_item_type), warframe_inventory[inv_item_type])
                )


# Get which items have been mastered thus far.
def filter_mastered_and_owned_gear(warframe_name, weapon_name_category, mastered_or_owned_warframes, mastered_or_owned_primaries, mastered_or_owned_secondaries, mastered_or_owned_melees, mastered_or_owned_amps, mastered_or_owned_arch_weapons, mastered_or_owned_others):
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
def filter_unmastered_warframes(warframe_name, mastered_or_owned_warframes, unmastered_warframes):
    for _, name in warframe_name.items():
        if name not in mastered_or_owned_warframes:
            unmastered_warframes.add(name)


# Filter Unmastered Weapons
def filter_unmastered_weapons(weapon_name_category, mastered_or_owned_primaries, mastered_or_owned_amps, mastered_or_owned_melees, mastered_or_owned_secondaries, mastered_or_owned_arch_weapons, mastered_or_owned_others, unmastered_primaries, unmastered_amps, unmastered_melees, unmastered_secondaries, unmastered_arch_weapons, unmastered_others):
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
def filter_items(warframe_name, weapon_name_category, warframe_inventory, mastered_or_owned_warframes, mastered_or_owned_primaries, mastered_or_owned_secondaries, mastered_or_owned_melees, mastered_or_owned_amps, mastered_or_owned_arch_weapons, mastered_or_owned_others, unmastered_warframes, unmastered_primaries, unmastered_secondaries, unmastered_melees, unmastered_amps, unmastered_arch_weapons, unmastered_others, duplicate_prime_parts, mastered_prime_parts):
    filter_duplicate_prime_parts(warframe_inventory, duplicate_prime_parts)
    filter_mastered_and_owned_gear(warframe_name, weapon_name_category, mastered_or_owned_warframes, mastered_or_owned_primaries, mastered_or_owned_secondaries, mastered_or_owned_melees, mastered_or_owned_amps, mastered_or_owned_arch_weapons, mastered_or_owned_others)
    filter_mastered_prime_parts(warframe_inventory, mastered_or_owned_warframes, mastered_or_owned_primaries, mastered_or_owned_secondaries, mastered_or_owned_melees, mastered_or_owned_amps, mastered_or_owned_arch_weapons, mastered_or_owned_others, mastered_prime_parts)
    filter_unmastered_warframes(warframe_name, mastered_or_owned_warframes, unmastered_warframes)
    filter_unmastered_weapons(weapon_name_category, mastered_or_owned_primaries, mastered_or_owned_amps, mastered_or_owned_melees, mastered_or_owned_secondaries, mastered_or_owned_arch_weapons, mastered_or_owned_others, unmastered_primaries, unmastered_amps, unmastered_melees, unmastered_secondaries, unmastered_arch_weapons, unmastered_others)