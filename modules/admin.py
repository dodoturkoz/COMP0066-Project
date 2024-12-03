import sqlite3
from database.setup import Database
from modules.user import User
from datetime import datetime

import pandas as pd
import numpy as np

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
        name: str,
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
            name,
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
                name,
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
            self.refresh_user_df()

            # Display the Admin menu
            print("\nHello Admin!")
            print("1. Register Patient to Practitioner")
            print("2. View All Users")
            print("3. View Specific User")
            print("4. Edit User Information")
            print("5. Disable a User")
            print("6. Delete a User")
            print("7. Exit")
            # TODO: We should probably have a cancel option during any of these 7 operations

            # Menu choices
            choice = input("Enter your choice (1-7): ").strip()

            # Assign a patient to clinician

            if choice == "1":
                print("\nAssign Patient to Clinician: \n")
                self.view_table("Unregistered Patients")
                new_patient_id = input("Choose a user_id to assign: ")

                print("\nClinicians List:\n")
                self.view_table("Patients per Clinician")
                new_clinician_id = input("Choose a user_id to assign: ")

                self.alter_user(new_patient_id, "clinician_id", new_clinician_id)

            # View all user info
            elif choice == "2":
                print("\nAll Users:")
                print(self.user_df)

            # View speicifc users - not sure if this is needed
            elif choice == "3":
                try:
                    user_id = int(input("Enter the user ID to view: "))
                    user_data = self.user_df[self.user_df["user_id"] == user_id]
                    if not user_data.empty:
                        print("\nUser Information:")
                        print(user_data)
                    else:
                        print("User not found.")
                except ValueError:
                    print("Invalid input. Please enter a valid user ID.")

            # Edit info
            elif choice == "4":
                print("\nDo you want to edit a patient or a clinician?")
                table_choice = input("Press 1 for patient, press 2 for clinician:")
                if table_choice == "1":
                    print("")
                    self.view_table("Patients")
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
            elif choice == "5":
                try:
                    user_id = int(input("Enter the User ID to disable: "))
                    self.disable_user(user_id)
                except Exception as e:
                    print(f"Error: {e}")

            # Deleting user
            elif choice == "6":
                try:
                    user_id = int(input("Enter the user ID to delete: "))
                    confirmation = (
                        input("Are you sure you want to delete this user? (yes/no): ")
                        .strip()
                        .lower()
                    )
                    if confirmation == "yes":
                        self.delete_user(user_id)
                    else:
                        print("Operation cancelled.")
                except Exception as e:
                    print(f"Error: {e}")

            # Exit
            elif choice == "7":
                print("Exiting Admin Menu.")
                return False

            else:
                print("Invalid choice. Please select a valid option.")
