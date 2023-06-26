import traceback, click, datetime, qa_functions, subprocess, os
from qa_gem import qa_global_error_manager as master_error_manager
from qa_functions.qa_std import *
from qa_functions.qa_custom import InvalidCLIArgument
from tkinter import messagebox
from qa_ui import AdminTools, QuizzingForm, RecoveryUtils, ThemingUtil, qa_splash
from threading import Thread
from qa_installer_functions.addons_installer import RunAddonsInstaller


LOGGING_FILE_NAME = datetime.datetime.now().strftime('%b %d, %Y %H-%M-%S')
_bg_window: Union[None, tk.Tk] = None
SPLASH: Union[None, qa_splash.Splash] = None

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
    def __init__(
            self,
            func: Callable[[object, Union[tk.Tk, tk.Toplevel], Any], tk.Toplevel],
            tokens: Dict[Any, Any]
    ) -> None:
        global _bg_window

        Thread.__init__(self)
        self.start()

        self.base_root = None

        self.func, self.tokens = func, tokens
        self.shell_ready = False
        self.shell: Union[None, tk.Toplevel, tk.Tk] = _bg_window

        self._run_acc = 0

    @staticmethod
    def close(*_0: Optional[Any], **_1: Optional[Any]) -> None:
        global SPLASH
        try:
            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.hide(SPLASH)

        except:
            pass

        messagebox.showerror('Crash', 'Unexpected shut down of application instance manager [FATAL]')
        sys.exit('AIM_SD')

    def tk_err_handler(self, _: Any, val: Any, _1: Any) -> None:
        global SPLASH
        try:
            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.hide(SPLASH)
        except:
            pass

        if self.tokens['weakhandling']:
            tb = traceback.format_exc()

            master_error_manager.InvokeException(
                master_error_manager.ExceptionObject(master_error_manager.ExceptionCodes.INTERNAL_ERROR),
                'ApplicationCrashError(Tk/Tcl)', f'Uncaught exception event (Tk/Tcl) => Error (AIM report) !? WeakHandling Enabled.\n\n', tb, offset=10
            )

            messagebox.showerror('Error', f"(WeakHandling) The application's UI has encountered an unhandled error. More info:\n\n{val}\n\n{tb}")

            try:
                if isinstance(SPLASH, qa_splash.Splash):
                    qa_splash.show(SPLASH)
            except:
                pass

        else:
            tb = traceback.format_exc()

            stderr(f'\n{"*"*10}\n\nApplication Instance Manager (AIM) Log:\n==>\tWARN @ Application crashed\n\n{"*"*10}\n')

            master_error_manager.InvokeException(
                master_error_manager.ExceptionObject(master_error_manager.ExceptionCodes.INTERNAL_ERROR),
                'ApplicationCrashError(Tk/Tcl)', f'Uncaught exception event (Tk/Tcl) => Crash (AIM report).\n\n', tb, offset=10
            )

            messagebox.showerror('Crash', f"The application's UI has encountered an unrecoverable error (crash). More info:\n\n{val}\n\n{tb}")
            sys.exit('AIM_TK_CRASH')

    def call(self) -> Union[None, tk.Tk, tk.Toplevel]:
        global _bg_window, _ico_map

        if self._run_acc >= 1:
            return self.shell

        if self.func in _ico_map:
            cast(Union[tk.Tk, tk.Toplevel], _bg_window).iconbitmap(_ico_map[self.func])  # type: ignore

        cast(Union[tk.Tk, tk.Toplevel], _bg_window).protocol("WM_DELETE_WINDOW", self.close)
        tk.Tk.report_callback_exception = self.tk_err_handler

        _ui_shell = self.func(self, _bg_window, **self.tokens)  # type: ignore
        self.shell_ready = True
        self.shell = _ui_shell

        self._run_acc += 1

        return _ui_shell

    def __del__(self) -> None:
        if isinstance(_bg_window, tk.Tk) and isinstance(self.base_root, (tk.Tk, tk.Toplevel)):
            self.base_root.quit()


