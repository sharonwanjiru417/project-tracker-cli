"""Tracker: the aggregate that owns all users, projects and tasks.

It enforces the relationships:
    User 1 --- * Project 1 --- * Task * --- 0..1 User (assignee)
Projects therefore have many contributors (the distinct assignees of their
tasks), giving a many-to-many link between users and projects.
"""

from models.project import Project
from models.task import Task
from models.user import User


class TrackerError(Exception):
    """Raised for any user-facing domain error (not found, duplicate, ...)."""


class Tracker:
    """In-memory store with lookup and mutation helpers."""

    def __init__(self):
        self.users = []
        self.projects = []
        self.tasks = []

    # ---- lookups ------------------------------------------------------------
    def find_user(self, ref):
        """Find a user by id or case-insensitive name; raise if missing."""
        ref = str(ref).strip()
        for user in self.users:
            if str(user.id) == ref or user.name.lower() == ref.lower():
                return user
        raise TrackerError(f"User '{ref}' not found.")

    def find_projects(self, ref, user=None):
        """Return projects matching an id or exact title (optionally for one user)."""
        ref = str(ref).strip()
        pool = self.projects if user is None else self.projects_for(user)
        by_id = [p for p in pool if str(p.id) == ref]
        if by_id:
            return by_id
        return [p for p in pool if p.title.lower() == ref.lower()]

    def find_project(self, ref, user=None):
        """Find exactly one project by id/title; raise if missing or ambiguous."""
        matches = self.find_projects(ref, user)
        if not matches:
            raise TrackerError(f"Project '{ref}' not found.")
        if len(matches) > 1:
            ids = ", ".join(str(p.id) for p in matches)
            raise TrackerError(
                f"Several projects are called '{ref}' (ids: {ids}). "
                "Use the project id or add --user."
            )
        return matches[0]

    def find_task(self, task_id):
        """Find a task by numeric id; raise if missing."""
        for task in self.tasks:
            if str(task.id) == str(task_id):
                return task
        raise TrackerError(f"Task #{task_id} not found.")

    def projects_for(self, user):
        """All projects owned by ``user``."""
        return [p for p in self.projects if p.owner_id == user.id]

    def tasks_for(self, project):
        """All tasks of ``project``."""
        return [t for t in self.tasks if t.project_id == project.id]

    def contributors(self, project):
        """Distinct users who are assigned at least one task in ``project``."""
        ids = {t.assigned_to for t in self.tasks_for(project) if t.assigned_to}
        return [u for u in self.users if u.id in ids]

    def get_user_by_id(self, user_id):
        """Return the user with this id, or None."""
        return next((u for u in self.users if u.id == user_id), None)

    # ---- mutations ----------------------------------------------------------
    def add_user(self, name, email=""):
        """Create a user; names must be unique (case-insensitive)."""
        if any(u.name.lower() == name.strip().lower() for u in self.users):
            raise TrackerError(f"User '{name}' already exists.")
        try:
            user = User(name, email)
        except ValueError as exc:
            raise TrackerError(str(exc)) from None
        self.users.append(user)
        return user

    def add_project(self, user_ref, title, description="", due_date=None):
        """Create a project for a user; titles are unique per user."""
        user = self.find_user(user_ref)
        if any(p.title.lower() == title.strip().lower() for p in self.projects_for(user)):
            raise TrackerError(f"{user.name} already has a project called '{title}'.")
        try:
            project = Project(title, user.id, description, due_date)
        except ValueError as exc:
            raise TrackerError(str(exc)) from None
        self.projects.append(project)
        return project

    def update_project(self, project_ref, user_ref=None, **changes):
        """Update title/description/due_date of a project (None values are ignored)."""
        user = self.find_user(user_ref) if user_ref else None
        project = self.find_project(project_ref, user)
        try:
            for field in ("title", "description", "due_date"):
                if changes.get(field) is not None:
                    setattr(project, field, changes[field])
        except ValueError as exc:
            raise TrackerError(str(exc)) from None
        return project

    def delete_project(self, project_ref, user_ref=None):
        """Delete a project and all of its tasks."""
        user = self.find_user(user_ref) if user_ref else None
        project = self.find_project(project_ref, user)
        self.tasks = [t for t in self.tasks if t.project_id != project.id]
        self.projects.remove(project)
        return project

    def add_task(self, project_ref, title, assignee_ref=None, user_ref=None):
        """Create a task in a project, optionally assigned to a user."""
        owner = self.find_user(user_ref) if user_ref else None
        project = self.find_project(project_ref, owner)
        assignee = self.find_user(assignee_ref) if assignee_ref else None
        try:
            task = Task(title, project.id, assignee.id if assignee else None)
        except ValueError as exc:
            raise TrackerError(str(exc)) from None
        self.tasks.append(task)
        return task

    def assign_task(self, task_id, user_ref):
        """Assign an existing task to a user."""
        task = self.find_task(task_id)
        task.assigned_to = self.find_user(user_ref).id
        return task

    def complete_task(self, task_id):
        """Mark a task as completed (error if it already is)."""
        task = self.find_task(task_id)
        if task.is_complete:
            raise TrackerError(f"Task #{task.id} is already completed.")
        task.complete()
        return task

    def search_projects(self, query, user_ref=None):
        """Search project titles/descriptions, optionally for one user."""
        user = self.find_user(user_ref) if user_ref else None
        pool = self.projects_for(user) if user else self.projects
        return [p for p in pool if p.matches(query)]

    # ---- serialisation ------------------------------------------------------
    def to_dict(self):
        """Serialise everything to a JSON-friendly dict."""
        return {
            "users": [u.to_dict() for u in self.users],
            "projects": [p.to_dict() for p in self.projects],
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Tracker from saved data, dropping orphaned records."""
        User.reset_counter()
        Project.reset_counter()
        Task.reset_counter()
        tracker = cls()
        tracker.users = [User.from_dict(d) for d in data.get("users", [])]
        user_ids = {u.id for u in tracker.users}
        tracker.projects = [
            Project.from_dict(d) for d in data.get("projects", [])
            if d.get("owner_id") in user_ids
        ]
        project_ids = {p.id for p in tracker.projects}
        tracker.tasks = [
            Task.from_dict(d) for d in data.get("tasks", [])
            if d.get("project_id") in project_ids
        ]
        return tracker
