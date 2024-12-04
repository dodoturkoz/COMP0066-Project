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
        self.refresh_user_appointments_df()
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

    def refresh_user_appointments_df(self):
        """
        Retrieves an updated version of the appointments table from SQL and
        presents it in Pandas
        """
        # TODO: figure out whether I keep the joins here or apply them to the
        # database process later.
        appointments_query = self.database.cursor.execute("""
        SELECT
            a.user_id AS patient_id,
            p.name AS patient_name,
            a.clinician_id,
            c.name AS clinician_name,
            date,
            is_confirmed, 
            is_complete
        FROM Appointments a
        LEFT JOIN Users p on p.user_id = a.user_id                                                                                                                                                                                               
        LEFT JOIN Users c on c.user_id = a.clinician_id;""")

        appointments_data = appointments_query.fetchall()
        self.appointments_df = pd.DataFrame(appointments_data)
        self.appointments_df.set_index("patient_id", inplace=True)
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

    def view_table(self, table_name: str):
        """
        Selects the relevant portion of the Pandas dataframe for the user, as
        defined by the table_name input.
        """
        if table_name == "Patients":
            patient_df = self.user_df.query(('role == "patient"'))
            patient_df = patient_df.filter(
                items=["username", "email", "name", "is_active"]
            )
            print(patient_df)
            # return (patient_df.index, patient_df.columns)
        elif table_name == "Clinicians":
            clinician_df = self.user_df.query(('role == "clinician"'))
            clinician_df = clinician_df.filter(
                items=["username", "email", "name", "is_active"]
            )
            print(clinician_df)
        elif table_name == "Unregistered Patients":
            unregistered_patient_df = self.user_df.query(
                ('role == "patient" and clinician_id != clinician_id')
            )
            unregistered_patient_df = unregistered_patient_df.filter(
                items=["username", "email", "name", "is_active", "clinician_id"]
            )
            print(unregistered_patient_df)
        elif table_name == "Patients per Clinician":
            pass
        elif table_name == "":
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
            ["username", "name", "email", "is_active", "role"],
        ]

        # Unpacking the attributes and instantiating a user object to edit
        # itself in the database.
        user, name, email, is_active, role = user_info
        altered_user = User(
            self.database,
            user_id=int(user_id),
            username=str(user),
            name=str(name),
            email=str(email),
            is_active=bool(is_active),
            role=role,
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

    def table_logic(self, table_name, function_name):
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
            print(f"Hello, {self.name}!")

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
                patient_ids, _ = self.view_table("Unregistered Patients")
                if not patient_ids:
                    print("No unregistered patients found.")
                    wait_terminal()
                    continue
                # chose patient
                patient_id = get_user_input_with_limited_choice(
                    "Enter the patient ID to assign:", patient_ids
                )
                # show the clinicians
                clinician_ids, _ = self.view_table("Clinicians")
                if not clinician_ids:
                    print("No clinicians found.")
                    wait_terminal() 
                    continue 
                #chose a clinician 
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
                self.view_table("Users")
                # wait_terminal

            # View speicifc users - not sure if this is needed
            elif selection == 3:
                print("\nView a Specific User\n")
                # Get all user IDs

                user_ids, _ = self.view_table("Users")
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
                print("\nDo you want to edit a patient or a clinician?")
                table_choice = input("Press 1 for patient, press 2 for clinician:")
                if table_choice == "1":
                    print("")
                    self.view_table("Patients")
                    # patient_ids, columns = self.view_table("Patients")
                    # user_id = get_user_input_with_limited_choice("Enter the user ID to edit: ", patient_ids)
                    # attribute = get_user_input_with_limited_choice("Enter the attribute to edit: ", columns)
                    user_id = int(input("\nEnter the user ID to edit: "))
                    attribute = input(
                        "Enter the attribute to edit (e.g., email, name): "
                    ).strip()
                    value = input("Enter the new value: ").strip()
                    try:
                        self.alter_user(user_id, attribute, value)
                        print("")
                    except Exception as e:
                        print(f"Error: {e}")
                elif table_choice == "2":
                    self.view_table("Clinicians")
                    user_id = int(input("\nEnter the user ID to edit: "))
                    attribute = input(
                        "Enter the attribute to edit (e.g., email, name): "
                    ).strip()
                    value = input("Enter the new value: ").strip()
                    try:
                        self.alter_user(user_id, attribute, value)
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    continue

            # Disable someone
            elif selection == 5:
                print("\nDisable User\n")
                #Get user IDs
                user_ids,_ = self.view_table("Users")
                if not user_ids:
                    print("No users found.")
                    wait_terminal()
                    continue 
                #chose someone 
                user_id = get_user_input_with_limited_choice(
                    "Enter the user ID to disable:", user_ids
                )

                #confirm 
                confirm = get_valid_yes_or_no(f"Are you sure you want to disable User {user_id}? (Y/N):")
                if confirm: 
                    self.alter_user(user_id, "is_active", False )
                    print(f"\n User {user_id} has been sucessfully disabled.")
                else:
                    print("\nCancelled.")
                # wait_terminal

            # Deleting user
            elif selection == 6:
                print("\nDelete a User\n")
                # Get user IDs
                user_ids, _ = self.view_table("Users")
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
                print("Goodby Admin.")
                return False
