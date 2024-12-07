import sqlite3
import pandas as pd
from datetime import datetime
from typing import Literal
from database.setup import Database
from modules.utilities.display_utils import display_choice, clear_terminal
from modules.utilities.dataframe_utils import filter_df_by_date


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


def get_clinician_appointments(database, clinician_id: int) -> list:
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


def get_unconfirmed_clinician_appointments(database, clinician_id: int) -> list:
    """Find all unconfirmed future appointments for a specified clinician"""
    appointments = get_clinician_appointments(database, clinician_id)

    return [
        appointment
        for appointment in appointments
        if appointment["status"] == "Pending" and appointment["date"] >= datetime.now()
    ]


def get_patient_appointments(database, user_id: int) -> list:
    """Find all appointments registered for a specific patient, including unconfirmed ones"""
    try:
        appointments = database.cursor.execute(
            """
                SELECT appointment_id, a.user_id, clinician_id, date, 
                status, patient_notes, clinician_notes,
                u.first_name, u.surname, u.email AS patient_email
                FROM Appointments AS a, Users AS u 
                WHERE a.user_id = ?
                AND a.user_id = u.user_id
            """,
            [user_id],
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
    appointments = get_clinician_appointments(database, clinician_id)
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
    clear_terminal()
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
            clear_terminal()
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
                    INSERT INTO Appointments (user_id, clinician_id, date, status, patient_notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                (
                    patient_id,
                    clinician_id,
                    chosen_time,
                    "Pending",
                    description,
                ),
            )
            database.connection.commit()
            clear_terminal()
            print(
                "\nYour appointment has been requested. You'll receive an email once your clinician has confirmed it."
            )
            return True
        except sqlite3.IntegrityError as e:
            clear_terminal()
            print(f"Failed to book appointment: {e}")
            return False


def cancel_appointment(database, appointment_id: int) -> bool:
    """
    Cancels an appointment by changing its status to 'Cancelled By Patient'.
    """
    try:
        database.cursor.execute(
            """
            UPDATE Appointments
            SET status = 'Cancelled By Patient'
            WHERE appointment_id = ?;
            """,
            (appointment_id,),
        )
        if database.cursor.rowcount > 0:
            database.connection.commit()
            clear_terminal()
            print("Appointment canceled successfully.")
            return True
        else:
            clear_terminal()
            print("Appointment not found or you are not authorized to cancel it.")
            return False
    except sqlite3.OperationalError as e:
        clear_terminal()
        print(f"Error canceling appointment: {e}")
        return False


def display_appointment_engagement(
    database: Database,
    user_type: Literal["patient", "clinician"],
    filter_id: int | None = None,
    relative_time: Literal["current", "next", "last", "none"] = "none",
    time_period: Literal["year", "month", "week", "day", "none"] = "none",
) -> pd.DataFrame | None:
    """
    Display all the appointments that the user has engaged with
    """

    id_attribute = "user_id" if user_type == "patient" else "clinician_id"

    # Query to build a dataframe form database information
    query = f"""
    SELECT a.status, a.{id_attribute}, u.first_name, u.surname, a.date
    FROM Appointments a JOIN Users u ON a.{id_attribute} = u.user_id
    {f"WHERE a.{id_attribute} = {filter_id}" if filter_id else ""}
    """
    appointment_cursor = database.cursor.execute(query)
    appointments_data = appointment_cursor.fetchall()
    appointments_df = pd.DataFrame(appointments_data)

    # Calling a function to filter by inputted time range
    filtered_appointments_df = filter_df_by_date(
        appointments_df, relative_time, time_period
    )

    if not filtered_appointments_df.empty:
        # Checking that our filters haven't returned an empty dataframe

        # Group by user_id and status to get the count of each status
        pivot_columns = ["first_name", "surname"]
        pivot_columns.insert(0, id_attribute)

        # Step 1: Create a pivot table with counts of each status per user
        status_counts = filtered_appointments_df.pivot_table(
            index=pivot_columns,
            columns="status",
            aggfunc="size",
            fill_value=0,
        )

        # Step 2: Add a 'total_appointments' column
        status_counts["Total Appointments"] = status_counts.sum(axis=1)

        # Step 3: Sort the DataFrame according to user type
        if user_type == "clinician":
            sort_by = (
                ["Cancelled By Clinician"]
                if "Cancelled By Clinician" in status_counts.columns
                else []
            )
        else:
            sort_by = []
            for column in ["Did Not Attend", "Cancelled By Patient"]:
                if column in status_counts.columns:
                    sort_by.append(column)

        status_counts = status_counts.sort_values(by=sort_by, ascending=False)

        return status_counts

    else:
        return "\nNo appointments could be found\n"
