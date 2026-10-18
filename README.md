# Project Tracker CLI

A Python command-line tool for managing **users**, **projects** and **tasks**
for a small team. Data is saved locally as JSON, so everything you add is still
there next time you run the tool.

## Features

- Create and list users (name + optional email)
- Add projects to a user, list them, search them, update them, delete them
- Add tasks to projects, assign them to users, mark them complete
- Projects show progress (`done/total`), overdue flags and their contributors
- Friendly error messages and exit codes (no tracebacks for normal mistakes)
- Corrupt or missing data files are handled safely (see *Persistence* below)

## Data model

```
User 1 ───< Project 1 ───< Task >─── 0..1 User (assignee)
```

- **One-to-many:** a user owns many projects; a project has many tasks.
- **Many-to-many:** users contribute to many projects through task assignments
  (`Tracker.contributors(project)`).
- `User` inherits from `Person`; names, emails, titles, dates and statuses are
  validated through `@property` setters; each class keeps an auto-increment
  id counter as a class attribute.

## Project layout

```
main.py            CLI entry point (argparse subcommands)
models/            Person, User, Project, Task, Tracker (relationships + rules)
utils/             storage.py (JSON I/O), validators.py, display.py, logger.py
data/data.json     local JSON storage
tests/             unittest-style tests (run with pytest or unittest)
requirements.txt   dependencies (a Pipfile is also provided)
```

## Setup

Requires Python 3.10+.

```bash
git clone <your-repo-url>
cd project-tracker-cli

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Using Pipenv instead: `pipenv install --dev`, then `pipenv shell`.

External packages:
- **rich**: coloured tables and messages (falls back to plain text if missing)
- **python-dateutil**: flexible due-date parsing (`"1 Dec 2026"` → `2026-12-01`)
- **pytest**: running the tests

## Usage

```bash
python main.py --help
python main.py <command> --help
```

| Command | Example |
|---|---|
| `add-user` | `python main.py add-user --name "Alex" --email alex@example.com` |
| `list-users` | `python main.py list-users` |
| `add-project` | `python main.py add-project --user "Alex" --title "CLI Tool" --due-date 2026-12-01` |
| `list-projects` | `python main.py list-projects --user "Alex"` |
| `search-projects` | `python main.py search-projects --query "cli" --user "Alex"` |
| `update-project` | `python main.py update-project --project "CLI Tool" --description "New text"` |
| `delete-project` | `python main.py delete-project --project "CLI Tool"` |
| `add-task` | `python main.py add-task --project "CLI Tool" --title "Implement add-task" --assign "Alex"` |
| `list-tasks` | `python main.py list-tasks --project "CLI Tool"` |
| `assign-task` | `python main.py assign-task --id 1 --user "Sam"` |
| `complete-task` | `python main.py complete-task --id 1` |

Global options (put them **before** the command):

- `--data-file PATH` use a different JSON file
- `--verbose` show debug logging

Users and projects can be referred to by name (case-insensitive) or by id.
If two users have a project with the same title, add `--user` or use the
project id.

## Persistence

All data lives in `data/data.json` (users, projects, tasks). Saves are atomic
(written to a temp file, then renamed). If the file is missing the tool starts
empty; if it is malformed, it is copied to `data.json.corrupt` and the tool
starts empty instead of crashing.

## Testing

```bash
pytest -v
# or, without pytest:
python -m unittest discover -s tests -t . -v
```

The tests cover model validation, relationships, search, serialisation, file
error handling and full CLI workflows against a temporary data file.

## Debugging

Run with `--verbose` to see log messages, e.g. when a data file is corrupt:

```bash
python main.py --verbose list-users
```

## Known issues / limitations

- Single-user local file: no locking if two terminals write at the same time.
- Users cannot be renamed or deleted yet.
- Tasks cannot be edited (title) or un-completed.
- Project titles are unique per user, but not across users.
