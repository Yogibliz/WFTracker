import os
from pathlib import Path

import inquirer

# Path to settings file
SETTINGS_FILE = Path(__file__).parent / "settings.txt"

# Default settings
DEFAULTS = {
    "WEAPON_PROGRESS_FILTER": 2,  # 0–? (depends on weapon parts)
    "WARFRAME_PROGRESS_FILTER": 1,  # 0–4
    "INCLUDE_NON_PRIME_WEAPONS_IN_SETS": 0,  # 0 = No | 1 = Yes
    "INCLUDE_NON_PRIME_WARFRAMES_IN_SETS": 0,  # 0 = No | 1 = Yes
}


def save_settings(settings):
    """Save settings to settings.txt file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            for key, value in settings.items():
                f.write(f"{key}={value}\n")
    except Exception as e:
        print(f"Error saving settings: {e}")


def load_settings():
    """Load settings from settings.txt file."""
    settings = DEFAULTS.copy()

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            if key in settings:
                                try:
                                    settings[key] = int(value)
                                except ValueError:
                                    pass
                                    # settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")

    return settings


# Load settings on import
_loaded_settings = load_settings()


# Make settings available as module attributes
WEAPON_PROGRESS_FILTER = _loaded_settings["WEAPON_PROGRESS_FILTER"]
WARFRAME_PROGRESS_FILTER = _loaded_settings["WARFRAME_PROGRESS_FILTER"]
INCLUDE_NON_PRIME_WEAPONS_IN_SETS = _loaded_settings[
    "INCLUDE_NON_PRIME_WEAPONS_IN_SETS"
]
INCLUDE_NON_PRIME_WARFRAMES_IN_SETS = _loaded_settings[
    "INCLUDE_NON_PRIME_WARFRAMES_IN_SETS"
]


def get_settings():
    """Get current settings as a dictionary."""
    return _loaded_settings.copy()


def update_setting(key, value):
    """Update a single setting and persist it."""
    if key in DEFAULTS:
        _loaded_settings[key] = value
        save_settings(_loaded_settings)
        globals()[key] = value
    else:
        raise KeyError(f"Unknown setting: {key}")


def settings_menu():
    """Display and modify settings menu using inquirer."""
    os.system("cls" if os.name == "nt" else "clear")

    questions = [
        inquirer.List(
            "setting_choice",
            message="Select a setting to modify",
            # ("label", "setting_key")
            choices=[
                (
                    f"Include Non-Prime Weapons: {'Yes' if _loaded_settings['INCLUDE_NON_PRIME_WEAPONS_IN_SETS'] == 1 else 'No'}",
                    "INCLUDE_NON_PRIME_WEAPONS_IN_SETS",
                ),
                (
                    f"Include Non-Prime Warframes: {'Yes' if _loaded_settings['INCLUDE_NON_PRIME_WARFRAMES_IN_SETS'] == 1 else 'No'}",
                    "INCLUDE_NON_PRIME_WARFRAMES_IN_SETS",
                ),
                (
                    f"Weapon Progress Filter: {_loaded_settings['WEAPON_PROGRESS_FILTER']}",
                    "WEAPON_PROGRESS_FILTER",
                ),
                (
                    f"Warframe Progress Filter: {_loaded_settings['WARFRAME_PROGRESS_FILTER']}",
                    "WARFRAME_PROGRESS_FILTER",
                ),
                (
                    "Restore Default Settings",
                    "RESTORE_DEFAULTS",
                ),
                ("Back to Menu", "back"),
            ],
        ),
    ]

    answers = inquirer.prompt(questions)

    if answers is None or answers["setting_choice"] == "back":
        return

    choice = answers["setting_choice"]

    if choice == "INCLUDE_NON_PRIME_WEAPONS_IN_SETS":
        toggle_questions = [
            inquirer.Confirm(
                "toggle_value",
                message="Include Non-Prime Weapons?",
                default=False,
            ),
        ]
        toggle_answer = inquirer.prompt(toggle_questions)
        if toggle_answer:
            new_value = 1 if toggle_answer["toggle_value"] else 0
            update_setting("INCLUDE_NON_PRIME_WEAPONS_IN_SETS", new_value)

    elif choice == "INCLUDE_NON_PRIME_WARFRAMES_IN_SETS":
        toggle_questions = [
            inquirer.Confirm(
                "toggle_value",
                message="Include Non-Prime Warframes?",
                default=False,
            ),
        ]
        toggle_answer = inquirer.prompt(toggle_questions)
        if toggle_answer:
            new_value = 1 if toggle_answer["toggle_value"] else 0
            update_setting("INCLUDE_NON_PRIME_WARFRAMES_IN_SETS", new_value)

    elif choice == "WEAPON_PROGRESS_FILTER":
        filter_questions = [
            inquirer.List(
                "weapon_filter",
                message="Weapon Progress Filter (0-3):",
                choices=["0", "1", "2", "3"],
                default=str(_loaded_settings["WEAPON_PROGRESS_FILTER"]),
            ),
        ]
        filter_answer = inquirer.prompt(filter_questions)
        if filter_answer:
            update_setting(
                "WEAPON_PROGRESS_FILTER", int(filter_answer["weapon_filter"])
            )

    elif choice == "WARFRAME_PROGRESS_FILTER":
        filter_questions = [
            inquirer.List(
                "warframe_filter",
                message="Warframe Progress Filter (0-4):",
                choices=["0", "1", "2", "3", "4"],
                default=str(_loaded_settings["WARFRAME_PROGRESS_FILTER"]),
            ),
        ]
        filter_answer = inquirer.prompt(filter_questions)
        if filter_answer:
            update_setting(
                "WARFRAME_PROGRESS_FILTER", int(filter_answer["warframe_filter"])
            )

    elif choice == "RESTORE_DEFAULTS":
        confirm_questions = [
            inquirer.Confirm(
                "confirm_restore",
                message="Are you sure you want to restore default settings?",
                default=False,
            ),
        ]
        confirm_answer = inquirer.prompt(confirm_questions)
        if confirm_answer and confirm_answer["confirm_restore"]:
            for key, value in DEFAULTS.items():
                update_setting(key, value)
