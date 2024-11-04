from typing import Union

from .admin import Admin
from .clinician import Clinician
from .patient import Patient
from .user import User
from ..database.setup import Database


def login(db: Database) -> Union[User, None]:
    """
    Attemps to log in the user, by requesting a username and password and
    checking if the combination exists in the database.

    Prints if the login was successfull or not, and returns None (FOR NOW!!)
    """

    username = input("Your username: ")
    password = input("Your password: ")

    user_data = db.cursor.execute(
        """
        SELECT user_id, username, email, role, is_active FROM Users
        WHERE username = :username AND password = :password
        """,
        {"username": username, "password": password},
    ).fetchone()

    if user_data:
        if user_data["role"] == "admin":
            return Admin(**user_data)
        elif user_data["role"] == "clinician":
            return Clinician(**user_data)
        elif user_data["role"] == "patient":
            return Patient(**user_data)
        else:
            raise Exception("User type not defined in the system")
    else:
        print("Your username and password combination does not exist in our system")
