"""
Application-wide logger.

CRITICAL PRIVACY RULE: this logger must never be used to log clipboard
content or saved expression text. Only technical/diagnostic messages
(e.g. "database connection failed", "hotkey registration error") should
be logged. Call sites are responsible for not passing sensitive text;
this module exists mainly to give a single, consistent place to
configure log rotation/format so that rule is easy to audit.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.utils.paths import get_log_path

_LOGGER_NAME = "personal_text_manager"
_configured = False


def get_logger() -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if not _configured:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        try:
            file_handler = RotatingFileHandler(
                get_log_path(), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            # If we can't write logs (e.g. locked down environment), fall
            # back to console only rather than crashing the app.
            pass

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        _configured = True
    return logger
