import sys, traceback, time, random, click, hashlib
from qa_functions.qa_std import *
from tkinter import messagebox
from qa_apps_admin_tools import RunApp as Admin_RunApp
from qa_apps_quizzing_form import RunApp as Quizzer_RunApp
from qa_apps_recovery_util import RunApp as RecoveryUtil_RunApp
from qa_apps_theming_util import RunApp as ThemingUtil_RunApp
from threading import Thread


_bg_window = None


class _Run(Thread):
    def __init__(self, func, tokens):
        global _bg_window

        Thread.__init__(self)
        self.start()

        self.base_root = None

        self.func, self.tokens = func, tokens
        self.shell_ready, self.shell = False, _bg_window

        self._run_acc = 0

    def call(self) -> Union[tk.Tk, tk.Toplevel]:
        global _bg_window

        if self._run_acc >= 1:
            return self.shell

        self.base_root = tk.Tk()
        self.base_root.withdraw()
        self.base_root.title('Quizzing Application - AIM || Running')

        _ui_shell = self.func(self, _bg_window, **self.tokens)
        self.shell_ready = True
        self.shell = _ui_shell

        self._run_acc += 1

        return _ui_shell

    def __del__(self):
        if self.base_root is not None:
            self.base_root.quit()


class _ApplicationInstanceManager:
    def __init__(self, name, tokens):
        global _bg_window

        self.name, self.tokens = name, tokens
        self.instance = self.launch_time = self.uid = None
        self.shell = _bg_window

    def run(self):
        global _application_map, _bg_window

        try:
            if self.name not in _application_map:
                raise InvalidCLIArgument("ApplicationName", f'{self.name}', _CLI_help_app_calls)

            func = _application_map[self.name]
            inst = _Run(func, self.tokens)
            ui_shell = inst.call()

        except Exception as E:
            self.shell = _bg_window
            self.error_handler(E.__class__, str(E))

    def error_handler(self, exception_class, exception_str):
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = ''.join(i for i in traceback.format_tb(exc_traceback))
            unique_hash = hashlib.sha3_512(
                f"{time.ctime(time.time())}{tb}{exception_str}{exception_class}{random.random()}".encode()
            ).hexdigest()
            error_hash = hashlib.md5(
                f"{exception_str}{exception_class}".encode()
            ).hexdigest()

            e_string = f"An error occurred during runtime; more info:\n\nError class: {exception_class}\n\nError: {exception_str}\n\nError Code: {error_hash}\n\nUnique Error Code: {unique_hash}\n\nTechnical Information:\n{tb}"
            sys.stderr.write(e_string)

            copy_to_clipboard(e_string, self.shell)

            messagebox.showerror(
                "Quizzing Application - App Instance Manger",
                f"THE FOLLOWING INFORMATION HAS BEEN COPIED TO YOUR CLIPBOARD; USE `CTRL+V` TO PASTE IT ANYWHERE.\n\n{e_string}"
            )

        except Exception as E:
            pass

    def __del__(self):
        global _bg_window
        _bg_window.quit()


_application_map = {
    Application.ADMINISTRATOR_TOOLS.name:       Admin_RunApp,
    Application.ADMINISTRATOR_TOOLS.value:      Admin_RunApp,
    Application.ADMINISTRATOR_TOOLS:            Admin_RunApp,
    'AdminTools':                               Admin_RunApp,

    Application.QUIZZING_FORM.name:             Quizzer_RunApp,
    Application.QUIZZING_FORM.value:            Quizzer_RunApp,
    Application.QUIZZING_FORM:                  Quizzer_RunApp,
    'QuizzingForm':                             Quizzer_RunApp,

    Application.THEMING_UTIL.name:              ThemingUtil_RunApp,
    Application.THEMING_UTIL.value:             ThemingUtil_RunApp,
    Application.THEMING_UTIL:                   ThemingUtil_RunApp,
    'ThemingUtil':                              ThemingUtil_RunApp,

    Application.RECOVERY_UTIL.name:             RecoveryUtil_RunApp,
    Application.RECOVERY_UTIL.value:            RecoveryUtil_RunApp,
    Application.RECOVERY_UTIL:                  RecoveryUtil_RunApp,
    'RecoveryUtil':                             RecoveryUtil_RunApp,
}


_CLI_help_app_calls = f"""To call an application, use the following tokens:
\tAdministrator Tools: {Application.ADMINISTRATOR_TOOLS.name}
\tQuizzing Form      : {Application.QUIZZING_FORM.name}
\tTheming Utility    : {Application.THEMING_UTIL.name}
\tRecovery Utility   : {Application.RECOVERY_UTIL.name}
"""

CLI_AllowedApplications = ['AdminTools', 'QuizzingForm', 'RecoveryUtil', 'ThemingUtil']


def default_cli_handling(**kwargs):
    print("CLI Tokens: ", kwargs, end="\n\n")


@click.group()
def _CLIHandler():
    pass


@_CLIHandler.command()
@click.argument('app_name', type=click.Choice(CLI_AllowedApplications))
@click.option('--open_file', help="open qa_files that is supplied in args", is_flag=True)
@click.option('--file_path', help="path of qa_files to open", default=None)
@click.option('--debug', help='enable debugging', is_flag=True)
def start_app(**kwargs):
    default_cli_handling(**kwargs)
    app = _ApplicationInstanceManager(kwargs.get('app_name'), kwargs)
    app.run()


@_CLIHandler.command()
@click.argument('file_path')
def check_file(**kwargs):
    default_cli_handling(**kwargs)
    return


if __name__ == "__main__":
    print("\n" * 50)
    print("Loaded modules; running application now.")

    _bg_window: tk.Tk = tk.Tk()
    _bg_window.withdraw()

    _CLIHandler()

else:
    sys.exit("cannot run qa_files `qa_main` as module")

