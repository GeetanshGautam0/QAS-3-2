from typing import *
from dataclasses import dataclass
from qa_enum import *


# Data Classes

@dataclass
class HexColor:
    color: str


@dataclass
class LoggingPackage:
    logging_level: LoggingLevel
    data: str
    file_path: str


@dataclass
class SaveFunctionArguments:
    append: bool
    encrypt: bool = False
    encryption_key: bytes = b''
    delete_backup: bool = False
    run_hash_check: bool = True

    list_val_sep: str = "\n"

    dict_key_val_sep: str = " "
    dict_line_sep: str = "\n"

    save_data_type: Union[str, bytes] = str


@dataclass
class ConverterFunctionArguments:
    list_line_sep: str = "\n"

    dict_key_val_sep: str = " "
    dict_line_sep: str = "\n"


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
