"""Unit tests for the model classes and the Tracker aggregate."""

import unittest

from models import Person, Project, Task, Tracker, TrackerError, User


class ModelTestCase(unittest.TestCase):
    """Reset id counters so tests are independent."""

    def setUp(self):
        User.reset_counter()
        Project.reset_counter()
        Task.reset_counter()
        self.tracker = Tracker()


class TestPersonAndUser(ModelTestCase):
    def test_user_inherits_person(self):
        self.assertTrue(issubclass(User, Person))

    def test_name_is_trimmed_and_required(self):
        self.assertEqual(User("  Alex ").name, "Alex")
        with self.assertRaises(ValueError):
            User("   ")

    def test_invalid_email_rejected(self):
        with self.assertRaises(ValueError):
            User("Alex", "not-an-email")

    def test_ids_auto_increment(self):
        self.assertEqual((User("A").id, User("B").id), (1, 2))

    def test_str_and_repr(self):
        user = User("Alex", "a@b.co")
        self.assertEqual(str(user), "Alex <a@b.co>")
        self.assertIn("User(id=1", repr(user))


class TestProjectAndTask(ModelTestCase):
    def test_due_date_validation(self):
        self.assertEqual(Project("P", 1, due_date="2030-01-02").due_date, "2030-01-02")
        with self.assertRaises(ValueError):
            Project("P", 1, due_date="02/01/2030")

    def test_overdue(self):
        self.assertTrue(Project("P", 1, due_date="2000-01-01").is_overdue)
        self.assertFalse(Project("P", 1).is_overdue)

    def test_matches_title_and_description(self):
        project = Project("CLI Tool", 1, description="Built with argparse")
        self.assertTrue(project.matches("cli"))
        self.assertTrue(project.matches("ARGPARSE"))
        self.assertFalse(project.matches("django"))

    def test_task_complete_and_status_validation(self):
        task = Task("Write docs", 1)
        self.assertEqual(task.status, "pending")
        task.complete()
        self.assertTrue(task.is_complete)
        with self.assertRaises(ValueError):
            task.status = "banana"

    def test_round_trip_dicts(self):
        task = Task("T", 3, assigned_to=2)
        clone = Task.from_dict(task.to_dict())
        self.assertEqual(clone.to_dict(), task.to_dict())


class TestTracker(ModelTestCase):
    def setUp(self):
        super().setUp()
        self.tracker.add_user("Alex", "alex@example.com")
        self.tracker.add_user("Sam")

    def test_duplicate_user_rejected(self):
        with self.assertRaises(TrackerError):
            self.tracker.add_user("alex")

    def test_add_project_links_to_user(self):
        project = self.tracker.add_project("Alex", "CLI Tool")
        alex = self.tracker.find_user("alex")
        self.assertEqual(self.tracker.projects_for(alex), [project])

    def test_unknown_user_raises(self):
        with self.assertRaises(TrackerError):
            self.tracker.add_project("Nobody", "X")

    def test_duplicate_title_same_user_rejected_but_ok_for_other_user(self):
        self.tracker.add_project("Alex", "Site")
        with self.assertRaises(TrackerError):
            self.tracker.add_project("Alex", "site")
        self.tracker.add_project("Sam", "Site")

    def test_ambiguous_project_title_needs_user(self):
        self.tracker.add_project("Alex", "Site")
        self.tracker.add_project("Sam", "Site")
        with self.assertRaises(TrackerError):
            self.tracker.add_task("Site", "T")
        task = self.tracker.add_task("Site", "T", user_ref="Sam")
        self.assertEqual(task.project_id, self.tracker.find_project("2").id)

    def test_tasks_and_contributors(self):
        self.tracker.add_project("Alex", "CLI Tool")
        self.tracker.add_task("CLI Tool", "A", assignee_ref="Alex")
        self.tracker.add_task("CLI Tool", "B", assignee_ref="Sam")
        self.tracker.add_task("CLI Tool", "C")
        project = self.tracker.find_project("CLI Tool")
        self.assertEqual(len(self.tracker.tasks_for(project)), 3)
        names = sorted(u.name for u in self.tracker.contributors(project))
        self.assertEqual(names, ["Alex", "Sam"])

    def test_complete_task_twice_errors(self):
        self.tracker.add_project("Alex", "P")
        task = self.tracker.add_task("P", "T")
        self.tracker.complete_task(task.id)
        with self.assertRaises(TrackerError):
            self.tracker.complete_task(task.id)

    def test_assign_task(self):
        self.tracker.add_project("Alex", "P")
        task = self.tracker.add_task("P", "T")
        self.tracker.assign_task(task.id, "Sam")
        self.assertEqual(task.assigned_to, self.tracker.find_user("Sam").id)

    def test_update_project(self):
        self.tracker.add_project("Alex", "P")
        project = self.tracker.update_project("P", description="new", due_date="2031-05-06")
        self.assertEqual((project.description, project.due_date), ("new", "2031-05-06"))

    def test_search_scoped_to_user(self):
        self.tracker.add_project("Alex", "Website redesign")
        self.tracker.add_project("Sam", "Website backend")
        self.assertEqual(len(self.tracker.search_projects("website")), 2)
        self.assertEqual(len(self.tracker.search_projects("website", "Sam")), 1)

    def test_delete_project_removes_tasks(self):
        self.tracker.add_project("Alex", "P")
        self.tracker.add_task("P", "T")
        self.tracker.delete_project("P")
        self.assertEqual((self.tracker.projects, self.tracker.tasks), ([], []))

    def test_serialisation_round_trip_and_counters(self):
        self.tracker.add_project("Alex", "P")
        self.tracker.add_task("P", "T", assignee_ref="Sam")
        restored = Tracker.from_dict(self.tracker.to_dict())
        self.assertEqual(restored.to_dict(), self.tracker.to_dict())
        self.assertEqual(restored.add_user("New").id, 3)  # counter synced

    def test_orphans_dropped_on_load(self):
        data = {
            "users": [{"id": 1, "name": "A", "email": ""}],
            "projects": [{"id": 1, "title": "P", "owner_id": 99}],
            "tasks": [{"id": 1, "title": "T", "project_id": 1}],
        }
        restored = Tracker.from_dict(data)
        self.assertEqual((restored.projects, restored.tasks), ([], []))


if __name__ == "__main__":
    unittest.main()
