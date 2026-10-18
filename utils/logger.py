"""Logging setup. Use ``--verbose`` on the CLI to see debug output."""

import logging


def setup_logging(verbose=False):
    """Configure root logging; DEBUG when verbose, WARNING otherwise."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s [%(name)s] %(message)s",
        force=True,
    )
