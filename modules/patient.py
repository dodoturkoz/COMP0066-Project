import sqlite3
from typing import Optional, Any

from modules.constants import RELAXATION_RESOURCES
from modules.user import User
from datetime import datetime

def mood_input():
    """
    Get mood from patient using a colour or number code in input
    """

    print("\n" + "\033[1m {}\033[00m".format("MOOD TRACKER:\n"))
    print("\033[32;40m {}\033[00m".format("6. dark green Outstanding  \U0001F44D \u0197  ") + "\U0001f600")
    print("\033[92;40m {}\033[00m".format("5. green Great                \u0197  ") + "\U0001F642")
    print("\033[93;40m {}\033[00m".format("4. yellow Okay                \u0197  ") + "\U0001F610")
    print("\033[31;40m {}\033[00m".format("3. orange Bit bad             \u0197  ") + "\U0001F641")
    print("\033[91;40m {}\033[00m".format("2. red Very bad               \u0197  ") + "\U0001F61E")
    print("\033[1;2;91;40m {}\033[00m".format("1. brown Terrible          \U0001F44E \u0197  ") + "\U0001F622")

    #We can add 0x0001F44D U+1F44D and U+1F44E for thumbs up and down if someone likes that. And put U+21A5 as up arrow and U+21A7
    #for the down arrow. U+23CA

    mood_colour=input("\nEnter your mood for today. Select an option from 6 to 1 or type the following words in lowercase only: dark green, green, yellow, orange, red, brown\n")
    if mood_colour =="dark green" or mood_colour =="6" or mood_colour =="6.":
        mood_description= "\033[32m {}\033[00m" .format("Dark green Outstanding \U0001f600")
    elif mood_colour =="green" or mood_colour =="5" or mood_colour =="5.":
        mood_description= "\033[92m {}\033[00m" .format("Green Great \U0001F642") 
    elif mood_colour =="yellow" or mood_colour =="4" or mood_colour =="4.":
        mood_description= "\033[93m {}\033[00m" .format("Yellow Okay \U0001F610") 
    elif mood_colour =="orange" or mood_colour =="3" or mood_colour =="3.":
        mood_description= "\033[33m {}\033[00m" .format("Orange Bit bad \U0001F641") 
    elif mood_colour =="red" or mood_colour =="2" or mood_colour =="2.":
        mood_description= "\033[91m {}\033[00m" .format("Red Very bad \U0001F61E") 
    elif mood_colour =="brown" or mood_colour =="1" or mood_colour =="1.":
        mood_description= "\033[47m[31m {}\033[00m" .format("Brown Terrible \U0001F622") 
    else:
        print("Please ensure you type a number from 6 to 1 or type the following words in lowercase only: dark green, green, yellow, orange, red, brown ")
        mood_description=mood_input()

    return mood_description


def comment_input():
    """
    Ask if patient wants to comment and then pass the comment to patient method.
    """
    do_comment = input("Would you like to enter any comments regarding your mood?\nChoose a number.\n1.Yes\n2.No\n ")
    if do_comment == "1" or do_comment == "1." or do_comment == "Yes" or do_comment == "yes":
        comment = input("Enter any comments regarding your mood:\n")
    elif do_comment == "2" or do_comment == "2." or do_comment == "No" or do_comment == "no":
        comment = "There is no comment associated with the mood of this day.\n"
    else:
        print("Please ensure you enter the number 1 or 2.") 
        comment=comment_input()

    return comment

