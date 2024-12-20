import sqlite3
from typing import Any
from database.setup import Database


class User:
    database: Database
    user_id: int
    username: str
    first_name: str
    surname: str
    email: str
    is_active: bool

    def __init__(
        self,
        database: Database,
        user_id: int,
        username: str,
        first_name: str,
        surname: str,
        email: str,
        is_active: bool,
        *args,
        **kwargs,
    ):
        self.database = database
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.surname = surname
        self.email = email
        self.is_active = is_active

    def edit_info(
        self, attribute: str, value: Any, success_message: str = None
    ) -> bool:
        """
        Updates the attribute both in the object and in the database,
        returns the result of the update
        """

        try:
            # First update on the database
            self.database.cursor.execute(
                f"UPDATE Users SET {attribute} = ? WHERE user_id = ?",
                (value, self.user_id),
            )
            self.database.connection.commit()

            # Then in the object if that particular attribute is stored here
            if hasattr(self, attribute):
                setattr(self, attribute, value)

            # Optional message to show the user when the operation is complete
            if success_message is None:
                print(
                    f"{attribute.replace('_', ' ').capitalize()} updated successfully."
                )
            else:
                print(success_message)

            # Return true as the update was successful
            return True

        # If there is an error with the query
        except sqlite3.OperationalError as e:
            print(
                f"There was an error updating the {attribute.replace('_', ' ').capitalize()}.\n Error: {e}"
            )
            return False

    def flow(self) -> bool:
        raise Exception("Need to override!")
