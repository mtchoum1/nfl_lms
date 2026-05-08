from settings import Settings
from user import User


class League:
    def __init__(self, id, name, users: list[User], settings: Settings):
        self.id = id
        self.name = name
        self.users = users
        self.settings = settings

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def __repr__(self):
        return f"League(id={self.id}, name={self.name})"
