import sqlite3
from typing import Optional, Any
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

    def display_previous_moods(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        pass

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

    @staticmethod
    def search_exercises(keyword: str = None):
        """
        Looks up exercises and displays them with both an audio file and the relevant transcript.
        """
        resources = [
            {"title": "Abuse",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/3917/0913/6697/NHS-Cumbria-Abuse.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/abuse-audio-transcript/"},
            {"title": "Alcohol and You",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/1617/0913/7944/NHS-Cumbria-AlcoholandYou.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/alcohol-and-you-audio-transcript/"},
            {"title": "Anxiety",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/7717/0913/9287/NHS-Cumbria-Anxiety.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/anxiety-audio-transcript/"},
            {"title": "Bereavement",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/7917/0913/7411/NHS-Cumbria-Bereavement.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/bereavement-audio-transcript/"},
            {"title": "Controlling Anger",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/6017/0913/7717/NHS-Cumbria-Controlling_Anger.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/controlling-anger-audio-transcript/"},
            {"title": "Coping with Low Mood",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/1417/0913/7117/NHS-Cumbria-Low-Mood.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/coping-with-low-mood-audio-transcript/"},
            {"title": "Coping with Suicidal Thoughts",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/9817/0913/6791/NHS-Cumbria-Suicidal_Thoughts.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/coping-with-suicidal-thoughts-audio-transcript/"},
            {"title": "Coping with Stress",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/2317/0913/7371/NHS-Cumbria-Stress.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/coping-with-stress-audio-transcript/"},
            {"title": "Eating Problems",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/8417/0913/7611/NHS-Cumbria-Eating_Problems.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/eating-problems-audio-transcript/"},
            {"title": "Low Self-Esteem",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/6817/0913/7411/NHS-Cumbria-Self-Esteem.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/low-self-esteem-audio-transcript/"},
            {"title": "OCD",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/3117/0913/6943/NHS-Cumbria-OCD.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/ocd-audio-transcript/"},
            {"title": "Panic Attacks",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/1917/0913/7571/NHS-Cumbria-Panic_Attacks.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/panic-attacks-audio-transcript/"},
            {"title": "Phobias",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/9617/0913/7267/NHS-Cumbria-Phobias.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/phobias-audio-transcript/"},
            {"title": "Sleep Problems",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/9417/0913/7267/NHS-Cumbria-Sleep_Problems.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/sleep-problems-audio-transcript/"},
            {"title": "Substance Misuse",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/7417/0913/7271/NHS-Cumbria-Substance_Misuse.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/substance-misuse-audio-transcript/"},
            {"title": "Tension",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/9517/0913/7789/NHS-Cumbria-Tension.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/tension-audio-transcript/"},
            {"title": "Trauma",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/7517/0913/7851/NHS-Cumbria-Trauma.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/trauma-audio-transcript/"},
            {"title": "Work Stress",
             "audio_file": "https://selfhelp.cntw.nhs.uk/application/files/6317/0913/7031/NHS-Cumbria-Work_Stress.mp3",
             "transcript": "https://www.cntw.nhs.uk/home/accessible-information/audio/self-help-guides-audio-transcripts/work-stress-audio-transcript/"}
        ]
        if keyword:
            filtered_resources = [
                resource for resource in resources if keyword.lower() in resource["title"].lower()
            ]
        else:
            filtered_resources = resources

        for resource in filtered_resources:
            print(f"Title: {resource['title']}")
            print(f"Audio File: {resource['audio_file']}")
            print(f"Transcript: {resource['transcript']}")

    def book_appointment(self, appointment_date: str, description: str) -> bool:
        """
        Allows the patient to book an appointment by specifying date and description.
        """
        try:
            self.database.cursor.execute(
                """
                INSERT INTO Appointments (user_id, appointment_date, description, is_completed)
                VALUES (?, ?, ?, 0)
                """,
                (self.user_id, appointment_date, description)
            )
            self.database.connection.commit()
            print("Appointment booked successfully.")
            return True
        except sqlite3.IntegrityError as e:
            print(f"Failed to book appointment: {e}")
            return False

    def cancel_appointment(self, appointment_id: int) -> bool:
        """
        Cancels an appointment by removing it from the database.
        """
        try:
            self.database.cursor.execute(
                """
                DELETE FROM Appointments WHERE appointment_id = ? AND user_id = ?
                """,
                (appointment_id, self.user_id)
            )
            if self.database.cursor.rowcount > 0:
                self.database.connection.commit()
                print("Appointment canceled successfully.")
                return True
            else:
                print("Appointment not found or you are not authorized to cancel it.")
                return False
        except sqlite3.OperationalError as e:
            print(f"Error canceling appointment: {e}")
            return False

    def view_appointments(self, date: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Views all appointments for the patient, optionally filtered by date.
        """
        query = "SELECT appointment_id, appointment_date, description, is_completed FROM Appointments WHERE user_id = ?"
        params = [self.user_id]

        if date:
            query += " AND DATE(appointment_date) = ?"
            params.append(date)

        query += " ORDER BY appointment_date ASC"

        try:
            self.database.cursor.execute(query, tuple(params))
            appointments = [
                {
                    "appointment_id": row["appointment_id"],
                    "appointment_date": row["appointment_date"],
                    "description": row["description"],
                    "is_completed": bool(row["is_completed"])
                }
                for row in self.database.cursor.fetchall()
            ]

            if appointments:
                print(f"\nAppointments for {date if date else 'all dates'}:\n")
                for appointment in appointments:
                    print(f"ID: {appointment['appointment_id']}")
                    print(f"Date: {appointment['appointment_date']}")
                    print(f"Description: {appointment['description']}")
                    print(f"Completed: {'Yes' if appointment['is_completed'] else 'No'}\n")
            else:
                print("No appointments found for the specified date or user.")

            return appointments

        except sqlite3.OperationalError as e:
            print(f"Error viewing appointments: {e}")
            return []

    def flow(self):
        """
        Displays the main patient menu and handles the selection of various options.
        """
        print("Hello Patient")
        while True:
            choice = input(
                "Please select an option:\n"
                "1. Edit Personal Info\n"
                "2. Record Mood of the Day\n"
                "3. Display Previous Moods\n"
                "4. Add Journal Entry \n"
                "5. Read Journal Entries \n"
                "6. Search Exercises\n"
                "7. Book Appointment\n"
                "8. View Appointments\n"
                "9. Cancel Appointment\n"
                "10. Log Out\n"
            )
            if choice == "1":
                attribute = input("Enter the attribute to edit (e.g., email): ")
                value = input(f"Enter the new value for {attribute}: ")
                self.edit_medical_info(attribute, value)
            elif choice == "2":
                mood = input("Enter your mood for today: ")
                self.mood_of_the_day(mood)
            elif choice == "3":
                self.display_previous_moods()
            elif choice == "4":
                content = input("Enter new journal entry: ")
                self.journal(content)
            elif choice == "5":
                date = input(
                    "Enter a date in YYYY-MM-DD format or leave blank to view all previous entries: "
                )
                self.display_journal(date)
            elif choice == "6":
                keyword = input("Enter keyword to search for exercises: ")
                self.search_exercises(keyword)
            elif choice == "7":
                date = input("Enter appointment date (YYYY-MM-DD): ")
                desc = input("Enter appointment description: ")
                self.book_appointment(date, desc)
            elif choice == "8":
                self.view_appointments()
            elif choice == "9":
                appointment_id = int(input("Enter appointment ID to cancel: "))
                self.cancel_appointment(appointment_id)
            elif choice == "10":
                return True
            else:
                print("Invalid choice. Please try again.")
