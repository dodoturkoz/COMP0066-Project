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
    df: pd.DataFrame

    def __init__(
        self,
        database: Database,
        user_id: int,
        username: str,
        name: str,
        email: str,
        is_active: bool,
        *args,
        **kwargs
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
        self.refresh()

    def refresh(self):
        # Want to run this on init
        # Have to explicitly init all user functions here as well 
        """
        Retrieves an updated version of the whole database from SQL and
        presents it in Pandas
        """
        complete_query = self.database.cursor.execute(f"""
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
        # For later: don't want to mix aggregation functions in just yet
        # LEFT JOIN JournalEntries j ON u.user_id = j.user_id
        # LEFT JOIN MoodEntries m ON u.user_id = m.user_id
        # LEFT JOIN Appointment a ON u.use_id = a.user_id
        data = complete_query.fetchall()
        self.df = pd.DataFrame(data)
        self.df.set_index("username", inplace=True)

    def view_table(self, table_name):
        """
        Selects the relevant portion of the Pandas dataframe for the user, as
        defined by the table_name input.
        """
        # Making a big query to all the databases and storing the inforamtion in Pandas
        if table_name == "Patients":
            pass
        if table_name == "Clinicians":
            pass
        if table_name == "Unregistered Patients":
            pass
        if table_name == "Unregistered Clinicians":
            pass
        if table_name == "":
            pass
        else:
            pass

    # def update_table(self, table_name, attribute, new_attribute_value):
    #     # So this works, but I need to see how it works in the classes.
    #     self.database.cursor.execute(f"""
    #     UPDATE {table_name}
    #     SET {attribute} = {new_attribute_value}
    #     """)

    def edit_table_info(self, table_name, user, attribute, value):
        """
        Executes the query to update the relevant entry in the database
        """
        if table_name == "Patients":
            pass
        if table_name == "Clinicians":
            # Selecting the relevant attributes of the relevant row of the 
            # dataframe
            user_info = self.df.loc[
                    user,
                    ["user_id", "name", "email", "is_active", "role"],
            ]

            # Unpacking the attributes and instantiating a user object to edit
            # itself in the database. 
            user_id, name, email, is_active, role = user_info
            user_to_edit = User(self.database, user_id, user, name, 
                                email, is_active, role)

            user_to_edit.edit_info(attribute, value)
            # return self.refresh
        
        # LONGER TERM CONSIDERATIONS: 
        # df.iloc[] takes the data in order of memory, so we can use this to impliment 
        # crude pagination, perhaps mixed with sorting by name
    def delete_user(self, table, row):
        """
        Executes the query to delete the relevant user in the database
        sessions
        """
        # Also a sketch. I'm not sure we need the table, but we definitely need
        # table and the column.

    # NB - add checks that these methods can only be applied to patients and practitioners

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
    
    def flow(self) -> bool:
        while True:
            print("\nAdmin Menu:")
            print("1. Register Patient to Practitioner")
            print("2. View User Information")
            print("3. Disable a User")
            print("4. Exit")

            choice = input("Enter your choice (1-4): ")

            if choice == "1":
                try:
                    patient_id = int(input("Enter patient ID: "))
                    practitioner_id = int(input("Enter practitioner ID: "))
                    self.register_patient(patient_id, practitioner_id)
                except ValueError:
                    print("Invalid input. Please enter numeric IDs.")
            elif choice == "2":
                try:
                    user_id = int(input("Enter user ID to view: "))
                    self.view_info(user_id)
                except ValueError:
                    print("Invalid input. Please enter a numeric ID.")
            elif choice == "3":
                try:
                    user_id = int(input("Enter user ID to disable: "))
                    self.disable_user(user_id)
                except ValueError:
                    print("Invalid input. Please enter a numeric ID.")
            elif choice == "4":
                print("Exiting Admin Menu.")
                return False
            else:
                print("Invalid choice. Please select a valid option.")
        return False