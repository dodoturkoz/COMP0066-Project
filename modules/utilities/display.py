import os
from datetime import datetime


# I have added the option to change the input string given when the choice is offered
def display_choice(
    header: str, options: list[str], choice_str: str = "Your selection: "
) -> int:
    """
    Displays a list of options to the user and returns their choice.
    """

    print(header)
    for i, option in enumerate(options):
        print(f"[{i + 1}] {option}")
    while True:
        choice = input(choice_str)
        if choice.isnumeric() and 1 <= int(choice) <= len(options):
            return int(choice)
        else:
            print("Invalid choice. Please try again.")


def display_dict(dict: dict[str, any]) -> None:
    """
    Displays a dictionary in a clean way.
    """
    for key, value in dict.items():
        print(
            f"{key.replace('_', ' ').capitalize()}: "
            + f"{value.date() if isinstance(value, datetime) else value}"
        )


def clear_terminal():
    # Check if the operating system is Windows
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
