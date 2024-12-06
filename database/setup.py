import sqlite3
from datetime import datetime, timedelta, date, time
import random


def old_date(days_ago):
    """Returns a random time with a date determined by parameter days_ago and today's date.)"""
    # Subtracts number of days from today's date to give a date.
    # Returns the given date with a random time
    return (
        datetime.now()
        - timedelta(
            days=days_ago,
            hours=random.randint(0, 12),
            minutes=random.randint(0, 60),
            seconds=random.randint(0, 60),
        )
    ).strftime("%Y-%m-%d %H:%M:%S")


def old_day(days_ago):
    """Returns a date relative to today's date by the number given in parameter."""
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def old_appointment_day(days_ago, hour):
    """Returns a date relative to today's date with a time that was passed into function."""
    # Only used for future and past dates.
    # have so many cases to ensure appointment not given on Sat or Sun for dummy dat
    # but will change this to a dictionary to make code cleaner.
    day_of_week = datetime.today().weekday()
    match day_of_week:
        case 0:
            # Today is Monday
            if days_ago == -6 or days_ago == -5:
                # Could have been Sunday or Sat
                days_ago = -7
                # Now will be Monday
            elif days_ago == 1 or days_ago == 2:
                # Could have been Sunday or Sat
                days_ago = 3
                # Now will be Friday

        case 1:
            # Today is Tuesday
            if days_ago == -5 or days_ago == -4:
                # Could have been Sunday or Sat
                days_ago = -6
                # Now will be Monday
            elif days_ago == 2 or days_ago == 3:
                # Could have been Sunday or Sat
                days_ago = 4
                # Now will be Friday

        case 2:
            # Today is Wednesday
            if days_ago == -4 or days_ago == -3:
                # Could have been Sunday or Sat
                days_ago = -5
                # Now will be Monday
            elif days_ago == 3:
                # Could have been Sunday or Sat
                days_ago = 5
                # Now will be Friday
        case 3:
            # Today is Thursday
            if days_ago == -3 or days_ago == -2:
                # Could have been Sunday or Sat
                days_ago = -4
                # Now will be Monday
        case 4:
            # Today is Friday
            if days_ago == -2 or days_ago == -1:
                # Could have been Sunday or Sat
                days_ago = -3
                # Now will be Monday
        case 5:
            # Today is Saturday
            if days_ago == -1:
                # Could have been Sunday
                days_ago = -2
                # Now will be Monday
        case 6:
            # Today is Sunday
            if days_ago == 1:
                # Could have been  Sat
                days_ago = 2
                # Now will be Monday
            elif days_ago == -6:
                # Could have been Sat
                days_ago = -8
                # Now will be Friday
    return datetime.combine(date.today(), time(hour, 0)) - timedelta(days=days_ago)