class _ApplicationInstanceManager:
    def __init__(self, name: str, tokens: Dict[Any, Any]) -> None:
        global _bg_window

        self.name, self.tokens = name, tokens
        self.instance = self.launch_time = self.uid = None
        self.shell = _bg_window

    def run(self) -> None:
        global _application_map, _bg_window, SPLASH, BOOT_STEPS, _title_map, LOGGING_FILE_NAME

        try:
            if self.name not in _application_map:
                raise InvalidCLIArgument("ApplicationName", f'{self.name}', "")

            if isinstance(SPLASH, qa_splash.Splash):
                title, img = _title_map[self.name]
                SPLASH.setTitle(title)
                SPLASH.setImg(img)
                qa_splash.update_step(SPLASH, 4, BOOT_STEPS)

            if self.tokens['debug'] or self.tokens['debug_all'] or self.tokens['debug_dev']:
                for Script in (AdminTools, QuizzingForm, RecoveryUtils, ThemingUtil):
                    Script.DEBUG_DEV_FLAG = self.tokens['debug_dev']                                    # type: ignore
                    Script.DEBUG_NORM = self.tokens['debug_all'] or self.tokens['debug_dev']            # type: ignore
                    Script.LOGGER_AVAIL = True                                                          # type: ignore
                    Script.LOGGER_FUNC = qa_functions.NormalLogger                                      # type: ignore
                    Script.LOGGING_FILE_NAME = LOGGING_FILE_NAME                                        # type: ignore

            if isinstance(SPLASH, qa_splash.Splash):
                qa_splash.update_step(SPLASH, 5, BOOT_STEPS)

            func: Callable[[object, Union[tk.Tk, tk.Toplevel], Any], tk.Toplevel] = _application_map[self.name]

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

    def error_handler(self, exception_class: Type[Exception], exception_str: str) -> None:
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = ''.join(i for i in traceback.format_tb(exc_traceback))
            
            unique_hash = hashlib.md5(
                f"{time.ctime(time.time())}{tb}{exception_str}{exception_class}{random.random()}".encode()
            ).hexdigest()
            
            unique_hash = hex(int(unique_hash, 16))            
            error_hash = hex(int(hashlib.md5(f"{exception_class}".encode()).hexdigest(), 16))
            std_hash = hex(int(hashlib.md5(f"{exception_class}{exception_str}".encode()).hexdigest(), 16))

            seq = '\n\t'; s = '\n'
            
            e_string = f"""
            
            -------------------------------------x-------------------------------------
            
            An error occurred during runtime; more info:
            
            Error class: <{exception_class}>
            Error: "{exception_str}"
            
            * Error TPR Code: {error_hash}
            * Error SEC Code: {std_hash}
            * Error PRC Code: {unique_hash}
            
            
            Technical Information:
            \"
                {seq.join(tb.split(s)).strip()} 
            \"
            ------------------------------------END------------------------------------
            
            """
            sys.stderr.write(e_string)

            if isinstance(self.shell, (tk.Tk, tk.Toplevel)):
                copy_to_clipboard(e_string, self.shell)

            messagebox.showerror(
                "Quizzing Application - App Instance Manger",
                f"THE FOLLOWING INFORMATION HAS BEEN COPIED TO YOUR CLIPBOARD; USE `CTRL+V` TO PASTE IT ANYWHERE.\n\n{e_string}"
            )

        except Exception as E:
            pass

    def __del__(self) -> None:
        global _bg_window
        cast(tk.Tk, _bg_window).quit()


_application_map: Dict[str, Callable[[object, Union[tk.Tk, tk.Toplevel], Any], tk.Toplevel]] = {
    'AdminTools':                               AdminTools.RunApp,      # type: ignore
    'QuizzingForm':                             QuizzingForm.RunApp,    # type: ignore
    'ThemingUtil':                              ThemingUtil.RunApp,     # type: ignore
    'RecoveryUtil':                             RecoveryUtils.RunApp,   # type: ignore

    'InstallThemeAddons':                       RunAddonsInstaller,     # type: ignore
}

_title_map = {
    'AdminTools':                               ('Administrator Tools', qa_functions.Files.AT_png),
    'QuizzingForm':                             ('Quizzing Tool', qa_functions.Files.QF_png),
    'ThemingUtil':                              ('Theming Utility', qa_functions.Files.TU_png),
    'RecoveryUtil':                             ('Recovery Utilities', qa_functions.Files.RU_png),

    'InstallThemeAddons':                       ('Addons Manager', qa_functions.Files.QF_png),
}

_ico_map = {
    AdminTools.RunApp:                                 qa_functions.Files.AT_ico,
    ThemingUtil.RunApp:                                qa_functions.Files.TU_ico,
    RecoveryUtils.RunApp:                              qa_functions.Files.RU_ico,
    QuizzingForm.RunApp:                               qa_functions.Files.QF_ico,
}

CLI_AllowedApplications: List[str] = ['AdminTools', 'QuizzingForm', 'RecoveryUtil', 'ThemingUtil', 'InstallThemeAddons']


def default_cli_handling(**kwargs: Optional[None]) -> None:
    print("CLI Tokens: ", kwargs, end="\n\n")


