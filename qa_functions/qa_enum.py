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


class Application(Enum):
    ADMINISTRATOR_TOOLS = 0
    QUIZZING_FORM = 1
    THEMING_UTIL = 2
    RECOVERY_UTIL = 3


class ThemeUpdateCommands(Enum):
    BG = 0
    FG = 1
    ACTIVE_BG = 2
    ACTIVE_FG = 3

    BORDER_COLOR = 4
    BORDER_SIZE = 5

    FONT = 6

    INVISIBLE_CONTAINER = 7

    WRAP_LENGTH = 8

    CUSTOM = -1


class ThemeUpdateVars(Enum):
    BG = 0
    FG = 1
    ACCENT = 2
    ERROR = 3
    WARNING = 4
    OKAY = 5

    GRAY = 16

    DEFAULT_FONT_FACE = 6
    ALT_FONT_FACE = 7

    FONT_SIZE_TITLE = 9
    FONT_SIZE_LARGE = 10
    FONT_SIZE_MAIN = 11
    FONT_SIZE_SMALL = 12
    FONT_SIZE_XL_TITLE = 16

    BORDER_SIZE = 14
    BORDER_COLOR = 15


class FileType(Enum):
    QA_ENC = 0
    QA_EXPORT = 1
    QA_FILE = 2
    QA_LOG = 3
    QA_QUIZ = 4
    QA_THEME = 5

