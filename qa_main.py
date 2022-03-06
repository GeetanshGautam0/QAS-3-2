import sys, os, traceback, tkinter as tk, qa_svh as svh, hashlib, time, random
from qa_std import *
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

        self.func, self.tokens = func, tokens
        self.shell_ready, self.shell = False, _bg_window

        self._run_acc = 0

    def call(self) -> Union[tk.Tk, tk.Toplevel]:
        global _bg_window

        if self._run_acc >= 1:
            return self.shell

        _ui_shell = self.func(self, _bg_window)
        self.shell_ready = True
        self.shell = _ui_shell

        self._run_acc += 1

        return _ui_shell


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
            inst.call()

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

    Application.QUIZZING_FORM.name:             Quizzer_RunApp,
    Application.QUIZZING_FORM.value:            Quizzer_RunApp,
    Application.QUIZZING_FORM:                  Quizzer_RunApp,

    Application.THEMING_UTIL.name:              ThemingUtil_RunApp,
    Application.THEMING_UTIL.value:             ThemingUtil_RunApp,
    Application.THEMING_UTIL:                   ThemingUtil_RunApp,

    Application.RECOVERY_UTIL.name:             RecoveryUtil_RunApp,
    Application.RECOVERY_UTIL.value:            RecoveryUtil_RunApp,
    Application.RECOVERY_UTIL:                  RecoveryUtil_RunApp
}


_CLI_help_app_calls = f"""To call an application, use the following tokens:
\tAdministrator Tools: {Application.ADMINISTRATOR_TOOLS.name}
\tQuizzing Form      : {Application.QUIZZING_FORM.name}
\tTheming Utility    : {Application.THEMING_UTIL.name}
\tRecovery Utility   : {Application.RECOVERY_UTIL.name}
"""


_CLI_master_help = \
    f"""{'-'*100}
Quizzing Application: CLI Help 

LEGEND:
    * <OPTIONAL> 
    * [REQUIRED]
    * {"{PICK ONE}"}

Syntax: <python> qa_main.{"{py / exe}"} [APPLICATION TOKEN] <Args> 

{_CLI_help_app_calls}
{'-'*100}
"""


if __name__ == "__main__":
    _bg_window: tk.Tk = tk.Tk()
    _bg_window.withdraw()

    CLI_tokens = [*sys.argv]

    if CLI_tokens[0].lower().strip() in ['python', 'python3']:
        CLI_tokens.pop(0)

    CLI_tokens.pop(0)  # Gets rid of script name

    assert len(CLI_tokens) > 0, "Insufficient information provided; use qa_main HELP for more information."

    if CLI_tokens[0].lower() == "help":
        sys.stdout.write(_CLI_master_help)

    else:
        app_name = CLI_tokens.pop(0)
        app = _ApplicationInstanceManager(app_name, CLI_tokens)
        app.run()

else:
    sys.exit("cannot run file `qa_main` as module")

