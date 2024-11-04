from .user import User


class Patient(User):
    def edit_medical_info(self):
        # Provides interface to change name, email, emergency contact
        # Could this reuse the same method as the Admin edit? With different permissions?
        # Perhaps define on parent (although practitioner doesn't need this)
        # David's Note: changed the name to edit_medical_info to avoid clash with parent
        pass

    def mood_of_the_day(self):
        # Interface for this
        pass

    def journal(self):
        # create journal entries
        pass

    def search_exercises(self, keyword):
        # Looks up exercises and displays them
        pass

    def book_appointment(self):
        # Display available slots, and select to request one
        # Q: System for appointments? Database?
        pass

    def cancel_appointment(self):
        # Display, and option to cancel
        pass

    def flow(self):
        print("Hello Patient")
        return False
