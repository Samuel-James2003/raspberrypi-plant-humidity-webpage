import logging

def init_logging(log_file="debug.log"):
    """
    Initialize the logging configuration.
    This sets up the log file, logging level, and format.
    """
    # Check if logging is already configured
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.debug("Logging has been initialized.")

def log_event(message, level="DEBUG", exc_info=False):
    """
    Log a message at the specified level.
    
    Parameters:
      - message: The log message.
      - level: The severity level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
      - exc_info: If True, include exception information.
    """
    # Ensure logging is initialized
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
