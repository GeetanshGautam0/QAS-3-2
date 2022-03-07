from typing import *
from dataclasses import dataclass
from qa_enum import *


# Globals
_DEFAULT_DATA_TYPE = bytes


# Data Classes
@dataclass
class HexColor:
    color:                      str


@dataclass
class Theme:
    # Theme Information
    theme_file_name:            str
    theme_file_display_name:    str
    theme_display_name:         str
    theme_code:                 str

    # Primary Colours
    background:                 HexColor
    foreground:                 HexColor

    # Accent Colours
    accent:                     HexColor
    error:                      HexColor
    warning:                    HexColor
    okay:                       HexColor

    # Font Faces
    font_face:                  str
    font_alt_face:              str

    # Font Sizes
    font_small_size:            Union[float, int]
    font_main_size:             Union[float, int]
    font_large_size:            Union[float, int]
    font_title_size:            Union[float, int]

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

    save_data_type:             Union[str, bytes] = _DEFAULT_DATA_TYPE


@dataclass
class ConverterFunctionArgs:
    list_line_sep:              str = "\n"

    dict_key_val_sep:           str = " "
    dict_line_sep:              str = "\n"


@dataclass
class OpenFunctionArgs:
    global _DEFAULT_DATA_TYPE

    d_type:                     Union[str, bytes] = bytes
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

    def __str__(self):
        return f"Cannot create backup for file {self.original_file}: {self.traceback}"


class CannotSave(Exception):
    def __init__(self, string: str = ""):
        self.str = string

    def __str__(self):
        return self.str


class UnexpectedEdgeCase(Exception):
    def __init__(self, string: str = ""):
        self.str = string

    def __str__(self):
        return self.str


class EncryptionError(Exception):
    def __init__(self, string: str = ""):
        self.str = string

    def __str__(self):
        return self.str


class InvalidCLIArgument(Exception):
    def __init__(self, arg_name, arg_got, arg_expected_str):
        self.an, self.ag, self.ae = arg_name, arg_got, arg_expected_str

    def __str__(self):
        return f"CLI Error: Invalid Argument: Argument `{self.an}` got token `{self.ag}`; {self.ae}"
