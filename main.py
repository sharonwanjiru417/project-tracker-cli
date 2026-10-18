"""Project Tracker CLI entry point.

Examples:
    python main.py add-user --name "Alex" --email alex@example.com
    python main.py add-project --user "Alex" --title "CLI Tool" --due-date 2026-12-01
    python main.py add-task --project "CLI Tool" --title "Implement add-task"
    python main.py complete-task --id 1
"""

import argparse
import sys

from models import Tracker, TrackerError
from utils import display
from utils.logger import setup_logging
from utils.storage import DEFAULT_DATA_FILE, load_data, save_data
from utils.validators import parse_due_date


def build_parser():
    """Create the argparse parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="tracker", description="Multi-user project tracker CLI."
    )
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE,
                        help="path to the JSON data file (default: data/data.json)")
    parser.add_argument("--verbose", action="store_true", help="show debug logging")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("add-user", help="create a user")
    p.add_argument("--name", required=True, help="user's name (must be unique)")
    p.add_argument("--email", default="", help="user's email address")

    sub.add_parser("list-users", help="list all users")

    p = sub.add_parser("add-project", help="add a project to a user")
    p.add_argument("--user", required=True, help="owner's name or id")
    p.add_argument("--title", required=True, help="project title")
    p.add_argument("--description", default="", help="project description")
    p.add_argument("--due-date", help="due date, e.g. 2026-12-31")

    p = sub.add_parser("list-projects", help="list projects (optionally for one user)")
    p.add_argument("--user", help="only show this user's projects")

    p = sub.add_parser("search-projects", help="search project titles/descriptions")
    p.add_argument("--query", required=True, help="text to search for")
    p.add_argument("--user", help="limit search to this user")

    p = sub.add_parser("update-project", help="edit a project")
    p.add_argument("--project", required=True, help="project title or id")
    p.add_argument("--user", help="owner (to disambiguate duplicate titles)")
    p.add_argument("--title", help="new title")
    p.add_argument("--description", help="new description")
    p.add_argument("--due-date", help="new due date")

    p = sub.add_parser("delete-project", help="delete a project and its tasks")
    p.add_argument("--project", required=True, help="project title or id")
    p.add_argument("--user", help="owner (to disambiguate duplicate titles)")

    p = sub.add_parser("add-task", help="add a task to a project")
    p.add_argument("--project", required=True, help="project title or id")
    p.add_argument("--title", required=True, help="task title")
    p.add_argument("--assign", help="user to assign the task to")
    p.add_argument("--user", help="project owner (to disambiguate duplicate titles)")

    p = sub.add_parser("list-tasks", help="list a project's tasks")
    p.add_argument("--project", required=True, help="project title or id")
    p.add_argument("--user", help="project owner (to disambiguate duplicate titles)")

    p = sub.add_parser("assign-task", help="assign a task to a user")
    p.add_argument("--id", required=True, help="task id")
    p.add_argument("--user", required=True, help="user name or id")

    p = sub.add_parser("complete-task", help="mark a task as completed")
    p.add_argument("--id", required=True, help="task id")

    return parser


def _project_row(tracker, project):
    """Build one table row describing a project."""
    owner = tracker.get_user_by_id(project.owner_id)
    tasks = tracker.tasks_for(project)
    done = sum(1 for t in tasks if t.is_complete)
    due = project.due_date or "-"
    if project.is_overdue:
        due += " (overdue)"
    return (project.id, project.title, owner.name if owner else "?", due,
            f"{done}/{len(tasks)}")


def _show_projects(tracker, projects):
    """Display a list of projects as a table."""
    rows = [_project_row(tracker, p) for p in projects]
    display.table("Projects", ["ID", "Title", "Owner", "Due", "Done"], rows)


def run_command(args, tracker):
    """Execute the chosen subcommand. Returns True if data changed."""
    cmd = args.command

    if cmd == "add-user":
        user = tracker.add_user(args.name, args.email)
        display.success(f"Added user {user}")
        return True

    if cmd == "list-users":
        rows = [(u.id, u.name, u.email or "-", len(tracker.projects_for(u)))
                for u in tracker.users]
        display.table("Users", ["ID", "Name", "Email", "Projects"], rows)
        return False

    if cmd == "add-project":
        due = parse_due_date(args.due_date) if args.due_date else None
        project = tracker.add_project(args.user, args.title, args.description, due)
        display.success(f"Added project {project}")
        return True

    if cmd == "list-projects":
        projects = (tracker.projects_for(tracker.find_user(args.user))
                    if args.user else tracker.projects)
        _show_projects(tracker, projects)
        return False

    if cmd == "search-projects":
        _show_projects(tracker, tracker.search_projects(args.query, args.user))
        return False

    if cmd == "update-project":
        due = parse_due_date(args.due_date) if args.due_date else None
        project = tracker.update_project(
            args.project, args.user,
            title=args.title, description=args.description, due_date=due)
        display.success(f"Updated project {project}")
        return True

    if cmd == "delete-project":
        project = tracker.delete_project(args.project, args.user)
        display.success(f"Deleted project '{project.title}' and its tasks")
        return True

    if cmd == "add-task":
        task = tracker.add_task(args.project, args.title, args.assign, args.user)
        display.success(f"Added task {task}")
        return True

    if cmd == "list-tasks":
        project = tracker.find_project(
            args.project, tracker.find_user(args.user) if args.user else None)
        rows = []
        for t in tracker.tasks_for(project):
            who = tracker.get_user_by_id(t.assigned_to)
            rows.append((t.id, t.title, t.status, who.name if who else "-"))
        display.table(f"Tasks for {project.title}",
                      ["ID", "Title", "Status", "Assigned to"], rows)
        names = ", ".join(u.name for u in tracker.contributors(project))
        if names:
            display.info(f"Contributors: {names}")
        return False

    if cmd == "assign-task":
        task = tracker.assign_task(args.id, args.user)
        display.success(f"Assigned task #{task.id} to {args.user}")
        return True

    if cmd == "complete-task":
        task = tracker.complete_task(args.id)
        display.success(f"Completed task {task}")
        return True

    raise TrackerError(f"Unknown command '{cmd}'.")


def main(argv=None):
    """Parse arguments, run the command, persist changes. Returns an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        return 0

    try:
        tracker = Tracker.from_dict(load_data(args.data_file))
        if run_command(args, tracker):
            save_data(tracker.to_dict(), args.data_file)
    except (TrackerError, ValueError) as exc:
        display.error(str(exc))
        return 1
    except OSError as exc:
        display.error(f"File problem: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
