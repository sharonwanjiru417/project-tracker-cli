"""Project model."""

from datetime import date


class Project:
    """A project owned by one user and containing many tasks."""

    _next_id = 1

    def __init__(self, title, owner_id, description="", due_date=None, project_id=None):
        self._title = None
        self._due_date = None
        self.id = project_id if project_id is not None else Project._take_id()
        self.title = title
        self.owner_id = owner_id
        self.description = (description or "").strip()
        self.due_date = due_date
        Project.sync_counter(self.id)

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

    @property
    def title(self):
        """Project title."""
        return self._title

    @title.setter
    def title(self, value):
        """Set the title, rejecting empty values."""
        value = (value or "").strip()
        if not value:
            raise ValueError("Project title cannot be empty.")
        self._title = value

    @property
    def due_date(self):
        """Due date as an ISO string (YYYY-MM-DD) or None."""
        return self._due_date

    @due_date.setter
    def due_date(self, value):
        """Set the due date; accepts None or an ISO ``YYYY-MM-DD`` string."""
        if value in (None, ""):
            self._due_date = None
            return
        try:
            date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("Due date must be in YYYY-MM-DD format.") from None
        self._due_date = value

    @property
    def is_overdue(self):
        """True if the due date is in the past."""
        return bool(self._due_date) and date.fromisoformat(self._due_date) < date.today()

    def matches(self, query):
        """Case-insensitive search across title and description."""
        query = query.lower()
        return query in self.title.lower() or query in self.description.lower()

    def to_dict(self):
        """Serialise to a JSON-friendly dict."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "owner_id": self.owner_id,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Project from a dict produced by :meth:`to_dict`."""
        return cls(
            title=data["title"],
            owner_id=data["owner_id"],
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            project_id=data["id"],
        )

    def __str__(self):
        due = f" (due {self.due_date})" if self.due_date else ""
        return f"#{self.id} {self.title}{due}"

    def __repr__(self):
        return f"Project(id={self.id}, title={self.title!r}, owner_id={self.owner_id})"
