# ----------------------- Menu Definitions -----------------------

SELLABLE_ITEMS = [
    {
        "label": "Print Excess Mastered Prime Parts",
        "func": "print_set_of_tuples_as_table",
        "args": ("mastered_prime_parts", "----- Excess Mastered Prime Parts -----"),
    },
    {
        "label": "Print Duplicate Primes Parts",
        "func": "print_set_of_tuples_as_table",
        "args": ("duplicate_prime_parts", "----- Duplicate Prime Parts (All) -----"),
    },
]

SETS = [
    {
        "label": "Print Weapon Parts as Part of Set",
        "func": "print_weapon_set_progress_as_table",
        "args": ("weapon_parts", "----- Prime Weapons Set Progress -----"),
    },
    {
        "label": "Print Warframe Parts as Part of Set",
        "func": "print_warframe_set_progress_as_table",
        "args": ("warframe_parts", "----- Prime Warframes Set Progress -----"),
    },
    {
        "label": "Print Archwing Parts as Part of Set",
        "func": "print_archwing_set_progress_as_table",
        "args": ("archwing_parts", "----- Prime Archwing Set Progress -----"),
    },
]

UNMASTERED_ITEMS = [
    {
        "label": "Print Unmastered Warframes & Archwings",
        "func": "print_set_as_table",
        "args": ("unmastered_warframes", "----- Unmastered Warframes & Archwings -----"),
    },
    {
        "label": "Print Unmastered Primary Weapons",
        "func": "print_set_as_table",
        "args": ("unmastered_primaries", "----- Unmastered Primary Weapons -----"),
    },
    {
        "label": "Print Unmastered Secondary Weapons",
        "func": "print_set_as_table",
        "args": ("unmastered_secondaries", "----- Unmastered Secondary Weapons -----"),
    },
    {
        "label": "Print Unmastered Melee Weapons",
        "func": "print_set_as_table",
        "args": ("unmastered_melees", "----- Unmastered Melee Weapons -----"),
    },
    {
        "label": "Print Unmastered Arch Weapons",
        "func": "print_set_as_table",
        "args": ("unmastered_arch_weapons", "----- Unmastered Arch Weapons -----"),
    },
    {
        "label": "Print Unmastered Amps",
        "func": "print_set_as_table",
        "args": ("unmastered_amps", "----- Unmastered Amps -----"),
    },
]

MASTERED_ITEMS = [
    {
        "label": "Print Mastered Warframes & Archwings",
        "func": "print_set_as_table",
        "args": ("mastered_or_owned_warframes", "----- Mastered or Owned Warframes & Archwings -----"),
    },
    {
        "label": "Print Mastered Primary Weapons",
        "func": "print_set_as_table",
        "args": ("mastered_or_owned_primaries", "----- Mastered or Owned Primary Weapons -----"),
    },
    {
        "label": "Print Mastered Secondary Weapons",
        "func": "print_set_as_table",
        "args": ("mastered_or_owned_secondaries", "----- Mastered or Owned Secondary Weapons -----"),
    },
    {
        "label": "Print Mastered Melee Weapons",
        "func": "print_set_as_table",
        "args": ("mastered_or_owned_melees", "----- Mastered or Owned Melee Weapons -----"),
    },
    {
        "label": "Print Mastered Arch Weapons",
        "func": "print_set_as_table",
        "args": ("mastered_or_owned_arch_weapons", "----- Mastered or Owned Arch Weapons -----"),
    },
    {
        "label": "Print Mastered Amps",
        "func": "print_set_as_table",
        "args": ("mastered_or_owned_amps", "----- Mastered or Owned Amps -----"),
    },
]

OPTIONS = [
    {
        "label": "Update Inventory",
        "func": "fetch_inventory_data",
        "args": ("warframe_inventory",),
    },
    {
        "label": "Settings Menu",
        "func": "settings_menu",
        "args": (),
    }
]

WARFRAME_MARKET = [
    {   # Will give option to choose between duplicate parts and excess mastered parts etc...
        "label": "Post sell orders to Warframe Market (for sellable items)",
        "func": "post_sell_orders_to_warframe_market",
        "args": (),
    },
]

START_MENU = [
    {
        "label": "Sellable Items",
        "func": "go_to_sellable_items_menu",
        "args": (),
    },
    {
        "label": "Sets",
        "func": "go_to_sets_menu",
        "args": (),
    },
    {
        "label": "Unmastered Items",
        "func": "go_to_unmastered_items_menu",
        "args": (),
    },
    {
        "label": "Mastered Items",
        "func": "go_to_mastered_items_menu",
        "args": (),
    },
    {
        "label": "Warframe Market Options",
        "func": "go_to_warframe_market_menu",
        "args": (),  
    },
    {
        "label": "Options",
        "func": "go_to_options_menu",
        "args": (),
    },
]

# Submenu groups mapping
SUBMENU_MAPPING = {
    "go_to_sellable_items_menu": SELLABLE_ITEMS,
    "go_to_sets_menu": SETS,
    "go_to_unmastered_items_menu": UNMASTERED_ITEMS,
    "go_to_mastered_items_menu": MASTERED_ITEMS,
    "go_to_warframe_market_menu": WARFRAME_MARKET,
    "go_to_options_menu": OPTIONS,
}