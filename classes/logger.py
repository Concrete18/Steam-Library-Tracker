from logging.handlers import RotatingFileHandler
import logging as lg


class Logger:
    def __init__(self) -> None:
        """
        Logger init.
        """
        pass

    format = "%(asctime)s %(levelname)s %(message)s"
    date_format = "%m-%d-%Y %I:%M:%S %p"
    log_formatter = lg.Formatter(format, datefmt=date_format)

    def create_log(self, log_path, log_level=lg.DEBUG):
        """
        Creates a logging instance that allows you to log in a file
        named after `log_name`.
        """
        logger = lg.getLogger(__name__)
        # Log Level
        logger.setLevel(log_level)

        my_handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=2,
        )
        my_handler.setFormatter(self.log_formatter)
        logger.addHandler(my_handler)
        return logger
