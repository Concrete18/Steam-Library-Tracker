from logging.handlers import RotatingFileHandler
import logging as lg


class Logger:
    def __init__(self) -> None:
        """
        Logger init.
        """
        pass

    base_format = "%(asctime)s %(levelname)s %(message)s"
    date_format = "%m-%d-%Y %I:%M:%S %p"

    def create_log(self, name, log_path="logfile.log", log_level=lg.DEBUG):
        """
        Creates a logging instance that allows you to log in a file
        named after `log_name`.
        """
        log_formatter = lg.Formatter(self.base_format, datefmt=self.date_format)
        logger = lg.getLogger(name)
        # Log Level
        logger.setLevel(log_level)
        my_handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=2,
        )
        my_handler.setFormatter(log_formatter)
        logger.addHandler(my_handler)
        return logger
