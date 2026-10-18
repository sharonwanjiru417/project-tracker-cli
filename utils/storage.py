"""JSON persistence helpers with defensive error handling."""

import json
import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)

DEFAULT_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "data.json"
)
EMPTY_DATA = {"users": [], "projects": [], "tasks": []}


def load_data(path=DEFAULT_DATA_FILE):
    """Load the saved dict from ``path``.

    * Missing file  -> returns empty data (first run).
    * Malformed JSON or wrong shape -> the bad file is backed up to
      ``<path>.corrupt`` and empty data is returned, so the tool never crashes.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        logger.info("No data file at %s; starting fresh.", path)
        return _empty()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Corrupt data file %s: %s", path, exc)
        _backup_corrupt(path)
        return _empty()
    except OSError as exc:
        raise OSError(f"Could not read {path}: {exc}") from exc

    if not isinstance(data, dict):
        logger.warning("Unexpected structure in %s", path)
        _backup_corrupt(path)
        return _empty()
    return data


def save_data(data, path=DEFAULT_DATA_FILE):
    """Write ``data`` to ``path`` atomically (temp file, then rename)."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise OSError(f"Could not save to {path}: {exc}") from exc


def _empty():
    """Return a fresh copy of the empty data structure."""
    return {key: [] for key in EMPTY_DATA}


def _backup_corrupt(path):
    """Copy an unreadable data file aside so the user can recover it."""
    try:
        shutil.copyfile(path, path + ".corrupt")
    except OSError:
        logger.exception("Could not back up corrupt file %s", path)
