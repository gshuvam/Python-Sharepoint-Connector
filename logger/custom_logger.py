import os
import logging
from datetime import datetime

class CustomLoggerSetup:
    SUCCESS_LEVEL_NUM = 25
    _logs_dir = 'logs'
    _file_handler = None
    _is_initialized = False

    @classmethod
    def get_logger(cls, name, log_dir=None):
        if not cls._is_initialized:
            cls._setup(log_dir)

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        return logger

    @classmethod
    def _setup(cls, log_dir=None):
        if log_dir:
            cls._logs_dir = log_dir

        logging.addLevelName(CustomLoggerSetup.SUCCESS_LEVEL_NUM, 'SUCCESS')

        class CustomLogger(logging.Logger):
            def success(self, message, *args, **kwargs):
                if self.isEnabledFor(CustomLoggerSetup.SUCCESS_LEVEL_NUM):
                    self._log(CustomLoggerSetup.SUCCESS_LEVEL_NUM, message, args, **kwargs)

        logging.setLoggerClass(CustomLogger)

        class CustomFormatter(logging.Formatter):
            grey = "\x1b[38;20m"
            green = "\x1B[32;20m"
            yellow = "\x1b[33;20m"
            red = "\x1b[31;20m"
            bold_red = "\x1b[31;1m"
            reset = "\x1b[0m"
            format = "%(asctime)s - %(name)s - %(message)s"

            FORMATS = {
                logging.DEBUG: green + format + reset,
                logging.INFO: grey + format + reset,
                CustomLoggerSetup.SUCCESS_LEVEL_NUM: green + format + reset,
                logging.WARNING: yellow + format + reset,
                logging.ERROR: red + format + reset,
                logging.CRITICAL: bold_red + format + reset
            }

            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                if log_fmt:
                    formatter = logging.Formatter(log_fmt)
                    return formatter.format(record)
                return super().format(record=record)

        if not os.path.exists(cls._logs_dir):
            os.mkdir(cls._logs_dir)

        log_file = os.path.join(cls._logs_dir, datetime.now().strftime("ListSync_%Y-%m-%d_%H-%M-%S.log"))
        cls._file_handler = logging.FileHandler(log_file)
        cls._file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
        cls._file_handler.setFormatter(file_formatter)

        #console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = CustomFormatter()
        console_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        if not any(isinstance(handler, logging.FileHandler) for handler in root_logger.handlers):
            root_logger.addHandler(cls._file_handler)
        if not any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
            root_logger.addHandler(cls._file_handler)
        root_logger.addHandler(console_handler)
        cls._is_initialized = True

def get_logger(name, log_dir=None):
    return CustomLoggerSetup.get_logger(name, log_dir)