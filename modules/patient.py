import sqlite3
from typing import Optional, Any

from modules.constants import RELAXATION_RESOURCES, MOODS
from modules.user import User
from modules.clinician import Clinician
from datetime import datetime


class Patient(User):
    MODIFIABLE_ATTRIBUTES = ["username", "email", "password"]

    def edit_patient_info(self) -> bool:
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
                print(f"\nMood Entries for {date if date else 'all dates'}:\n")
                for entry in entries:
                    print(f"Date: {str(entry['date']).split()[0]}")
                    print("Mood: " + str(entry["mood"]))
                    print(f"Content: {entry['text']}\n")

            else:
                print("No mood entries found for the specified date.")

            return entries

        except sqlite3.OperationalError as e:
            print(f"Database error occurred: {e}")
            return []

    def mood_of_the_day(self) -> bool:
        """
        Manages the mood entry for the current day:
        - Updates the existing entry if one exists.
        - Creates a new mood entry if none exists.
        """

        def mood_input():
            """
            Get mood input from the patient using a number or color name.
            """
            print("\nMOOD TRACKER:\n")

            # display mood options
            for num, mood in MOODS.items():
                mood_display = f"{mood['ansi']}{num}. {mood['description']} [{mood['color']}]\033[00m"
                print(mood_display)

            valid_inputs = {num: mood for num, mood in MOODS.items()}
            valid_inputs.update(
                {mood["color"].lower(): mood for mood in MOODS.values()}
            )

            while True:
                mood_choice = input(
                    "\nEnter your mood for today (number 6 to 1 or color name): "
                ).lower()
                if mood_choice in valid_inputs:
                    selected_mood = valid_inputs[mood_choice]
                    return f"{selected_mood['ansi']}{num}. {selected_mood['description']} [{selected_mood['color']}]\033[00m"
                print(
                    "Invalid input. Please enter a number from 6 to 1 or a valid color name."
                )

        def comment_input():
            """
            Ask the user to comment on their mood.
            """
            while True:
                do_comment = input(
                    "Would you like to add a comment? (y/n): "
                ).lower()
                if do_comment in ("yes", "y", "1"):
                    return input("Enter your comment: ")
                elif do_comment in ("no", "n", "2"):
                    return "No comment provided."
                print("Invalid input. Please enter y or n.")

        mood = mood_input()
        comment = comment_input()

        today_date = datetime.now().strftime("%Y-%m-%d")
        query_check = "SELECT text, mood FROM MoodEntries WHERE user_id = ? AND DATE(date) = ?"
        query_update = "UPDATE MoodEntries SET text = ?, mood = ? WHERE user_id = ? AND DATE(date) = ?"
        query_insert = "INSERT INTO MoodEntries (user_id, text, date, mood) VALUES (?, ?, ?, ?)"

        try:
            # Check if an entry already exists for today
            self.database.cursor.execute(
                query_check, (self.user_id, today_date)
            )
            entry = self.database.cursor.fetchone()

            if entry:
                print(
                    f"\nExisting entry found:\nMood: {entry['mood']}\nComment: {entry['text']}"
                )
                print("New Mood: ", mood)
                print("New Comment: ", comment)

                # Confirm update
                consent = input(
                    "Do you want to update the mood entry for today? (Yes/No): "
                ).lower()
                if consent in ("yes", "y", "1"):
                    self.database.cursor.execute(
                        query_update, (comment, mood, self.user_id, today_date)
                    )
                    self.database.connection.commit()
                    print("Mood entry updated successfully.")
                    return True
                else:
                    print("Mood entry was not updated.")
                    return False
            else:
                # Insert new mood entry
                self.database.cursor.execute(
                    query_insert, (self.user_id, comment, today_date, mood)
                )
                self.database.connection.commit()
                print("Mood entry added successfully.")
                return True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                self.edit_patient_info()
            elif choice == "2":
                self.mood_of_the_day()
            elif choice == "3":
                date = input(
                    "Enter a date in YYYY-MM-DD format or "
                    + "leave blank to view all previous entries: "
                )
                self.display_previous_moods(date)
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
            next_step = input("Would you like to:\n1. Continue\n2. Quit\n")
            if next_step.strip() != "1":
                print("Goodbye!")
                break
