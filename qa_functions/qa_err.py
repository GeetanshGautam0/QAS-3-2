from typing import *
from .qa_custom import *
import time, sys


LOGGER_AVAIL = False
LOGGER_FUNCTION = lambda arg1: None
LOGGER_FILE = None


def raise_error(error_type, error_params: tuple, error_level: ErrorLevels, traceback: Optional[str] = ""):
    err_str = f"{time.ctime(time.time())}: [{error_level.name} ERROR]: {str(error_type(*error_params, ))}\n\n{traceback}".strip()

    log(err_str)
    raise error_type(*error_params)


def log(data: str):
    global LOGGER_AVAIL, LOGGER_FUNCTION, LOGGER_FILE

    sys.stderr.write(f"Quizzing Application at {data}")

    if not LOGGER_AVAIL or not isinstance(LOGGER_FILE, str):
        return
    LOGGER_FUNCTION(LoggingPackage(LoggingLevel.ERROR, data, LOGGER_FILE))
