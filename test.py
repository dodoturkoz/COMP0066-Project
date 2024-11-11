class User:
    """
    The global user profile through which all children are descended from.

    The user profile handles generic data such as email, password, first name, last name,
    date of birth, address.
    """

    def __init__(self, first_name, last_name, date_of_birth) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth

    pass
