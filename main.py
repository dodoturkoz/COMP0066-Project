from database.setup import Database
from modules.login import login, signup
from modules.emergency import display_emergency_numbers
from modules.utilities.display import display_choice, clear_terminal

db = Database()

try:
    clear_terminal()
    print("Welcome to Breeze, your Mental Health and Wellbeing partner!\n")
    display_emergency_numbers()
    run = True
    while run:
        selection = display_choice(
            "Please select an option to continue:", ["Log In", "Sign Up", "Quit"]
        )
        if selection == 3:
            run = False
            continue
        if selection == 2:
            signup(db)
            continue
        user = login(db)
        if user:
            run = user.flow()
            # NOTE: if flow returns True -> login screen
            # if flow returns False -> quits app

except ValueError as e:
    # If instead of selecting a number the user types something, we get a ValueError
    # Note: at some point we need to review that this fails gracefully anywhere in the app
    print(e)  # TODO: delete this when we finish development
    print("Please make sure your input is a number.")
finally:
    # If we pass the execution loop, explicitly closes db connection
    db.close()
