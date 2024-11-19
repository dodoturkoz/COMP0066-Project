from database.setup import Database
from modules.user import User
from modules.patient import Patient
from datetime import datetime


class Clinician(User):
    
    def __init__(
        self,
        database: Database,
        user_id: str,
        username: str,
        name: str,
        email: str,
        is_active: bool,
        *args,
        **kwargs,
    ):
        super().__init__(
            database, user_id, username, name, email, is_active, *args, **kwargs
        )

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
        """

        # Option to approve/reject confirmed appointments?

        cur = self.database.cursor
        appointments = cur.execute(f"""
            SELECT * 
            FROM Appointments 
            WHERE clinician_id = {self.user_id}""").fetchall()

        for appointment in appointments:
            patient_name = cur.execute(f"""
            SELECT name 
            FROM USERS 
            WHERE user_id = {appointment["user_id"]}""").fetchone()
            print(f"""{appointment["date"].strftime('%a %d %b %Y, %I:%M%p')} - {patient_name} - {'Confirmed' if appointment["is_confirmed"] else 'Not Confirmed'}""")

        self.database.close()

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
            print(f"\nHello, {self.name}!\n")
            selection = input(
                "What would you like to do?\n"
                "[1] Calendar\n"  # Calendar view
                "[2] Your Patients\n"  # Dashboard of all patients
                "[3] Outstanding Case Summaries\n"
                "[4] Referrals\n"  # Clinician could assign and book here
                "[5] Quit\n"
            )

            if int(selection) not in [1, 2, 3, 4, 5]:
                print("Invalid selection")
                continue
            if int(selection) == 5:
                return False
            if int(selection) == 1:
                self.view_calendar()
