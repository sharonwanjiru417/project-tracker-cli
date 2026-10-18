"""User model (inherits from Person)."""

from models.person import Person


class User(Person):
    """A team member who owns projects and can be assigned tasks."""

    _next_id = 1

    def __init__(self, name, email="", user_id=None):
        super().__init__(name, email)
        self.id = user_id if user_id is not None else User._take_id()
        User.sync_counter(self.id)

    @classmethod
    def _take_id(cls):
        """Return the next free id and advance the counter."""
        value = cls._next_id
        cls._next_id += 1
        return value

    @classmethod
    def sync_counter(cls, used_id):
        """Make sure future ids never collide with ``used_id``."""
        cls._next_id = max(cls._next_id, used_id + 1)

    @classmethod
    def reset_counter(cls):
        """Reset the id counter (used when loading data and in tests)."""
        cls._next_id = 1

    def to_dict(self):
        """Serialise to a JSON-friendly dict."""
        return {"id": self.id, "name": self.name, "email": self.email}

    @classmethod
    def from_dict(cls, data):
        """Build a User from a dict produced by :meth:`to_dict`."""
        return cls(name=data["name"], email=data.get("email", ""), user_id=data["id"])

    def __repr__(self):
        return f"User(id={self.id}, name={self.name!r}, email={self.email!r})"
