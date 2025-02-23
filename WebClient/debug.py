import logging
from logging.handlers import TimedRotatingFileHandler

def init_logging(log_file="debug.log"):
    """
    Initialize the logging configuration.
    This sets up a TimedRotatingFileHandler that rotates the log daily
    and keeps logs for the last 3 days.
    """
    logger = logging.getLogger()
    if not logger.hasHandlers():
        # Create a handler that rotates the log daily and keeps 3 backup files (3 days).
        handler = TimedRotatingFileHandler(
            log_file,
            when="D",        # Rotate daily
            interval=1,
            backupCount=3    # Keep logs for 3 days
        )
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.debug("Logging has been initialized.")

def log_event(message, level="DEBUG", exc_info=False):
    """
    Log a message at the specified level.
    
    Parameters:
      - message: The log message.
      - level: The severity level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
      - exc_info: If True, include exception information.
    """

    init_logging()
    
    level = level.upper()
    if level == "DEBUG":
        logging.debug(message)
    elif level == "INFO":
        logging.info(message)
    elif level == "WARNING":
        logging.warning(message)
    elif level == "ERROR":
        logging.error(message, exc_info=exc_info)
    elif level == "CRITICAL":
        logging.critical(message, exc_info=exc_info)
    else:
        logging.debug(message)
