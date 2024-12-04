import sqlite3
from database.setup import Database
from modules.user import User
from modules.utilities.display_utils import (
    clear_terminal,
    display_choice,
    wait_terminal,
)
from modules.utilities.input_utils import (
    get_user_input_with_limited_choice,
    get_valid_yes_or_no,
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
        # It might be worth rewriting this query, cutting out the joins and
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

    def view_table(self, user_type: str, sub_type: str):
        """
        Selects the relevant portion of the Pandas dataframe for the user, as
        defined by the inputs.
        """
        if user_type == "patients" and sub_type == "none":
            patient_df = self.user_df.query(('role == "patient"'))
            patient_df = patient_df.filter(
                items=["username", "email", "name", "is_active"]
            )
            print(patient_df)
            # return (patient_df.index, patient_df.columns)
        elif user_type == "clinicians" and sub_type == "none":
            clinician_df = self.user_df.query(('role == "clinician"'))
            clinician_df = clinician_df.filter(
                items=["username", "email", "name", "is_active"]
            )
            print(clinician_df)
        elif user_type == "patients" and sub_type == "registration":
            unregistered_patient_df = self.user_df.query(
                ('role == "patient" and clinician_id != clinician_id')
            )
            unregistered_patient_df = unregistered_patient_df.filter(
                items=["username", "email", "name", "is_active", "clinician_id"]
            )
            print(unregistered_patient_df)
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
            print(registration_df)

        elif user_type == "":
            pass

        else:
            pass

    def view_user(self, user_id: int, attribute: str, value: any):
        # This is a working assumption, but I think whenever an admin wants to
        # view or edit an individual row, they should use a function from that
        # class
        pass

    def alter_user(self, user_id: int, attribute: str, value: any):
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
        altered_user = User(
            self.database,
            user_id=int(user_id),
            username=str(user),
            first_name=str(first_name),
            surname=str(surname),
            email=str(email),
            is_active=bool(is_active),
            role=str(role),
        )

        altered_user.edit_info(attribute, value)

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

    def function_logic(self, function_name):
        # DRAFT: This might be a way to reduce logic overhead
        pass

        # if function_name == "update":
        #     self.update_information()
        # elif function_name == "delete":
        #     self.delete_user()

    def table_logic(self, user_type, function_name):
        # DRAFT: This might be a way to reduce logic overhead
        pass

        # if table_name == "Patients":
        #     return self.function_logic(self, function_name)

    # REMINDER: When I finish with my changes, I'll have to commit them using
    # the following function: self.datbaase.commit()

    # Admin FLow
    def flow(self) -> bool:
        while True:
            clear_terminal()
            print(f"Hello, {self.username}!")

            # Display the Admin menu
            choices = [
                "Assign Patient to Clinician",
                "View User Information",
                "View a Specific User",
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
                print("\nAssign Patient to Clinician \n")
                # show the unregistered patients
                patient_ids = self.view_table("patients", "registration")
                if not patient_ids:
                    print("No unregistered patients found.")
                    wait_terminal()
                    continue
                # chose patient
                patient_id = get_user_input_with_limited_choice(
                    "Enter the patient ID to assign:", patient_ids, invalid_options_text= "Invalid Patient ID, please chose from the list"
                )
                # show the clinicians
                clinician_ids, _ = self.view_table("clinicians", "registration")
                if not clinician_ids:
                    print("No clinicians found.")
                    wait_terminal()
                    continue
                # chose a clinician
                clinician_id = get_user_input_with_limited_choice(
                    "Enter the clinician ID to assign:", clinician_ids
                )
                #call the function 
                #self.assign_patient_to_clinician(patient_id, clinician_id)
                #cant find the assign/register function? will just placehold for now 
                print(f"Pateint {patient_id} successfully assigned to Clinician {clinician_id}.")
                #wait_terminal 


            # View all user info
            elif selection == 2:
                print("\nView all User information \n")
                self.view_table("users")
                # wait_terminal

            # View speicifc users - not sure if this is needed
            elif selection == 3:
                print("\nView a Specific User\n")
                # Get all user IDs

                user_ids, _ = self.view_table("users")
                if not user_ids:
                    print("No users found.")
                    wait_terminal() 
                    continue
                # select the specific person
                user_id = get_user_input_with_limited_choice(
                    "Enter the user ID to view:", user_ids
                )
                user_data = self.df.loc[user_id]
                print("\nUser infromation\n")
                print(user_data)
                #wait_terminal()
                

            # Edit info
            elif selection == 4:
                print("\nEdit User Information")
                user_type_choice = get_user_input_with_limited_choice(
                    "Do you want to edit a Patient or a Clinician?:",["Patient","Clinician"] 
                )
                table_name = "Patients" if user_type_choice == "Patient" else "Clinicians"

                user_ids, columns = self.view_table(table_name.lower(), "none")
                if not user_ids: 
                    print(f" No {table_name.lower()} found.")
                    wait_terminal()
                    continue 
                user_id = get_user_input_with_limited_choice(
                    "Enter the user ID to edit:", user_ids
                )
                attribute = get_user_input_with_limited_choice(
                    "Enter the attribute to edit:",columns
                    )
                value = input(f"Enter the new value for {attribute}:").strip()
                self.alter_user(user_id, attribute, value)
                print(f"\n Successfully updated {attribute} for User {user_id} to {value}.")
                #wait_terminal()


            # Disable someone
            elif selection == 5:
                print("\nDisable User\n")
                action =  get_user_input_with_limited_choice(
                    "Would you like to disable or re-enable a user?", ["disable","re-enable"]
                )
                user_ids, _ = self.view_table("Users")
                if not user_ids:
                    print(f"No users available to {action.lower()}.")
                    wait_terminal()
                    continue

                #chose someone 
                user_id = get_user_input_with_limited_choice(
                    "Enter the user ID to {action.lower()}:", user_ids
                )

                #confirm 
                confirm = get_valid_yes_or_no(f"Are you sure you want to disable User {user_id}? (Y/N):")
                if confirm: 
                    new_status = False if action == "disable" else True 
                    self.alter_user(user_id, "is_active", new_status )
                    print(f"\n User {user_id} has been sucessfully {"disabled" if not new_status else "re-enabled"}.")
                else:
                    print("\nCancelled.")
                # wait_terminal

            # Deleting user
            elif selection == 6:
                print("\nDelete a User\n")
                # Get user IDs
                user_ids, _ = self.view_table("users")
                if not user_ids:
                    print("No user found")
                    wait_terminal() 
                    continue 
                #chose someone 
                user_id = get_user_input_with_limited_choice(
                    "Enter the User ID to delete:", user_ids
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
                # wait_terminal

            # Exit
            elif selection == 7:
                print("Goodbye Admin.")
                return False
