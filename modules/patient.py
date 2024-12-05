import sqlite3
from typing import Optional, Any
from datetime import datetime


from database.setup import Database
from modules.utilities.input_utils import (
    get_valid_string,
    get_valid_email,
    get_valid_date,
    get_valid_yes_or_no,
)
from modules.utilities.display_utils import display_choice, clear_terminal
from modules.appointments import (
    request_appointment,
    cancel_appointment,
)
from modules.constants import RELAXATION_RESOURCES, MOODS
from modules.user import User


class Patient(User):
    MODIFIABLE_ATTRIBUTES = [
        "username",
        "email",
        "password",
        "first_name",
        "surname",
    ]

    def __init__(
        self,
        database: Database,
        user_id: int,
        username: str,
        first_name: str,
        surname: str,
        email: str,
        is_active: bool,
        clinician_id: int,
        *args,
        **kwargs,
    ):
        super().__init__(
            database,
            user_id,
            username,
            first_name,
            surname,
            email,
            is_active,
            *args,
            **kwargs,
        )

        self.clinician_id = clinician_id
        self.clinician = self.get_clinician()

    def get_clinician(self) -> Optional[User]:
        if self.clinician_id:
            clinician_data = (
                self.database.cursor.execute(
                    """
                    SELECT user_id, username, first_name, surname, email, is_active
                    FROM Users
                    WHERE user_id = ?
                    """,
                    (self.clinician_id,),
                )
                .fetchone()
                .values()
            )
            if clinician_data:
                return User(self.database, *clinician_data)
        return None

    def edit_patient_info(self) -> bool:
        """
        Allows the patient to change their details.
        """
        clear_terminal()
        options = [
            "Username",
            "Email",
            "Password",
            "First Name",
            "Surname",
            "Emergency Email",
        ]

        try:
            # Display editable attributes
            choice = display_choice("Select an attribute to edit:", options)
            attribute = options[choice - 1].lower().replace(" ", "_")

            # Handle specific validation for emails
            if attribute in ["email", "emergency_email"]:
                value = get_valid_email(
                    f"Enter the new value for {options[choice - 1]}: "
                )
            else:
                # General string validation for other attributes
                # TODO for things like username/email we should check if it's unique
                value = get_valid_string(
                    f"Enter the new value for {options[choice - 1]}: "
                )

            # Use the parent class's edit_info method for all updates
            success = self.edit_info(attribute, value)

            if success:
                return True
            else:
                print(f"Failed to update {options[choice - 1]}. Please try again.")
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
                    old_mood = MOODS[str(entry["mood"])]
                    show_moods = f"{old_mood['ansi']} {old_mood['description']}\033[00m"
                    print(f"Date: {str(entry['date']).split()[0]}")
                    print("Mood: " + show_moods)
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
                print(
                    f"{mood['ansi']}{num}. {mood['description']} [{mood['color']}]\033[00m"
                )

            valid_inputs = {str(num): mood for num, mood in MOODS.items()}
            valid_inputs.update(
                {mood["color"].lower(): mood for mood in MOODS.values()}
            )

            while True:
                mood_choice = get_valid_string(
                    "\nEnter your mood for today (number 6 to 1 or color name): "
                ).lower()
                if mood_choice in valid_inputs:
                    selected_mood = valid_inputs[mood_choice]
                    return selected_mood["int"]
                print(
                    "Invalid input. Please enter a number from 6 to 1 or a valid color name."
                )

        def comment_input():
            """
            Ask the user to comment on their mood.
            """
            if get_valid_yes_or_no(prompt="Would you like to add a comment? (Y/N): "):
                return get_valid_string("Enter your comment: ", max_len=250)
            return "No comment provided."

        mood = mood_input()
        comment = comment_input()

        today_date = datetime.now().strftime("%Y-%m-%d")
        query_check = (
            "SELECT text, mood FROM MoodEntries WHERE user_id = ? AND DATE(date) = ?"
        )
        query_update = "UPDATE MoodEntries SET text = ?, mood = ? WHERE user_id = ? AND DATE(date) = ?"
        query_insert = (
            "INSERT INTO MoodEntries (user_id, text, date, mood) VALUES (?, ?, ?, ?)"
        )

        try:
            # Check if an entry already exists for today
            self.database.cursor.execute(query_check, (self.user_id, today_date))
            entry = self.database.cursor.fetchone()

            if entry:
                old_mood = MOODS[str(entry["mood"])]
                show_mood = f"{old_mood['ansi']} {old_mood['description']}\033[00m"
                print(
                    f"\nExisting entry found:\nMood: {show_mood}\nComment: {entry['text']}"
                )
                new_mood = MOODS[str(mood)]
                show_new_mood = f"{new_mood['ansi']} {new_mood['description']}\033[00m"
                print("New Mood: ", show_new_mood)
                print("New Comment: ", comment)
                # Confirm update
                if get_valid_yes_or_no(
                    "Do you want to update the mood entry for today? (Y/N): "
                ):
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

    def display_journal(self, date: Optional[str] = None) -> list[dict[str, str]]:
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
                print(f"\nJournal Entries for {date if date else 'all dates'}:\n")
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

        if not filtered_resources:
            print("No resources found matching the search criteria.")

        for resource in filtered_resources:
            print(f"Title: {resource['title']}")
            print(f"Audio File: {resource['audio_file']}")
            print(f"Transcript: {resource['transcript']}")

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

        while True:
            clear_terminal()
            greeting = (
                f"Hello, {self.first_name} {self.surname}!"
                if not self.clinician
                else f"Hello, {self.first_name} {self.surname}! Your assigned clinician is {self.clinician.first_name} {self.clinician.surname}."
            )
            print(greeting)

            options = [
                "Edit Personal Info",
                "Record Mood of the Day",
                "Display Previous Moods",
                "Add Journal Entry",
                "Read Journal Entries",
                "Search Exercises",
            ]

            # if/else statement to show different options to users
            # based on whether they already have a clinician or not.
            if self.clinician_id:
                options.extend(["Appointments", "Log Out", "Quit"])
            else:
                options.extend(["Log Out", "Quit"])

            choice = display_choice("Please select an option:", options)

            def acting_on_choice(choice):
                """
                Recursive function to match different methods to different choices/options
                Only quit and logout option/choice not matched here.
                """
                # Acting_on_choice function only called twice. 1. At the end of flow
                # code to allow patients to go into different options from main menu.
                # 2. Inside the acting_on_choice function in the next step when patient
                # are allowed to retry the same action. Using this function, the choice
                # (integer matching to case and methods) does not change and you can
                # endlessly retry the same option until you decide to exit the menu.
                # If patients choose to exit menu when retry the same action is shown,
                # the function just completes and the outer while true loop happens
                # where the main menu is shown. On second thoughts, can use while loop
                # instead. Recursive function was just more intuitive for me at that time.

                # requires python version >= 3.10
                # using pattern matching to handle the choices
                # action variable used for next step logic implemented at the end
                # after you do methods in each option. Action variable only used twice.
                # action = "Option to redo previous action" means that after doing
                # methods for the option you picked you get the chance to redo that
                # prevous action or choose to exit back to the menu.
                # action = "Exit back to main menu" is only used for appointments
                # when the patient wants to exit back to the main menu straight
                # after pressing appointment option without using any methods.
                # This is in case 7 (appointments) and case 4 (Exit appointments), which
                # only exists if you have a clinician id.

                action = "Option to redo previous action"
                match choice:
                    case 1:
                        self.edit_patient_info()
                    case 2:
                        self.mood_of_the_day()
                    case 3:
                        date = get_valid_date(
                            "Enter a valid date (YYYY-MM-DD) or leave blank to view all entries: ",
                            min_date=datetime(1900, 1, 1),
                            max_date=datetime.now(),
                            min_date_message="Date must be after 1900-01-01.",
                            max_date_message="Date cannot be in the future.",
                            allow_blank=True,
                        )
                        if date is None:
                            self.display_previous_moods("")
                        else:
                            self.display_previous_moods(date.strftime("%Y-%m-%d"))
                    case 4:
                        content = get_valid_string("Enter new journal entry: ")
                        self.journal(content)
                    case 5:
                        date = get_valid_date(
                            "Enter a valid date (YYYY-MM-DD) or leave blank to view all entries: ",
                            min_date=datetime(1900, 1, 1),
                            max_date=datetime.now(),
                            min_date_message="Date must be after 1900-01-01.",
                            max_date_message="Date cannot be in the future.",
                            allow_blank=True,
                        )
                        if date is None:
                            self.display_journal("")
                        else:
                            self.display_journal(date.strftime("%Y-%m-%d"))
                    case 6:
                        keyword = input("Enter keyword to search for exercises: ")
                        self.search_exercises(keyword)

                    case 7:
                        # if statement here since case 7 would be appointments if
                        # the patient had a clinician. Otherwise it would be log out.
                        if self.clinician_id:
                            appointment_options = [
                                "Book Appointment",
                                "View Appointments",
                                "Cancel Appointment",
                                "Exit appointments",
                            ]
                            selected_choice = display_choice(
                                "Please select an option:", appointment_options
                            )

                            # Options within appointments option in patient menu.
                            match selected_choice:
                                case 1:
                                    # Book Appointment
                                    request_appointment(
                                        self.database,
                                        self.user_id,
                                        self.clinician_id,
                                    )
                                case 2:
                                    # View Appointments
                                    self.view_appointments()
                                case 3:
                                    # Cancel appointment
                                    self.view_appointments()
                                    appointment_id = int(
                                        input("Enter appointment ID to cancel: ")
                                    )
                                    cancel_appointment(self.database, appointment_id)
                                case 4:
                                    # Setting action to exit back to main menu so that
                                    # exit appointments does not lead to the options
                                    # Retry the same action or go back to main menu.
                                    action = "Exit back to main menu"

                # if the previous step was not exit appointments from appointments
                # option, we show the option to retry the same action.
                # Action variables allow choice of which methods/ options can lead
                # to retrying that same method and which option cannot. e.g.
                # if re-reading journal entries is something we do not want an option
                # to redo the same action, we just put action = "Exit back to main menu"
                # over there.
                if action != "Exit back to main menu":
                    next_step = display_choice(
                        "Would you like to:",
                        ["Retry the same action", "Go back to the main menu"],
                        choice_str="Your selection: ",
                    )

                    # So if the users choose option 1, acting_on_choice recursive
                    # function is called on again. And you keep going back to that case
                    # and method you were using before.
                    # If next_step == 2, there is nothing to do since the function
                    # just completes and you return to while true loop and see main menu.

                    if next_step == 1:
                        acting_on_choice(choice)

            # Matching choices here outside of the acting on choice function
            # if the choice is to logout or quit.
            match choice:
                case 7:
                    # Option 7 is appointments if there is a clinician. This is already
                    # put in place in acting on choice function.

                    # If there is no clinician, option 7 is logout
                    if not self.clinician_id:
                        clear_terminal()
                        return True
                case 8:
                    # If there is a clinician, option 8 is logout.
                    if self.clinician_id:
                        clear_terminal()
                        return True

                    # If there is no clinician, option 8 is quit.
                    if not self.clinician_id:
                        clear_terminal()
                        print("Thanks for using Breeze! Goodbye!")
                        return False
                case 9:
                    # Option only exists if there is a clinicin. Option in such
                    # case is to quit.
                    clear_terminal()
                    print("Thanks for using Breeze! Goodbye!")
                    return False

            # Calling upon acting_on_choice function for patient to do different
            # methods when they have chosen an option from the main menu.
            acting_on_choice(choice)
