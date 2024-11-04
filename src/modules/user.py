class User:
    user_id: str
    username: str
    email: str
    is_active: bool

    def __init__(
        self, user_id: str, username: str, email: str, is_active: bool, *args, **kwargs
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.is_active = is_active

    def edit_info(self):
        pass

    def flow(self) -> bool:
        raise Exception("Need to override!")
