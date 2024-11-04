from src.database.setup import Database
from src.modules.login import login

db = Database()
run = True

print("Welcome to Breeze, your Mental Health and Wellbeing partner!\n")

while run:
    selection = input("Please select an option to continue:\n 1. Log In\n 2. Quit\n")

    if int(selection) == 2:
        run = False
        continue
    user = login(db)
    if user is not None:
        run = user.flow()

# If we pass the execution loop, exit the app so db connection closes
exit()
