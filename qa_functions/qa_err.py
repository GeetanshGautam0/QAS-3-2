import time, sys
from . import qa_custom
from . import qa_enum
from typing import *


LOGGER_AVAIL = False
LOGGER_FUNCTION = lambda *args: 0
LOGGER_FILE = None


def raise_error(error_type: Type[Exception], error_params: List[Any], error_level: qa_enum.ErrorLevels, traceback: Optional[str] = "") -> None:
    err_str = f"{time.ctime(time.time())}: [{error_level.name} ERROR]: {str(error_type(*error_params, ))}\n\n{traceback}".strip()

    log(err_str)
    raise error_type(*error_params)


def log(data: str) -> None:
    global LOGGER_AVAIL, LOGGER_FUNCTION, LOGGER_FILE

    sys.stderr.write(f"Quizzing Application at {data}")

    if not LOGGER_AVAIL or not isinstance(LOGGER_FILE, str):
        return

    LOGGER_FUNCTION(qa_custom.LoggingPackage(qa_enum.LoggingLevel.ERROR, data, LOGGER_FILE))
