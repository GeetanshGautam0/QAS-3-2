import sys, traceback, click, datetime, qa_functions, subprocess, os, qa_splash
from qa_functions.qa_std import *
from tkinter import messagebox, ttk
import qa_apps_admin_tools as AdminTools
import qa_apps_quizzing_form as QuizzingForm
import qa_apps_recovery_util as RecoveryUtils
import qa_apps_theming_util as ThemingUtil
from threading import Thread
from qa_installer_functions.addons_installer import RunAddonsInstaller


_bg_window, SPLASH = None, None

BOOT_STEPS = {
    1: 'Checking for Updates',
    2: 'Handling CLI',
    3: "Initializing Instance Manager",
    4: "Configuring Loggers + Debuggers",
    5: "Fetching Application Entry Point",
    6: "Setting Up '_Run' Method",
    7: "Initializing App",
}


class _Run(Thread):
    def __init__(self, func, tokens):
        global _bg_window

        Thread.__init__(self)
        self.start()

        self.base_root = None

        self.func, self.tokens = func, tokens
        self.shell_ready, self.shell = False, _bg_window

        self._run_acc = 0

    def close(self, *_0, **_1):
        global SPLASH
        try:
            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.hide(SPLASH)

        except:
            pass

        messagebox.showerror('Crash', 'Unexpected shut down of application instance manager [FATAL]')
        sys.exit('AIM_SD')

    def tk_err_handler(self, _, val, _1):
        global SPLASH
        try:
            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.hide(SPLASH)
        except:
            pass

        if self.tokens['weakhandling']:
            messagebox.showerror('Error', f"(WeakHandling) The application's UI has encountered an unhandled error. More info:\n\n{val}\n\n{traceback.format_exc()}")
            try:
                if isinstance(SPLASH, qa_splash.Splash):
                    qa_splash.show(SPLASH)
            except:
                pass

        else:
            messagebox.showerror('Crash', f"The application's UI has encountered an unrecoverable error (crash). More info:\n\n{val}\n\n{traceback.format_exc()}")
            sys.exit('AIM_TK_CRASH')

    def call(self) -> Union[tk.Tk, tk.Toplevel]:
        global _bg_window, _ico_map

        if self._run_acc >= 1:
            return self.shell

        if self.func in _ico_map:
            cast(Union[tk.Tk, tk.Toplevel], _bg_window).iconbitmap(_ico_map[self.func])

        cast(Union[tk.Tk, tk.Toplevel], _bg_window).protocol("WM_DELETE_WINDOW", self.close)
        tk.Tk.report_callback_exception = self.tk_err_handler

        _ui_shell = self.func(self, _bg_window, **self.tokens)
        self.shell_ready = True
        self.shell = _ui_shell

        self._run_acc += 1

        return _ui_shell

    def __del__(self):
        if isinstance(_bg_window, tk.Tk):
            self.base_root.quit()


class _ApplicationInstanceManager:
    def __init__(self, name, tokens):
        global _bg_window

        self.name, self.tokens = name, tokens
        self.instance = self.launch_time = self.uid = None
        self.shell = _bg_window

    def run(self):
        global _application_map, _bg_window, SPLASH, BOOT_STEPS, _title_map

        try:
            if self.name not in _application_map:
                raise InvalidCLIArgument("ApplicationName", f'{self.name}', "")
                sys.exit(-1)

            if isinstance(SPLASH, qa_splash.Splash):
                title, img = _title_map[self.name]
                SPLASH.setTitle(title)
                SPLASH.setImg(img)
                qa_splash.update_step(SPLASH, 4, BOOT_STEPS)

            if self.tokens['debug'] or self.tokens['debug_all']:
                for Script in (AdminTools, QuizzingForm, RecoveryUtils, ThemingUtil):
                    Script.DEBUG_NORM = self.tokens['debug_all']
                    Script.LOGGER_AVAIL = True
                    Script.LOGGER_FUNC = qa_functions.NormalLogger
                    Script.LOGGING_FILE_NAME = datetime.datetime.now().strftime('%b %d, %Y %H-%M-%S')

            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.update_step(SPLASH, 5, BOOT_STEPS)

            func = _application_map[self.name]

            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.update_step(SPLASH, 6, BOOT_STEPS)

            inst = _Run(func, self.tokens)

            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.update_step(SPLASH, len(BOOT_STEPS), BOOT_STEPS)
                qa_splash.show_completion(SPLASH, BOOT_STEPS)

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
    'AdminTools':                               AdminTools.RunApp,
    'QuizzingForm':                             QuizzingForm.RunApp,
    'ThemingUtil':                              ThemingUtil.RunApp,
    'RecoveryUtil':                             RecoveryUtils.RunApp,

    'InstallThemeAddons':                       RunAddonsInstaller,
}

