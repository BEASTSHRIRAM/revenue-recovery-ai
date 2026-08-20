"""Structured-ish console logging.

Kept deliberately small: one formatter that stays readable in a terminal during
development, and a single `configure_logging()` entry point called from the app
lifespan so import order never decides log formatting.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import settings

_FORMAT = "%(asctime)s  %(levelname)-7s  %(name)-28s  %(message)s"
_DATE_FORMAT = "%H:%M:%S"

_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # These are chatty at INFO and drown out our own signal.
    for noisy in ("httpx", "httpcore", "apscheduler.executors.default"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
