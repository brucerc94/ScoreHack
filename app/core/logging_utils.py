from __future__ import annotations

import logging
import sys

LOGGER_NAME = "scorecapture"
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"


def configure_logging() -> logging.Logger:
    """Configura una sola salida de consola para toda la aplicación."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)

    return logger
