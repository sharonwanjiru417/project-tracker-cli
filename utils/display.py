"""Terminal output. Uses ``rich`` for tables/colours; falls back to plain text."""

try:
    from rich.console import Console
    from rich.table import Table

    _console = Console()
    HAS_RICH = True
except ImportError:  # pragma: no cover - exercised only without rich installed
    _console = None
    HAS_RICH = False


def success(message):
    """Print a success message."""
    _print(f"[green]✔[/green] {message}", f"OK: {message}")


def error(message):
    """Print an error message to the terminal."""
    _print(f"[bold red]Error:[/bold red] {message}", f"Error: {message}")


def info(message):
    """Print a neutral message."""
    _print(message, message)


def table(title, columns, rows):
    """Print ``rows`` (list of tuples) under ``columns`` as a table."""
    if not rows:
        info(f"No {title.lower()} found.")
        return
    if HAS_RICH:
        tbl = Table(title=title)
        for col in columns:
            tbl.add_column(col)
        for row in rows:
            tbl.add_row(*[str(cell) for cell in row])
        _console.print(tbl)
    else:
        print(title)
        print(" | ".join(columns))
        print("-" * 40)
        for row in rows:
            print(" | ".join(str(cell) for cell in row))


def _print(rich_text, plain_text):
    """Print using rich markup when available, plain text otherwise."""
    if HAS_RICH:
        _console.print(rich_text)
    else:
        print(plain_text)