class Patient(User):
    MODIFIABLE_ATTRIBUTES = ["username", "email", "password"]

    def edit_medical_info(self) -> bool:
        """
        Allows the patient to change their details.
        """
        # should the user be able to change their name? yes
        options = {
            1: "username",
            2: "email",
            3: "password",
            4: "emergency_email",
            5: "date_of_birth",
        }

        print("Select an attribute to edit:")
        for number, attribute in options.items():
            print(f"{number}. {attribute.replace('_', ' ').capitalize()}")

        try:
            choice = int(
                input("Enter the number corresponding to the attribute: ")
            )
            attribute = options.get(choice)

            if not attribute:
                print("Invalid choice. Please select a valid option.")
                return False

            value = input(
                f"Enter the new value for {attribute.replace('_', ' ').capitalize()}: "
            )

            # Update the Users table
            if attribute in self.MODIFIABLE_ATTRIBUTES:
                return self.edit_info(attribute, value)

            # Update the Patients table
            elif attribute in ["emergency_email", "date_of_birth"]:
                self.database.cursor.execute(
                    f"UPDATE Patients SET {attribute} = ? WHERE user_id = ?",
                    (value, self.user_id),
                )
                self.database.connection.commit()
                print(
                    f"{attribute.replace('_', ' ').capitalize()} updated successfully."
                )
                return True
            else:
                print(f"Invalid attribute: {attribute}.")
                return False

        except ValueError:
            print("Invalid input. Please enter a number.")
            return False
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def display_previous_moods(
        self, date: Optional[str] = None
    ) -> list[dict[str, str]]:
        """
        Displays patient's moods, optionally filtering by a specific date.
        """
        query = "SELECT date, text, mood FROM MoodEntries WHERE user_id = ?"
        params = [self.user_id]

        if date:
            query += " AND DATE(date) = ?"
            params.append(date)

        query += " ORDER BY date ASC"

        try:
            self.database.cursor.execute(query, tuple(params))
            entries = [
                {"date": row["date"], "text": row["text"], "mood": row["mood"]}
                for row in self.database.cursor.fetchall()
            ]

            if entries:
                print(
                    f"\nMood Entries for {date if date else 'all dates'}:\n"
                )
                for entry in entries:
                    print(f"Date: {entry['date']}")
                    print("Mood:" + str(entry['mood']))
                    print(f"Content: {entry['text']}\n")

            else:
                print("No mood entries found for the specified date.")

            return entries

        except sqlite3.OperationalError as e:
            print(f"Database error occurred: {e}")
            return []

    def mood_of_the_day(self, mood: str, comment: str) -> bool:
        # Interface for this
        """
        1. Check if mood entry for the day exists.
        2. Update mood for the day is entry for the day exists
        3. Creates a new mood and comment entry for the patient if record for the day does not exist.
        """

        query = "SELECT mood FROM MoodEntries WHERE user_id = ? AND DATE(date) = ?"
        params = [self.user_id,datetime.now().strftime("%Y-%m-%d")]

        try:
            self.database.cursor.execute(query, tuple(params))
            entries =  self.database.cursor.fetchone()

        except Exception as e:
            print(f"Error checking whether mood entry already exists for the day: {e}")
            return False

        #Update mood since previously described mood of the day,
        if entries:    

            query = "UPDATE MoodEntries SET text = ?, mood = ? WHERE DATE(date) = ? AND user_id = ?"
            params = [comment, mood, datetime.now().strftime("%Y-%m-%d"), self.user_id]
            
            try:                
                self.database.cursor.execute(query, tuple(params))
                self.database.connection.commit()
                print("Mood entry updated successfully.")
                return True
            
            except Exception as e:
                print(f"Error updating mood entry: {e}")
                return False
        
        #Insert new mood since mood not previously recorded that day.
        elif not entries:
            try:
                self.database.cursor.execute(
                    "INSERT INTO MoodEntries (user_id, text, date, mood) VALUES (?, ?, ?, ?)",
                    (
                        self.user_id,
                        comment,
                        datetime.now().strftime("%Y-%m-%d"),
                        mood,
                    ),
                )
                self.database.connection.commit()
                print("Mood entry added successfully.")
                return True
            except Exception as e:
                print(f"Error adding mood entry: {e}")
                return False
        
    def display_journal(
        self, date: Optional[str] = None
    ) -> list[dict[str, str]]:
        """
        Displays patient's journal entries, optionally filtering by a specific date.
        """
        query = "SELECT date, text FROM JournalEntries WHERE user_id = ?"
        params = [self.user_id]

        if date:
            query += " AND DATE(date) = ?"
            params.append(date)

        query += " ORDER BY date ASC"

        try:
            self.database.cursor.execute(query, tuple(params))
            entries = [
                {"date": row["date"], "text": row["text"]}
                for row in self.database.cursor.fetchall()
            ]

            if entries:
                print(
                    f"\nJournal Entries for {date if date else 'all dates'}:\n"
                )
                for entry in entries:
                    print(f"Date: {entry['date']}")
                    print(f"Content: {entry['text']}\n")
            else:
                print("No journal entries found for the specified date.")

            return entries

        except sqlite3.OperationalError as e:
            print(f"Database error occurred: {e}")
            return []

    def journal(self, content: str) -> bool:
        """
        Creates a journal entry for the patient.
        """
        try:
            self.database.cursor.execute(
                "INSERT INTO JournalEntries (user_id, text, date) VALUES (?, ?, ?)",
                (
                    self.user_id,
                    content,
                    datetime.now().strftime("%Y-%m-%d"),
                ),
            )
            self.database.connection.commit()
            print("Journal entry added successfully.")
            return True
        except Exception as e:
            print(f"Error adding journal entry: {e}")
            return False

    @staticmethod
    def search_exercises(keyword: str = None):
        """
        Looks up exercises and displays them with
        both an audio file and the relevant transcript.
        """
        if keyword:
            filtered_resources = [
                resource
                for resource in RELAXATION_RESOURCES
                if keyword.lower() in resource["title"].lower()
            ]
        else:
            filtered_resources = RELAXATION_RESOURCES

        for resource in filtered_resources:
            print(f"Title: {resource['title']}")
            print(f"Audio File: {resource['audio_file']}")
            print(f"Transcript: {resource['transcript']}")

    def book_appointment(self, appointment_date: str, description: str) -> bool:
        """
        Allows the patient to book an appointment by specifying date and description.
        """
        # need to add a check to make sure date is today or later
        # what about the time of the appointment?
        try:
            # Check if the patient has an assigned clinician
            self.database.cursor.execute(
                "SELECT clinician_id FROM Patients WHERE user_id = ?",
                (self.user_id,),
            )
            clinician_id = self.database.cursor.fetchone()

            if not clinician_id:
                print("No clinician assigned. Please contact the admin.")
                return False

            self.database.cursor.execute(
                """
                INSERT INTO Appointments (user_id, clinician_id, date, notes, is_complete)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    self.user_id,
                    clinician_id,
                    appointment_date,
                    description,
                ),
            )
            self.database.connection.commit()
            print("Appointment booked successfully.")
            return True
        except sqlite3.IntegrityError as e:
            print(f"Failed to book appointment: {e}")
            return False

    def cancel_appointment(self, appointment_id: int) -> bool:
        """
        Cancels an appointment by removing it from the database.
        """
        try:
            self.database.cursor.execute(
                """
                DELETE FROM Appointments WHERE appointment_id = ? AND user_id = ?
                """,
                (appointment_id, self.user_id),
            )
            if self.database.cursor.rowcount > 0:
                self.database.connection.commit()
                print("Appointment canceled successfully.")
                return True
            else:
                print(
                    "Appointment not found or you are not authorized to cancel it."
                )
                return False
        except sqlite3.OperationalError as e:
            print(f"Error canceling appointment: {e}")
            return False

    def view_appointments(self) -> list[dict[str, Any]]:
        """
        Views all appointments for the patient.
        """
        query = (
            "SELECT appointment_id, date, notes, is_complete "
            "FROM Appointments "
            "WHERE user_id = ?"
        )

        try:
            self.database.cursor.execute(query, (self.user_id,))
            appointments = [
                {
                    "appointment_id": row["appointment_id"],
                    "date": row["date"],
                    "notes": row["notes"],
                    "is_complete": bool(row["is_complete"]),
                }
                for row in self.database.cursor.fetchall()
            ]

            if appointments:
                print("\nYour Appointments:\n")
                for appointment in appointments:
                    print(f"ID: {appointment['appointment_id']}")
                    print(f"Date: {appointment['date']}")
                    print(f"Notes: {appointment['notes']}")
                    print(
                        f"Completed: {'Yes' if appointment['is_complete'] else 'No'}\n"
                    )
            else:
                print("You don't have any appointments.")

            return appointments

        except sqlite3.OperationalError as e:
            print(f"Error viewing appointments: {e}")
            return []

    def flow(self):
        """
        Displays the main patient menu and handles the selection of various options.
        """
        print("Hello Patient")
        while True:
            choice = input(
                "Please select an option:\n"
                "1. Edit Personal Info\n"
                "2. Record Mood of the Day\n"
                "3. Display Previous Moods\n"
                "4. Add Journal Entry \n"
                "5. Read Journal Entries \n"
                "6. Search Exercises\n"
                "7. Book Appointment\n"
                "8. View Appointments\n"
                "9. Cancel Appointment\n"
                "10. Log Out\n"
            )
            if choice == "1":
                self.edit_medical_info()
            elif choice == "2":
                mood = mood_input()
                comment = comment_input()
                self.mood_of_the_day(mood, comment)
            elif choice == "3":
                self.display_previous_moods()
            elif choice == "4":
                content = input("Enter new journal entry: ")
                self.journal(content)
            elif choice == "5":
                date = input(
                    "Enter a date in YYYY-MM-DD format or "
                    + "leave blank to view all previous entries: "
                )
                self.display_journal(date)
            elif choice == "6":
                keyword = input("Enter keyword to search for exercises: ")
                self.search_exercises(keyword)
            elif choice == "7":
                date = input("Enter appointment date (YYYY-MM-DD): ")
                desc = input("Enter appointment description: ")
                self.book_appointment(date, desc)
            elif choice == "8":
                self.view_appointments()
            elif choice == "9":
                self.view_appointments()
                appointment_id = int(input("Enter appointment ID to cancel: "))
                self.cancel_appointment(appointment_id)
            elif choice == "10":
                return True
            else:
                print("Invalid choice. Please try again.")
            print(
                "---------------------------"
            )  # Visual separator after action
            next_step = input("Would you like to:\n1. Continue\n2. Log Out\n")
            if next_step.strip() != "1":
                print("Goodbye!")
                break