_title_map = {
    'AdminTools':                               ('Administrator Tools', qa_functions.Files.AT_png),
    'QuizzingForm':                             ('Quizzing Tool', qa_functions.Files.QF_png),
    'ThemingUtil':                              ('Theming Utility', qa_functions.Files.TU_png),
    'RecoveryUtil':                             ('Recovery Utilities', qa_functions.Files.RU_png),

    'InstallThemeAddons':                       ('Addons Manager', qa_functions.Files.QF_png),
}

_ico_map = {
    AdminTools:                                 qa_functions.Files.AT_ico,
    ThemingUtil:                                qa_functions.Files.TU_ico,
    RecoveryUtils:                              qa_functions.Files.RU_ico,
    QuizzingForm:                               qa_functions.Files.QF_ico,
}

CLI_AllowedApplications = ['AdminTools', 'QuizzingForm', 'RecoveryUtil', 'ThemingUtil', 'InstallThemeAddons']


def default_cli_handling(**kwargs):
    print("CLI Tokens: ", kwargs, end="\n\n")


@click.group()
def _CLIHandler():
    pass


@_CLIHandler.command()
@click.argument('app_name', type=click.Choice(CLI_AllowedApplications))
@click.option('--open_file', help="open qa_files that is supplied in args", is_flag=True)
@click.option('--file_path', help="path of qa_files to open", default=None)
@click.option('--ttk_theme', help="TTK theme to use (default = clam)", default='clam')
@click.option('--debug', help='enable debugging', is_flag=True)
@click.option('--debug_all', help='enable debugging (ALL LEVELS)', is_flag=True)
@click.option('--weakHandling', help='weak error handling', is_flag=True)
def start_app(**kwargs):
    global BOOT_STEPS; SPLASH

    default_cli_handling(**kwargs)

    if isinstance(SPLASH, qa_splash.Splash):
        qa_splash.update_step(SPLASH, 3, BOOT_STEPS)

    app = _ApplicationInstanceManager(kwargs.get('app_name'), kwargs)
    app.run()


@_CLIHandler.command()
@click.argument('file_path')
def check_file(**kwargs):
    default_cli_handling(**kwargs)
    return


def check_up_tickets():
    if len(qa_functions.YieldAllNVFlagsAsList('L_UPDATE')) > 0:
        if messagebox.askyesno('QA Updater', 'Outstanding update tickets exist; do you want to execute the updater now?'):
            subprocess.Popen([os.path.abspath('.qa_update\\.qa_update_app.exe'), 'update', '--ReadFlags'])
            sys.exit(0)


def check_for_updates():
    if not qa_functions.Diagnostics.app_version()[0]:
        qa_functions.ClearAppNVFlags('L_UPDATE')
        sys.stdout.write('App needs to updated.\n')

        if messagebox.askyesno('QA Updater', 'A new version of the app is available; do you want to update the app now?'):
            qa_functions.CreateNVFlag('L_UPDATE', 'UPDATE_ALL')
            subprocess.Popen([os.path.abspath('.qa_update\\.qa_update_app.exe'), 'update', '--ReadFlags'])
            sys.exit(0)
    else:
        sys.stdout.write("App configuration implies app is up to date.\n")


if __name__ == "__main__":
    _bg_window = cast(tk.Tk, tk.Tk())
    _bg_window.withdraw()

    sys.stdout.write("Loaded modules; running application now.\n")

    SPLASH = cast(qa_splash.Splash, qa_splash.Splash(tk.Toplevel(), 'Quizzing Application', qa_functions.Files.QF_png))
    qa_splash.update_step(SPLASH, 1, BOOT_STEPS)

    check_for_updates()
    check_up_tickets()

    qa_splash.update_step(SPLASH, 2, BOOT_STEPS)

    _CLIHandler()

else:
    sys.exit("cannot run qa_files `qa_main` as module")

