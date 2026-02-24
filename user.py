class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name

    def __repr__(self):
        return f"User(id={self.id}, name={self.name})"

    def __str__(self):
        return f"User(id={self.id}, name={self.name})"

    def __eq__(self, other):
        return self.id == other.id and self.name == other.name

    def __ne__(self, other):
        return self.id != other.id or self.name != other.name

    def __hash__(self):
        return hash((self.id, self.name))

    