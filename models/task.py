"""Task model."""

PENDING = "pending"
COMPLETED = "completed"
VALID_STATUSES = (PENDING, COMPLETED)


class Task:
    """A unit of work that belongs to one project and may be assigned to a user.

    Class attribute ``_next_id`` provides auto-incrementing ids.
    """

    _next_id = 1

    def __init__(self, title, project_id, assigned_to=None, status=PENDING, task_id=None):
        self._title = None
        self._status = PENDING
        self.id = task_id if task_id is not None else Task._take_id()
        self.title = title
        self.project_id = project_id
        self.assigned_to = assigned_to  # user id or None
        self.status = status
        Task.sync_counter(self.id)

    # ---- id counter helpers -------------------------------------------------
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

    # ---- properties ---------------------------------------------------------
    @property
    def title(self):
        """Task title."""
        return self._title

    @title.setter
    def title(self, value):
        """Set the title, rejecting empty values."""
        value = (value or "").strip()
        if not value:
            raise ValueError("Task title cannot be empty.")
        self._title = value

    @property
    def status(self):
        """Either ``pending`` or ``completed``."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the status, rejecting unknown values."""
        if value not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}.")
        self._status = value

    @property
    def is_complete(self):
        """True when the task has been completed."""
        return self._status == COMPLETED

    # ---- behaviour ----------------------------------------------------------
    def complete(self):
        """Mark the task as completed."""
        self.status = COMPLETED

    def to_dict(self):
        """Serialise to a JSON-friendly dict."""
        return {
            "id": self.id,
            "title": self.title,
            "project_id": self.project_id,
            "assigned_to": self.assigned_to,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Task from a dict produced by :meth:`to_dict`."""
        return cls(
            title=data["title"],
            project_id=data["project_id"],
            assigned_to=data.get("assigned_to"),
            status=data.get("status", PENDING),
            task_id=data["id"],
        )

    def __str__(self):
        mark = "x" if self.is_complete else " "
        return f"[{mark}] #{self.id} {self.title}"

    def __repr__(self):
        return (f"Task(id={self.id}, title={self.title!r}, "
                f"status={self.status!r}, assigned_to={self.assigned_to})")
