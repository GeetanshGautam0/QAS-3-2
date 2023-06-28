from typing import *
from dataclasses import dataclass
from .qa_enum import *
from .qa_info import App
import re, os, sys
from copy import deepcopy


# Globals
_DEFAULT_DATA_TYPE = bytes


class ANSI:
    FG_BRIGHT_MAGENTA = '\x1b[35;1m'
    FG_BRIGHT_YELLOW = '\x1b[33;1m'
    BOLD = '\x1b[1m'
    RESET = '\x1b[0m'


class HexColor:
    def __init__(self, color: str):
        self.color = color.upper()
        assert self.check(), 'Color provided does not match expected pattern (1)'

    def check(self) -> Union[str, None]:
        res = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', self.color)
        return str(res) if res is not None else None


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
    title_font_face:            str
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

    def check(self) -> bool:
        f = True
        c = True
        n = True
        o = False

        for val in (
                self.font_face, self.font_alt_face, self.theme_code,
                self.theme_file_name, self.theme_file_path, self.theme_display_name,
                self.theme_file_display_name
        ):
            f &= isinstance(val, str)
            if not f:
                break

        if f:
            o = os.path.exists(self.theme_file_path.replace('APP_DATA_DIR', App.appdata_dir))

        for color in (
            self.background, self.foreground, self.accent,
            self.error, self.warning, self.okay,
            self.gray, self.border_color
        ):
            if not c:
                break

            c &= isinstance(color, HexColor)

        for num, MIN, MAX in (
            (self.font_title_size, 10, 40),
            (self.font_large_size, 10, 30),
            (self.font_xl_title_size, 15, 45),
            (self.font_main_size, 5, 25),
            (self.font_small_size, 5, 20),
            (self.border_size, 0, 10),
        ):
            if not n:
                break

            n &= isinstance(num, (float, int))
            if n:
                n &= MIN <= num <= MAX

        for ind, value in enumerate([f, o, c, n]):
            if not value:
                sys.stderr.write(f'{ANSI.BOLD}[{ANSI.FG_BRIGHT_MAGENTA}THEME INT DIAG FAILURE{ANSI.RESET}{ANSI.BOLD}]{ANSI.RESET} TID : log : F : 0xF{ind}\n')

        if not o:
            sys.stdout.write(f'\t{ANSI.BOLD}{ANSI.FG_BRIGHT_YELLOW}* 0xA1 (O) : FAILURE : DEBLog : {self.theme_file_path.replace("APP_DATA_DIR", App.appdata_dir)}{ANSI.RESET}\n')

        return f & c & n & o


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


class UnprogrammedBehavior(Exception):
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


class FlattenedDict(dict):  # type: ignore
    def __init__(self, org_dict: Dict[Any, Any], strict_flattening: bool = True) -> None:
        super().__init__()
        self.od = org_dict
        self._sf = strict_flattening

    @property
    def __flattened(self) -> Dict[str, Any]:

        def rec_search(d: Union[Dict[Any, Any], Tuple[Any], List[Any], Set[Any]], rt: str) -> Dict[str, Any]:
            od = deepcopy(d)
            nd = {}  # type: ignore

            if isinstance(od, dict):
                for k, v in od.items():
                    if isinstance(v, dict):
                        nd = {**nd, **rec_search(v, f'{rt}/{k}')}

                    elif isinstance(v, (list, set, tuple)) & self._sf:
                        for i, n0 in enumerate(v):
                            if isinstance(n0, (list, set, tuple, dict)):
                                nd = {**nd, **rec_search(n0, f'{rt}/{k}/{i}')}  # type: ignore

                            else:
                                nd[f'{rt}/{k}/{i}'] = n0

                    else:
                        nd[f'{rt}/{k}'] = v

            elif isinstance(od, (list, set, tuple)) & self._sf:
                for i, n0 in enumerate(od):
                    if isinstance(n0, (list, set, tuple, dict)):
                        nd = {**nd, **rec_search(n0, f'{rt}/{i}')}  # type: ignore

                    else:
                        nd[f'{rt}/{i}'] = n0

            return nd

        return rec_search(self.od, '')

    def __str__(self) -> str:
        return f'QA.QF.FD: {self.__flattened}'

    def __repr__(self) -> str:
        return f'FlattenedDict({self.__flattened})'
