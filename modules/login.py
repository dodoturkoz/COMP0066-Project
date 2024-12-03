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
        user_id = user_data["user_id"]
        role = user_data["role"]

        if role == "admin":
            return Admin(database=db, **user_data)
        elif role == "clinician":
            return Clinician(database=db, **user_data)
        elif role == "patient":
            # fetch additional patient-specific data
            patient_data = db.cursor.execute(
                """
                SELECT emergency_email, date_of_birth, diagnosis, clinician_id
                FROM Patients
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

            if not patient_data:
                raise Exception("Patient data not found for user ID.")

            # merge the user and patient data
            # old way: combined_data = {**user_data, **patient_data}
            combined_data = user_data | patient_data
            return Patient(database=db, **combined_data)
        else:
            raise Exception("User role is not defined in the system.")
    else:
        print("Invalid username or password.")
        return None


def registration_input(
    existing_usernames: list[str], existing_emails: list[str]
) -> dict[str, Union[str, datetime]]:
    """
    Gets the registration information and returns i
    """
    # Collect user information in a dictionar
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
    while True:
        username = get_valid_string("Your username: ", max_len=25, min_len=3)
        if username in existing_usernames:
            print("Username already exists. Please try again.")
            continue
        else:
            registration_info["username"] = username
            break

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
        "Your first name: ", max_len=50, min_len=1
    )
    registration_info["surname"] = get_valid_string(
        "Your surname: ", max_len=50, min_len=1
    )
    # Get a valid email that is not already in the database
    registration_info["email"] = get_valid_email(
        prompt="Your email: ", existing_emails=existing_emails
    )

    if registration_info["role"] == "patient":
        registration_info["emergency_email"] = get_valid_email(
            prompt="Your emergency contact email: "
        )
        registration_info["date_of_birth"] = get_valid_date(
            prompt="Your date of birth (YYYY-MM-DD): ",
            min_date=datetime(1900, 1, 1),
            max_date=datetime.today(),
            max_date_message="Date of birth cannot be in the future. Please try again.",
        )

    print("\nThis is your registration information:")
    display_dict(registration_info)
    register = get_valid_yes_or_no("Is this information correct? (Y/N): ")
    if register:
        return registration_input(existing_usernames)
    else:
        return registration_info


def signup(db: Database) -> bool:
    """
    Signs the user as a practicioner or clinician (not admin for now).

    Returns a boolean representing wether the signup was successful or not.
    If it is not successfull, prints a message to the user before quitting the app.
    """

    # Get a list of registered unique usernames
    existing_usernames = db.cursor.execute("SELECT username FROM Users").fetchall()
    existing_emails = db.cursor.execute("SELECT email FROM Users").fetchall()
    user_info = registration_input(existing_usernames, existing_emails)

    try:
        user_id = len(existing_usernames) + 1
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
            message = f"Welcome to Breeze {user_info['first_name'].title()},\n\nWe will asign you a clinician soon; in the meantime, feel free to use our journaling and mood tracking options.\n\nBest regards,\nBreeze Team"
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
