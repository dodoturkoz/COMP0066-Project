from ..database.setup import Database

def login(db: Database) -> None:
    """
    Attemps to log in the user, by requesting a username and password and
    checking if the combination exists in the database.

    Prints if the login was successfull or not, and returns None (FOR NOW!!)
    """

    username = input('Your username: ')
    password = input('Your password: ')
    
    user_data = db.cursor.execute("""SELECT user_id, username, email, is_active FROM Users
                                  WHERE username = :username AND password = :password""",
                                  {'username': username, 'password': password}).fetchone()
    
    if user_data:
        username = user_data["username"]
        print(f"You have logged in as {username}")
        print(f"The following information about you is available: {user_data}")
    else:
        print("Your username and password combination does not exist in our system")