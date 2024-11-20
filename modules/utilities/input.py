import re
from typing import Union


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
