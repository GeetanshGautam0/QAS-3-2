import urllib3, json, os, hashlib, traceback, sys
from .qa_info import ConfigurationFile, App, Files
from .qa_std import HTTP_HEADERS_NO_CACHE
from .qa_theme_loader import Test as TestTheme
from .qa_updater_call import RunUpdater
from typing import *


HTTP = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=1.0, read=1.5),
    retries=False
)


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
            return True, (None,), ("Latest version unknown: failed to contact server.", ), RunTest
        elif res.status != 200:
            return True, (None,), (f"Latest version unknown: {res.data}.", ), RunTest

        success, res = tr(json.loads, res.data.decode())
        if not success:
            return True, (None,), ("Latest version unknown",), RunTest

        lVer = res['application']['version']
        lBuild = res['application']['build_number']
        if lVer < App.version and not App.DEV_MODE:
            return False, ("Unsupported application version", ), (True, ), Fix.UpdateApp
        elif lVer > App.version:
            return False, ("New version available", ), (True, ), Fix.UpdateApp
        elif lBuild > App.build_number:
            return False, ("New application build available",), (True,), Fix.UpdateApp
        else:
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

        with open(Files.default_theme_file, 'r') as file:
            raw = file.read()
            file.close()

        with open(Files.default_theme_hashes, 'r') as file:
            hash_raw = file.read()
            file.close()

        success, res = tr(json.loads, raw)

        if not success:
            return False, (str(res[0]), ), (None, ), cast(Any, Fix.Reset.reset_defaults)

        success, res2 = tr(json.loads, hash_raw)
        if not success:
            return False, (str(res2[0]),), (None, ), cast(Any, Fix.Reset.reset_defaults)

        success, failures, warnings = cast(Tuple[bool, List[str], List[str]],  TestTheme.check_file(res, True))

        if not success:
            return False, (*failures, ), (*warnings, ), cast(Any, Fix.Reset.reset_defaults)

        f_name = res['file_info']['name']
        f_hash = hashlib.sha3_512(raw.encode()).hexdigest()
        success &= res2[f_name] == f_hash
        if not success:
            return False, ("Hash mismatch", ), (None, ), cast(Any, Fix.Reset.reset_defaults)

        del hash_raw, raw, f_name, f_hash, success, failures, res, res2

        return True, ("Default theme(s) passed tests", ), (*warnings, ), RunTest


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

