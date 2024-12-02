from modules.clinician import Clinician
from modules.patient import Patient
from modules.utilities.display import display_choice, clear_terminal
from datetime import datetime
import sqlite3


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


def get_appointments(clinician: Clinician) -> list:
    """Find all appointments registered for a specific clinician, including unconfirmed ones"""
    try:
        appointments = clinician.database.cursor.execute(
            """
                SELECT appointment_id, a.user_id, clinician_id, date, 
                is_confirmed, is_complete, patient_notes, clinician_notes,
                u.first_name, u.surname 
                FROM Appointments AS a, Users AS u 
                WHERE clinician_id = ?
                AND a.user_id = u.user_id
            """,
            [clinician.user_id],
        ).fetchall()
        return appointments
    except Exception as e:
        print(f"Error: {e}")


def print_appointment(appointment: dict) -> None:
    print(
        f"{appointment['appointment_id']} - {appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
        + f" - {appointment['first_name']} {appointment['surname']} - "
        + f"{'Confirmed' if appointment['is_confirmed'] else 'Not Confirmed'}\n"
    )

def display_appointment_options(clinician: Clinician, appointments: list):

    appointment_strings = []

    for appointment in appointments:
        print_appointment(appointment)
        appointment_strings.append(
            f"{appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
            + f" - {appointment['first_name']} {appointment['surname']} - "
            + f"{'Confirmed' if appointment['is_confirmed'] else 'Not Confirmed'}"
        )

    options = [
        "View appointment notes",
        "Confirm/Reject Appointments",
        "Return to Main Menu",
    ]
    next = display_choice("What would you like to do now?", options)

    # View appointment notes
    if next == 1:

        if len(appointments) > 1:
            clear_terminal()
            selected = display_choice(
                "Please choose an appointment to view", appointment_strings
            )
            selected_appointment = appointments[selected - 1]
        else:
            selected_appointment = appointments[0]

        if selected_appointment["clinician_notes"]:
            print("\nYour notes:")
            print(selected_appointment["clinician_notes"])
        if selected_appointment["patient_notes"]:
            print("\nPatient notes:")
            print(selected_appointment["patient_notes"] + "\n")

    # Confirm/Reject appointments
    elif next == 2:
        clinician.view_requested_appointments()
    # Exit
    elif next == 3:
        return False

def get_available_slots(clinician: Clinician, day: datetime) -> list:
    """Find all available slots for a clinician on a specified day"""
    appointments = get_appointments(clinician)
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


def request_appointment(patient: Patient, clinician: Clinician) -> bool:
    """Allows a patient to request an appointment with their clinician"""

    # Check that the patient is registered with this clinician
    clinician.database.cursor.execute(
        "SELECT clinician_id FROM Patients WHERE user_id = ?", [patient.user_id]
    )
    clinician_id = clinician.database.cursor.fetchone()

    if clinician_id != clinician.user_id:
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
        slots = get_available_slots(clinician, requested_date)

        if not slots:
            choose_again = input(
                "Sorry, your clinician has no availability on that day - would you like to choose another day? (Y/N) "
            )
            if choose_again == "N":
                return False
            else:
                continue

        time_slot_strings = [{slot.strftime("%H:%M")} for slot in slots]
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
            clinician.database.cursor.execute(
                """
                    INSERT INTO Appointments (user_id, clinician_id, date, patient_notes)
                    VALUES (?, ?, ?, ?)
                    """,
                (
                    patient.user_id,
                    clinician.user_id,
                    chosen_time,
                    description,
                ),
            )
            clinician.database.connection.commit()
            print(
                "\nYour appointment has been requested. You'll receive an email once your clinician has confirmed it."
            )
            return True
        except sqlite3.IntegrityError as e:
            print(f"Failed to book appointment: {e}")
            return False
