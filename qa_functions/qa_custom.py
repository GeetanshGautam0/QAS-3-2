from typing import *
from dataclasses import dataclass
from .qa_enum import *
import re


# Globals
_DEFAULT_DATA_TYPE = bytes


class HexColor:
    def __init__(self, color: str):
        self.color = color.upper()
        assert self.check, 'Color provided does not match expected pattern (1)'

    def check(self) -> Union[str, None]:
        res = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', self.color)
        return cast(str, res) if res is not None else None


# Data Classes
@dataclass
class Theme:
    # Theme Information
    theme_file_name:            str
    theme_file_display_name:    str
    theme_display_name:         str
    theme_code:                 str

    theme_file_path:            str

    # Primary Colours
    background:                 HexColor
    foreground:                 HexColor

    # Accent Colours
    accent:                     HexColor
    error:                      HexColor
    warning:                    HexColor
    okay:                       HexColor

    # Additional Colours
    gray:                       HexColor

    # Font Faces
    font_face:                  str
    font_alt_face:              str

    # Font Sizes
    font_small_size:            Union[float, int]
    font_main_size:             Union[float, int]
    font_large_size:            Union[float, int]
    font_title_size:            Union[float, int]
    font_xl_title_size:         Union[float, int]

    # Border Information
    border_size:                Union[float, int]
    border_color:               HexColor


@dataclass
class LoggingPackage:
    logging_level: LoggingLevel
    data:                       str
    file_name:                  str
    script_name:                str


@dataclass
class SaveFunctionArgs:
    global _DEFAULT_DATA_TYPE

    append:                     bool
    encrypt:                    bool = False
    encryption_key:             bytes = b''
    delete_backup:              bool = False
    run_hash_check:             bool = True

    list_val_sep:               str = "\n"

    dict_key_val_sep:           str = " "
    dict_line_sep:              str = "\n"

    new_old_data_sep:           str = "\n"

    save_data_type:             type = _DEFAULT_DATA_TYPE


@dataclass
class ConverterFunctionArgs:
    list_line_sep:              Union[str, bytes] = "\n"

    dict_key_val_sep:           Union[str, bytes] = " "
    dict_line_sep:              Union[str, bytes] = "\n"


@dataclass
class OpenFunctionArgs:
    global _DEFAULT_DATA_TYPE

    d_type:                     type = bytes
    lines_mode:                 bool = False


# Instance Classes

class File:
    def __init__(self, file_path: str):
        assert isinstance(file_path, str)

        self.file_path = file_path
        self.path, self.file_name = File.split_file_path(self.file_path)

    @staticmethod
    def split_file_path(file_path: str) -> Tuple[str, str]:
        assert isinstance(file_path, str)

        tokens = file_path.replace("\\", '/').split('/')
        return "\\".join(i for i in tokens[:-1:]), tokens[-1]


# Exceptions

class CannotCreateBackup(Exception):
    def __init__(self, original_file: str, traceback: str):
        self.original_file, self.traceback = original_file, traceback

    def __str__(self) -> str:
        return f"Cannot create backup for file {self.original_file}: {self.traceback}"


class CannotSave(Exception):
    def __init__(self, string: str = ""):
        self.str = string

    def __str__(self) -> str:
        return self.str


class UnexpectedEdgeCase(Exception):
    def __init__(self, string: str = ""):
        self.str = string

    def __str__(self) -> str:
        return self.str


class EncryptionError(Exception):
    def __init__(self, string: str = ""):
        self.str = string

    def __str__(self) -> str:
        return self.str


class InvalidCLIArgument(Exception):
    def __init__(self, arg_name: Any, arg_got: Any, arg_expected_str: Any):
        self.an, self.ag, self.ae = arg_name, arg_got, arg_expected_str

    def __str__(self) -> str:
        return f"CLI Error: Invalid Argument: Argument `{self.an}` got token `{self.ag}`; {self.ae}"
