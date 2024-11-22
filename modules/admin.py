from database.setup import Database as db
from modules.user import User
import pandas as pd
import numpy as np

class Admin(User):

    def view_unregistered_patients(self): 
        """A for loop that iterates through the relationship table, moving the information from the database into memory and
         displaying it to the admin in CSV format using Pandas. """

        # David - it probably makes sense to construct a relationship table in the database, which takes two user keys as its
        # primary key, and for the sake of completeness it would also be good to add a date created column as that might be 
        # useful. 
         
        # Another consideration is that appointments table should flow through this relationship table, as the patient / clinician 
        # combination should be the same in both instances. 
        pass 

    def register_patient(self, Patient, Practitioner):
        """Creates a new row in the relationship table to reflect a new patient registration"""
        # This will need to update attributes for both patient and practitioner
       # First, we need to take the 
        Patient.edit_info()
            #We need to have created the relevant table in the database before we can get this working 

    def view_info(self, User):
        """Shows the admin all of the attributes on a user table for the user"""

        # N.B. Should we display username and password? It's probably worth editing this so as not to do that... 
        # Q - Does this count as a 'summary'?
        pass

    def disable_user(self, User):
        """Change the value of the disabled value from false to true for the selected user"""
        User.view_info(User)

        # First, makes a query into the database that takes the 
        if User = 
         
        #Then, edit the user information
        User.edit_info(is_active, False)
        # NB - add checks that these methods can only be applied to patients and practitioners
        pass

    def flow(self) -> bool:
        print("Hello Admin")
        return False