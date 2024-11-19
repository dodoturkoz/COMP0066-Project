from database.setup import Database
from modules.login import login

db = Database()

try:
    print("\nWelcome to Breeze, your Mental Health and Wellbeing partner!")
    run = True
    while run:
        selection = input(
            "Please select an option to continue:\n [1] Log In\n [2] Quit\n"
        )
        if selection not in ["1", "2"]:
            print("\nInvalid option. Please select from the choices listed above.\n")
            continue
        if int(selection) == 2:
            run = False
            break
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
