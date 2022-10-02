import urllib3, json, os, hashlib, traceback, sys
from .qa_info import ConfigurationFile, App, Files
from .qa_std import HTTP_HEADERS_NO_CACHE, ANSI
from .qa_theme_loader import Test as TestTheme
from .qa_updater_call import RunUpdater
from .qa_info import file_hash
from .qa_svh import compile_svh
from .qa_file_handler import File, Open, OpenFunctionArgs, ConverterFunctionArgs, data_type_converter
from typing import *


HTTP = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=1.0, read=1.5),
    retries=False
)


def consoleEntry(*data: Any, hdr: bool = True) -> None:
    if hdr:
        sys.stdout.write(f'{ANSI.BOLD}[{ANSI.FG_BRIGHT_CYAN}DIAGNOSTICS DEBUG LOG{ANSI.RESET}{ANSI.BOLD}]{ANSI.RESET} %s\n' % ' '.join(str(d) for d in data))
    else:
        sys.stdout.write('%s\n' % ' '.join(str(d) for d in data))


class Diagnostics:  # ALL: -> (bool, messages, codes/warnings, fix_func)
    @staticmethod
    def app_version() -> Tuple[bool, Tuple[Union[None, str]], Tuple[Union[bool, None, str]], Any]:
        global HTTP

        success, res = tr(
            HTTP.request,
            'GET',
            f'{ConfigurationFile.json_data["application"]["root_update_url"]}/.config/main_config.json',
            headers=HTTP_HEADERS_NO_CACHE
        )
        if not success:
            consoleEntry('Diagnostics::appVersion : !sc : failed to contact server')
            return True, (None,), ("Latest version unknown: failed to contact server.", ), RunTest
        elif res.status != 200:
            consoleEntry(f'Diagnostics::appVersion : !sc : {res.data=}')
            return True, (None,), (f"Latest version unknown: {res.data}.", ), RunTest

        success, res = tr(json.loads, res.data.decode())
        if not success:
            consoleEntry(f'Diagnostics::appVersion : !sc : UNKNOWN (0x01)')
            return True, (None,), ("Latest version unknown",), RunTest

        lVer = res['application']['version']
        lBuild = res['application']['build_number']

        consoleEntry(f'Diagnostics::appVersion : version : {lVer}')
        consoleEntry(f'Diagnostics::appVersion : build   : {lBuild}')

        if lVer < App.version and not App.DEV_MODE:
            consoleEntry('DAV 0x01')
            return False, ("Unsupported application version", ), (True, ), Fix.UpdateApp
        elif lVer > App.version:
            consoleEntry('DAV 0x02')
            return False, ("New version available", ), (True, ), Fix.UpdateApp
        elif lBuild > App.build_number:
            consoleEntry('DAV 0x03')
            return False, ("New application build available",), (True,), Fix.UpdateApp
        else:
            consoleEntry('DAV T')
            return True, ("Up to date", ), (True, ), RunTest

    @staticmethod
    def global_check() -> Tuple[bool, Tuple[Union[None, str]], Tuple[Union[bool, None, str]], Any]:
        alr_cr_ver, _, alr_cd, _ = Diagnostics.app_version()
        if not isinstance(alr_cd, bool):
            return True, (None, ), ("Cannot test app version", ), RunTest

        elif not alr_cd:
            return True, (None, ), ("Cannot test app version",), RunTest

    @staticmethod
    def default_theme() -> Tuple[bool, Tuple[Union[None, str], ...], Tuple[Union[bool, None, str], ...], Any]:
        if not os.path.isfile(Files.default_theme_file) or not os.path.isfile(Files.default_theme_hashes):
            return False, ("File doesn't exist", ), (None, ), Fix.Reset.reset_defaults

        with open(Files.default_theme_file, 'r') as theme_file:
            raw = theme_file.read().strip()
            theme_file.close()

        with open(Files.default_theme_hashes, 'r') as file:
            hash_raw = file.read()
            file.close()

        success, res = tr(json.loads, raw)

        consoleEntry(f'Diagnostics::default_theme : !sc : HS DUMP')

        if not success:
            consoleEntry('\t : F 0x01', hdr=False)
            return False, (str(res[0]), ), (None, ), cast(Any, Fix.Reset.reset_defaults)

        success, res2 = tr(json.loads, hash_raw)
        if not success:
            consoleEntry('\t : F 0x02', hdr=False)
            return False, (str(res2[0]),), (None, ), cast(Any, Fix.Reset.reset_defaults)

        success, failures, warnings = cast(Tuple[bool, List[str], List[str]],  TestTheme.check_file(res, True))

        if len(failures):
            consoleEntry('\n\t * [FAILURE] '.join(('', *failures)), hdr=False)

        if len(warnings):
            consoleEntry('\n\t * [WARNING] '.join(('', *warnings)), hdr=False)

        if not success:
            return False, (*failures, ), (*warnings, ), cast(Any, Fix.Reset.reset_defaults)

        f_name = res['file_info']['name']
        f_hash = hashlib.sha3_512(raw.encode()).hexdigest()
        success &= res2[f_name] == f_hash

        consoleEntry(f'\n\t * <HASH VALUE> {res2[f_name]=}', f'\n\t * <HASH VALUE> {f_hash=}', hdr=False)

        if not success:
            consoleEntry('Diagnostics::default_theme : !sc : HS DUMP : F 0x03')
            return False, ("Hash mismatch", ), (None, ), cast(Any, Fix.Reset.reset_defaults)

        del hash_raw, raw, f_name, f_hash, success, failures, res, res2

        return True, ("Default theme(s) passed tests", ), (*warnings, ), RunTest

    @staticmethod
    def script_hash() -> Tuple[bool, Tuple[Union[None, str], ...], Tuple[Union[bool, None, str], ...], Any]:
        # ALL: -> (bool, messages, codes/warnings, fix_func)
        failures = []
        svh = compile_svh()

        for f, h in svh.items():
            if file_hash.get(f) != h:
                failures.append(f'Incorrect hash stored for file "{f}"')
                consoleEntry(f'Diagnostics::script_hash : 0x00 : {f}\n\t : {h} \n\t : {file_hash.get(f)}')

        if not failures:
            consoleEntry('DSH T')

        return len(failures) == 0, (*failures,), ('.JSON files not tested', '.SVG files not tested', '.PNG files not tested'), cast(Any, Fix.UpdateApp)


