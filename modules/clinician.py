from database.setup import Database
from modules.user import User
from modules.patient import Patient
from datetime import datetime
from modules.utilities.display import clear_terminal


class Clinician(User):
    def get_available_slots(self, day: datetime) -> list:
        """Used to get all available slots for a clinician on a specified day"""
        pass

    def request_appointment(self, slot: datetime) -> bool:
        """Use to request a specific timeslot"""
        pass

    def view_calendar(self):
        """
        This allows the clinician to view all upcoming appointments,
        showing whether they are confirmed or not.

        Ben I have modified this as the connection was being closed prematurely
        and causing errors on successive calls.
        """

        # Option to approve/reject confirmed appointments?
        clear_terminal()
        cur = self.database.connection
        try:
            appointments = cur.execute(f"""
                SELECT * 
                FROM Appointments 
                WHERE clinician_id = {self.user_id}""").fetchall()
        except Exception as e:
            print(f"Error: {e}")
        if appointments:
            for appointment in appointments:
                patient_name = cur.execute(f"""
                SELECT name 
                FROM USERS 
                WHERE user_id = {appointment["user_id"]}""").fetchone()
                print(
                    f"{appointment["date"].strftime('%a %d %b %Y, %I:%M%p')}"
                    + f" - {patient_name} - "
                    + f"{'Confirmed' if appointment["is_confirmed"] else 'Not Confirmed'}\n"
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
            selection = input(
                "What would you like to do?\n"
                "[1] Calendar\n"  # Calendar view
                "[2] Your Patient Dashboard\n"  # Dashboard of all patients
                "[3] -\n"  # Extras here e.g. link to medical news websites
                "[4] -\n"  # Extras here  - or streamline
                "[5] Quit\n"
            )
            if int(selection) not in [1, 2, 3, 4, 5]:
                print("Invalid selection")
                continue
            if int(selection) == 1:
                self.view_calendar()
            if int(selection) == 2:
                pass
            if int(selection) == 3:
                pass
            if int(selection) == 4:
                pass
            if int(selection) == 5:
                clear_terminal()
                print("Thanks for using Breeze!")
                return False
