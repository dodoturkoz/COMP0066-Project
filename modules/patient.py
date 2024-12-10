import sqlite3
from typing import Optional, Any
from datetime import datetime


from database.setup import Database
from modules.utilities.input_utils import (
    get_user_input_with_limited_choice,
    get_valid_string,
    get_valid_email,
    get_valid_date,
    get_valid_yes_or_no,
)
from modules.utilities.display_utils import (
    display_choice,
    clear_terminal,
    wait_terminal,
)
from modules.appointments import (
    request_appointment,
    cancel_appointment,
    get_patient_appointments,
)
from modules.constants import RELAXATION_RESOURCES, MOODS, SEARCH_OPTIONS
from modules.user import User


class Patient(User):
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

        # fetch additional patient-specific data
        patient_data = database.cursor.execute(
            """
            SELECT emergency_email, date_of_birth, diagnosis, clinician_id
            FROM Patients
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not patient_data:
            raise Exception("Patient data not found for user ID.")

        self.emergency_email = patient_data["emergency_email"]
        self.diagnosis = patient_data["diagnosis"]
        self.clinician_id = patient_data["clinician_id"]
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

    def edit_info(self, attribute: str, value: Any, confirmation: str = None) -> bool:
        if attribute in [
            "clinician_id",
            "diagnosis",
            "emergency_email",
            "date_of_birth",
        ]:
            return self.edit_patient_info(
                attribute, value, success_message=confirmation
            )
        else:
            return super().edit_info(attribute, value, success_message=confirmation)

    def edit_patient_info(
        self, attribute: str, value: Any, success_message: str = None
    ) -> bool:
        """
        Updates attributes fromt the Patients table both in the object
        and in the database, returns the result of the update
        """

        try:
            # First update on the database
            self.database.cursor.execute(
                f"UPDATE Patients SET {attribute} = ? WHERE user_id = ?",
                (value, self.user_id),
            )
            self.database.connection.commit()

            # Then in the object if that particular attribute is stored here
            if hasattr(self, attribute):
                setattr(self, attribute, value)

            if success_message is None:
                print(
                    f"{attribute.replace('_', ' ').capitalize()} updated successfully."
                )
            else:
                print(success_message)

            # Return true as the update was successful
            return True

        # If there is an error with the query
        except sqlite3.OperationalError as e:
            print(
                f"There was an error updating the {attribute.replace('_', ' ').capitalize()}.\n Error: {e}"
            )
            return False

    def edit_self_info(self) -> bool:
        """
        Allows the patient to change their details.
        """
        clear_terminal()
        # TODO: Add option to edit birth date
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
            choice = display_choice(
                "Select an attribute to edit:",
                options,
                enable_zero_quit=True,
                zero_option_message="Go back to main menu",
            )

            if not choice:
                return False

            def update_attribute():
                """
                Requests new value and update patient details. Give option to return
                to main menu or edit personal info main.
                """
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
                        f"Enter the new value for {options[choice - 1]}: ",
                        max_len=25,
                        min_len=0 if attribute == "password" else 1,
                        is_name=True if attribute in ["first_name", "surname"] else False,
                    )

                # Use the parent class's edit_info method for all updates
                success = self.edit_info(attribute, value)

                if success:
                    clear_terminal()
                    print(
                        f"{attribute.replace('_', ' ').capitalize()} updated successfully."
                    )
                    the_step = display_choice(
                        "Would you like to:",
                        ["Go back to editing info"],
                        choice_str="Your selection: ",
                        enable_zero_quit=True,
                        zero_option_message="Go to Main Menu",
                    )

                    if the_step == 1:
                        return 2
                    if the_step == 0:
                        return True
                else:
                    clear_terminal()
                    print(f"Failed to update {options[choice - 1]}. Please try again.")
                    return 2

            selected = update_attribute()
            if selected == 2:
                self.edit_self_info()
            if selected:
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
        clear_terminal()
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
        clear_terminal()
        self.database.cursor.execute(
            "SELECT text, mood FROM MoodEntries WHERE user_id = ? AND DATE(date) = ?",
            (self.user_id, datetime.now().strftime("%Y-%m-%d")),
        )
        entry = self.database.cursor.fetchone()

        if entry:
            print("You already have an entry for today.")
            old_mood = MOODS[str(entry["mood"])]
            show_mood = f"{old_mood['ansi']} {old_mood['description']}\033[00m"
            print(f"Existing entry found:\nMood: {show_mood}\nComment: {entry['text']}")
            choice = display_choice(
                "\nSelect an option:",
                ["Continue to replace old mood entry"],
                enable_zero_quit=True,
                zero_option_message="Go back to main menu to keep old mood entry",
            )

            if not choice:
                return False

        def mood_input():
            """
            Get mood input from the patient using a number or color name.
            """
            clear_terminal()

            print("\nMOOD TRACKER:\n")

            # display mood options
            for num, mood in MOODS.items():
                print(
                    f"{mood['ansi']}[{num}] {mood['description']} [{mood['color']}]\033[00m"
                )
            print("[0] Return back to main menu")
            valid_inputs = {str(num): mood for num, mood in MOODS.items()}
            valid_inputs.update(
                {mood["color"].lower(): mood for mood in MOODS.values()}
            )

            while True:
                mood_choice = get_valid_string(
                    "\nEnter your mood for today (number 6 to 1 or color name)."
                    "\nAlternatively, enter 0 to return to main menu."
                    "\nYour selection: "
                ).lower()
                print(mood_choice)
                if mood_choice == "0":
                    return mood_choice
                elif mood_choice in valid_inputs:
                    selected_mood = valid_inputs[mood_choice]
                    return selected_mood["int"]
                else:
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
        if mood == "0":
            return False
        comment = comment_input()
        clear_terminal()
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
                print(f"\nExisting entry:\nMood: {show_mood}\nComment: {entry['text']}")
                new_mood = MOODS[str(mood)]
                show_new_mood = f"{new_mood['ansi']} {new_mood['description']}\033[00m"
                print(f"\nNew entry:\nMood: {show_new_mood}\nComment: {comment}")
                # Confirm update
                if get_valid_yes_or_no(
                    "Are you sure you want to replace old mood entry for today? (Y/N): "
                ):
                    self.database.cursor.execute(
                        query_update, (comment, mood, self.user_id, today_date)
                    )
                    self.database.connection.commit()
                    print("Mood entry updated successfully.")
                    wait_terminal("Press enter to return to main menu.")
                    return True
                else:
                    print("Mood entry was not updated.")
                    wait_terminal("Press enter to return to main menu.")
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
        clear_terminal()
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
        clear_terminal()

        def searching_exercises(keyword):
            """
            Recursive fuction to search exercises with keyword or if you do not get
            results, choose a given keyword.
            """
            clear_terminal()
            if keyword:
                filtered_resources = [
                    resource
                    for resource in RELAXATION_RESOURCES
                    if keyword.lower() in resource["title"].lower()
                ]
            else:
                filtered_resources = RELAXATION_RESOURCES

            if not filtered_resources:
                print(f"No resources found matching {keyword}.")
                search_decision = display_choice(
                    "Would you like to:",
                    [
                        "Search keywords again with different keyword",
                        "Choose from given keywords",
                    ],
                    choice_str="Your selection: ",
                    enable_zero_quit=True,
                    zero_option_message="Go back to main menu",
                )
                if search_decision == 0:
                    clear_terminal()
                    return False

                elif search_decision == 1:
                    clear_terminal()
                    try_search_again = input(
                        "Enter keyword to search for exercises. "
                        "\nPress enter to see all exercises:"
                    )
                    searching_exercises(try_search_again)
                else:
                    clear_terminal()
                    search_decision = display_choice(
                        "Choose a keyword or go back to main menu:",
                        SEARCH_OPTIONS,
                        choice_str="Your selection: ",
                        enable_zero_quit=True,
                        zero_option_message="Go back to main menu",
                    )
                    if search_decision == 0:
                        clear_terminal()
                        return False

                    else:
                        clear_terminal()
                        search_decision -= 1
                        searching_exercises(SEARCH_OPTIONS[search_decision])

            for resource in filtered_resources:
                print(f"Title: {resource['title']}")
                print(f"Audio File: {resource['audio_file']}")
                print(f"Transcript: {resource['transcript']}\n")

            if filtered_resources:
                do_again = display_choice(
                    "Would you like to:",
                    ["Search exercises again"],
                    choice_str="Your selection: ",
                    enable_zero_quit=True,
                    zero_option_message="Go back to main menu",
                )
                if do_again == 0:
                    clear_terminal()
                    return False
                elif do_again == 1:
                    clear_terminal()
                    searching_exercises(
                        input("Enter keyword to search for exercises: ")
                    )
            else:
                return False

        leave = searching_exercises(keyword)
        if not leave:
            return False

    def view_appointments(self) -> list[dict[str, Any]]:
        """
        Views all appointments for the patient, including their status.
        """

        try:
            raw_appointments = get_patient_appointments(self.database, self.user_id)

            appointments = [
                {
                    "appointment_id": row["appointment_id"],
                    "date": row["date"],
                    "patient_notes": row["patient_notes"],
                    "status": row["status"],
                }
                for row in raw_appointments
            ]

            if appointments:
                print("\nYour Appointments:\n")
                for appointment in appointments:
                    print(f"ID: {appointment['appointment_id']}")
                    print(f"Date: {appointment['date']}")
                    print(f"Your Notes: {appointment['patient_notes']}")
                    print(f"Status: {appointment['status']}")
                    print("-" * 40)
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
            ]

            # Add options based on whether patient has an assigned clinician
            if self.clinician_id:
                options.extend(["Self-Help Exercises", "Appointments"])
            else:
                options.append("Self-Help Exercises")

            choice = display_choice(
                "Please select an option:",
                options,
                enable_zero_quit=True,
                zero_option_message="Log out",
            )

            # Log out if no choice is made.
            if not choice:
                clear_terminal()
                return True

            def acting_on_choice(choice):
                """
                Matches menu choices to their corresponding actions.
                """
                # Recursively handles menu actions. Users can retry the same option
                # or exit back to the main menu.
                action = "Option to redo previous action"
                match choice:
                    case 1:
                        self.edit_self_info()
                    case 2:
                        self.mood_of_the_day()
                        action = "Exit back to main menu"
                    case 3:
                        clear_terminal()

                        def date_options():
                            clear_terminal()
                            selected_option = display_choice(
                                "Would you like to:",
                                ["View all entries", "View a particular date"],
                                choice_str="Your selection: ",
                                enable_zero_quit=True,
                                zero_option_message="Go back to main menu",
                            )
                            if selected_option == 0:
                                return False
                            elif selected_option == 1:
                                clear_terminal()
                                date = ""
                            else:
                                clear_terminal()
                                date = get_valid_date(
                                    "Enter a valid date (DD-MM-YYYY): ",
                                    min_date=datetime(1900, 1, 1),
                                    max_date=datetime.now(),
                                    min_date_message="Date must be after 1900-01-01.",
                                    max_date_message="Date cannot be in the future.",
                                    allow_blank=False,
                                )

                            self.display_previous_moods(
                                date.strftime("%Y-%m-%d") if date else ""
                            )
                            if selected_option == 1:
                                display_choice(
                                    "When you are ready, enter 0:",
                                    [],
                                    choice_str="Your selection: ",
                                    enable_zero_quit=True,
                                    zero_option_message="Go back to main menu",
                                )
                            if selected_option == 2:
                                date_decision = display_choice(
                                    "Would you like to:",
                                    [
                                        "Go to date menu",
                                    ],
                                    choice_str="Your selection: ",
                                    enable_zero_quit=True,
                                    zero_option_message="Go back to main menu",
                                )
                                if date_decision == 1:
                                    date_options()
                                elif date_decision == 0:
                                    return False

                        date_options()
                        action = "Exit back to main menu"
                    case 4:

                        def write():
                            """
                            Add journal entries or go back using 0.
                            """
                            clear_terminal()
                            content = get_valid_string(
                                "Enter new journal entry or 0 to go back:  "
                            )
                            if content == "0":
                                return False
                            else:
                                self.journal(content)
                                decision = display_choice(
                                    "Press 0 when ready to:",
                                    [],
                                    choice_str="Your selection: ",
                                    enable_zero_quit=True,
                                    zero_option_message="Return back to the main menu",
                                )
                                if decision == 0:
                                    return False

                        write()
                        action = "Exit back to main menu"
                    case 5:
                        clear_terminal()

                        def date_options():
                            clear_terminal()
                            selected_option = display_choice(
                                "Would you like to:",
                                ["View all entries", "View a particular date"],
                                choice_str="Your selection: ",
                                enable_zero_quit=True,
                                zero_option_message="Go back to main menu",
                            )
                            if selected_option == 0:
                                return False
                            elif selected_option == 1:
                                clear_terminal()
                                date = ""
                            else:
                                clear_terminal()
                                date = get_valid_date(
                                    "Enter a valid date (DD-MM-YYYY): ",
                                    min_date=datetime(1900, 1, 1),
                                    max_date=datetime.now(),
                                    min_date_message="Date must be after 1900-01-01.",
                                    max_date_message="Date cannot be in the future.",
                                    allow_blank=False,
                                )

                            self.display_journal(
                                date.strftime("%Y-%m-%d") if date else ""
                            )
                            if selected_option == 1:
                                display_choice(
                                    "When you are ready, enter 0:",
                                    [],
                                    choice_str="Your selection: ",
                                    enable_zero_quit=True,
                                    zero_option_message="Go back to main menu",
                                )

                            if selected_option == 2:
                                date_decision = display_choice(
                                    "Would you like to:",
                                    [
                                        "Go to date menu",
                                    ],
                                    choice_str="Your selection: ",
                                    enable_zero_quit=True,
                                    zero_option_message="Go back to main menu",
                                )
                                if date_decision == 1:
                                    date_options()
                                elif date_decision == 0:
                                    return False

                        date_options()
                        action = "Exit back to main menu"
                    case 6:
                        clear_terminal()
                        keyword = input(
                            "Here you can find self-help exercises by the NHS on various topics.\n"
                            "If individual links are broken in the future, you can access all the audio files and their transcripts at:\n"
                            "https://www.cntw.nhs.uk/home/accessible-information/audio/audio-files/\n\n"
                            "Choose an option:\n"
                            "- Enter a keyword to search for exercises.\n"
                            "- Leave blank and press Enter to see all exercises.\n"
                            "- Enter 0 to go back to the main menu.\n\n"
                        )
                        if keyword == "0":
                            return False
                        else:
                            self.search_exercises(keyword)
                        action = "Exit back to main menu"
                    case 7:
                        clear_terminal()
                        appointment_options = [
                            "Book Appointment",
                            "View Appointments",
                            "Cancel Appointment",
                        ]
                        selected_choice = display_choice(
                            "Please select an option:",
                            appointment_options,
                            enable_zero_quit=True,
                        )
                        if not selected_choice:
                            return False

                        # Options within appointments option in patient menu.
                        match selected_choice:
                            case 1:
                                # Book Appointment
                                request_appointment(
                                    self.database, self.user_id, self.clinician_id
                                )
                            case 2:
                                # View Appointments
                                self.view_appointments()
                            case 3:
                                # Cancel appointment
                                my_appointments = self.view_appointments()
                                appointment_id = get_user_input_with_limited_choice(
                                    "Enter appointment ID to cancel: ",
                                    [
                                        appointment["appointment_id"]
                                        for appointment in my_appointments
                                        if appointment["date"] >= datetime.now()
                                    ],
                                    "Invalid appointment ID. Please try again, keeping in mind you can only cancel appointments in the future.",
                                )
                                cancel_appointment(self.database, appointment_id)
                            case 4:
                                action = "Exit back to main menu"

                # Provide option to retry the action unless exiting back to the menu.
                if action != "Exit back to main menu":
                    if choice != 1:
                        next_step = display_choice(
                            "Would you like to:",
                            ["Retry the same action"],
                            choice_str="Your selection: ",
                            enable_zero_quit=True,
                        )
                        if not next_step:
                            return False
                        if next_step == 1:
                            acting_on_choice(choice)

            # Call to process the selected option.
            acting_on_choice(choice)
