from datetime import datetime
import sqlite3
from typing import Any
from database.setup import Database, diagnoses
from modules.user import User
from modules.patient import Patient
from modules.clinician import Clinician
from modules.utilities.display_utils import (
    clear_terminal,
    display_choice,
    wait_terminal,
)
from modules.utilities.input_utils import (
    get_user_input_with_limited_choice,
    get_valid_date,
    get_valid_string,
    get_valid_yes_or_no,
    get_valid_email,
)

import pandas as pd

# POTENTIALLY RELEVANT METHODS (FROM OTHER CLASSES):
"""
USER: 
    def edit_info(self, attribute: str, value: Any) -> bool:
    """
# Updates the attribute both in the object and in the database,
# Returns the result of the update
"""
    def view_info(self, attribute: self, attribute:str, value: Any ) -> bool: 
        """
# Returns information stored about a user in the database

""" 
PATIENT: 
    def view_appointments(self) -> list[dict[str, Any]]:    
    """
# Views all information for the patient.
"""
    def edit_medical_info(self) -> bool:
    """
# Allows the patient to change their details.


class Admin(User):
    user_df: pd.DataFrame
    appointments_df: pd.DataFrame
    patient_moods_df: pd.DataFrame
    patient_journals_df: pd.DataFrame

    def __init__(
        self,
        database: Database,
        user_id: int,
        username: str,
        first_name: str,
        surname: str,
        email: str,
        is_active: bool,
        *args,
        **kwargs,
    ):
        User.__init__(
            self,
            database,
            user_id,
            username,
            first_name,
            surname,
            email,
            is_active,
        )
        self.refresh_user_df()
        self.refresh_appointments_df()
        self.refresh_patient_journals_df()
        self.refresh_patient_moods()

    def refresh_user_df(self):
        """
        Retrieves an updated version of the user database from SQL and
        presents it in Pandas
        """
        user_query = self.database.cursor.execute("""                 
        SELECT
                u.user_id,
                username,
                password,
                email,
                first_name,
                surname,
                is_active,
                role,
                emergency_email,
                date_of_birth,
                diagnosis,
                clinician_id
        FROM Users u
        LEFT JOIN Patients p ON u.user_id = p.user_id;""")

        user_data = user_query.fetchall()
        self.user_df = pd.DataFrame(user_data)
        self.user_df["clinician_id"] = self.user_df["clinician_id"].astype(
            pd.Int64Dtype()
        )
        self.user_df.set_index("user_id", inplace=True)

    def refresh_appointments_df(self):
        """
        Retrieves an updated version of the appointments table from SQL and
        presents it in Pandas
        """
        # TODO: figure out whether I keep the joins here or apply them to the
        # database process later.
        appointments_query = self.database.cursor.execute("""
        SELECT *
        FROM Appointments;""")

        appointments_data = appointments_query.fetchall()
        self.appointments_df = pd.DataFrame(appointments_data)
        self.appointments_df.set_index("appointment_id", inplace=True)
        # It might be worth rewriting this quer, cutting out the joins and
        # assuming that I'm just going to connect it with the user_df

    def refresh_patient_journals_df(self):
        """
        Retrieves an updated version of the patients journal table from SQL
        and presents it in Pandas
        """

        journals_query = self.database.cursor.execute("""
        SELECT *
        FROM JournalEntries;""")

        journal_data = journals_query.fetchall()
        self.patient_journals_df = pd.DataFrame(journal_data)
        # self.patient_information_df.set_index("user_id", inplace=True)

        # Load patient journal information into memory. When manipulating it, I
        # will likely group by date, then join with the big users table to show
        # to the user

    def refresh_patient_moods(self):
        """
        Retrieves an updated version of the patient moods table from SQL and
        presents it in Pandas
        """

        moods_query = self.database.cursor.execute("""
        SELECT * 
        FROM MoodEntries;""")

        moods_data = moods_query.fetchall()
        self.patient_moods_df = pd.DataFrame(moods_data)
        # self.patient_information_df.set_index("user_id", inplace=True)

    def time_modifications(self, dataframe: pd.DataFrame, time_period: str):
        """
        Plug in a dataframe (in practice, moods or journals) to create a row
        around a specific time
        """
        if time_period == "last week":
            pass
        pass

    def view_table(
        self, user_type: str, sub_type: str = "none"
    ) -> tuple[pd.Index, pd.Index]:
        """
        Selects the relevant portion of the Pandas dataframe for the user, as
        defined by the inputs.
        """
        if user_type == "patients" and sub_type == "none":
            patient_df = self.user_df.query(('role == "patient"'))
            patient_df = patient_df.filter(
                items=["username", "email", "name", "is_active"]
            )
            print("\nBreeze Patients:")
            print(patient_df)
            return (patient_df.index, patient_df.columns)

        elif user_type == "clinicians" and sub_type == "none":
            clinician_df = self.user_df.query(('role == "clinician"'))
            clinician_df = clinician_df.filter(
                items=["username", "email", "name", "is_active"]
            )
            print("\nBreeze Clinicians:")
            print(clinician_df)
            return clinician_df.index, clinician_df.columns

        elif user_type == "patients" and sub_type == "registration":
            unregistered_patient_df = self.user_df.query(
                ('role == "patient" and clinician_id.isna()')
            )
            unregistered_patient_df = unregistered_patient_df.filter(
                items=["username", "email", "name", "is_active", "clinician_id"]
            )
            print("\nPatientes without a clinician assinged:")
            print(unregistered_patient_df)
            return unregistered_patient_df.index, unregistered_patient_df.columns

        elif user_type == "clinicians" and sub_type == "registration":
            clinician_df = self.user_df.query(('role == "clinician"'))[
                ["first_name", "surname", "email"]
            ]

            patient_df = (
                self.user_df.query(('role == "patient"'))
                .groupby(("clinician_id"))
                .agg({"username": "count"})
                .rename(columns={"username": "registered_patients"})
            )

            registration_df = pd.merge(
                clinician_df, patient_df, left_index=True, right_on="clinician_id"
            )
            print("\nBreeze Clinicians:")
            print(registration_df)
            return registration_df.index, registration_df.columns

        else:
            print("\nBreeze Users:")
            print(self.user_df)
            return self.user_df.index, self.user_df.columns

    def alter_user(self, user_id: int, attribute: str, value: Any) -> bool:
        """
        Executes the query to update the relevant entry in the database
        """
        # Selecting the relevant attributes of the relevant row of the
        # dataframe
        user_info = self.user_df.loc[
            user_id,
            ["username", "first_name", "surname", "email", "is_active", "role"],
        ]

        # Unpacking the attributes and instantiating a user object to edit
        # itself in the database.
        user, first_name, surname, email, is_active, role = user_info
        altered_user_data = {
            "user_id": user_id,
            "username": user,
            "first_name": first_name,
            "surname": surname,
            "email": email,
            "is_active": is_active,
            "role": role,
        }
        if role == "patient":
            altered_user = Patient(self.database, **altered_user_data)
        elif role == "clinician":
            altered_user = Clinician(self.database, **altered_user_data)
        else:
            altered_user = User(self.database, **altered_user_data)

        result = altered_user.edit_info(attribute, value)
        self.refresh_user_df()
        return result

        # LONGER TERM CONSIDERATIONS:
        # df.iloc[] takes the data in order of memory, so we can use this to impliment
        # crude pagination, perhaps mixed with sorting by name

    def delete_user(self, user_id: int):
        """
        Executes the query to delete the relevant user in the database
        """
        try:
            self.database.cursor.execute(
                "DELETE FROM Users WHERE user_id = ?", (user_id,)
            )
            self.database.connection.commit()

            # Return true as the operation was completed successfully
            return True

        # If there is an error with the query
        except sqlite3.OperationalError:
            print("Error updating, likely you selected an invalid user_id")
            return False

        # TODO: Add checks that these methods can only be applied to patients and practitioners

    def assing_patient_flow(self) -> bool:
        """
        Assigns a patient to a clinician, returns bool with the result
        of the update
        """

        clear_terminal()
        print("\nAssign Patient to Clinician \n")

        # show the unregistered patients
        patient_ids, _ = self.view_table("patients", "registration")

        if patient_ids.empty:
            print("No unassigned patients found.")
            wait_terminal()
            return False

        # chose patient
        patient_id = get_user_input_with_limited_choice(
            "Enter the patient ID to assign: ",
            patient_ids,
            invalid_options_text="Invalid Patient ID, please chose from the list",
        )

        # show the clinicians
        clinician_ids, _ = self.view_table("clinicians", "registration")

        if clinician_ids.empty:
            print("No clinicians found.")
            return wait_terminal()

        # chose a clinician
        clinician_id = get_user_input_with_limited_choice(
            "Enter the clinician ID to assign: ",
            clinician_ids,
            invalid_options_text="Invalid Clinician ID, please chose from list.",
        )

        result = self.alter_user(patient_id, "clinician_id", clinician_id)
        if result:
            print(
                f"Patient {patient_id} successfully assigned to Clinician {clinician_id}."
            )
            return wait_terminal(return_value=True)
        else:
            print("Error assigning patient to clinician.")
            return wait_terminal()

    def edit_user_flow(self) -> bool:
        """
        Logic to edit any user in the database
        """
        clear_terminal()
        print("\nEdit User Information")

        user_ids, attributes = self.view_table("users")
        if user_ids.empty:
            print(" No users found.")
            return wait_terminal()

        user_id = get_user_input_with_limited_choice(
            "Enter the user ID to edit: ",
            user_ids,
            invalid_options_text="Invalid User ID, please try again.",
        )
        attribute = get_user_input_with_limited_choice(
            "Enter the attribute to edit: ",
            attributes,
            invalid_options_text="Invalid attribute. Please select a valid option from the columns of the previous table.",
        )

        clinician_ids = self.user_df.query(('role == "clinician"')).index

        # Handle input according to the column they are trying to edit
        if attribute in ["user_id", "role"]:
            print(f"Attribute {attribute} cannot be changed.")
            return wait_terminal()
        elif user_id in clinician_ids and attribute in [
            "clinician_id",
            "diagnosis",
            "emergency_email",
            "date_of_birth",
        ]:
            print(f"Attribute {attribute} cannot be changed for a clinician.")
            return wait_terminal()
        elif attribute in ["email", "emergency_email"]:
            value = get_valid_email(f"Enter the new value for {attribute}: ")
        elif attribute == "is_active":
            value = get_valid_yes_or_no(f"Enter the new value for {attribute} (Y/N): ")
        elif attribute == "diagnosis":
            value = display_choice("Select the diagnosis for the patient: ", diagnoses)
        elif attribute == "date_of_birth":
            value = get_valid_date(
                "Enter the new date of birth (YYYY-MM-DD): ",
                datetime(1900, 1, 1),
                datetime.now(),
            )
        elif attribute == "clinician_id":
            value = get_user_input_with_limited_choice(
                "Enter the new clinician ID: ",
                clinician_ids,
                invalid_options_text="Invalid Clinician ID, please try again.",
            )
        else:
            value = get_valid_string(
                f"Enter the new value for {attribute}: ",
                max_len=25,
                min_len=0 if attribute == "password" else 1,
            )

        self.alter_user(user_id, attribute, value)
        print(f"\n Successfully updated {attribute} for User {user_id} to {value}.")
        wait_terminal()

    # Admin FLow
    def flow(self) -> bool:
        while True:
            clear_terminal()
            print(f"Hello, {self.username}!")

            # Display the Admin menu
            choices = [
                "Assign Patient to Clinician",
                "View User Information",
                "Edit User Information",
                "Disable User",
                "Delete User",
                "Quit",
            ]
            # TODO: We should probably have a cancel option during any of these 7 operations

            # Menu choices
            selection = display_choice("What would you like to do?", choices)

            # Assign a patient to clinician

            if selection == 1:
                self.assing_patient_flow()

            # View all user info
            elif selection == 2:
                clear_terminal()
                self.view_table("users")
                wait_terminal()

            # Edit info
            elif selection == 3:
                self.edit_user_flow()

            # Disable someone
            elif selection == 4:
                print("\nDisable User\n")
                action = get_user_input_with_limited_choice(
                    "Would you like to disable or re-enable a user?",
                    ["disable", "re-enable"],
                    invalid_options_text="Invalid choice. Please select 'disable' or 're-enable'",
                )
                # Change to display with two options - which handles input.
                user_ids, _ = self.view_table("Users")
                if user_ids.empty:
                    print(f"No users available to {action.lower()}.")
                    wait_terminal()
                    continue

                # chose someone
                user_id = get_user_input_with_limited_choice(
                    "Enter the user ID to {action.lower()}:",
                    user_ids,
                    invalid_options_text="Invalid User ID, please try again.",
                )

                # confirm
                confirm = get_valid_yes_or_no(
                    f"Are you sure you want to disable User {user_id}? (Y/N):"
                )
                if confirm:
                    new_status = False if action == "disable" else True
                    self.alter_user(user_id, "is_active", new_status)
                    print(
                        f"\n User {user_id} has been sucessfully {"disabled" if not new_status else "re-enabled"}."
                    )
                else:
                    print("\nCancelled.")
                wait_terminal()

            # Deleting user
            elif selection == 5:
                print("\nDelete a User\n")
                # Get user IDs
                user_ids, _ = self.view_table("users")
                if user_ids.empty:
                    print("No user found")
                    wait_terminal()
                    continue
                # chose someone
                user_id = get_user_input_with_limited_choice(
                    "Enter the User ID to delete:",
                    user_ids,
                    invalid_options_text="Invalid User ID, try again.",
                )
                # confirm
                confirm = get_valid_yes_or_no(
                    f"Are you sure you want to delete User {user_id}?(Y/N):"
                )
                if confirm:
                    self.delete_user(user_id)
                    print(f"\nUser {user_id} has been successfully deleted.")
                else:
                    print("\nCancelled.")
                wait_terminal()

            # Exit
            elif selection == 6:
                print("Goodbye Admin.")
                return False
