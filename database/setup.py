import sqlite3

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


class Database:
    connection: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self):
        # Connect to the database and make the connection and cursor available
        # TODO: evaluate if we want to put a try/except block here
        self.connection = sqlite3.connect("breeze.db")
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()
        self.__setup_tables()
        self.__create_default_users()

    def __setup_tables(self):
        # Ensure that all the tables are created
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT CHECK( role IN {roles} ),
            is_active BOOLEAN NOT NULL
            )"""
        )

        # MoodLog Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS MoodLog (
                log_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                mood_colour TEXT,
                timestamp TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)

        # Journal Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Journal (
                entry_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)

        # Exercises Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Exercises (
                exercise_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                duration INTEGER CHECK(duration >= 0),
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)

        # Appointments Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Appointments (
                appointment_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                description TEXT NOT NULL,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)

        self.connection.commit()

    def __create_default_users(self):
        # Create the default users if the users table is empty
        users = self.cursor.execute("SELECT username FROM Users")
        if len(users.fetchall()) == 0:
            users = [
                (None, "admin1", "", "admin1@email.com", "admin", True),
                (None, "patient1", "", "patient1@email.com", "patient", True),
                (None, "patient2", "", "patient2@email.com", "patient", True),
                (None, "patient3", "", "patient3@email.com", "patient", True),
                (None, "mhwp1", "", "mhwp1@email.com", "clinician", True),
                (None, "mhwp2", "", "mhwp2@email.com", "clinician", True),
            ]
            self.cursor.executemany("INSERT INTO Users VALUES(?, ?, ?, ?, ?, ?)", users)
            self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
