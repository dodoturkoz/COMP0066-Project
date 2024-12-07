import re
from typing import Union
from datetime import datetime
from collections.abc import Iterable


def get_valid_email(prompt: str, existing_emails: Union[list[str], None] = None) -> str:
    """
    Get a valid email from the user and return it
    """
    while True:
        email = input(prompt)
        if existing_emails and email in existing_emails:
            print("Email already exists. Please try again.")
            continue
        elif re.match(r"^\S+@\S+\.\S+$", email) is None:
            print("Invalid email format. Please try again.")
            continue
        else:
            return email


def get_valid_date(
    prompt: str,
    min_date: datetime,
    max_date: datetime,
    min_date_message: Union[str, None] = None,
    max_date_message: Union[str, None] = None,
    allow_blank: bool = False,
) -> Union[datetime, None]:
    """
    Get a valid date from the user and return it
    """
    while True:
        date = input(prompt).strip()
        # check for blank input
        if allow_blank and not date:
            return None
        try:
            valid_date = datetime.strptime(date, "%Y-%m-%d")
            if valid_date > max_date:
                print(
                    max_date_message
                    if max_date_message
                    else f"Input date must be before {max_date.date()}, please try again."
                )
                continue
            elif valid_date < min_date:
                print(
                    min_date_message
                    if min_date_message
                    else f"Input date must be after {min_date.date()}, please try again."
                )
                continue
            else:
                return valid_date
        except Exception:
            print("Invalid date format. Please try again.")
            continue


def get_valid_yes_or_no(prompt: str = "Your input (Y/N): ") -> bool:
    """
    Get a valid yes or no value from the user and return the corresponding boolean value.
    """
    while True:
        value = input(prompt).strip().lower()
        if value in ["y", "yes"]:
            return True
        elif value in ["n", "no"]:
            return False
        else:
            print("Invalid boolean value. Please try again.")
            continue


def get_valid_string(
    prompt: str,
    max_len: int = 250,
    min_len: int = 0,
    is_name: bool = False,
    allow_spaces: bool = True,
) -> str:
    """
    Get a valid string of more than 2 characters and less than 50
    from the user and return it; with options to allow only names
    and disallow spaces.

    Not that is_name always allows spaces.
    """
    while True:
        value = input(prompt)
        if len(value) >= min_len and len(value) <= max_len:
            if is_name:
                # Check that the name only contains letters, spaces, hyphens, and apostrophes
                if re.match("^[A-Za-z]+([ '-][A-Za-z]+)*$", value):
                    return value
                else:
                    print("Your input contains invalid characters. Please try again.")
                    continue
            else:
                if allow_spaces or " " not in value:
                    return value
                else:
                    print("Your input can't contain spaces. Please try again.")
                    continue
        else:
            print(
                f"Invalid input. Please try again. Input must be between {min_len} and {max_len} characters."
            )
            continue

def get_user_input_with_limited_choice(
    prompt: str,
    options: Iterable[str | int],
    invalid_options_text: str = "Invalid choice. Please try again.",
) -> str | int:
    """
    Get a valid input from the user from a list of options and return it;
    unlike display_choice, this is a free-form input for the user.

    For now, this function only supports integers and string objects, but
    can be extended if needed.
    """
    while True:
        raw_value = input(prompt).strip()
        if raw_value.isdigit():
            value = int(raw_value)
        else:
            value = raw_value

        if value in options:
            return value
        else:
            print(invalid_options_text)
            continue
