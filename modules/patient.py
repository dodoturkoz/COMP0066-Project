import sqlite3
from typing import Optional
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

    def display_journal(self, date: Optional[str] = None) -> list[dict[str, str]]:
        """
        Displays patient's journal entries, optionally filtering by a specific date.
        """
        query = "SELECT timestamp, content FROM Journal WHERE user_id = ?"
        params = [self.user_id]

        if date:
            query += " AND DATE(timestamp) = ?"
            params.append(date)

        query += " ORDER BY timestamp ASC"

        try:
            self.database.cursor.execute(query, tuple(params))
            entries = [
                {"timestamp": row["timestamp"], "content": row["content"]}
                for row in self.database.cursor.fetchall()
            ]

            if entries:
                print(f"\nJournal Entries for {date if date else 'all dates'}:\n")
                for entry in entries:
                    print(f"Timestamp: {entry['timestamp']}")
                    print(f"Content: {entry['content']}\n")
            else:
                print("No journal entries found for the specified date.")

            return entries

        except sqlite3.OperationalError as e:
            print(f"Database error occurred: {e}")
            return []

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
                "3. Read Journal Entries\n"
                "4. Add Journal Entry\n"
                "5. Search Exercises\n"
                "6. Book Appointment\n"
                "7. Cancel Appointment\n"
                "8. Log Out\n"
            )
            if choice == "1":
                attribute = input("Enter the attribute to edit (e.g., email): ")
                value = input(f"Enter the new value for {attribute}: ")
                self.edit_medical_info(attribute, value)
            elif choice == "2":
                mood = input("Enter your mood for today: ")
                self.mood_of_the_day(mood)
            elif choice == "3":
                date = input(
                    "Enter a date in YYYY-MM-DD format or leave blank to view all previous entries: "
                )
                self.display_journal(date)
            elif choice == "4":
                content = input("Enter new journal entry: ")
                self.journal(content)
            elif choice == "5":
                keyword = input("Enter keyword to search for exercises: ")
                self.search_exercises(keyword)
            elif choice == "6":
                date = input("Enter appointment date (YYYY-MM-DD): ")
                time = input("Enter appointment time (HH:MM): ")
                self.book_appointment(date, time)
            elif choice == "7":
                appointment_id = int(input("Enter appointment ID to cancel: "))
                self.cancel_appointment(appointment_id)
            elif choice == "8":
                return True
            else:
                print("Invalid choice. Please try again.")
