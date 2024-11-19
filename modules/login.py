from typing import Union

from modules.admin import Admin
from modules.clinician import Clinician
from modules.patient import Patient
from modules.user import User
from database.setup import Database
from modules.utilities import clear_terminal


def login(db: Database) -> Union[User, None]:
    """
    Attemps to log in the user, by requesting a username and password and
    checking if the combination exists in the database.

    Prints if the login was successfull or not, and returns None (FOR NOW!!)
    """
    clear_terminal()
    username = input("Your username: ")
    password = input("Your password: ")

    user_data = db.cursor.execute(
        """
        SELECT user_id, username, name, email, role, is_active FROM Users
        WHERE username = :username AND password = :password
        """,
        {"username": username, "password": password},
    ).fetchone()

    if user_data:
        if user_data["role"] == "admin":
            return Admin(database=db, **user_data)
        elif user_data["role"] == "clinician":
            return Clinician(database=db, **user_data)
        elif user_data["role"] == "patient":
            return Patient(database=db, **user_data)
        else:
            raise Exception("User type not defined in the system")
    else:
        print("Invalid password or username entered.")
        print("Press Enter to return to the homepage.")
        while True:
            if input() == "":
                clear_terminal()
                return False
