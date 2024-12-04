from database.setup import Database
from modules.login import login, signup
from modules.emergency import display_emergency_numbers
from modules.utilities.display_utils import (
    display_choice,
    clear_terminal,
    wait_terminal,
)

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
            if user.is_active:
                run = user.flow()
            else:
                print(
                    "Your account is currently inactive. Please contact an administrator."
                )
                wait_terminal("Press enter to log out.")

            # NOTE: if flow returns True -> login screen
            # if flow returns False -> quits app

except ValueError as e:
    # If instead of selecting a number the user types something, we get a ValueError
    # Note: right now this is not falling gracefully, we should handle this better
    print(e)  # TODO: delete this when we finish development
    
finally:
    # If we pass the execution loop, explicitly closes db connection
    db.close()
