import re
from typing import Union
from datetime import datetime


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
) -> datetime:
    """
    Get a valid date from the user and return it
    """
    while True:
        date = input(prompt)
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
    Get a valid yes or no value from the user and return it
    """
    while True:
        value = input(prompt)
        if value.lower() in ["y", "yes"]:
            return True
        elif value.lower() in ["n", "no"]:
            return False
        else:
            print("Invalid boolean value. Please try again.")
            continue


def get_valid_string(prompt: str, max_len: int = 250, min_len: int = 0) -> str:
    """
    Get a valid string of more than 2 characters and less than 50
    from the user and return it
    """
    while True:
        value = input(prompt)
        if value and len(value) > min_len and len(value) < max_len:
            return value
        else:
            print(
                f"Invalid input. Please try again. Input must be between {min_len} and {max_len} characters."
            )
            continue
