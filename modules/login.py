from datetime import datetime
from typing import Union

from modules.admin import Admin
from modules.clinician import Clinician
from modules.patient import Patient
from modules.user import User
from modules.utilities.display import display_choice, display_dict
from database.setup import Database, roles
from modules.utilities.input import get_valid_email
from modules.utilities.send_email import send_email
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
        "name": "",
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
        username = input("Your username: ")
        if username in existing_usernames:
            print("Username already exists. Please try again.")
            continue
        else:
            registration_info["username"] = username
            break

    # Get a password and confirm it
    while True:
        password = input("Your password: ")
        password_confirm = input("Confirm your password: ")
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            continue
        else:
            registration_info["password"] = password
            break

    registration_info["name"] = input("Your name: ")

    # Get a valid email that is not already in the database
    registration_info["email"] = get_valid_email(
        prompt="Your email: ", existing_emails=existing_emails
    )

    if registration_info["role"] == "patient":
        registration_info["emergency_email"] = get_valid_email(
            prompt="Your emergency contact email: "
        )
        while True:
            # TODO: Discuss if we are setting a minimum age for patients
            date_of_birth = input("Your date of birth (YYYY-MM-DD): ")
            try:
                date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d")
                if date_of_birth > datetime.now():
                    print("Date of birth cannot be in the future. Please try again.")
                    continue
                else:
                    registration_info["date_of_birth"] = date_of_birth
                    break
            except Exception:
                print("Invalid date format. Please try again.")
                continue

    print("\nThis is your registration information:")
    display_dict(registration_info)
    cont_selection = display_choice(
        "Is this information correct?", ["Yes, continue", "No, correct information"]
    )
    if cont_selection == 2:
        return registration_input(existing_usernames)
    else:
        return registration_info


def signup(db: Database) -> bool:
    """
    Signs the user as a practicioner or clinician (not admin for now).

    Returns a boolean representing wether the signup was successful or not.
    If it is not successfull, prints a message to the user before quitting the app.
    """

    # Get a list of registered unique usernams
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
            VALUES (:user_id, :username, :password, :name, :email, :role, :is_active)
            """,
            {
                "user_id": user_id,
                "username": user_info["username"],
                "password": user_info["password"],
                "name": user_info["name"],
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
            message = (
                f"Welcome to Breeze {user_info['name'].title()},\n\nWe will asign you a clinician soon; in the meantime, feel free to use our journaling and mood tracking options.\n\nBest regards,\nBreeze Team"
            )
        else:
            message = (
                f"Welcome to Breeze {user_info['name'].title()},\n\nAn admin will review and activate your profile soon.\n\nBest regards,\nBreeze Team"
            )
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