@click.group()
def _CLIHandler() -> None:
    pass


@_CLIHandler.command()
@click.argument('app_name', type=click.Choice(CLI_AllowedApplications))
@click.option('--open_file', help="open qa_files that is supplied in args", is_flag=True)
@click.option('--file_path', help="path of qa_files to open", default=None)
@click.option('--ttk_theme', help="TTK theme to use (default = 'alt')", default='alt')
@click.option('--debug', help='save console output', is_flag=True)
@click.option('--debug_all', help='enable (+save) debugging (ALL LEVELS)', is_flag=True)
@click.option('--debug_dev', help='enable (+save) [DEVELOPER] debug messages (also needs to be enabled in config file.)', is_flag=True)
@click.option('--weakHandling', help='weak error handling', is_flag=True)
def start_app(**kwargs: Optional[None]) -> None:
    global BOOT_STEPS, SPLASH

    default_cli_handling(**kwargs)

    if isinstance(SPLASH, qa_splash.Splash):
        qa_splash.update_step(SPLASH, 3, BOOT_STEPS)

    app = _ApplicationInstanceManager(cast(str, kwargs.get('app_name')), kwargs)
    app.run()


@_CLIHandler.command()
@click.argument('file_path', type=str)
def check_file(**kwargs: Optional[None]) -> None:
    default_cli_handling(**kwargs)
    return


def check_up_tickets() -> None:
    global SPLASH

    if len(qa_functions.YieldAllNVFlagsAsList('L_UPDATE')) > 0:
        qa_splash.hide(cast(qa_splash.Splash, SPLASH))

        if messagebox.askyesno('QA Updater', 'Outstanding update tickets exist; do you want to execute the updater now?'):
            subprocess.Popen([os.path.abspath('.qa_update\\qa_update_app.exe'), 'update', '--ReadFlags'])
            sys.exit(0)

        qa_splash.show(cast(qa_splash.Splash, SPLASH))


def check_files() -> None:
    if qa_functions.ConfigurationFile.json_data['application']['dev_mode']:
        return

    global SPLASH

    res = qa_functions.qa_diagnostics.Diagnostics.script_hash()
    if not res[0]:
        qa_splash.hide(cast(qa_splash.Splash, SPLASH))

        messagebox.showwarning("QA Startup Checker", 'One or more warnings (listed below) were raised by the diagnostics function.\n\nFailures: \n\t* ' + (
            '\n\t* '.join(cast(Iterable[str], res[1])).strip() if len(res[1]) > 0 else 'None'
        ))

        if messagebox.askyesno('QA Startup Checker', 'Updating the app MAY fix the aforementioned warnings; DO YOU WANT TO UPDATE / RESET THE APPLICATION.\n\nNote: no data will be destroyed in this process.'):
            subprocess.Popen([os.path.abspath('.qa_update\\qa_update_app.exe'), 'update', '--UpdateAll'])
            sys.exit(0)

        qa_splash.show(cast(qa_splash.Splash, SPLASH))


def check_for_updates() -> None:
    global SPLASH

    if not qa_functions.Diagnostics.app_version()[0]:
        qa_functions.ClearAppNVFlags('L_UPDATE')
        sys.stdout.write('App needs to updated.\n')

        qa_splash.hide(cast(qa_splash.Splash, SPLASH))

        if messagebox.askyesno('QA Updater', 'A new version of the app is available; do you want to update the app now?'):
            qa_functions.CreateNVFlag('L_UPDATE', 'UPDATE_ALL')
            subprocess.Popen([os.path.abspath('.qa_update\\qa_update_app.exe'), 'update', '--ReadFlags'])
            sys.exit(0)

        qa_splash.show(cast(qa_splash.Splash, SPLASH))

    else:
        sys.stdout.write("App configuration implies app is up to date.\n")


if __name__ == "__main__":
    master_error_manager.LOGGING_FILE_NAME = LOGGING_FILE_NAME
    master_error_manager.RedirectExceptionHandler()

    _bg_window = tk.Tk()
    _bg_window.withdraw()

    sys.stdout.write("Loaded modules; running application now.\n")

    SPLASH = qa_splash.Splash(tk.Toplevel(), 'Quizzing Application', qa_functions.Files.QF_png)
    qa_splash.update_step(SPLASH, 1, BOOT_STEPS)

    check_for_updates()
    check_up_tickets()
    check_files()

    qa_splash.update_step(SPLASH, 2, BOOT_STEPS)

    _CLIHandler()

else:
    sys.exit("cannot run qa_files `qa_main` as module")

