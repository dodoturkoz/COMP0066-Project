from database.setup import Database
from modules.login import login

db = Database()

try:
    print("Welcome to Breeze, your Mental Health and Wellbeing partner!\n")
    while True:
        selection = input(
            "Please select an option to continue:\n 1. Log In\n 2. Quit\n"
        )
        if selection not in ["1", "2"]:
            print("Invalid option. Please select 1 or 2.")
            continue
        if int(selection) == 2:
            break
        user = login(db)
        if user:
            user.flow()

except ValueError as e:
    # If instead of selecting a number the user types something, we get a ValueError
    print(e)  # TODO: delete this when we finish development
    print("Please make sure your input is a number.")
finally:
    # If we pass the execution loop, exit the app so db connection closes
    db.close()
