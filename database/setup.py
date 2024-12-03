import sqlite3
from datetime import datetime

roles = ("admin", "patient", "clinician")
diagnoses = (
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

            #Check if there is previous entries of journal.
            #Add entries if there is not.
            #5 entries added per patient, 1 for each day. Can change to random per day since not mood of day.
            journal_entries = self.cursor.execute("SELECT user_id FROM JournalEntries")
            if len(journal_entries.fetchall()) == 0:
                journal_entries = [
                    (1, 2, datetime(2024, 11, 20, hour=12, minute=0), "I am worried about my financial issues. None"),
                    (2, 2, datetime(2024, 11, 21, hour=12, minute=0), "I am watching tv but I still feel sad. None"),
                    (3, 2, datetime(2024, 11, 22, hour=12, minute=0), "I tried to read a book but that is not helpful. None"),
                    (4, 2, datetime(2024, 11, 23, hour=12, minute=0), "I feel scared about my future. None"),
                    (5, 2, datetime(2024, 11, 24, hour=12, minute=0), "I tried meditation and it made me feel better. None"),
                    (6, 3, datetime(2024, 11, 20, hour=12, minute=0), "I got great assessment week grades and I am proud of myself. None"),
                    (7, 3, datetime(2024, 11, 21, hour=12, minute=0), "I got a detention for forgetting my planner. I cannot find my planner and I don't know what to do. None"),
                    (8, 3, datetime(2024, 11, 22, hour=12, minute=0), "I hate mathematics. I am stuck on my homework. None"),
                    (9, 3, datetime(2024, 11, 23, hour=12, minute=0), "I hate studying gcse computer science. We only get to rewrite the textbook. None"),
                    (10, 3, datetime(2024, 11, 24, hour=12, minute=0), "Teacher just mentioned year 10 work experience. I feel excited about it. None"),
                    (11, 4, datetime(2024, 11, 20, hour=12, minute=0), "My dog died. I don't feel well. I miss Rex. Depression"),
                    (12, 4, datetime(2024, 11, 21, hour=12, minute=0), "I am still thinking about Rex and how we used to play together. Depression"),
                    (13, 4, datetime(2024, 11, 22, hour=12, minute=0), "I think my parents are angry with me. They think I am overreacting with Rex's death. Depression"),
                    (14, 4, datetime(2024, 11, 23, hour=12, minute=0), "My parents just don't understand me. They want throw away Rex's stuff from house. Depression"),
                    (15, 4, datetime(2024, 11, 24, hour=12, minute=0), "I am thinking of moving out of house. I just don't know how to tell my family. Depression"),
                    (16, 7, datetime(2024, 11, 20, hour=12, minute=0), "I don't feel like spending time with my relatives but they are not leaving me. Schizophrenia"),
                    (17, 7, datetime(2024, 11, 21, hour=12, minute=0), "I can see my dead mother across the road but my friends cannot. Schizophrenia"),
                    (18, 7, datetime(2024, 11, 22, hour=12, minute=0), "I keep seeing and hearing my mother. She is telling me that she is actually here but my relatives said she is not here. Schizophrenia"),
                    (19, 7, datetime(2024, 11, 23, hour=12, minute=0), "I don't want to speak to anyone. They screamed at me, saying my mother is dead and I should just accept that. Schizophrenia"),
                    (20, 7, datetime(2024, 11, 24, hour=12, minute=0), "I made up with my relatives. They apologised and we are going out for dinner. Schizophrenia"),
                    (21, 8, datetime(2024, 11, 20, hour=12, minute=0), "I am grateful to have friends who care for me. They are helping me manage my symptoms.Drug induced psychosis"),
                    (22, 8, datetime(2024, 11, 21, hour=12, minute=0), "I have been hearing random voices. Drug induced psychosis"),
                    (23, 8, datetime(2024, 11, 22, hour=12, minute=0), "I am currently reading books. I love J.K. Rowling. Drug induced psychosis"),
                    (24, 8, datetime(2024, 11, 23, hour=12, minute=0), "The voices are telling me to take more drugs.Drug induced psychosis"),
                    (25, 8, datetime(2024, 11, 24, hour=12, minute=0), "I heard voices again. They scare me.Drug induced psychosis"),
                    (26, 9, datetime(2024, 11, 20, hour=12, minute=0), "I have not felt well for so many days now. I am eating chocolate gifted by my sister. But I don't feel any happier from that.Bipolar disorder"),
                    (27, 9, datetime(2024, 11, 21, hour=12, minute=0), "I don't feel like getting out of my bed.Bipolar disorder"),
                    (28, 9, datetime(2024, 11, 22, hour=12, minute=0), "I have blocked everyone on social media. I don't know if they will be angry with me. Bipolar disorder"),
                    (29, 9, datetime(2024, 11, 23, hour=12, minute=0), "I feel really great today. I spent some time with friends. Bipolar disorder"),
                    (30, 9, datetime(2024, 11, 24, hour=12, minute=0), "I have not felt well for so many days now. I am eating chocolate gifted by my sister. But I don't feel any happier from that.Bipolar disorder"),
                    (31, 10, datetime(2024, 11, 20, hour=12, minute=0), "I am finding it hard to make friends at my new sixth form. It is just so hard to approach other students. Autism"),
                    (32, 10, datetime(2024, 11, 21, hour=12, minute=0), "I think other students think I am rude. Autism"),
                    (33, 10, datetime(2024, 11, 22, hour=12, minute=0), "I feel other students are currently making fun of me. Autism"),
                    (34, 10, datetime(2024, 11, 23, hour=12, minute=0), "I feel a bit scared asking the teacher for help. Autism"),
                    (35, 10, datetime(2024, 11, 24, hour=12, minute=0), "I feel so relieved. The teacher spoke to other students and now those students are my friends. Autism"),
                    (36, 11, datetime(2024, 11, 20, hour=12, minute=0), "I saw a great movie today. It made me feel happy. OCD"),
                    (37, 11, datetime(2024, 11, 21, hour=12, minute=0), "I lost my job today since they thought I was spending too much time cleaning rather than babysitting. OCD"),
                    (38, 11, datetime(2024, 11, 22, hour=12, minute=0), "It has been a day since I lost my job. But, I am glad my parents support and understand me. OCD"),
                    (39, 11, datetime(2024, 11, 23, hour=12, minute=0), "I am going for an interview. I feel anxious OCD"),
                    (40, 11, datetime(2024, 11, 24, hour=12, minute=0), "I was rejected as a baby-sitter when they found out I had OCD. OCD"),
                    (41, 12, datetime(2024, 11, 20, hour=16, minute=0), "I did not get the grades I wanted. I hate myself.Depression"),
                    (42, 12, datetime(2024, 11, 21, hour=8, minute=0), "I have not ate since I saw my grades yesterday. My carer is worried about me. Depression"),
                    (43, 12, datetime(2024, 11, 21, hour=10, minute=0), "I went out with my carer and ate something.Depression"),
                    (44, 12, datetime(2024, 11, 23, hour=12, minute=0), "I went shopping with my carer and felt better.Depression"),
                    (45, 12, datetime(2024, 11, 24, hour=12, minute=0), "I still can't stop thinking about my grades.Depression"),
                    (46, 13, datetime(2024, 11, 20, hour=12, minute=0), "I am regaining interest in everyday activities. Right now, I am going to grocery shopping with my granddaughter. schizo"),
                    (47, 13, datetime(2024, 11, 21, hour=12, minute=0), "I am having a psychotic episode from someone mentioning my dead wife. My brother is taking care of me. schizo"),
                    (48, 13, datetime(2024, 11, 22, hour=12, minute=0), "I feel better now after yesterday's episode. schizo"),
                    (49, 13, datetime(2024, 11, 23, hour=12, minute=0), "I am excited to go to my grandaughter's graduation ceremony. schizo"),
                    (50, 13, datetime(2024, 11, 24, hour=12, minute=0), "I am seeing my dead wife at the graduation ceremony. schizo"),
                    (51, 14, datetime(2024, 11, 20, hour=12, minute=0), "I caught my boyfriend cheating on me. I am finding it really hard to not think about drugs right now.drug"),
                    (52, 14, datetime(2024, 11, 21, hour=12, minute=0), "I feel great. I can hear my plants speaking to me.drug"),
                    (53, 14, datetime(2024, 11, 22, hour=12, minute=0), "I am admitted at the hospital. I feel angry. Why did I take so much drugs?.drug"),
                    (54, 14, datetime(2024, 11, 23, hour=12, minute=0), "The hospital staff is nice and are helping me move on.drug"),
                    (55, 14, datetime(2024, 11, 24, hour=12, minute=0), "Exercise and chocolate. They are exactly what I need.drug"),
                    (56, 15, datetime(2024, 11, 20, hour=12, minute=0), "Hey, I got a first for my degree. Feel on top of the world.bipolar"),
                    (57, 15, datetime(2024, 11, 21, hour=12, minute=0), "I have felt so great in the past few weeks. Everything is working well for me.bipolar"),
                    (58, 15, datetime(2024, 11, 22, hour=12, minute=0), "I have spent thousands of pounds on a new pair of shoes. I feel I deserve it. bipolar"),
                    (59, 15, datetime(2024, 11, 23, hour=12, minute=0), "I don't feel well. I woke up late but still feel tired. bipolar"),
                    (60, 15, datetime(2024, 11, 24, hour=12, minute=0), "I don't feel like meeting or talking with anyone but my journal.bipolar"),
                    (61, 16, datetime(2024, 11, 20, hour=12, minute=0), "I just made a new friend today. Autism"),
                    (62, 16, datetime(2024, 11, 21, hour=12, minute=0), "I feel slightly shy talking with my new friend. Autism"),
                    (63, 16, datetime(2024, 11, 22, hour=12, minute=0), "My new friend thinks I am too wierd and don't understand sarcasm. Autism"),
                    (64, 16, datetime(2024, 11, 23, hour=12, minute=0), "I lost my friend. I hate him. They were not following the plan I had set for us. Autism"),
                    (65, 16, datetime(2024, 11, 24, hour=12, minute=0), "I feel nobody wants to be my friend. Autism"),
                    (66, 17, datetime(2024, 11, 20, hour=12, minute=0), "I feel my previous CBT is working. I am not spending as much time in checking the doors are closed.ocd"),
                    (67, 17, datetime(2024, 11, 21, hour=12, minute=0), "The amount of time I spend checking the doors are closed is decreasing. I feel I am making progress in managing my symptoms. ocd"),
                    (68, 17, datetime(2024, 11, 22, hour=12, minute=0), "My mum accidently left a door open. I just spent 30 mins checking all the doors in the house are closed. I feel scared. ocd"),
                    (69, 17, datetime(2024, 11, 23, hour=12, minute=0), "I feel anxious. I am checking doors every now and then.ocd"),
                    (70, 17, datetime(2024, 11, 24, hour=12, minute=0), "I feel scared. My mum is reassuring me everything is okay and she is apologising but I still feel scared.ocd"),
                    (71, 18, datetime(2024, 11, 20, hour=12, minute=0), "I am reading eviction notice from my landlord. I don't know what to do. I feel scared and miserable. depression"),
                    (72, 18, datetime(2024, 11, 21, hour=12, minute=0), "Everyday is getting more difficult for me. depression"),
                    (73, 18, datetime(2024, 11, 22, hour=12, minute=0), "I now need to deal with council tax arrears. I am scared about my future. depression"),
                    (74, 18, datetime(2024, 11, 23, hour=23, minute=11), "I am unable to sleep. depression"),
                    (75, 18, datetime(2024, 11, 24, hour=12, minute=0), "My sister has came to help me and I feel very guilty. depression"),
                    (76, 19, datetime(2024, 11, 20, hour=12, minute=0), "I have been hearing voices again. They were saying everyone hates me.schizophrenia"),
                    (77, 19, datetime(2024, 11, 21, hour=12, minute=0), "I feel very scared. I can see my friends screaming I am dumb and worthless.schizophrenia"),
                    (78, 19, datetime(2024, 11, 22, hour=12, minute=0), "My boss is shouting at me and firing me. He says I don't know how to do anything. schizophrenia"),
                    (79, 19, datetime(2024, 11, 23, hour=12, minute=0), "I can hear my friends repeatedly screaming I am dumb and worthless. I stop hearing their voices. schizophrenia"),
                    (80, 19, datetime(2024, 11, 24, hour=12, minute=0), "My friends came to visit and reassure me they do not think I am dumb. But, I still hear their voices saying I am dumb when they are not there.schizophrenia"),
                    (81, 20, datetime(2024, 11, 20, hour=12, minute=0), "I feel constant sweating. My life has gone so difficult after I tried to withdraw from drugs. drug induced"),
                    (82, 20, datetime(2024, 11, 21, hour=12, minute=0), "I can still hear some voices despite not taking drugs anymore. What is happening to me? drug induced"),
                    (83, 20, datetime(2024, 11, 22, hour=12, minute=0), "I took some drugs. I can see dangerous people with knives. I feel scared drug induced"),
                    (84, 20, datetime(2024, 11, 23, hour=12, minute=0),"I am admitted to the hospital. The people with knives are there but the doctor cannot see them. drug induced"),
                    (85, 20, datetime(2024, 11, 24, hour=12, minute=0), "I could not sleep the whole day and night. The people with knives are still there. drug induced")
                ]
                self.cursor.executemany(
                    "INSERT INTO JournalEntries VALUES(?, ?, ?, ?)", journal_entries
                )
            
            #Check if there is previous entries of mood.
            #Add entries if there is not.
            #5 entries added per patient, 1 for each day. Can take out some days when patients don't add mood.  
            MoodEntries = self.cursor.execute("SELECT user_id FROM MoodEntries")
            if len(MoodEntries.fetchall()) == 0:
                MoodEntries = [
                    (1, 2, datetime(2024, 11, 20), "\U0001f7e8 4. yellow Content \U0001f610", "No comment provided."),
                    (2, 2, datetime(2024, 11, 21), "\033[33m 3. Neutral \U0001f641 [Orange] \033[00m", "No comment provided."),
                    (3, 2, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (4, 2, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (5, 2, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (6, 3, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (7, 3, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (8, 3, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (9, 3, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (10, 3, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (11, 4, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (12, 4, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (13, 4, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (14, 4, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (15, 4, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (16, 7, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (17, 7, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (18, 7, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (19, 7, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (20, 7, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (21, 8, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (22, 8, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (23, 8, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (24, 8, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (25, 8, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (26, 9, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (27, 9, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (28, 9, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (29, 9, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (30, 9, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (31, 10, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (32, 10, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (33, 10, datetime(2024, 11, 2), "Mood", "No comment provided."),
                    (34, 10, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (35, 10, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (36, 11, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (37, 11, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (38, 11, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (39, 11, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (40, 11, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (41, 12, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (42, 12, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (43, 12, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (44, 12, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (45, 12, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (46, 13, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (47, 13, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (48, 13, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (49, 13, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (50, 13, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (51, 14, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (52, 14, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (53, 14, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (54, 14, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (55, 14, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (56, 15, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (57, 15, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (58, 15, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (59, 15, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (60, 15, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (61, 16, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (62, 16, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (63, 16, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (64, 16, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (65, 16, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (66, 17, datetime(2024, 11, 20), "Mood", "Feel like I am facing my fears"),
                    (67, 17, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (68, 17, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (69, 17, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (70, 17, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (71, 18, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (72, 18, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (73, 18, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (74, 18, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (75, 18, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (76, 19, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (77, 19, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (78, 19, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (79, 19, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (80, 19, datetime(2024, 11, 24), "Mood", "No comment provided."),
                    (81, 20, datetime(2024, 11, 20), "Mood", "No comment provided."),
                    (82, 20, datetime(2024, 11, 21), "Mood", "No comment provided."),
                    (83, 20, datetime(2024, 11, 22), "Mood", "No comment provided."),
                    (84, 20, datetime(2024, 11, 23), "Mood", "No comment provided."),
                    (85, 20, datetime(2024, 11, 24), "Mood", "No comment provided.")
                ]
                self.cursor.executemany(
                    "INSERT INTO MoodEntries VALUES(?, ?, ?, ?, ?)", MoodEntries
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
