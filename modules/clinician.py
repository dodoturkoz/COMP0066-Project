from modules.user import User
from modules.patient import Patient
from modules.utilities.display import clear_terminal, display_choice, wait_terminal
from datetime import datetime
import sqlite3
from database.setup import diagnoses


class Clinician(User):
    MODIFIABLE_ATTRIBUTES = ["username", "email", "password"]

    def view_calendar(self):
        """
        This allows the clinician to view all their past and
        upcoming appointments.
        """
        # Importing here to avoid circular imports
        from modules.appointments import (
            get_appointments,
            display_appointment_options,
        )

        clear_terminal()
        appointments = get_appointments(self)

        if not appointments:
            print("You have no registered appointments.")
        else:

            view_options = ["All", "Past", "Upcoming"]
            view = display_choice(
                "Which appointments would you like to view?", view_options
            )

            # Show all appointments
            if view == 1:
                display_appointment_options(self, appointments)

            # Show past appointments
            elif view == 2:
                display_appointment_options(
                    self,
                    list(filter(lambda app: app["date"] < datetime.now(), appointments)),
                )

            # Show upcoming appointments
            elif view == 3:
                display_appointment_options(
                    self,
                    list(filter(lambda app: app["date"] >= datetime.now(), appointments)),
                )

        wait_terminal()

    def view_requested_appointments(self):
        """This allows the clinician to view all appointments that have been
        requested but not confirmed yet, and gives the option to confirm or
        reject them"""
        # Importing here to avoid circular imports
        from modules.appointments import get_appointments

        clear_terminal()
        appointments = get_appointments(self)
        unconfirmed_appointments = []
        choice_strings = []

        # Find any unconfirmed appointments and store them in the array
        # Add a string for each appointment to the choice_strings array
        # Q: Should this display past appointments that were unconfirmed? Should those exist at all?
        if appointments:
            for appointment in appointments:
                if not appointment["is_confirmed"]:
                    unconfirmed_appointments.append(appointment)
                    choice_strings.append(
                        f"{appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
                        + f" - {appointment['first_name']} {appointment['surname']}"
                    )
            choice_strings.append("Exit")

            while unconfirmed_appointments:
                # Let user choose an appointment
                confirm_choice = display_choice(
                    "Here are your unconfirmed appointments:",
                    choice_strings,
                    f"Would you like to confirm or reject any appointment? Please choose from the following options {[*range(1, len(unconfirmed_appointments) + 2)]}: ",
                )

                if confirm_choice == len(unconfirmed_appointments) + 1:
                    return False
                else:
                    options = ["Confirm", "Reject", "Go Back"]
                    accept_or_reject = display_choice(
                        f"You have selected {choice_strings[confirm_choice - 1]} - would you like to confirm or reject the appointment?",
                        options,
                    )

                    # Confirm the appointment
                    if accept_or_reject == 1:
                        accepted_appointment = unconfirmed_appointments[
                            confirm_choice - 1
                        ]

                        try:
                            self.database.cursor.execute(
                                """
                                UPDATE Appointments
                                SET is_confirmed = 1
                                WHERE appointment_id = ?""",
                                [accepted_appointment["appointment_id"]],
                            )
                            self.database.connection.commit()
                            print(
                                "The appointment has been confirmed. An email with full details will be sent to you and the patient."
                            )

                            # Remove the appointment from the list so it is not displayed to the user again
                            unconfirmed_appointments.remove(accepted_appointment)

                            # Need to implement email

                        except sqlite3.IntegrityError as e:
                            print(f"Failed to confirm appointment: {e}")
                            return False

                        next_action = display_choice(
                            "What would you like to do next?",
                            ["Accept/Reject another appointment", "Exit"],
                        )
                        if next_action == 1:
                            continue
                        else:
                            return True

                    # Delete the appointment
                    # TO-DO: Change the table so that it isn't deleted in the system, set as cancelled
                    elif accept_or_reject == 2:
                        rejected_appointment = unconfirmed_appointments[
                            confirm_choice - 1
                        ]
                        try:
                            self.database.cursor.execute(
                                """
                                DELETE FROM Appointments
                                WHERE appointment_id = ?""",
                                [rejected_appointment["appointment_id"]],
                            )
                            self.database.connection.commit()
                            print(
                                "The appointment has been rejected. A confirmation email will be sent to you and the patient."
                            )

                            # Remove the appointment from the list so it is not displayed to the user again
                            unconfirmed_appointments.remove(rejected_appointment)

                            # Need to implement email

                        except sqlite3.IntegrityError as e:
                            print(f"Failed to confirm appointment: {e}")
                            return False

                        next_action = display_choice(
                            "What would you like to do next?",
                            ["Accept/Reject another appointment", "Exit"],
                        )
                        if next_action == 1:
                            continue
                        else:
                            return True

                    elif accept_or_reject == 3:
                        continue

            if not unconfirmed_appointments:
                print("You have no unconfirmed appointments.")
        else:
            print("There are no requested appointments.")
        wait_terminal()

    def get_all_patients(self):
        try:
            return self.database.cursor.execute(
                """SELECT * 
                FROM Patients
                INNER JOIN Users ON Patients.user_id = Users.user_id
                WHERE clinician_id = ?""",
                [self.user_id],
            ).fetchall()
        except Exception as e:
            print(f"Error: {e}")

    def get_all_patients_by_diagnosis(self, diagnosis: str):
        try:
            return self.database.cursor.execute(
                """SELECT * 
                FROM Patients
                INNER JOIN Users ON Patients.user_id = Users.user_id
                WHERE clinician_id = ? AND diagnosis = ?""",
                [self.user_id, diagnosis],
            ).fetchall()
        except Exception as e:
            print(f"Error: {e}")

    def edit_patient_info(self, patient: Patient):
        """Edit patient information

        WORK IN PROGRESS! -> User obj has no MODIFIABLE ATTRIBUTES
        """

        while True:
            edit_choice = display_choice(
                "What would you like to edit?",
                ["First Name", "Surname", "Diagnosis", "Exit"],
                "Please choose from the above options: ",
            )
            if edit_choice == 1:
                new_first_name = input("Please enter the new first name: ")
                patient.edit_info("first_name", new_first_name)
            if edit_choice == 2:
                new_surname = input("Please enter the new surname: ")
                patient.edit_info("surname", new_surname)
            if edit_choice == 3:
                new_diagnosis = input("Please enter the new diagnosis: ")
                patient.edit_info("diagnosis", new_diagnosis)
            if edit_choice == 4:
                return False

    def view_dashboard(self):
        """View the dashboard.

        All methods used are declared as class methods to allow for other classes to access them.
        """
        clear_terminal()
        dashboard_home_choice = display_choice(
            "Welcome to your dashboard. Where would you like to go?",
            ["View All", "Filter By Diagnosis", "Exit"],
        )
        if dashboard_home_choice == 1:
            clear_terminal()
            patients = self.get_all_patients()
            print("Here are all your patients:")
            for patient in patients:
                print(
                    f"ID: {patient['user_id']} - {patient['first_name']} {patient['surname']} - {patient['diagnosis']}"
                )
            decision = input(
                "Would you like to edit any patient's information? (Y/N): "
            )
            if decision == "Y":
                patient_id = int(input("Please enter the patient's ID: "))
                patient_details = self.database.cursor.execute(
                    """
                    SELECT * 
                    FROM Patients
                    INNER JOIN Users ON Patients.user_id = Users.user_id
                    WHERE Patients.user_id = ?""",
                    [patient_id],
                ).fetchone()
                patient = Patient(self.database, *patient_details)
                self.edit_patient_info(patient)
                clear_terminal()
                return False
            if decision == "N":
                wait_terminal()

        if dashboard_home_choice == 2:
            clear_terminal()
            # Filter by diagnosis
            diagnosis = display_choice(
                "Please enter the diagnosis you would like to filter by: ", diagnoses
            )
            patients = self.get_all_patients_by_diagnosis(diagnosis)
            print(f"Here are all your patients with the diagnosis {diagnosis}:")
            for patient in patients:
                print(
                    f"ID: {patient['user_id']} - {patient['first_name']} {patient['surname']} - {patient['diagnosis']}"
                )
            wait_terminal()
        if dashboard_home_choice == 3:
            # Edit patient info
            clear_terminal()
            return False

    def flow(self) -> bool:
        """Controls flow of the program from the clinician class

        The program stays within the while loop until a condition is met that
        breaks the flow. We return to False to indicate to Main.py that our User
        has quit.
        """
        while True:
            clear_terminal()
            print(f"Hello, {self.first_name} {self.surname}!")

            choices = [
                "Calendar",
                "Your Patient Dashboard",
                "View Requested Appointments",
                "Quit",
            ]
            selection = display_choice("What would you like to do?", choices)

            if selection == 1:
                self.view_calendar()
            if selection == 2:
                self.view_dashboard()
            if selection == 3:
                self.view_requested_appointments()
            if selection == 4:
                clear_terminal()
                print("Thanks for using Breeze!")
                return False
