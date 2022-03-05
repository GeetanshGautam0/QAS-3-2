import sys, os, traceback, tkinter as tk, qa_svh as svh, hashlib, time, random
from qa_std import *
from tkinter import messagebox


_bg_window = None


class ADMIN_TOOLS:
    def call(self):
        pass


class QUIZZING_FORM:
    def call(self):
        pass


class THEMING_UTIL:
    def call(self):
        pass


class RECOVERY_UTIL:
    def call(self):
        pass


class _Application:
    def __init__(self, name, tokens):
        global _bg_window

        self.name, self.tokens = name, tokens
        self.instance = self.launch_time = self.uid = None
        self.shell = _bg_window

    def run(self):
        try:
            if self.name not in _application_map:
                raise InvalidCLIArgument("ApplicationName", f'{self.name}', _CLI_help_app_calls)

        except Exception as E:
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
    Application.ADMINISTRATOR_TOOLS.name:       ADMIN_TOOLS,
    Application.ADMINISTRATOR_TOOLS.value:      ADMIN_TOOLS,
    Application.ADMINISTRATOR_TOOLS:            ADMIN_TOOLS,

    Application.QUIZZING_FORM.name:             QUIZZING_FORM,
    Application.QUIZZING_FORM.value:            QUIZZING_FORM,
    Application.QUIZZING_FORM:                  QUIZZING_FORM,

    Application.THEMING_UTIL.name:              THEMING_UTIL,
    Application.THEMING_UTIL.value:             THEMING_UTIL,
    Application.THEMING_UTIL:                   THEMING_UTIL,

    Application.RECOVERY_UTIL.name:             RECOVERY_UTIL,
    Application.RECOVERY_UTIL.value:            RECOVERY_UTIL,
    Application.RECOVERY_UTIL:                  RECOVERY_UTIL
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

    CLI_tokens = sys.argv
    if CLI_tokens[0].lower().strip() in ['python', 'python3']:
        CLI_tokens.pop(0)

    CLI_tokens.pop(0)  # Gets rid of script name

    assert len(CLI_tokens) > 0, "Insufficient information provided; use qa_main HELP for more information."

    if CLI_tokens[0].lower() == "help":
        sys.stdout.write(_CLI_master_help)

    else:
        app_name = CLI_tokens.pop(0)
        app = _Application(app_name, CLI_tokens)
        app.run()

else:
    sys.exit("cannot run file `qa_main` as module")

