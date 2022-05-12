from .qa_colors import Convert as ConvertColor
from .qa_colors import Functions as ColorFunctions

from .qa_custom import *

from .qa_enum import LoggingLevel as ENUM_LoggingLevel
from .qa_enum import ScriptLevelID as ENUM_ScriptLevelID
from .qa_enum import ExitCodes as ENUM_ExitCodes
from .qa_enum import CLI as ENUM_CLI
from .qa_enum import ErrorLevels as ENUM_ErrorLevels
from .qa_enum import Application as ENUM_Application

from .qa_err import raise_error as _re

from .qa_file_handler import Open as OpenFile
from .qa_file_handler import Save as SaveFile

from .qa_info import *

from .qa_logger import threaded_logger as _tl
from .qa_logger import normal_logger as _nl
from .qa_logger import clear_logs as _cl

from .qa_nv_flags import create_flag as _cf
from .qa_nv_flags import delete_flag as _df
from .qa_nv_flags import check_flag as _chf
from .qa_nv_flags import clear_all_app_flags as _caaf
from .qa_nv_flags import clear_all_flags as _caf
from .qa_nv_flags import yield_all_flags as _yaf
from .qa_nv_flags import yield_all_flags_as_list as _yafal

from .qa_std import *

from .qa_svh import create_script_version_hash as _csvh
from .qa_svh import check_hash as _ch

from .qa_theme_loader import Load as LoadTheme
from .qa_theme_loader import Test as TestTheme
from .qa_theme_loader import TTK as TTKTheme


def RaiseError(error_type, error_params: tuple, error_level: ErrorLevels, traceback: Optional[str] = ""):
    return _re(error_type, error_params, error_level, traceback)


def ThreadedLogger(logging_package: List[LoggingPackage]) -> None:
    return _tl(logging_package)


def NormalLogger(logging_package: List[LoggingPackage]) -> None:
    return _nl(logging_package)


def ClearLogs(ignore_list: tuple = ()) -> bool:
    return _cl(ignore_list)


def CreateNVFlag(script: str, name: str):
    return _cf(script, name)


def DeleteNVFlag(script: str, name: str):
    return _df(script, name)


def CheckNVFlag(script: str, name: str):
    return _chf(script, name)


def ClearAppNVFlags(script: str):
    return _caaf(script)


def ClearAllNVFlags():
    return _caf()


def YieldAllNVFlags(script: str):
    return _yaf(script)


def YieldAllNVFlagsAsList(script: str):
    return _yafal(script)


def CreateScriptVersionHash(file_path) -> str:
    return _csvh(file_path)


def CheckScriptVersionHash(script: str, expected_hash: str, script_type: str, self_id: str = "<Unknown>") -> None:
    return _ch(script, expected_hash, script_type, self_id)
