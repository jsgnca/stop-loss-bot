# logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "stoploss",
                 log_file: str = "bot.log",
                 level: str = "INFO") -> logging.Logger:
    """
    Console + rotating file logger.
    Usage:
        from logger import setup_logger
        log = setup_logger()
        log.info("hello")
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    lvl = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(lvl)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(lvl)

    fh = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3)
    fh.setFormatter(fmt)
    fh.setLevel(lvl)

    logger.addHandler(ch)
    logger.addHandler(fh)

    # Don’t duplicate logs up the root logger
    logger.propagate = False
    return logger
