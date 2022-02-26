from enum import Enum


class LoggingLevel(Enum):
    INFO = 0
    DEBUG = 1
    WARNING = 2
    ERROR = 3


class ScriptLevelID(Enum):
    CALL = 0
    MAIN = 1
    BACKEND = 2


class ExitCodes(Enum):
    NORMAL = 0
    UNCAUGHT_ERROR = -1
    GENERAL_ERROR = 1
    UNKNOWN = 2


class CLI(Enum):
    UNKNOWN = 0
    COMMAND = 1
    ARGUMENT = 2


class ErrorLevels(Enum):
    FATAL = 0
    NON_FATAL = 1

