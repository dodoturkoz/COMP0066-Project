from database.setup import Database
from modules.login import login, signup
from modules.emergency import display_emergency_numbers
from modules.utilities.display_utils import (
    display_choice,
    clear_terminal,
    wait_terminal,
)

try:
    db = Database()
    clear_terminal()
    print("Welcome to Breeze, your Mental Health and Wellbeing partner!\n")
    display_emergency_numbers()
    run = True
    while run:
        selection = display_choice(
            "\nPlease select an option to continue:", ["Log In", "Sign Up", "Quit"]
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
except KeyboardInterrupt:
    # Do nothing if the user presses Ctrl+C, just move to the finally block
    pass
finally:
    # If we pass the execution loop, explicitly closes db connection
    clear_terminal()
    print("\nThanks for using Breeze. Goodbye!")
    db.close()
