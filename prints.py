import os
import time

from prettytable import PrettyTable

import settings
from fetch import fetch_inventory_data
from menu import START_MENU, SUBMENU_MAPPING

# ----------------------- Global Context -----------------------
# This dictionary holds all the data structures needed by menu functions
_context = {}

# ----------------------- Formatting Helper -----------------------


# Helper to format if part is owned and built status
# Returns: ✓ for built component, - for blueprint only, ✗ for not owned
def has_part(bp_count, comp_count):
    if comp_count >= 1:
        return "✓"  # Has built component
    elif bp_count >= 1:
        return "-"  # Has blueprint but not built
    else:
        return "✗"  # Not owned


# ----------------------- Printing -----------------------


# Display a generic menu from a menu items list
def display_menu(menu_items, title, allow_back=False):
    """Generic menu display function.

    Returns:
        Tuple of (selected_option, selected_item) or (None, None) if going back
    """
    menu = PrettyTable(["Index", "Action"])
    menu.align["Action"] = "l"
    menu.title = title

    for index, item in enumerate(menu_items):
        menu.add_row([index + 1, item["label"]])

    selected_option = -1

    # Automatically calculate valid range based on list size
    while selected_option not in range(len(menu_items)):
        os.system("cls" if os.name == "nt" else "clear")
        print(menu)

        user_input = input(
            "What do you want to do? (q to quit"
            + (", b to go back" if allow_back else "")
            + "): "
        )

        if user_input == "q":
            exit()

        if allow_back and user_input == "b":
            return None, None

        try:
            selected_option = int(user_input) - 1
        except ValueError:
            continue

    return selected_option, menu_items[selected_option]


# Basic Main Menu
def main_menu(context):
    """Main menu with access to all data through context."""
    global _context
    _context = context

    selected_option, selection = display_menu(START_MENU, "----- Main Menu -----")

    # Check if this is a submenu navigation function
    func_name = selection["func"]
    if func_name in SUBMENU_MAPPING:
        submenu(SUBMENU_MAPPING[func_name], selection["label"])
    else:
        print_selection(selected_option, START_MENU)


# Submenu handler for navigating to category submenus
def submenu(menu_items, title):
    """Display a submenu and handle selection."""
    while True:
        selected_option, _ = display_menu(
            menu_items, f"----- {title} -----", allow_back=True
        )

        # User pressed 'b' to go back to main menu
        if selected_option is None:
            main_menu(_context)
            return

        print_selection(selected_option, menu_items, from_submenu=True)


