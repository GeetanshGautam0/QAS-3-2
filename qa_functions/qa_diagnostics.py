import sys, os, json, traceback, hashlib, urllib3

try:
    from qa_functions import *
except:
    from . import qa_theme_loader

try:
    from qa_installer_functions import update
except:
    from ..qa_installer_functions import update


HTTP = urllib3.PoolManager()


class Diagnostics:  # ALL: -> (bool, failures, warnings, fix_func)
    @staticmethod
    def app_version():
        global HTTP
        success, res = tr(
            HTTP.request,
            'GET',
            f'{ConfigurationFile.json_data["application"]["root_update_url"]}/.config/main_config.json'
        )
        if not success:
            return True, (), ("Latest version unknown: failed to contact server.", ), RunTest
        elif res.status != 200:
            return True, (), (f"Latest version unknown: {res.data}.", ), RunTest

        success, res = tr(json.loads, res.data.decode())
        if not success:
            return True, (), ("Latest version unknown",), RunTest

        lVer = res['application']['version']
        if lVer > App.version:
            return False, ("New version available", ), (True, ), Fix.UpdateApp
        else:
            return True, ("Up to date", ), (True, ), RunTest

    @staticmethod
    def global_check():
        alr_cr_ver, _, alr_cd, _ = Diagnostics.app_version()
        if not isinstance(alr_cd, bool):
            return True, (), ("Cannot test app version", ), RunTest
        elif not alr_cd:
            return True, (), ("Cannot test app version",), RunTest

    @staticmethod
    def default_theme():
        if not os.path.isfile(Files.default_theme_file) or not os.path.isfile(Files.default_theme_hashes):
            return False, ("File doesn't exist", ), (), Fix.Reset.reset_defaults

        with open(Files.default_theme_file, 'r') as file:
            raw = file.read()
            file.close()

        with open(Files.default_theme_hashes, 'r') as file:
            hash_raw = file.read()
            file.close()

        success, res = tr(json.loads, raw)

        if not success:
            return False, (str(res[0]), ), (), Fix.Reset.reset_defaults
        res: Dict

        success, res2 = tr(json.loads, hash_raw)
        if not success:
            return False, (str(res2[0]),), (), Fix.Reset.reset_defaults

        success, failures, warnings = TestTheme.check_file(res, True)
        if not success:
            return False, failures, warnings, Fix.Reset.reset_defaults

        f_name = res['file_info']['name']
        f_hash = hashlib.sha3_512(raw.encode()).hexdigest()
        success &= res2[f_name] == f_hash
        if not success:
            return False, ("Hash mismatch", ), (), Fix.Reset.reset_defaults

        del hash_raw, raw, f_name, f_hash, success, failures, res, res2

        return True, ("Default theme(s) passed tests", ), warnings, RunTest


class Fix:
    class Reset:
        @staticmethod
        def default_theme(re_str=False):
            if re_str:
                return '-c DEFAULT_THEME'
            update.RunUpdater('-c DEFAULT_THEME')

        @staticmethod
        def fix_functions_mod(re_str=False):
            if re_str:
                return '-c MODULES_QA_FUNCTIONS'
            update.RunUpdater('-c MODULES_QA_FUNCTIONS')

        @staticmethod
        def fix_files_mod(re_str=False):
            if re_str:
                return '-c MODULES_QA_FILES'
            update.RunUpdater('-c MODULES_QA_FILES')

        @staticmethod
        def fix_update_mod(re_str=False):
            if re_str:
                return '-c MODULES_QA_FILES'
            update.RunUpdater('-c MODULES_QA_FILES')

        @staticmethod
        def reset_defaults(re_str=False):
            if re_str:
                return '-c ICONS -c DEFAULT_THEMES'
            update.RunUpdater('-c ICONS -c DEFAULT_THEMES')

    def UpdateApp(self, re_str=False):
        if re_str:
            return 'UPDATE_ALL'

        update.RunUpdater('--UpdateAll')


def RunTest(function: Callable = lambda *a, **k: True, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except Exception as E:
        sys.stderr.write(f"{traceback.format_exc()}\n")
        return None, E


def tr(func: Callable, *args, **kwargs):
    try:
        return True, func(*args, **kwargs)
    except Exception as E:
        return False, [E, traceback.format_exc()]


_REQ_RESTART = [Fix.UpdateApp, ]
_UC_FUNC = [*dir(Fix.Reset)]

