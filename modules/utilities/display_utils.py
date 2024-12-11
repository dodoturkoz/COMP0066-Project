import os
from datetime import datetime
from typing import Union, Callable


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

def new_screen(wait: bool = True):
    """
    Decorator to clear the terminal before a function is called.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            clear_terminal()
            result = func(*args, **kwargs)
            if wait:
                wait_terminal()
            return result

        return wrapper

    return decorator

def display_menu(
    menu: dict[str, Union[Callable, dict[str, Union[Callable, dict]]]],
    header: str = "What would you like to do?",
    quit_message: str = "Log Out",
) -> None | Callable:
    """
    Displays a menu with options and calls the corresponding function.
    """
    while True:
        clear_terminal()
        options = list(menu.keys())
        choice = display_choice(
            header, options, enable_zero_quit=True, zero_option_message=quit_message
        )
        if choice == 0:
            return
        elif type(menu[options[choice - 1]]) is dict:
            display_menu(menu[options[choice - 1]], header, "Go Back")
        else:
            menu[options[choice - 1]]()