# Print the selected option in the menu
def print_selection(index, menu_items, from_submenu=False):
    os.system("cls" if os.name == "nt" else "clear")

    selection = menu_items[index]

    func_name = selection["func"]

    # Build the namespace with context values and functions
    local_namespace = _context.copy()

    # Add all the print functions and utility functions to the namespace
    local_namespace.update(
        {
            "print_set_of_tuples_as_table": print_set_of_tuples_as_table,
            "print_set_as_table": print_set_as_table,
            "print_warframe_set_progress_as_table": print_warframe_set_progress_as_table,
            "print_archwing_set_progress_as_table": print_archwing_set_progress_as_table,
            "print_weapon_set_progress_as_table": print_weapon_set_progress_as_table,
            "print_sentinel_set_progress_as_table": print_sentinel_set_progress_as_table,
            "print_sellable_prime_sets_as_table": print_sellable_prime_sets_as_table,
            "fetch_inventory_data": fetch_inventory_data,
            "settings_menu": settings.settings_menu,
        }
    )

    if func_name in local_namespace:
        func_to_call = local_namespace[func_name]
        # Call function with variable arguments
        # First, resolve any string references to local variables
        args = []
        for arg in selection.get("args", ()):
            # Arguments through context -- Magic
            if isinstance(arg, str) and arg in local_namespace:
                args.append(local_namespace[arg])
            else:
                args.append(arg)
        func_to_call(*args)
    else:
        print(f"Error: Function '{func_name}' not found.")

    # Skip the "go back" prompt when updating inventory or going to settings
    if func_name == "fetch_inventory_data" or func_name == "settings_menu":
        if func_name == "fetch_inventory_data":
            print("Inventory updated!")
            time.sleep(0.75)
        main_menu(_context)
    else:
        go_back = ""
        while go_back != "b":
            go_back = input("Go back to menu or quit? (b/q): ").lower()
            if go_back == "q":
                exit()
        # If we came from a submenu, return to submenu, otherwise main menu
        if from_submenu:
            return
        main_menu(_context)


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
        bp_bp, bp_comp = entry["blueprint"][1], entry["blueprint"][2]
        neu_bp, neu_comp = entry["neuroptics"][1], entry["neuroptics"][2]
        cha_bp, cha_comp = entry["chassis"][1], entry["chassis"][2]
        sys_bp, sys_comp = entry["systems"][1], entry["systems"][2]

        # Add 1 to progress for each part owned (either built or blueprint)
        progress = sum(
            1
            for counts in [
                (bp_bp, bp_comp),
                (neu_bp, neu_comp),
                (cha_bp, cha_comp),
                (sys_bp, sys_comp),
            ]
            if counts[0] >= 1 or counts[1] >= 1
        )

        row = [
            entry["name"],
            has_part(bp_bp, bp_comp),
            has_part(neu_bp, neu_comp),
            has_part(cha_bp, cha_comp),
            has_part(sys_bp, sys_comp),
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
        bp_bp, bp_comp = entry["blueprint"][1], entry["blueprint"][2]
        har_bp, har_comp = entry["harness"][1], entry["harness"][2]
        wing_bp, wing_comp = entry["wings"][1], entry["wings"][2]
        sys_bp, sys_comp = entry["systems"][1], entry["systems"][2]

        # Add 1 to progress for each part owned (either built or blueprint)
        progress = sum(
            1
            for counts in [
                (bp_bp, bp_comp),
                (har_bp, har_comp),
                (wing_bp, wing_comp),
                (sys_bp, sys_comp),
            ]
            if counts[0] >= 1 or counts[1] >= 1
        )

        row = [
            entry["name"],
            has_part(bp_bp, bp_comp),
            has_part(har_bp, har_comp),
            has_part(wing_bp, wing_comp),
            has_part(sys_bp, sys_comp),
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
        # Use full weapon name + "Blueprint" instead of just "Blueprint"
        blueprint_name = f"{entry['name']} Blueprint"
        parts_str_list = [f"{blueprint_name}: {entry['blueprint'][1]}"]
        amount = 1
        progress = 0

        if entry["blueprint"][1] >= 1:
            progress += 1

        for part_name, bp_count, comp_count in entry["parts"]:
            if comp_count >= 1 or bp_count >= 1:
                progress += 1
            amount += 1
            parts_str_list.append(f"{part_name}: {comp_count + bp_count}")

        progress_str = f"Progress: {progress}/{amount}"
        formatted_parts = ", ".join(parts_str_list)

        table.add_row([entry["name"], formatted_parts, progress_str])
    print(table)


# For the prime_sentinel_sets.
def print_sentinel_set_progress_as_table(sentinel_set, title):
    table = PrettyTable(
        ["Item", "Blueprint", "Cerebrum", "Carapace", "Systems", "Progress"]
    )
    table.title = title
    table.sortby = "Progress"
    table.reversesort = True

    for entry in sentinel_set.values():
        bp_bp, bp_comp = entry["blueprint"][1], entry["blueprint"][2]
        cer_bp, cer_comp = entry["cerebrum"][1], entry["cerebrum"][2]
        car_bp, car_comp = entry["carapace"][1], entry["carapace"][2]
        sys_bp, sys_comp = entry["systems"][1], entry["systems"][2]

        # Add 1 to progress for each part owned (either built or blueprint)
        progress = sum(
            1
            for counts in [
                (bp_bp, bp_comp),
                (cer_bp, cer_comp),
                (car_bp, car_comp),
                (sys_bp, sys_comp),
            ]
            if counts[0] >= 1 or counts[1] >= 1
        )

        row = [
            entry["name"],
            has_part(bp_bp, bp_comp),
            has_part(cer_bp, cer_comp),
            has_part(car_bp, car_comp),
            has_part(sys_bp, sys_comp),
            f"{progress}/4",
        ]
        table.add_row(row)
    print(table)


# For sellable prime sets
def print_sellable_prime_sets_as_table(sellable_prime_sets, title):
    table = PrettyTable(["Set Name", "Count"])
    table.title = title
    table.sortby = "Count"
    table.reversesort = True

    for name, count in sorted(sellable_prime_sets.items()):
        table.add_row([name, count])
    print(table)
