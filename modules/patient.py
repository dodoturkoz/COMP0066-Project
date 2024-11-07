import COMP0066-Project
import sqlite3
from typing import Any
from ..database.setup import Database
#Got the .. from searching on bing and copilot automatically showing it to me. May have to remove if can't use.
#Can't we just import the COMP0066-Project. https://realpython.com/python-import/
from datetime import datetime
from datetime import date
#Code working with datetime module was taken from https://docs.python.org/3.12/library/datetime.html#datetime.date.strftime

#class Patient(User) - Made Patient a child class of User (parent class)
class Patient(User):
    # database: Database, user_id: int, username: str, email: str -> Why is this important in David's code?
    is_active: bool
    def __init__(self,name:str,emergency_contact:str,MHWP:str,condition:str):
        self.name=name
        self.emergency_contact=emergency_contact
        self.MHWP=MHWP
        self.condition=condition

    def edit_info(self,change:str,new:str): #David changed from edit_info to edit_medical_info but I thought we were trying to
        # overwrite and because of the inheritance and scope stuff, the patient should do edit_info in patient and if there is no
        #such method, edit_info in users. We do not want patients to change their role, maybe username, user_id. Not sure if patients
        #Can be allowed to disable accounts in a NHS app i.e. is it part of a treatment or just a general support system for patients
        #to opt in to get support. 
        """
        Updates the attribute both in the object and in the database,
        returns the result of the update
        """
        #Code taken from David's function for editing info for users since overwriting was mentioned in the meeting for limiting options available to patients.
        if change=="email" or change=="password":
            try:
                # First update on the database
                self.database.cursor.execute(
                    f"UPDATE Users SET {change} = ? WHERE user_id = ?",
                    (new, self.user_id),
                )
                self.database.connection.commit()

                # Then in the object if that particular attribute is stored here
                if hasattr(self, change):
                    setattr(self, change, new)

                # Return true as the update was successful
                return True

            # If there is an error with the query
            except sqlite3.OperationalError:
                print(
                   "Error updating, likely the selected attribute does not exist for Users"
                )
                return False
        

        if change=="name" or change== "emergency_contact" or change=="MHWP" or change=="condition":
            #Below method taken from David user.py based on the fact that we could create table in setup for patients since 
            #in meeting it was mentioned to store persistant data in tables and name, emergency_contact and mhwp and condition. 
            #can be persistant data that is required even when the program finishes. So i just took the same method so that they
            #can do the same thing as they did with editing info in user table but with patient table. Given that user table
            #does not contain patient rows and the points raised in the meeting about emergency contact being duplicated 
            #I believe we create a separate table for patients with userid, name, emergency_contact and mhwp and condition.
            """
            Updates the changing attribute both in the object and in the database,
            returns the result of the update
            """
            try:
                # First update on the database
                self.database.cursor.execute(
                    f"UPDATE Patients SET {change} = ? WHERE user_id = ?",
                    (new, self.user_id),
                )
                self.database.connection.commit()

                # Then in the object if that particular attribute is stored here
                if hasattr(self, change):
                    setattr(self, change, new)

                # Return true as the update was successful
                return True

            # If there is an error with the query
            except sqlite3.OperationalError:
                print(
                    "Error updating, likely the selected attribute does not exist for Users"
                )
                return False
        #Above
        # Provides interface to change name
        # email
        # emergency contact
        # Could this reuse the same method as the Admin edit? With different permissions?
        # Perhaps define on parent (although practitioner doesn't need this)
        # David's Note: changed the name to edit_medical_info to avoid clash with parent
        

    def mood_of_the_day(self,mood:int,action:str,comments:str):
        #Interface conversion of mood to integer if mood....
        #The below function is based on 7 day mood only table. In such case, the if statement and action 
        #parameter will not be needed since need to only update mood on table rather than use sql insert statement.

        #Checking day of the week to work with mood and comments table
        """
        Updates the attribute corresponding to the current day with mood and comments in 2 different tables in the database only,
        returns the result of the update
        """

        d = date.today()
        thisday=d.strftime("%A")

        if action=="update" or action=="Update" or action=="UPDATE": #needed if not using 7 day table
         #Updating the mood table
            try:
                # Only update on the database since no object data
                self.database.cursor.execute(
                    f"UPDATE Mood SET {thisday} = ? WHERE user_id = ?",
                    (int(mood), self.user_id),
                )
                self.database.connection.commit()

                # Return true as the update was successful
                return True

            # If there is an error with the query
            except sqlite3.OperationalError:
                print(
                   "Error updating, likely the selected attribute does not exist for Mood"
                )
                return False
                
            
        #Updating the comments table
        try:
            # Only update on the database since no object data
            self.database.cursor.execute(
                "UPDATE Comments SET {thisday} = ? WHERE user_id = ?",
                (comments, self.user_id),
            )
            self.database.connection.commit()
               # Return true as the update was successful
            return True
            # If there is an error with the query
        except sqlite3.OperationalError:
            print(
               "Error updating, likely the selected attribute does not exist for Comments"
            )
            return False

        #Add function is needed if we dont use the 7 day table only. 
        #elif action=="add" or action=="Add" or action=="ADD":
        

        # Interface for this. Mood will be persistant data because after the program exits, the clinician should be able to see mood.


    def journal(self,action:str):
        """
        Based on action- either
        1. View a table of date/time and journalled text with SQL query for only that userid.
        2.Insert into the table (journal) text called journal linked to a timestamp and the userid in the database only.
        """
        # view journal entries
        if action=="view" or action=="View" or action=="VIEW": 
         #Updating the mood table
            try:
                # Only update on the database since no object data
                self.database.cursor.execute(
                    "SELECT date_time,journal FROM Journal WHERE user_id = ?",
                )
                self.database.connection.commit()

                # Return true as the update was successful
                return True

            # If there is an error with the query
            except sqlite3.OperationalError:
                print(
                   "Error seeing data, likely the selected attribute does not exist for Mood"
                )
                return False
        
        # add journal entries
        if action=="add" or action=="Add" or action=="ADD": 
            journal=input("What would you like to write in your journal?")
            
            date_time= datetime.now() #Put date_time = current date time timestamp. Need to check data type storage in sqlite 3 to change format based on sqlite3
         #Updating the mood table
            try:
                # Only update on the database since no object data
                self.database.cursor.execute(
                    "INSERT INTO Journal VALUES (date_time,self.user_id, journal)"),
                self.database.connection.commit()

                # Return true as the update was successful
                return True

            # If there is an error with the query
            except sqlite3.OperationalError:
                print(
                   "Error inserting data into Journal table"
                )
                return False

    def search_exercises(self, keyword):
        """
        Search exercise based on a keyword in a dictionary
        """
        # Looks up exercises and displays them. Won't be persistant data so not in tables.
        #Dictionary of key words like categories, urls since can't use find with string.
        #Can also create lists with variable name as category and 3 urls stored in each list to give patient options.
        #e.g. morning=["https://insighttimer.com/jonathanlehmann/guided-meditations/morning-meditation-with-music","https://insighttimer.com/metamorfize/guided-meditations/morning-motivation-3"]
        #if keyword="morning":
        #print("You might find the following exercises useful:")
        #print(morning)
        website={"sleep": "https://insighttimer.com/indiemusicbox/guided-meditations/deep-sleep",
        "morning":"https://insighttimer.com/jonathanlehmann/guided-meditations/morning-meditation-with-music",
        "prayer":"https://insighttimer.com/mariagullo/guided-meditations/st-patricks-prayer-in-the-christian-tradition-i-arise-today-dot-dot-dot",
        "mantra":"https://insighttimer.com/prashantipaz/guided-meditations/kalki-mantra-for-protection",
        "motivation":"https://insighttimer.com/metamorfize/guided-meditations/morning-motivation-3",
        "piano":"https://insighttimer.com/indiemusicbox/guided-meditations/piano-meditation",
        "breathing":"https://insighttimer.com/andrewjohnson/guided-meditations/breathing-relaxation-1"}
        try:
            if str(keyword) in website:
                print("Based on your keyword, you might find " + str(website[str(keyword)]) +" useful")
            else:
                print("You must choose from the following keywords only: sleep, morning, prayer, mantra, motivation, piano or breathing")
            #Can try to implement choose 1 option here.
        except Exception as e:
            print("Sorry, the ability to search exercises is temporarily unavailable. Please visit https://insighttimer.com/guided-meditations and https://www.freemindfulness.org/download for now")

    def book_appointment(self):
        # Display available slots, and select to request one
        # Q: System for appointments? Database?
        pass

    def cancel_appointment(self):
        # Display, and option to cancel
        pass

    def flow(self):
        print("Hello Patient")
        return False


