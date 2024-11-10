from modules.user import User
from modules.patient import Patient


class Clinician(User):
    
    def view_calendar(self):
        # Display calendar with all appointments, as well as requested appointments
        # Option to approve/reject confirmed appointments?
        pass

    def view_requested_appointments(self):
        # Show all requested appointments, with option to approve/reject
        pass

    def edit_patient_info(self, patient: Patient):
        # Provide interface to add info to a patient's record - condition, extra notes, etc.
        pass

    def view_dashboard(self):
        # Display summary of all patients' data + chart per patient with mood tracking
        pass

    def flow(self) -> bool:
        '''Controls flow of the program from the clinician class

        The program stays within the while loop until a condition is met that
        breaks the flow. We return to False to indicate to Main.py that our User
        has quit.
        '''
        run = True
        while run:
            print(f"\nHello, {self.username}!\n")
            selection = input("""What would you like to do?\n 
[1] Today's Appointments\n
[2] Recent Patients\n
[3] Outstanding Case Summaries\n
[4] Incoming Referrals\n
[5] Quit\n"""
            )

            if int(selection) not in [1,2,3,4,5]:
                print("Invalid selection")
                continue
            if int(selection) == 5:
                return False