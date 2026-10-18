"""Input parsing helpers (uses python-dateutil)."""

from dateutil import parser as date_parser


def parse_due_date(text):
    """Turn free-form text like ``2026-12-01`` or ``1 Dec 2026`` into ISO format.

    Raises ``ValueError`` with a friendly message on bad input.
    """
    if text is None:
        return None
    try:
        return date_parser.parse(text, dayfirst=False).date().isoformat()
    except (ValueError, OverflowError):
        raise ValueError(
            f"Could not understand date '{text}'. Try YYYY-MM-DD, e.g. 2026-12-31."
        ) from None
