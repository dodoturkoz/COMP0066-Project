import sqlite3

roles = ("admin", "patient", "clinician")
clinicians =()
#Can have list to equal clinicians if cannot use the table for check? 
mood = (6,5,4,3,2,1)
#Not sure if we defined how to set mood but can keep it as a number between 6 (great) to 1(bad) for storage and making chart purposes.

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
        self.connection.commit()
        # Creating the patient table, can check whether the MHWP name is in the list of names of clinicians used by Philip and Ben.
        #Name does not have to be unique, does it?
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS Patients (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            condition TEXT NOT NULL,
            emergency_contact_email TEXT NOT NULL UNIQUE,
            MHWP TEXT CHECK( MHWP IN {clinicians} ),
            notes TEXT
            )"""
        )
        self.connection.commit()
        
        #Don't know whether the mood table below will be okay since we need to have only one mood for the day. 
        #With a table like below, it can just be joined to patient table.
        #self.cursor.execute(
        #   f"""
        #    CREATE TABLE IF NOT EXISTS Mood (
        #    user_id INTEGER PRIMARY KEY,
         #   date DATE,
          #  time TIME NOT NULL,
           # comments TEXT NOT NULL,
            #mood INTEGER CHECK( MHWP IN {mood} )
            #)"""
        #)
        #self.connection.commit()

        #OR we could create the below as separate a mood table and a separate comments table.
        #But this will only record data for last 7 days only as each time the patient is updating data in the program based on the
        #day of the week. Hence, clinician only sees data on patient mood for the past 7 days only.
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS Mood (
            user_id INTEGER PRIMARY KEY,
            monday INTEGER CHECK( MHWP IN {mood} ),
            tuesday INTEGER CHECK( MHWP IN {mood} ),
            wednesday INTEGER CHECK( MHWP IN {mood} ),
            thursday INTEGER CHECK( MHWP IN {mood} ),
            friday INTEGER CHECK( MHWP IN {mood} ),
            saturday INTEGER CHECK( MHWP IN {mood} ),
            sunday INTEGER CHECK( MHWP IN {mood} ),
            )"""
        )
        self.connection.commit()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Comments (
            user_id INTEGER PRIMARY KEY,
            monday TEXT,
            tuesday TEXT,
            wednesday TEXT,
            thursday TEXT,
            friday TEXT,
            saturday TEXT,
            sunday TEXT,
            )"""
        )
        self.connection.commit()

        #Below is to record the journalling thoughts or text so that it could be accessed by clinician and patient.

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Journal (
            date_time TIMESTAMP PRIMARY KEY,
            user_id INTEGER NOT NULL,
            journal TEXT NOT NULL,
            )"""
        )
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
