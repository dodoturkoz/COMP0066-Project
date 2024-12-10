import sqlite3
from datetime import datetime

from database.setup import diagnoses
from modules.appointments import (
    get_clinician_appointments,
    get_unconfirmed_clinician_appointments,
    print_appointment,
)
from modules.patient import Patient
from modules.user import User
from modules.utilities.display_utils import (
    clear_terminal,
    display_choice,
    wait_terminal,
)
from modules.utilities.input_utils import get_valid_string, get_valid_yes_or_no
from modules.utilities.send_email import send_email


class Clinician(User):
    def __init__(self, database, **kwargs):
        super().__init__(database, **kwargs)
        self.should_logout = False

    def flow(self) -> bool:
        """Controls flow of the program from the clinician class

        The program stays within the while loop until a condition is met that
        breaks the flow. We return to False to indicate to Main.py that our User
        has quit.
        """

        while True:
            if self.should_logout:
                return True
            clear_terminal()
            print(f"Hello, {self.first_name} {self.surname}!")
            self.print_notifications()
            choices = [
                "Calendar",
                "Your Patient Dashboard",
                "View Requested Appointments",
            ]
            selection = display_choice(
                "What would you like to do?",
                choices,
                "Please choose from the above options: ",
                enable_zero_quit=True,
                zero_option_message="Log Out",
            )

            if selection == 1:
                self.view_calendar()
            if selection == 2:
                self.flow_patient_dashboard()
            if selection == 3:
                self.view_requested_appointments()
            if not selection:
                self.should_logout = True
                clear_terminal()
                return True

                # return True because flow() logs out when True is returned

    def flow_patient_dashboard(self):
        """View the dashboard.

        All methods used are declared as class methods to allow for other classes to access them.
        """
        if self.should_logout:
            return True

        clear_terminal()
        choice = display_choice(
            "Welcome to your dashboard. Where would you like to go?",
            ["View All", "Filter By Diagnosis"],
            enable_zero_quit=True,
            zero_option_callback=self.flow,
            zero_option_message="Return to main menu",
        )

        if choice == 1:
            self.flow_patient_summary()

        if choice == 2:
            self.flow_filtered_diagnosis_list()

        # Return to main menu
        if not choice:
            return False

    def flow_edit_patient_info_screen(self, patient: Patient):
        """Edit patient information screen"""
        if self.should_logout:
            return True
        clear_terminal()

        choice = display_choice(
            f"Your patient is {patient.first_name} {patient.surname}. Diagnosis: {patient.diagnosis}. What would you like to do?",
            [
                "Edit Diagnosis",
            ],
            "Please choose from the above options: ",
            enable_zero_quit=True,
            zero_option_callback=self.flow_patient_summary,
            zero_option_message="Return to patient list",
        )

        # Edit Diagnosis
        if choice == 1:
            clear_terminal()
            self.flow_choose_from_list_and_update_diagnosis(patient)
            # wait_terminal(
            #     "Press enter to continue",
            #     redirect_function=lambda: self.flow_edit_patient_info_screen(patient),
            # )
        if not choice:
            return False

    def flow_filtered_diagnosis_list(self):
        if self.should_logout:
            return True
        patients: list[Patient] = self.get_all_patients()
        clear_terminal()

        choice: int = display_choice(
            "Please enter the diagnosis you would like to filter by: ",
            diagnoses,
            enable_zero_quit=True,
            zero_option_callback=self.flow_patient_dashboard,
            zero_option_message="Return to the dashboard",
        )

        if not choice:
            return False

        clear_terminal()
        self.print_filtered_patients_list_by_diagnosis(choice, patients)
        ###TO DO -> Select patient from this screen
        wait_terminal()

    def flow_patient_summary(self):
        if self.should_logout:
            return True
        patients: list[Patient] = self.get_all_patients()
        clear_terminal()

        patient_strings: list[str] = self.create_pretty_patient_list(patients)
        selected = display_choice(
            "Choose your patient:",
            [*patient_strings],
            "Choose a patient: ",
            enable_zero_quit=True,
            zero_option_callback=self.flow_patient_dashboard,
        )
        if not selected:
            return False

        return self.flow_edit_patient_info_screen(patients[selected - 1])

    def flow_choose_from_list_and_update_diagnosis(self, patient: Patient):
        """Displays a list of diagnoses and allows the user to choose one"""
        if self.should_logout:
            return True

        try:
            choice = display_choice(
                f"Please choose a new diagnosis for {patient.first_name} {patient.surname}. Current Diagnosis: {patient.diagnosis}",
                diagnoses,
                enable_zero_quit=True,
            )

            if not choice:
                return False

            diagnosis = diagnoses[choice - 1]
            patient.edit_info(
                "diagnosis", diagnosis, f"Diagnosis updated to {diagnosis}."
            )
            wait_terminal(
                "Press enter to return to patient overview.",
                redirect_function=lambda: self.flow_edit_patient_info_screen(patient),
            )

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def view_notes(self, appointment: dict):
        """Print out clinician and patient notes for a given appointment"""
        if appointment["clinician_notes"]:
            print("\nYour notes:")
            print(appointment["clinician_notes"])
        if appointment["patient_notes"]:
            print("\nPatient notes:")
            print(appointment["patient_notes"] + "\n")

    def add_notes(self, appointment: dict):
        """Used to add clinician notes for a given appointment"""
        clear_terminal()
        if appointment["clinician_notes"]:
            if get_valid_yes_or_no(
                "There are already notes stored for this appointment. Would you like to edit them? (Y/N) "
            ):
                self.edit_notes(appointment)
        else:
            note = (
                get_valid_string("Please enter your notes for this appointment:")
                + f" [{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}]"
            )

            try:
                self.database.cursor.execute(
                    """
                    UPDATE Appointments
                    SET clinician_notes = ?
                    WHERE appointment_id = ?""",
                    [note, appointment["appointment_id"]],
                )
                self.database.connection.commit()
                print(f"Your notes were stored as:\n{note}")
                wait_terminal()

            except sqlite3.IntegrityError as e:
                print(f"Failed to add note: {e}")

    def edit_notes(self, appointment: dict):
        """Used to edit clinician notes for a given appointment"""
        clear_terminal()
        current_notes = appointment["clinician_notes"]
        print("Here are your previously saved notes for the appointment:")
        print(current_notes)

        updated_notes = (
            current_notes
            + "\n"
            + (
                get_valid_string("Please enter your new notes for this appointment: ")
                + f" [{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}]"
            )
        )

        try:
            self.database.cursor.execute(
                """
                UPDATE Appointments
                SET clinician_notes = ?
                WHERE appointment_id = ?""",
                [updated_notes, appointment["appointment_id"]],
            )
            self.database.connection.commit()
            clear_terminal()
            print(f"Your notes were stored as:\n{updated_notes}")
            wait_terminal()
        except sqlite3.IntegrityError as e:
            print(f"Failed to add note: {e}")

    def print_notifications(self):
        """Checks if the clinician has requested appointments, or past appointments
        without notes, to display as notifications on the main menu"""
        requested_appointments = get_unconfirmed_clinician_appointments(
            self.database, self.user_id
        )
        appointments_without_notes = self.get_all_appointments_without_notes()

        if requested_appointments:
            if len(requested_appointments) == 1:
                print("You have\033[31m 1 requested appointment\033[0m to review.")
            else:
                print(
                    f"You have\033[31m {len(requested_appointments)} requested appointments\033[0m to review."
                )

        if appointments_without_notes:
            if len(appointments_without_notes) == 1:
                print("You have 1 previous appointment to add notes for.")
            else:
                print(
                    f"There are {len(appointments_without_notes)} previous appointments to add notes for."
                )

    def display_appointment_options(self, appointments: list):
        """This function presents options to the clinician based on the
        list of appointments passed into it."""
        clear_terminal()
        appointment_strings = []

        # Loop through the appointments, printing them for the user and saving a string
        # for each in appointment_strings
        for appointment in appointments:
            print_appointment(appointment)
            appointment_strings.append(
                f"{appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
                + f" - {appointment['first_name']} {appointment['surname']} - "
                + f"{appointment['status']}"
            )

        # Offer choice to the user
        options = [
            "View appointment notes",
            "Add notes to an appointment",
            "Confirm/Reject Appointments",
        ]
        next = display_choice(
            "What would you like to do now?",
            options,
            enable_zero_quit=True,
            zero_option_message="Return to appointments overview",
        )
        if next == 0:
            return self.view_calendar()

        # View appointment notes
        if next == 1:
            # If there is only one appointment, select that - otherwise offer a choice
            if len(appointments) > 1:
                clear_terminal()
                selected = display_choice(
                    "Please choose an appointment to view",
                    appointment_strings,
                    enable_zero_quit=True,
                    zero_option_message="Back to appointments",
                )
                if selected == 0:
                    return self.display_appointment_options(appointments)
                selected_appointment = appointments[selected - 1]
            else:
                selected_appointment = appointments[0]

            # Display the appointment notes
            self.view_notes(selected_appointment)

            # If notes already exist, offer the option to edit
            if selected_appointment["clinician_notes"]:
                if get_valid_yes_or_no(
                    "Would you like to edit your notes for this appointment? (Y/N) "
                ):
                    self.edit_notes(selected_appointment)
            # If not, offer the option to add notes
            elif get_valid_yes_or_no(
                "Would you like to add notes to this appointment? (Y/N) "
            ):
                self.add_notes(selected_appointment)

        # Add notes
        elif next == 2:
            # If there is only one appointment, select that - otherwise offer a choice
            if len(appointments) > 1:
                clear_terminal()
                selected = display_choice(
                    "Please choose an appointment to add notes to",
                    appointment_strings,
                    enable_zero_quit=True,
                    zero_option_message="Back to appointments",
                )
                if selected == 0:
                    return self.display_appointment_options(appointments)
                selected_appointment = appointments[selected - 1]
            else:
                selected_appointment = appointments[0]

            self.add_notes(selected_appointment)

        # Confirm/Reject appointments
        elif next == 3:
            self.view_requested_appointments()

    def get_all_appointments_without_notes(self) -> list:
        """Returns all the clinician's past appointments that have no notes recorded"""

        # Get all appointments for this clinician
        appointments = get_clinician_appointments(self.database, self.user_id)

        # Select past appointments without notes and return them in a list
        return [
            appointment
            for appointment in appointments
            if not appointment["clinician_notes"]
            and appointment["date"] < datetime.now()
        ]

    def view_calendar(self):
        """
        This allows the clinician to view all their past and
        upcoming appointments.
        """

        clear_terminal()
        # Get all appointments for this clinician
        appointments = get_clinician_appointments(self.database, self.user_id)

        if not appointments:
            print("You have no registered appointments.")
        else:
            # Offer a choice of different sets of appointments, grouped by time
            view_options = ["All", "Past", "Upcoming", "Past appointments without notes"]
            view = display_choice(
                "Which appointments would you like to view?",
                view_options,
                enable_zero_quit=True,
                zero_option_message="Return to Main Menu",
            )

            # Show all appointments
            if view == 1:
                self.display_appointment_options(appointments)

            # Show past appointments
            elif view == 2:
                self.display_appointment_options(
                    list(
                        filter(lambda app: app["date"] < datetime.now(), appointments)
                    ),
                )

            # Show upcoming appointments
            elif view == 3:
                self.display_appointment_options(
                    list(
                        filter(lambda app: app["date"] >= datetime.now(), appointments)
                    ),
                )

            # Show past appointments without notes
            elif view == 4:
                self.display_appointment_options(self.get_all_appointments_without_notes())

    def view_requested_appointments(self):
        """This allows the clinician to view all appointments that have been
        requested but not confirmed yet, and gives the option to confirm or
        reject them"""

        clear_terminal()
        # Get all unconfirmed appointments for this clinician
        unconfirmed_appointments = get_unconfirmed_clinician_appointments(
            self.database, self.user_id
        )
        choice_strings = []

        # Find any unconfirmed appointments (in the future) and store them in the array
        # Add a string for each appointment to the choice_strings array
        for appointment in unconfirmed_appointments:
            choice_strings.append(
                f"{appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
                + f" - {appointment['first_name']} {appointment['surname']}"
            )

        # If there are unconfirmed appointments, offer choice to the user
        while unconfirmed_appointments:
            # Let user choose an appointment
            confirm_choice = display_choice(
                "Here are your unconfirmed appointments:",
                choice_strings,
                enable_zero_quit=True,
                zero_option_message="Return to Main Menu",
            )

            # If user selects 'Exit', go back to the main menu
            if confirm_choice == 0:
                return False
            else:
                clear_terminal()
                options = ["Confirm", "Reject", "Go Back"]
                accept_or_reject = display_choice(
                    f"You have selected {choice_strings[confirm_choice - 1]} - would you like to confirm or reject the appointment?",
                    options,
                )

                # Confirm the appointment
                if accept_or_reject == 1:
                    accepted_appointment = unconfirmed_appointments[confirm_choice - 1]

                    try:
                        # Set the appointment as confirmed in the DB
                        self.database.cursor.execute(
                            """
                            UPDATE Appointments
                            SET status = "Confirmed"
                            WHERE appointment_id = ?""",
                            [accepted_appointment["appointment_id"]],
                        )
                        self.database.connection.commit()
                        clear_terminal()
                        print(
                            "The appointment has been confirmed. An email with full details will be sent to you and the patient."
                        )

                        # Remove the appointment from the list so it is not displayed to the user again
                        unconfirmed_appointments.remove(accepted_appointment)
                        choice_strings.remove(choice_strings[confirm_choice - 1])

                        # Email messages to send to the client and the clinician
                        clinician_confirmation = f"Your appointment with {appointment["first_name"]} {appointment["surname"]} has been confirmed for {appointment['date'].strftime('%I:%M%p on %A %d %B %Y')}."
                        patient_confirmation = f"Your appointment with {self.first_name} {self.surname} has been confirmed for {appointment['date'].strftime('%I:%M%p on %A %d %B %Y')}."

                        # Email the clinician
                        send_email(
                            self.email,
                            "Appointment confirmed",
                            clinician_confirmation,
                        )

                        # Email the client
                        send_email(
                            appointment["patient_email"],
                            "Appointment confirmed",
                            patient_confirmation,
                        )

                    except sqlite3.IntegrityError as e:
                        print(f"Failed to confirm appointment: {e}")
                        return False

                    # If there are unconfirmed appointments, offer 
                    # option to go back and choose another appointment
                    if unconfirmed_appointments:
                        next_action = display_choice(
                            "What would you like to do next?",
                            ["Accept/Reject another appointment"],
                        enable_zero_quit=True,
                        zero_option_message='Exit'
                        )
                        if next_action == 1:
                            clear_terminal()
                            continue
                        else:
                            return True
                    else:
                        return True

                # Reject the appointment
                elif accept_or_reject == 2:
                    rejected_appointment = unconfirmed_appointments[confirm_choice - 1]
                    try:
                        self.database.cursor.execute(
                            """
                            UPDATE Appointments
                            SET status = "Rejected"
                            WHERE appointment_id = ?""",
                            [rejected_appointment["appointment_id"]],
                        )
                        self.database.connection.commit()
                        clear_terminal()
                        print(
                            "The appointment has been rejected. A notification email will be sent to you and the patient."
                        )

                        # Remove the appointment from the list so it is not displayed to the user again
                        unconfirmed_appointments.remove(rejected_appointment)
                        choice_strings.remove(choice_strings[confirm_choice - 1])

                        # Send emails to the client and the clinician
                        clinician_rejection = f"You have rejected {appointment["first_name"]} {appointment["surname"]}'s request for an appointment on {appointment['date'].strftime('%I:%M%p on %A %d %B %Y')}."
                        patient_rejection = f"Your request for an appointment with {self.first_name} {self.surname} on {appointment['date'].strftime('%I:%M%p on %A %d %B %Y')} has been rejected. Please use the online booking system to choose a different time."

                        # Email the clinician
                        send_email(
                            self.email,
                            "Appointment confirmed",
                            clinician_rejection,
                        )

                        # Email the client
                        send_email(
                            appointment["patient_email"],
                            "Appointment confirmed",
                            patient_rejection,
                        )

                    except sqlite3.IntegrityError as e:
                        print(f"Failed to confirm appointment: {e}")
                        return False

                    # If there are still unconfirmed appointments, offer the choice of
                    # what to do next
                    if unconfirmed_appointments:
                        next_action = display_choice(
                            "What would you like to do next?",
                            ["Accept/Reject another appointment"],
                        enable_zero_quit=True,
                        zero_option_message="Exit",
                        )
                        if next_action == 1:
                            clear_terminal()
                            continue
                        else:
                            return True
                    else:
                        return True

                elif accept_or_reject == 3:
                    continue

        if not unconfirmed_appointments:
            print("You have no unconfirmed appointments.")

        wait_terminal()

    def create_pretty_patient_list(self, patients: list[Patient]) -> list:
        return [
            f"""ID: {patient.user_id} - {patient.first_name} {patient.surname} - {patient.diagnosis} - {patient.mood}"""
            for patient in patients
        ]

    def get_all_patients(self) -> list[Patient]:
        try:
            patients = self.database.cursor.execute(
                """
                SELECT Users.*, Patients.*, 
                (SELECT mood FROM MoodEntries 
                WHERE MoodEntries.user_id = Users.user_id 
                ORDER BY entry_id DESC LIMIT 1) as mood
                FROM Patients
                JOIN Users ON Patients.user_id = Users.user_id 
                LEFT JOIN MoodEntries ON Users.user_id = MoodEntries.user_id
                WHERE Patients.clinician_id = ?
                GROUP BY Users.user_id
            """,
                [self.user_id],
            ).fetchall()

            if not patients:
                print("You have no patients.")
                return []

            patient_list = []
            for patient_data in patients:
                patient = Patient(self.database, **patient_data)
                patient.mood = (
                    patient_data["mood"] if patient_data["mood"] else "None recorded"
                )
                patient_list.append(patient)

            return patient_list

        except Exception as e:
            print(f"Error: {e}")

    def print_filtered_patients_list_by_diagnosis(self, choice: int, patients) -> None:
        """Prints a list of filtered patients"""
        filtered_patients = [
            patient
            for patient in patients
            if patient.diagnosis == diagnoses[choice - 1]
        ]

        for patient in self.create_pretty_patient_list(filtered_patients):
            print(patient)

        if not filtered_patients:
            print("There are no patients with that diagnosis.")
            return False
