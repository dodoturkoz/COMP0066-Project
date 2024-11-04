from modules.user import User


class Clinician(User):
    def view_calendar(self):
        # Display
        pass

    def flow(self) -> bool:
        print("Hello Clinician")
        return False