roles = ("admin", "patient", "clinician")
diagnoses = (
    "Not Specified",
    "Depression",
    "Anxiety",
    "Bipolar Disorder",
    "Schizophrenia",
    "PTSD",
    "OCD",
    "ADHD",
    "Autism",
    "Drug Induced Psychosis",
    "Other",
)
statuses = (
    "Pending",
    "Confirmed",
    "Rejected",
    "Attended",
    "Did Not Attend",
    "Cancelled By Patient",
    "Cancelled By Clinician",
)


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
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS Patients (
                user_id INTEGER PRIMARY KEY,
                emergency_email TEXT,
                date_of_birth DATETIME,
                diagnosis TEXT CHECK( diagnosis IN {diagnoses} ),
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
                mood INTEGER NOT NULL,
                text TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        """)

        # Appointments Table
        # If the clinician is deleted the appointment still remains so we dont lose the
        # notes for the user, but we can change this to CASCADE
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS Appointments (
                appointment_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                clinician_id INTEGER,
                date DATETIME NOT NULL,
                status TEXT NOT NULL CHECK( status IN {statuses} ),
                patient_notes TEXT,
                clinician_notes TEXT,            
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

            # Check if previous entries of journal.
            # Add entries if there is not.
            journal_entries = self.cursor.execute("SELECT user_id FROM JournalEntries")
            if len(journal_entries.fetchall()) == 0:
                journal_entries = [
                    (
                        1,
                        2,
                        old_date(5),
                        "Hey, I got a first for my degree. Feel on top of the world.",
                    ),
                    (
                        2,
                        2,
                        old_date(4),
                        "I have felt so great in the past few weeks. Everything is amazing.",
                    ),
                    (
                        3,
                        2,
                        old_date(3),
                        "I have spent hundreds of pounds on new clothes. I feel great.",
                    ),
                    (
                        4,
                        2,
                        old_date(2),
                        "I don't feel well. I woke up late but still feel tired.",
                    ),
                    (
                        5,
                        2,
                        old_date(1),
                        "I don't feel like meeting or talking with anyone but my journal.",
                    ),
                    (
                        6,
                        3,
                        old_date(5),
                        "I am worried about my financial issues.",
                    ),
                    (
                        7,
                        3,
                        old_date(4),
                        "I am watching tv but I still feel sad.",
                    ),
                    (
                        8,
                        3,
                        old_date(3),
                        "I tried to read a book but that is not helpful.",
                    ),
                    (
                        9,
                        3,
                        old_date(2),
                        "I feel scared about my future.",
                    ),
                    (
                        10,
                        3,
                        old_date(1),
                        "I tried meditation and it made me feel better.",
                    ),
                    (
                        11,
                        4,
                        old_date(5),
                        "My dog died. I don't feel well. I miss Rex.",
                    ),
                    (
                        12,
                        4,
                        old_date(4),
                        "I am still thinking about Rex and how we used to play together.",
                    ),
                    (
                        13,
                        4,
                        old_date(3),
                        "My family is angry with me and think I overeacted with Rex's death.",
                    ),
                    (
                        14,
                        4,
                        old_date(2),
                        "I hate my family. They threw out Rex's stuff from house.",
                    ),
                    (
                        15,
                        4,
                        old_date(1),
                        "I am feeling sick.",
                    ),
                    (
                        16,
                        7,
                        old_date(5),
                        "The voices are quieter but I can still hear them. I cannot escape them.",
                    ),
                    (
                        17,
                        7,
                        old_date(4),
                        "I think the world is different than other people see it. Sometimes I wonder if I am the only one who knows the truth.",
                    ),
                    (
                        18,
                        7,
                        old_date(3),
                        "I am trying to stay calm, but it is hard when the thoughts are so loud. I feel like no one gets me.",
                    ),
                    (
                        19,
                        7,
                        old_date(2),
                        "Sometimes I feel like I am invisible. It is like I am surrounded by people but no one notices me.",
                    ),
                    (
                        20,
                        8,
                        old_date(5),
                        "I can hear things, things that are not there. I know they are not real, but they still feel real.",
                    ),
                    (
                        21,
                        8,
                        old_date(4),
                        "It is so hard to tell what is real and what is not. I keep second-guessing everything I see and hear.",
                    ),
                    (
                        22,
                        8,
                        old_date(3),
                        "I am afraid to leave my room. I do not know who to trust. The world feels like a dream, but it is not a good one.",
                    ),
                    (
                        23,
                        8,
                        old_date(2),
                        "I do not know how to explain what is happening in my head. I just want it to stop.",
                    ),
                    (
                        24,
                        9,
                        old_date(5),
                        "I feel on top of the world today, like everything is possible. I can't stop talking, can't stop moving. Everything feels so alive.",
                    ),
                    (
                        25,
                        9,
                        old_date(4),
                        "But there is this nagging feeling that I am pushing too hard. I am scared I am going to crash soon.",
                    ),
                    (
                        26,
                        9,
                        old_date(3),
                        "I woke up feeling like everything was a blur. I do not want to talk to anyone, but I know I should. I feel like a stranger to myself.",
                    ),
                    (
                        27,
                        9,
                        old_date(2),
                        "I am hoping tomorrow will be better. I just want the heaviness to go away.",
                    ),
                    (
                        28,
                        10,
                        old_date(5),
                        "I do not like the loud noises today. It is hard to focus with everything around me. I wish it was quieter.",
                    ),
                    (
                        29,
                        10,
                        old_date(4),
                        "I just want to be left alone. Social situations are so draining. I don't know how to explain it.",
                    ),
                    (
                        30,
                        10,
                        old_date(3),
                        "I feel out of place. Sometimes I just want to retreat into my own space. Why cannot people understand that?",
                    ),
                    (
                        31,
                        10,
                        old_date(2),
                        "It is hard to communicate how I am feeling. Words do not always make sense to me, and that makes me frustrated.",
                    ),
                    (
                        32,
                        11,
                        old_date(5),
                        "I checked the door five times today. I know it is locked, but I have to be sure.",
                    ),
                    (
                        33,
                        11,
                        old_date(4),
                        "I cannot stop thinking about germs. Every surface feels dirty, and I need to clean it again. It never feels clean enough.",
                    ),
                    (
                        34,
                        11,
                        old_date(3),
                        "The thoughts are overwhelming today. I am afraid I will forget something important. I need to check again.",
                    ),
                    (
                        35,
                        11,
                        old_date(2),
                        "I want to let go, but I feel trapped by these rituals. It is exhausting.",
                    ),
                    (
                        36,
                        12,
                        old_date(5),
                        "Waking up feels like a task. I just want to sleep and forget about today.",
                    ),
                    (
                        37,
                        12,
                        old_date(4),
                        "It is like no matter what I do, I cannot feel good. I try, but nothing works.",
                    ),
                    (
                        38,
                        12,
                        old_date(3),
                        "Today feels like yesterday. I wish I could feel something, anything. I do not know how much longer I can do this.",
                    ),
                    (
                        39,
                        12,
                        old_date(2),
                        "It is hard to explain how I am feeling. It is not sadness, it is just numbness.",
                    ),
                    (
                        40,
                        13,
                        old_date(5),
                        "I saw someone in the crowd who wasn't there. They were talking to me, but no one else seemed to notice.",
                    ),
                    (
                        41,
                        13,
                        old_date(4),
                        "Sometimes I feel like I'm living in a world only I can see. It's so confusing, so isolating.",
                    ),
                    (
                        42,
                        13,
                        old_date(3),
                        "I keep hearing voices, telling me things I do not want to hear. I do not know how to make them stop.",
                    ),
                    (
                        43,
                        13,
                        old_date(2),
                        "I feel like I'm losing grip on reality. Every day feels like a new challenge.",
                    ),
                    (
                        44,
                        14,
                        old_date(5),
                        "The colors around me are too bright. It is overwhelming.",
                    ),
                    (
                        45,
                        14,
                        old_date(4),
                        "I feel like everyone is watching me, but they are pretending not to. It is scary.",
                    ),
                    (
                        46,
                        14,
                        old_date(3),
                        "I know this is not real, but it feels so real. I cannot trust my own mind anymore.",
                    ),
                    (
                        47,
                        14,
                        old_date(2),
                        "I keep thinking I am being followed. I don't know who I can trust anymore.",
                    ),
                    (
                        48,
                        15,
                        old_date(5),
                        "Everything feels amazing. I'm talking faster, thinking clearer. I've got so much energy!",
                    ),
                    (
                        49,
                        15,
                        old_date(4),
                        "But sometimes, I wonder if I'm doing too much. I feel like I'm going to burn out if I'm not careful.",
                    ),
                    (
                        50,
                        15,
                        old_date(3),
                        "Today I woke up feeling heavy, like a weight was pressing on me.",
                    ),
                    (
                        51,
                        15,
                        old_date(2),
                        "It's hard to explain why I feel this way. I just want the sadness to go away.",
                    ),
                    (
                        52,
                        16,
                        old_date(5),
                        "I didn't understand why everyone was talking so fast today. I just needed a moment to process.",
                    ),
                    (
                        53,
                        16,
                        old_date(4),
                        "I like being by myself. Sometimes, I don't get the jokes people make. Why does it have to be so confusing?",
                    ),
                    (
                        54,
                        16,
                        old_date(3),
                        "The world feels loud today. It's hard to focus on one thing because there's too much going on.",
                    ),
                    (
                        55,
                        16,
                        old_date(2),
                        "I wish people would just slow down. I need things to be simple, but they're always complicated.",
                    ),
                    (
                        56,
                        17,
                        old_date(5),
                        "I can't stop washing my hands. I know they're clean, but I have to do it again.",
                    ),
                    (
                        57,
                        17,
                        old_date(4),
                        "Everything has to be in its right place. If it's not, I feel like something terrible will happen.",
                    ),
                    (
                        58,
                        17,
                        old_date(3),
                        "The thoughts are so intrusive. I keep checking if everything is okay, but it never feels like it is.",
                    ),
                    (
                        59,
                        17,
                        old_date(2),
                        "I just want to escape these thoughts, but they keep coming back.",
                    ),
                    (
                        60,
                        18,
                        old_date(5),
                        "The days feel so long. I'm trying to get through them, but it feels like everything is pointless.",
                    ),
                    (
                        61,
                        18,
                        old_date(4),
                        "I just don't have the energy to do anything. I want to feel better, but I don't know how.",
                    ),
                    (
                        62,
                        18,
                        old_date(3),
                        "Today feels worse than yesterday. I can't get out of bed..",
                    ),
                    (
                        63,
                        18,
                        old_date(2),
                        "I don't know how to explain how I feel. It's not just sadness; it's a complete loss of hope.",
                    ),
                    (
                        64,
                        19,
                        old_date(5),
                        "I saw shadows moving, but no one else did. Why does this keep happening to me?",
                    ),
                    (
                        65,
                        19,
                        old_date(4),
                        "It's like I can't trust my senses anymore. What if it's all in my head?",
                    ),
                    (
                        66,
                        19,
                        old_date(3),
                        "The voices won't leave me alone. They keep repeating the same thing over and over.",
                    ),
                    (
                        67,
                        19,
                        old_date(2),
                        "I feel so lost, like I'm not even in control of my own thoughts.",
                    ),
                    (
                        68,
                        20,
                        old_date(5),
                        "I'm seeing things again, things that aren't there. I don't know how to handle it.",
                    ),
                    (
                        69,
                        20,
                        old_date(1),
                        "I don't know if people are real or if they're just a part of this hallucination. It's so confusing.",
                    ),
                    (
                        70,
                        20,
                        old_date(1),
                        "Everything feels like a blur. I'm afraid to leave the house. What if I can't trust anything I see?",
                    ),
                    (
                        71,
                        20,
                        old_date(1),
                        "I can't tell if I'm awake or dreaming. It's like I'm living in a nightmare that won't end.",
                    ),
                ]
                self.cursor.executemany(
                    "INSERT INTO JournalEntries VALUES(?, ?, ?, ?)", journal_entries
                )

            # Check if there is previous entries of mood.
            # Add entries if there is not.
            MoodEntries = self.cursor.execute("SELECT user_id FROM MoodEntries")
            if len(MoodEntries.fetchall()) == 0:
                MoodEntries = [
                    (1, 2, old_day(5), 6, "Happy about university grades."),
                    (2, 2, old_day(4), 6, "Been watching tv."),
                    (3, 2, old_day(3), 6, "Shopping spree time."),
                    (4, 2, old_day(2), 3, "Feel sick."),
                    (5, 2, old_day(1), 1, "No comment provided."),
                    (6, 3, old_day(5), 1, "Council tax arrears."),
                    (7, 3, old_day(4), 2, "No comment provided."),
                    (8, 3, old_day(3), 1, "I hate books."),
                    (
                        9,
                        3,
                        old_day(2),
                        1,
                        "I don't think everything will get alright.",
                    ),
                    (10, 3, old_day(1), 3, "Meditation and yoga helped."),
                    (11, 4, old_day(5), 3, "I loved my dog."),
                    (12, 4, old_day(4), 1, "I cannot stop thinking on my dog."),
                    (
                        13,
                        4,
                        old_day(3),
                        1,
                        "Having fights throughout the day with my family.",
                    ),
                    (14, 4, old_day(2), 2, "No comment provided."),
                    (15, 4, old_day(1), 1, "Been vomiting and have fever."),
                    (16, 7, old_day(5), 2, "Hear voices."),
                    (17, 7, old_day(4), 1, "Alone."),
                    (18, 7, old_day(3), 2, "Nobody gets me."),
                    (19, 7, old_day(2), 3, "Voices again."),
                    (20, 8, old_day(5), 1, "Scared."),
                    (21, 8, old_day(4), 3, "I just feel confused."),
                    (22, 8, old_day(3), 2, "No comment provided."),
                    (23, 8, old_day(2), 6, "Life is amazing."),
                    (24, 9, old_day(5), 5, "No comment provided."),
                    (
                        25,
                        9,
                        old_day(4),
                        3,
                        "I don't know why I suddenly feel so different.",
                    ),
                    (26, 9, old_day(3), 1, "Just want to stop feeling so sad."),
                    (27, 9, old_day(2), 1, "No comment provided."),
                    (28, 10, old_day(5), 2, "Overwhelmed by noise"),
                    (29, 10, old_day(4), 2, "Feel misunderstood."),
                    (30, 10, old_day(3), 2, "No comment provided."),
                    (31, 10, old_day(2), 2, "World too complicated."),
                    (32, 11, old_day(5), 3, "No comment provided."),
                    (33, 11, old_day(4), 2, "Always scared."),
                    (34, 11, old_day(3), 1, "Feel sick."),
                    (35, 11, old_day(2), 1, "No comment provided."),
                    (36, 12, old_day(5), 2, "Numb, gray mornings"),
                    (37, 12, old_day(4), 1, "Everything feels pointless"),
                    (38, 12, old_day(3), 2, "Worse than yesterday"),
                    (39, 12, old_day(2), 1, "Trapped in darkness"),
                    (40, 13, old_day(5), 1, "Seeing unrecognized figures"),
                    (41, 13, old_day(4), 1, "Living in isolation"),
                    (42, 13, old_day(3), 1, "Voices repeating relentlessly"),
                    (43, 13, old_day(2), 2, "Losing grip, confusion"),
                    (44, 14, old_day(5), 2, "Colors too bright"),
                    (45, 14, old_day(4), 1, "Paranoia and fear"),
                    (46, 14, old_day(3), 3, "Confusion"),
                    (47, 14, old_day(2), 3, "Uncertain about reality"),
                    (48, 15, old_day(5), 6, "Energy, excitement, speed"),
                    (49, 15, old_day(4), 5, "Cautious of burnout"),
                    (50, 15, old_day(3), 2, "Heavy, disconnected feelings"),
                    (51, 15, old_day(2), 1, "Wanting the sadness"),
                    (52, 16, old_day(5), 3, "Too much noise."),
                    (53, 16, old_day(4), 3, "Want to be alone"),
                    (54, 16, old_day(3), 2, "Life too complex."),
                    (55, 16, old_day(2), 2, "Just want peace."),
                    (56, 17, old_day(5), 3, "No comment provided."),
                    (57, 17, old_day(4), 2, "In constant fear."),
                    (58, 17, old_day(3), 1, "No comment provided."),
                    (59, 17, old_day(2), 2, "Feel trapped."),
                    (60, 18, old_day(5), 1, "Heavy, pointless days"),
                    (61, 18, old_day(4), 2, "No energy."),
                    (62, 18, old_day(3), 3, "Feel worse today."),
                    (63, 18, old_day(2), 1, "Feel trapped."),
                    (64, 19, old_day(5), 2, "No comment provided."),
                    (65, 19, old_day(4), 2, "Seeing shadows move."),
                    (66, 19, old_day(3), 3, "Confused on reality."),
                    (67, 19, old_day(2), 1, "Constantly hearing voices."),
                    (68, 20, old_day(5), 3, "Overwhelmed by hallucinations."),
                    (69, 20, old_day(4), 1, "IDK what is real anymore."),
                    (70, 20, old_day(3), 3, "No comment provided."),
                    (71, 20, old_day(2), 2, "Confused."),
                ]
                self.cursor.executemany(
                    "INSERT INTO MoodEntries VALUES(?, ?, ?, ?, ?)", MoodEntries
                )

            # First appointment was datetime(2024, 11, 20, hour=12, minute=0).
            # Second appointment was datetime(2024, 12, 11, hour=16, minute=0).
            appointments = self.cursor.execute("SELECT user_id FROM Appointments")
            if len(appointments.fetchall()) == 0:
                appointments = [
                    (
                        1,
                        2,
                        5,
                        old_appointment_day(3, 9),
                        "Attended",
                        "I feel changes in medication is required given current change in condition.",
                        "I feel patient should continue with the given medication.",
                    ),
                    (
                        2,
                        7,
                        5,
                        old_appointment_day(2, 10),
                        "Did Not Attend",
                        "Condition worsened.",
                        None,
                    ),
                    (
                        3,
                        10,
                        5,
                        old_appointment_day(1, 11),
                        "Rejected",
                        None,
                        None,
                    ),
                    (
                        4,
                        13,
                        5,
                        old_appointment_day(1, 12),
                        "Attended",
                        "Condition improved.",
                        "Condition worsened.",
                    ),
                    (
                        5,
                        16,
                        5,
                        old_appointment_day(-1, 13),
                        "Confirmed",
                        None,
                        None,
                    ),
                    (
                        6,
                        19,
                        5,
                        old_appointment_day(-1, 14),
                        "Cancelled By Clinician",
                        None,
                        None,
                    ),
                    (
                        7,
                        19,
                        5,
                        old_appointment_day(-2, 15),
                        "Cancelled By Patient",
                        None,
                        None,
                    ),
                    (
                        8,
                        2,
                        5,
                        old_appointment_day(-2, 16),
                        "Confirmed",
                        "Condition worsened. Discuss medicine.",
                        None,
                    ),
                    (
                        9,
                        2,
                        5,
                        old_appointment_day(-3, 9),
                        "Confirmed",
                        "Condition improved. Discuss therapy options.",
                        None,
                    ),
                    (
                        10,
                        7,
                        5,
                        old_appointment_day(-5, 10),
                        "Pending",
                        "Condition improving.",
                        None,
                    ),
                    (
                        11,
                        2,
                        5,
                        old_appointment_day(-6, 11),
                        "Pending",
                        None,
                        None,
                    ),
                    (
                        12,
                        8,
                        6,
                        old_appointment_day(3, 9),
                        "Attended",
                        "I feel changes in medication is required given current change in condition.",
                        "I feel patient should continue with the given medication.",
                    ),
                    (
                        13,
                        11,
                        6,
                        old_appointment_day(2, 10),
                        "Did Not Attend",
                        "Condition worsened.",
                        None,
                    ),
                    (
                        14,
                        14,
                        6,
                        old_appointment_day(1, 11),
                        "Rejected",
                        None,
                        None,
                    ),
                    (
                        15,
                        17,
                        6,
                        old_appointment_day(1, 12),
                        "Attended",
                        "Condition improved.",
                        "Condition worsened.",
                    ),
                    (
                        16,
                        20,
                        6,
                        old_appointment_day(-1, 13),
                        "Confirmed",
                        None,
                        None,
                    ),
                    (
                        17,
                        8,
                        6,
                        old_appointment_day(-2, 14),
                        "Cancelled By Patient",
                        None,
                        None,
                    ),
                    (
                        18,
                        14,
                        6,
                        old_appointment_day(-2, 15),
                        "Confirmed",
                        "Condition worsened.",
                        None,
                    ),
                ]
                self.cursor.executemany(
                    "INSERT INTO Appointments VALUES(?, ?, ?, ?, ?, ?, ?)", appointments
                )

            self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
