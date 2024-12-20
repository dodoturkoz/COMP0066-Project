from datetime import datetime
from typing import Union

from modules.admin import Admin
from modules.clinician import Clinician
from modules.patient import Patient
from modules.user import User
from modules.utilities.display_utils import (
    display_choice,
    display_dict,
    clear_terminal,
)
from database.setup import Database, roles
from modules.utilities.input_utils import (
    get_new_user_email,
    get_new_username,
    get_valid_email,
    get_valid_date,
    get_valid_yes_or_no,
    get_valid_string,
)
from modules.utilities.send_email import send_email


def login(db: Database) -> Union[User, None]:
    """
    Attempts to log in the user by requesting a username and password and
    checking if the combination exists in the database.

    Returns a User object (Admin, Clinician, or Patient) if successful, or None if not.
    """
    clear_terminal()
    username = input("Your username: ")
    password = input("Your password: ")

    # fetch basic user data
    user_data = db.cursor.execute(
        """
        SELECT user_id, username, first_name, surname, email, role, is_active
        FROM Users
        WHERE username = :username AND password = :password
        """,
        {"username": username, "password": password},
    ).fetchone()

    if user_data:
        role = user_data["role"]

        if role == "admin":
            return Admin(database=db, **user_data)
        elif role == "clinician":
            return Clinician(database=db, **user_data)
        elif role == "patient":
            return Patient(database=db, **user_data)
        else:
            raise Exception("User role is not defined in the system.")
    else:
        print("Invalid username or password.")
        return None


def registration_input(db: Database) -> dict[str, Union[str, datetime]]:
    """
    Gets the registration information and returns it
    """
    # Collect user information in a dictionary
    registration_info = {
        "username": "",
        "password": "",
        "first_name": "",
        "surname": "",
        "email": "",
        "role": "",
    }

    # 1 will be patient, 2 clinician
    user_type = display_choice(
        "Select the type of user you are:", ["Patient", "Clinician"]
    )
    registration_info["role"] = roles[user_type]

    # Get a unique username
    registration_info["username"] = get_new_username(db)

    # Get a password and confirm it
    while True:
        password = get_valid_string("Your password: ", max_len=25, min_len=0)
        password_confirm = get_valid_string(
            "Confirm your password: ", max_len=25, min_len=0
        )
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            continue
        else:
            registration_info["password"] = password
            break

    registration_info["first_name"] = get_valid_string(
        "Your first name: ", max_len=50, min_len=1, is_name=True
    )
    registration_info["surname"] = get_valid_string(
        "Your surname: ", max_len=50, min_len=1, is_name=True
    )

    # Get a valid email that is not already in the database
    registration_info["email"] = get_new_user_email(db)

    if registration_info["role"] == "patient":
        registration_info["emergency_email"] = get_valid_email(
            prompt="Your emergency contact email: "
        )
        registration_info["date_of_birth"] = get_valid_date(
            prompt="Your date of birth (DD-MM-YYYY): ",
            min_date=datetime(1900, 1, 1),
            max_date=datetime.today(),
            max_date_message="Date of birth cannot be in the future. Please try again.",
        )

    print("\nThis is your registration information:")
    display_dict(registration_info)
    register = get_valid_yes_or_no("Is this information correct? (Y/N): ")
    if register:
        return registration_info
    else:
        return registration_input(db)


def signup(db: Database) -> bool:
    """
    Signs the user as a practitioner or clinician (not admin for now).

    Returns a boolean representing whether the signup was successful or not.
    If it is not successful, prints a message to the user before quitting the app.
    """

    clear_terminal()

    # Get the number of registered users
    existing_users = db.cursor.execute("SELECT COUNT(*) FROM Users").fetchall()
    user_info = registration_input(db)

    try:
        user_id = existing_users[0] + 1
        is_patient = user_info["role"] == "patient"

        # Insert general user info
        db.cursor.execute(
            """
            INSERT INTO Users
            VALUES (:user_id, :username, :password, :first_name, :surname, :email, :role, :is_active)
            """,
            {
                "user_id": user_id,
                "username": user_info["username"],
                "password": user_info["password"],
                "first_name": user_info["first_name"],
                "surname": user_info["surname"],
                "email": user_info["email"],
                "role": user_info["role"],
                "is_active": is_patient,
            },
        )

        if is_patient:
            db.cursor.execute(
                """
                INSERT INTO Patients
                VALUES (:user_id, :emergency_email, :date_of_birth, :diagnosis, :clinician_id)
                """,
                {
                    "user_id": user_id,
                    "emergency_email": user_info["emergency_email"],
                    "date_of_birth": user_info["date_of_birth"],
                    "diagnosis": None,
                    "clinician_id": None,
                },
            )

        db.connection.commit()
        # Send registration email
        if user_info["role"] == "patient":
            message = f"Welcome to Breeze {user_info['first_name'].title()},\n\nWe will assign you a clinician soon; in the meantime, feel free to use our journaling and mood tracking options.\n\nBest regards,\nBreeze Team"
        else:
            message = f"Welcome to Breeze {user_info['first_name'].title()} {user_info['surname'].title()},\n\nAn admin will review and activate your profile soon.\n\nBest regards,\nBreeze Team"
        send_email(
            user_info["email"],
            "Welcome to Breeze",
            message,
        )

        print("\nYou are now registered with Breeze")
        return True
    except Exception as e:
        print(e)
        print("\nSomething went wrong with your registration")
        return False
