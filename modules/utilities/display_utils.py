import os
from datetime import datetime


# I have added the option to change the input string given when the choice is offered
def display_choice(
    header: str,
    options: list[str],
    choice_str: str = "Your selection: ",
    enable_zero_quit: bool = False,
    zero_option_callback: callable = None,
    zero_option_message: str = "Go back",
) -> int:
    """
    Displays a list of options to the user and returns their choice.

    Optionally allows the user to quit (or another screen via callback) by entering 0.
    """

    print(header)
    for i, option in enumerate(options):
        print(f"[{i + 1}] {option}")
    if enable_zero_quit:
        print(f"[0] {zero_option_message}")
    while True:
        choice = input(choice_str)
        if choice.isnumeric() and 1 <= int(choice) <= len(options):
            return int(choice)
        elif choice.isnumeric() and int(choice) == 0 and enable_zero_quit:
            if zero_option_callback:
                return zero_option_callback()
            else:
                return 0

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


def wait_terminal(
    wait_text: str = "Press enter to return to the dashboard",
    return_value: bool = False,
    redirect_function=None,
) -> bool:
    """We can use this function to wait for the user to press enter
    before continuing, such as after displaying a message or data."""
    while True:
        if input(wait_text) is not None:
            clear_terminal()
            if redirect_function:
                return redirect_function()

            return return_value