class Fix:
    class Reset:
        @staticmethod
        def default_theme(re_str: bool = False, *args: Any, **kwargs: Any) -> Union[str, None]:
            if re_str:
                return '-c DEFAULT_THEME'
            RunUpdater('-c DEFAULT_THEME')
            return None

        @staticmethod
        def fix_functions_mod(re_str: bool = False, *args: Any, **kwargs: Any) -> Union[None, str]:
            if re_str:
                return '-c MODULES_QA_FUNCTIONS'
            RunUpdater('-c MODULES_QA_FUNCTIONS')
            return None

        @staticmethod
        def fix_files_mod(re_str: bool = False, *args: Any, **kwargs: Any) -> Union[None, str]:
            if re_str:
                return '-c MODULES_QA_FILES'
            RunUpdater('-c MODULES_QA_FILES')
            return None

        @staticmethod
        def fix_update_mod(re_str: bool = False, *args: Any, **kwargs: Any) -> Union[None, str]:
            if re_str:
                return '-c MODULES_QA_FILES'
            RunUpdater('-c MODULES_QA_FILES')
            return None

        @staticmethod
        def reset_defaults(re_str: bool = False, *args: Any, **kwargs: Any) -> Union[None, str]:
            if re_str:
                return '-c ICONS -c DEFAULT_THEMES'
            RunUpdater('-c ICONS -c DEFAULT_THEMES')
            return None

    @staticmethod
    def UpdateApp(re_str: bool = False, *args: Any, **kwargs: Any) -> Union[None, str]:
        if re_str:
            return 'UPDATE_ALL'
        RunUpdater('--UpdateAll')
        return None


def RunTest(function: Any = lambda *a, **k: True, *args: Any, **kwargs: Any) -> Any:
    try:
        return function(*args, **kwargs)
    except Exception as E:
        sys.stderr.write(f"{traceback.format_exc()}\n")
        return None, E


def tr(func: Any, *args: Any, **kwargs: Any) -> Tuple[bool, Any]:
    try:
        return True, func(*args, **kwargs)
    except Exception as E:
        return False, [E, traceback.format_exc()]


_REQ_RESTART = [Fix.UpdateApp, ]
_UC_FUNC = [Fix.Reset.reset_defaults, Fix.Reset.default_theme, Fix.Reset.fix_files_mod, Fix.Reset.fix_update_mod, Fix.Reset.fix_functions_mod, Fix.UpdateApp]