# A function to ask for mood in a user-friendly way and return mood_no to represent mood with a number.
#Used code from https://www.geeksforgeeks.org/print-colors-python-terminal/ and https://ss64.com/nt/syntax-ansi.html
def mood_no():
    def DarkGreen(skk): print("\033[32m {}\033[00m" .format(skk))
    def Green(skk): print("\033[92m {}\033[00m".format(skk))
    def Yellow(skk): print("\033[93m {}\033[00m".format(skk))
    def Brown(skk): print("\033[33m {}\033[00m".format(skk))
    def Red(skk): print("\033[91m {}\033[00m".format(skk))
    def Orange(skk): print("\033[31m {}\033[00m".format(skk))

    DarkGreen("dark green Outstanding :>")
    Green("green Great :)")
    Yellow("yellow Okay :|")
    Orange("orange Bit bad :[")
    Red("red Very bad :(")
    Brown("brown Terrible :<")
    mood_colour=input("Type your mood using the following words: dark green, green, yellow, orange, red, brown ")
    if mood_colour =="dark green":
        mood_no=6
    elif mood_colour =="dark green":
        mood_no=5
    elif mood_colour =="dark green":
        mood_no=4
    elif mood_colour =="dark green":
        mood_no=3
    elif mood_colour =="dark green":
        mood_no=2
    elif mood_colour =="dark green":
        mood_no=1
    else:
        print("Please ensure you type using the following words in lowercase: dark green, green, yellow, orange, red, brown ")
        mood_no=mood_no()

    return mood_no

#something.edit_info(input("What medical information would you like to update. Please type name, email or emergency contact. "),input("Please type what you want to change the field you have selected to "))
#something.mood_of_the_day(mood_no(),input("Would you like to add any comments on your mood. "))
#something.journal(input("Would you like to view your journal or add to your journal. Please type view or add. "))
#something.search_exercises(input"Please type a keyword from the following to search for a specific category of exercise: \nsleep, morning, prayer, mantra, motivation, piano or breathing ")
