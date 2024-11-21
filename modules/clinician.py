from modules.user import User
from modules.patient import Patient
from datetime import datetime
from modules.utilities.display import clear_terminal
import sqlite3


class Clinician(User):
    def get_appointments(self) -> list:
        """Find all appointments registered for the clinician, including unconfirmed ones"""
        try:
            appointments = self.database.cursor.execute(
                """
                SELECT * 
                FROM Appointments 
                WHERE clinician_id = ?""",
                [self.user_id],
            ).fetchall()
            return appointments
        except Exception as e:
            print(f"Error: {e}")

    def get_available_slots(self, day: datetime) -> list:
        """Used to get all available slots for a clinician on a specified day"""
        appointments = self.get_appointments()
        possible_hours = [9, 10, 11, 12, 14, 15, 16]
        available_slots = []

        for hour in possible_hours:
            if datetime(day.year, day.month, day.day, hour, 0) not in [
                appointment["date"] for appointment in appointments
            ]:
                available_slots.append(datetime(day.year, day.month, day.day, hour, 0))

        return available_slots

    def request_appointment(self, patient: Patient) -> bool:
        """Allows the patient to request an appointment with their clinician"""

        # Loop to take a requested date from the user
        def choose_date() -> datetime:
            while True:
                try:
                    date_string = input(
                        "Please enter a date when you would like to see your clinician (DD/MM/YY):"
                    )

                    requested_date = datetime.strptime(date_string, "%d/%m/%y")
                    if requested_date < datetime.today():
                        print("You cannot book an appointment before the current date.")
                    else:
                        return requested_date
                except ValueError:
                    print(
                        "You have entered an invalid date. Please enter in the format DD/MM/YY."
                    )

        # Loop to select a valid time from the available slots
        def choose_slot(slots: list) -> datetime:
            print("Here are the available times on that day:")
            print(f"[{i + 1}] {slot.strftime('%H:%M')}" for i, slot in enumerate(slots))

            while True:
                selection = int(
                    input(
                        f"Which time would you like to request? [{range(1, len(slots))}] "
                    )
                )

                if selection not in list(range(1, len(slots))):
                    print(f"Please select from options [{range(1, len(slots))}]")
                    continue
                else:
                    return slots[selection - 1]

        # Check that the patient is registered with this clinician
        self.database.cursor.execute(
            "SELECT clinician_id FROM Patients WHERE user_id = ?", [patient.user_id]
        )
        clinician_id = self.database.cursor.fetchone()

        if clinician_id != self.user_id:
            print(
                "You are not registered with this clinician. Please contact the admin."
            )
            return False

        # Take a description from the user - Phil can you advise on correct language here?
        description = input(
            "Please describe why you would like to see your clinician (optional):"
        )

        while True:
            # Take in a requested date
            requested_date = choose_date()

            # Get available slots on that day
            slots = self.get_available_slots(requested_date)

            if not slots:
                choose_again = input(
                    "Sorry, your clinician has no availability on that day - would you like to choose another day? (Y/N)"
                )
                if choose_again == "N":
                    return False
                else:
                    continue

            chosen_time = choose_slot(slots)
            break

        try:
            self.database.cursor.execute(
                """
                    INSERT INTO Appointments (user_id, clinician_id, date, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                (
                    patient.user_id,
                    self.user_id,
                    chosen_time,
                    description,
                ),
            )
            self.database.connection.commit()
            print("Your appointment has been requested. You'll receive an email once your clinician has confirmed it.")
            return True
        except sqlite3.IntegrityError as e:
            print(f"Failed to book appointment: {e}")
            return False

    def view_calendar(self):
        """
        This allows the clinician to view all upcoming appointments,
        showing whether they are confirmed or not.
        """

        # Option to approve/reject confirmed appointments?
        clear_terminal()
        appointments = self.get_appointments()
        if appointments:
            for appointment in appointments:
                patient_name = self.database.cursor.execute(
                    """
                SELECT name 
                FROM USERS 
                WHERE user_id = ?""",
                    [appointment["user_id"]],
                ).fetchone()
                print(
                    f"{appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
                    + f" - {patient_name} - "
                    + f"{'Confirmed' if appointment['is_confirmed'] else 'Not Confirmed'}\n"
                )
        else:
            print("There are no appointments.")
        while True:
            if input("Press enter to return to the dashboard") == "":
                clear_terminal()
                return True

    def view_requested_appointments(self):
        # Show all requested appointments, with option to approve/reject
        pass

    def edit_patient_info(self, patient: Patient):
        # Provide interface to add info to a patient's record - condition,
        # extra notes, etc.
        # Does this make more sense as
        # View Patients -> Select patient -> Edit info ?
        pass

    def view_dashboard(self):
        # Display summary of all patients' data + chart per patient
        # with mood tracking
        pass

    def flow(self) -> bool:
        """Controls flow of the program from the clinician class

        The program stays within the while loop until a condition is met that
        breaks the flow. We return to False to indicate to Main.py that our User
        has quit.
        """
        run = True
        while run:
            clear_terminal()
            print(f"Hello, {self.name}!")
            # Ben I have preserved number five as quit for now -> appreciate it
            # looks a little odd.
            try:
                selection = input(
                    "What would you like to do?\n"
                    "[1] Calendar\n"  # Calendar view
                    "[2] Your Patient Dashboard\n"  # Dashboard of all patients
                    "[3] -\n"  # Extras here e.g. link to medical news websites
                    "[4] -\n"  # Extras here  - or streamline
                    "[5] Quit\n"
                )
            except Exception as e:
                if selection not in ["1", "2", "3", "4", "5"]:
                    pass
                print("Invalid selection:" + e)

            if selection == "1":
                self.view_calendar()
            if selection == "2":
                pass
            if selection == "3":
                pass
            if selection == "4":
                pass
            if selection == "5":
                clear_terminal()
                print("Thanks for using Breeze!")
                return False
