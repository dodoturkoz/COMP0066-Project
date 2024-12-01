import sqlite3
from datetime import datetime

from modules.utilities.display import display_choice


def choose_date() -> datetime:
    """Loop to take a valid requested date from the user to book an appointment with a clinician"""
    while True:
        try:
            date_string = input(
                "Please enter a date when you would like to see your clinician (DD/MM/YY): "
            )

            requested_date = datetime.strptime(date_string.strip(), "%d/%m/%y")

            # Constructing a datetime for today's date minus the current time -
            # this allows patients to book slots on the day
            today = datetime.today()
            current_day = datetime(today.year, today.month, today.day)
            if requested_date < current_day:
                print("You cannot book an appointment before the current date.")
            elif requested_date.weekday() in [5, 6]:
                print(
                    "Your clinician only works Monday-Friday. Please choose a date during the week."
                )
            else:
                return requested_date
        except ValueError:
            print(
                "You have entered an invalid date. Please enter in the format DD/MM/YY."
            )


def get_appointments(database, clinician_id: int) -> list:
    """Find all appointments registered for a specific clinician, including unconfirmed ones"""
    try:
        appointments = database.cursor.execute(
            """
                SELECT * 
                FROM Appointments 
                WHERE clinician_id = ?""",
            [clinician_id],
        ).fetchall()
        return appointments
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_available_slots(database, clinician_id: int, day: datetime) -> list:
    """Find all available slots for a clinician on a specified day"""
    appointments = get_appointments(database, clinician_id)
    possible_hours = [9, 10, 11, 12, 14, 15, 16]
    available_slots = []

    # This checks whether an appointment already exists at that day and time
    # and that it isn't earlier than the current time
    for hour in possible_hours:
        if (
            datetime(day.year, day.month, day.day, hour, 0)
            not in [appointment["date"] for appointment in appointments]
            and datetime(day.year, day.month, day.day) > datetime.now()
        ):
            available_slots.append(datetime(day.year, day.month, day.day, hour, 0))

    return available_slots


def request_appointment(database, patient_id: int, clinician_id: int) -> bool:
    """Allows a patient to request an appointment with their clinician"""

    # Check that the patient is registered with this clinician
    result = database.cursor.execute(
        "SELECT clinician_id FROM Patients WHERE user_id = ?", [patient_id]
    ).fetchone()

    if not result or result != clinician_id:
        print("You are not registered with this clinician. Please contact the admin.")
        return False

    # Take a description from the user
    description = input(
        "Please describe why you would like to see your clinician (optional): "
    )

    while True:
        # Take in a requested date
        requested_date = choose_date()

        # Get available slots on that day
        slots = get_available_slots(database, clinician_id, requested_date)

        if not slots:
            choose_again = input(
                "Sorry, your clinician has no availability on that day - would you like to choose another day? (Y/N) "
            )
            if choose_again.upper() == "N":
                return False
            else:
                continue

        time_slot_strings = [slot.strftime("%H:%M") for slot in slots]
        time_slot_strings.append("Select a different day")

        # Offer time slots to the user
        chosen_slot = display_choice(
            "\nHere are the available times on that day:",
            time_slot_strings,
            f"""\nWhich time would you like to request? 
Please choose out of the following options: {[*range(1, len(slots) + 2)]} """,
        )

        if chosen_slot == len(time_slot_strings):
            return False
        else:
            chosen_time = slots[chosen_slot - 1]

        try:
            database.cursor.execute(
                """
                    INSERT INTO Appointments (user_id, clinician_id, date, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                (
                    patient_id,
                    clinician_id,
                    chosen_time,
                    description,
                ),
            )
            database.connection.commit()
            print(
                "\nYour appointment has been requested. You'll receive an email once your clinician has confirmed it."
            )
            return True
        except sqlite3.IntegrityError as e:
            print(f"Failed to book appointment: {e}")
            return False
