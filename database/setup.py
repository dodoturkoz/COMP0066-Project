import sqlite3
from datetime import datetime

roles = ("admin", "patient", "clinician")


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row):
    """
    Defines that rows from the DB should be returned as dictionaries if
    they have more than one column, and just the value of the item if
    selecting a single row

    Thus, db.cursor.execute("SELECT username FROM Users").fetchall()
    returns ['admin1', 'patient1']s

    While db.cursor.execute("SELECT username, email FROM Users").fetchall()
    returns
        [{'username': 'admin1', 'email': 'admin1@email.com'},
        {'username': 'patient1', 'email': 'patient1@email.com'}]
    """

    if len(cursor.description) > 1:
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}
    else:
        return row[0]


# Functions copied from the sqlite3 documentation - allowing us to insert and retrieve dates as python datetimes
def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()


def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())


sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("datetime", convert_datetime)


class Database:
    connection: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self):
        # Connect to the database and make the connection and cursor available
        # TODO: evaluate if we want to put a try/except block here
        self.connection = sqlite3.connect(
            "breeze.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.__setup_tables()
        self.__create_default_users()

    def __setup_tables(self):
        # Users Table
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                first_name TEXT,
                surname TEXT,
                email TEXT NOT NULL UNIQUE,
                role TEXT CHECK( role IN {roles} ),
                is_active BOOLEAN NOT NULL
            )"""
        )

        # Patient Information Table
        # Please keep in mind dates are stored as text in SQLite
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Patients (
                user_id INTEGER PRIMARY KEY,
                emergency_email TEXT,
                date_of_birth DATETIME,
                diagnosis TEXT,
                clinician_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (clinician_id) REFERENCES Users(user_id) ON DELETE SET NULL
            )
        """)

        # Journal Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS JournalEntries (
                entry_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date DATETIME NOT NULL,
                text TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        """)

        # Mood Table (Mood + Text)
        # To simplify, I am thinking of storing the mood as a whole string (with colour and all)
        # Nevertheless, we can change this to a FK to a Mood table or whatever we think is best
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS MoodEntries (
                entry_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date DATETIME NOT NULL,
                mood TEXT,
                text TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        """)

        # Appointments Table
        # We can use is_completed to mark if the user actually attended the appointment
        # If the clinician is deleted the appoitment still remains so we dont lose the
        # notes for the user, but we can change this to CASCADE
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Appointments (
                appointment_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                clinician_id INTEGER,
                date DATETIME NOT NULL,
                is_confirmed BOOLEAN DEFAULT 0,
                is_complete BOOLEAN DEFAULT 0,
                notes TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (clinician_id) REFERENCES Users(user_id) ON DELETE SET NULL
            )
        """)

        self.connection.commit()

    def __create_default_users(self):
        # Create the default users if the users table is empty
        users = self.cursor.execute("SELECT username FROM Users")
        if len(users.fetchall()) == 0:
            users = [
                (1, "admin1", "", "Admin", "Admin", "admin1@email.com", "admin", True),
                (
                    2,
                    "patient1",
                    "",
                    "Patient",
                    "One",
                    "patient1@email.com",
                    "patient",
                    True,
                ),
                (
                    3,
                    "patient2",
                    "",
                    "Patient",
                    "Two",
                    "patient2@email.com",
                    "patient",
                    True,
                ),
                (
                    4,
                    "patient3",
                    "",
                    "Patient",
                    "Three",
                    "patient3@email.com",
                    "patient",
                    True,
                ),
                (
                    5,
                    "mhwp1",
                    "",
                    "Clinician",
                    "One",
                    "mhwp1@email.com",
                    "clinician",
                    True,
                ),
                (
                    6,
                    "mhwp2",
                    "",
                    "Clinician",
                    "Two",
                    "mhwp2@email.com",
                    "clinician",
                    True,
                ),
                (
                    7,
                    "mikebrown",
                    "",
                    "Mike",
                    "Brown",
                    "mikebrown@email.com",
                    "patient",
                    True,
                ),
                (
                    8,
                    "emilyjones",
                    "",
                    "Emily",
                    "Jones",
                    "emilyjones@email.com",
                    "patient",
                    False,
                ),
                (
                    9,
                    "davidwilson",
                    "",
                    "David",
                    "Wilson",
                    "davidwilson@email.com",
                    "patient",
                    True,
                ),
                (
                    10,
                    "lindataylor",
                    "",
                    "Linda",
                    "Taylor",
                    "lindataylor@email.com",
                    "patient",
                    True,
                ),
                (
                    11,
                    "robertanderson",
                    "",
                    "Robert",
                    "Anderson",
                    "robertanderson@email.com",
                    "patient",
                    False,
                ),
                (
                    12,
                    "patriciathomas",
                    "",
                    "Patricia",
                    "Thomas",
                    "patriciathomas@email.com",
                    "patient",
                    True,
                ),
                (
                    13,
                    "charlesjackson",
                    "",
                    "Charles",
                    "Jackson",
                    "charlesjackson@email.com",
                    "patient",
                    True,
                ),
                (
                    14,
                    "barbarawhite",
                    "",
                    "Barbara",
                    "White",
                    "barbarawhite@email.com",
                    "patient",
                    False,
                ),
                (
                    15,
                    "jamesharris",
                    "",
                    "James",
                    "Harris",
                    "jamesharris@email.com",
                    "patient",
                    True,
                ),
                (
                    16,
                    "marymartin",
                    "",
                    "Mary",
                    "Martin",
                    "marymartin@email.com",
                    "patient",
                    True,
                ),
                (
                    17,
                    "williamlee",
                    "",
                    "William",
                    "Lee",
                    "williamlee@email.com",
                    "patient",
                    True,
                ),
                (
                    18,
                    "elizabethwalker",
                    "",
                    "Elizabeth",
                    "Walker",
                    "elizabethwalker@email.com",
                    "patient",
                    False,
                ),
                (
                    19,
                    "richardhall",
                    "",
                    "Richard",
                    "Hall",
                    "richardhall@email.com",
                    "patient",
                    True,
                ),
                (
                    20,
                    "susanallen",
                    "",
                    "Susan",
                    "Allen",
                    "susanallen@email.com",
                    "patient",
                    True,
                ),
            ]
            self.cursor.executemany(
                "INSERT INTO Users VALUES(?, ?, ?, ?, ?, ?, ?, ?)", users
            )

            # NOTE: We need to define the default state we want for the app
            # For now, we are defining that patient1 is assigned to mhwp1 and the othet two are not assigned
            # This should allow us to test what happens when a patient is not assigned to a clinician
            patients = [
                (2, "emergency1@gmail.com", datetime(2000, 1, 1), None, 5),
                (3, "emergency2@gmail.com", datetime(1990, 6, 1), None, None),
                (4, "emergency5@gmail.com", datetime(1982, 11, 3), "Depression", None),
                (7, "emergency6@gmail.com", datetime(1983, 12, 4), "Schizophrenia", 5),
                (
                    8,
                    "emergency7@gmail.com",
                    datetime(1984, 1, 5),
                    "Drug Induced Psychosis",
                    6,
                ),
                (
                    9,
                    "emergency8@gmail.com",
                    datetime(1985, 2, 6),
                    "Bipolar Disorder",
                    None,
                ),
                (10, "emergency9@gmail.com", datetime(1986, 3, 7), "Autism", 5),
                (11, "emergency10@gmail.com", datetime(1987, 4, 8), "OCD", 6),
                (12, "emergency11@gmail.com", datetime(1988, 5, 9), "Depression", None),
                (
                    13,
                    "emergency12@gmail.com",
                    datetime(1989, 6, 10),
                    "Schizophrenia",
                    5,
                ),
                (
                    14,
                    "emergency13@gmail.com",
                    datetime(1990, 7, 11),
                    "Drug Induced Psychosis",
                    6,
                ),
                (
                    15,
                    "emergency14@gmail.com",
                    datetime(1991, 8, 12),
                    "Bipolar Disorder",
                    None,
                ),
                (16, "emergency15@gmail.com", datetime(1992, 9, 13), "Autism", 5),
                (17, "emergency16@gmail.com", datetime(1993, 10, 14), "OCD", 6),
                (
                    18,
                    "emergency17@gmail.com",
                    datetime(1994, 11, 15),
                    "Depression",
                    None,
                ),
                (
                    19,
                    "emergency18@gmail.com",
                    datetime(1995, 12, 16),
                    "Schizophrenia",
                    5,
                ),
                (
                    20,
                    "emergency19@gmail.com",
                    datetime(1996, 1, 17),
                    "Drug Induced Psychosis",
                    6,
                ),
            ]
            self.cursor.executemany(
                "INSERT INTO Patients VALUES(?, ?, ?, ?, ?)", patients
            )

            appointments = [
                (
                    1,
                    2,
                    5,
                    datetime(2024, 11, 20, hour=12, minute=0),
                    False,
                    False,
                    "detailed notes",
                )
            ]
            self.cursor.executemany(
                "INSERT INTO Appointments VALUES(?, ?, ?, ?, ?, ?, ?)", appointments
            )

            self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
