from database.setup import Database
from modules.login import login

db = Database()

try:
    print("Welcome to Breeze, your Mental Health and Wellbeing partner!\n")
    run = True
    while run:
        selection = input(
            "Please select an option to continue:\n 1. Log In\n 2. Quit\n"
        )
        if selection not in ["1", "2"]:
            print("Invalid option. Please select 1 or 2.")
            continue
        if int(selection) == 2:
            run = False
            continue
        user = login(db)
        if user:
            run = user.flow() # NOTE: if flow returns True, goes back to login screen, if false, quits the app

except ValueError as e:
    # If instead of selecting a number the user types something, we get a ValueError
    # Note: at some point we need to review that this fails gracefully anywhere in the app
    print(e)  # TODO: delete this when we finish development
    print("Please make sure your input is a number.")
finally:
    # If we pass the execution loop, explicitly closes db connection
    db.close()
