from modules.user import User


class Admin(User):
    def register_patient(self, Patient, Practitioner):
        # This will need to update attributes for both patient and practitioner
        pass

    def view_info(self, User):
        # Displays all relevant info for a specific user
        # Q - Does this count as a 'summary'?
        pass

    def disable_user(self, User):
        # Disables the user - how will this be implemented?
        # Store as an attribute on the user itself?
        # NB - add checks that these methods can only be applied to patients 
        # and practitioners
        pass

    def flow(self) -> bool:
        print("Hello Admin")
        return False
