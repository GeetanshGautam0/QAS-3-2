from typing import *

from .qa_colors import Convert as ConvertColor, Functions as ColorFunctions
from .qa_custom import HexColor, Theme, LoggingPackage, SaveFunctionArgs, ConverterFunctionArgs, OpenFunctionArgs, File, \
    CannotSave, CannotCreateBackup, UnexpectedEdgeCase, EncryptionError, InvalidCLIArgument, FlattenedDict
from .qa_enum import LoggingLevel, ScriptLevelID, ExitCodes, CLI, ErrorLevels, Application, FileType
from .qa_err import raise_error as _re
from .qa_file_handler import Open as OpenFile, Save as SaveFile
from .qa_info import ConfigurationFile, App, Extensions, Files, Encryption, OnlineFiles, file_hash as ScriptHashes
from .qa_logger import threaded_logger as _tl, normal_logger as _nl, clear_logs as _cl
from .qa_nv_flags import create_flag as _cf, delete_flag as _df, check_flag as _chf, clear_all_app_flags as _caaf, clear_all_flags as _caf, \
    yield_all_flags as _yaf, yield_all_flags_as_list as _yafal
from .qa_std import float_map, check_hex_contrast, data_at_dict_path, show_bl_err, split_filename_direc, dict_check_redundant_data, \
    dict_check_redundant_data_inter_dict, copy_to_clipboard, brute_force_decoding, data_type_converter, gen_short_uid, SMem, clamp, \
    ANSI, AppLogColors, flatten_list, ExceptionCodes, stdout, stderr
from .qa_svh import create_script_version_hash as _csvh, check_hash as _ch
from .qa_theme_loader import Load as LoadTheme, Test as TestTheme, TTK as TTKTheme
from .qa_diagnostics import Diagnostics, Fix
from .qa_updater_call import RunUpdater, UpdateSuite, InstallThemeAddons


def RaiseError(error_type: Type[Exception], error_params: List[Any], error_level: ErrorLevels, tb: Optional[str] = "") -> None:
    _re(error_type, error_params, error_level, tb)


def ThreadedLogger(logging_package: List[LoggingPackage]) -> None:
    _tl(logging_package)


def NormalLogger(logging_package: List[LoggingPackage]) -> None:
    _nl(logging_package)


def ClearLogs(ignore_list: Tuple[Any, ...] = ()) -> bool:
    return _cl(ignore_list)


def CreateNVFlag(script: str, name: str) -> None:
    _cf(script, name)


def DeleteNVFlag(script: str, name: str) -> None:
    _df(script, name)


def CheckNVFlag(script: str, name: str) -> bool:
    return _chf(script, name)


def ClearAppNVFlags(script: str) -> None:
    _caaf(script)


def ClearAllNVFlags() -> None:
    _caf()


def YieldAllNVFlags(script: str) -> Generator[str, Any, None]:
    return _yaf(script)


def YieldAllNVFlagsAsList(script: str) -> List[str]:
    return _yafal(script)


def CreateScriptVersionHash(file_path: str) -> str:
    return _csvh(file_path)


def CheckScriptVersionHash(script: str, expected_hash: str, script_type: str, self_id: str = "<Unknown>") -> None:
    _ch(script, expected_hash, script_type, self_id)
