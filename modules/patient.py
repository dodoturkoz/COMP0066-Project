from modules.user import User
from datetime import datetime


class Patient(User):
    MODIFIABLE_ATTRIBUTES = ["username", "email", "password"]

    def edit_medical_info(self, attribute: str, value: str) -> bool:
        # Provides interface to change name, email, emergency contact
        # Could this reuse the same method as the Admin edit? With different permissions?
        # Perhaps define on parent (although practitioner doesn't need this)
        # David's Note: changed the name to edit_medical_info to avoid clash with parent
        return self.edit_info(attribute, value)

    def mood_of_the_day(self, mood: str) -> bool:
        # Interface for this
        pass

    def journal(self, content: str) -> bool:
        """
        Creates a journal entry for the patient.
        """
        try:
            self.database.cursor.execute(
                "INSERT INTO Journal (user_id, content, timestamp) VALUES (?, ?, ?)",
                (self.user_id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            self.database.connection.commit()
            print("Journal entry added successfully.")
            return True
        except Exception as e:
            print(f"Error adding journal entry: {e}")
            return False

    def search_exercises(self, keyword: str):
        # Looks up exercises and displays them
        pass

    def book_appointment(self, date: str, time: str) -> int:
        # Display available slots, and select to request one
        # Q: System for appointments? Database?
        pass

    def cancel_appointment(self, appointment_id: int) -> bool:
        # Display, and option to cancel
        pass

    def flow(self):
        """
        Displays the main patient menu and handles the selection of various options.
        """
        print("Hello Patient")
        while True:
            choice = input(
                "Please select an option:\n"
                "1. Edit Medical Info\n"
                "2. Record Mood of the Day\n"
                "3. Add Journal Entry\n"
                "4. Search Exercises\n"
                "5. Book Appointment\n"
                "6. Cancel Appointment\n"
                "7. Log Out\n"
            )
            if choice == "1":
                attribute = input("Enter the attribute to edit (e.g., email): ")
                value = input(f"Enter the new value for {attribute}: ")
                self.edit_medical_info(attribute, value)
            elif choice == "2":
                mood = input("Enter your mood for today: ")
                self.mood_of_the_day(mood)
            elif choice == "3":
                content = input("Write your journal entry: ")
                self.journal(content)
            elif choice == "4":
                keyword = input("Enter keyword to search for exercises: ")
                self.search_exercises(keyword)
            elif choice == "5":
                date = input("Enter appointment date (YYYY-MM-DD): ")
                time = input("Enter appointment time (HH:MM): ")
                self.book_appointment(date, time)
            elif choice == "6":
                appointment_id = int(input("Enter appointment ID to cancel: "))
                self.cancel_appointment(appointment_id)
            elif choice == "7":
                return True
            else:
                print("Invalid choice. Please try again.")
