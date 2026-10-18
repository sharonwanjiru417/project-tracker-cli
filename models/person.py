"""Base class for people in the system (parent of :class:`models.user.User`)."""

import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Person:
    """A named person with an email address.

    ``name`` and ``email`` are exposed through properties so that every
    assignment goes through validation (encapsulation).
    """

    def __init__(self, name, email=""):
        self._name = None
        self._email = ""
        self.name = name
        self.email = email

    @property
    def name(self):
        """The person's display name."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name, rejecting empty values."""
        value = (value or "").strip()
        if not value:
            raise ValueError("Name cannot be empty.")
        self._name = value

    @property
    def email(self):
        """The person's email address (may be blank)."""
        return self._email

    @email.setter
    def email(self, value):
        """Set the email, rejecting malformed non-empty values."""
        value = (value or "").strip()
        if value and not EMAIL_PATTERN.match(value):
            raise ValueError(f"'{value}' is not a valid email address.")
        self._email = value

    def __str__(self):
        return f"{self.name} <{self.email}>" if self.email else self.name

    def __repr__(self):
        return f"{type(self).__name__}(name={self.name!r}, email={self.email!r})"
