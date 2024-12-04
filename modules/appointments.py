import sqlite3
import pandas as pd
from datetime import datetime
from typing import Literal
from database.setup import Database

from modules.utilities.display_utils import display_choice


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
                SELECT appointment_id, a.user_id, clinician_id, date, 
                status, patient_notes, clinician_notes,
                u.first_name, u.surname, u.email AS patient_email
                FROM Appointments AS a, Users AS u 
                WHERE clinician_id = ?
                AND a.user_id = u.user_id
            """,
            [clinician_id],
        ).fetchall()
        return appointments
    except Exception as e:
        print(f"Error: {e}")
        return []


def print_appointment(appointment: dict) -> None:
    print(
        f"{appointment['appointment_id']} - {appointment['date'].strftime('%a %d %b %Y, %I:%M%p')}"
        + f" - {appointment['first_name']} {appointment['surname']} - "
        + f"{appointment['status']}\n"
    )


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
                    INSERT INTO Appointments (user_id, clinician_id, date, patient_notes)
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


def cancel_appointment(database, appointment_id: int) -> bool:
    """
    Cancels an appointment by removing it from the database.
    """
    try:
        database.cursor.execute(
            """
            UPDATE Appointments
            SET status = 'Cancelled by Patient'
            WHERE appointment_id = ?;
            """,
            (appointment_id,),
        )
        if database.cursor.rowcount > 0:
            database.connection.commit()
            print("Appointment canceled successfully.")
            return True
        else:
            print("Appointment not found or you are not authorized to cancel it.")
            return False
    except sqlite3.OperationalError as e:
        print(f"Error canceling appointment: {e}")
        return False

#TODO: Consume this where appropriate
def display_appointment_engagement(
    database: Database,
    user_type: Literal["patient", "clinician"],
    clinician_id: int | None = None,
) -> pd.DataFrame | None:
    """
    Display all the appointments that the user has engaged with
    """

    id_attribute = "user_id" if user_type == "patient" else "clinician_id"

    query = f"""
    SELECT a.status, a.{id_attribute}, u.first_name, u.surname
    FROM Appointments a JOIN Users u ON a.user_id = u.user_id
    {f"WHERE a.clinician_id = {clinician_id}" if clinician_id else ""}
    """

    appointment_cursor = database.cursor.execute(query)
    appointments_data = appointment_cursor.fetchall()
    appointments_df = pd.DataFrame(appointments_data)

    # Group by user_id and status to get the count of each status
    pivot_columns = ["first_name", "surname"]
    pivot_columns.insert(0, id_attribute)

    # Step 1: Create a pivot table with counts of each status per user
    status_counts = appointments_df.pivot_table(
        index=pivot_columns,
        columns="status",
        aggfunc="size",
        fill_value=0,
    )

    # Step 2: Add a 'total_appointments' column
    status_counts["Total Appointments"] = status_counts.sum(axis=1)

    # Step 3: Sort the DataFrame according to user type
    if user_type == "clinician":
        sort_by = ["Cancelled By Clinician"] if "Cancelled By Clinician" in status_counts.columns else []
    else:
        sort_by = []
        for column in ["Did Not Attend", "Cancelled By Patient"]:
            if column in status_counts.columns:
                sort_by.append(column)
                
    sort_by = ["Did Not Attend", "Cancelled By Patient"] if user_type == "patient" else ["Cancelled By Clinician"]
    status_counts = status_counts.sort_values(by=sort_by, ascending=False)

    print(status_counts)
    return status_counts