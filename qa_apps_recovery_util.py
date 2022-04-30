from threading import Thread
import tkinter as tk, sys
from tkinter import ttk
from typing import *
import qa_functions, qa_prompts
from qa_functions.qa_diagnostics import RunTest, Diagnostics
from qa_prompts import configure_scrollbar_style, configure_button_style, configure_entry_style, gsuid
from qa_functions.qa_enum import *
from PIL import ImageTk, Image


script_name = "APP_RU"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
APP_TITLE = "Quizzing Application | Recovery Utilities"


class _UI(Thread):
    def __init__(self, root, ic, ds, **kwargs):
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        ratio = 4 / 3
        wd_w = 700
        wd_w = wd_w if wd_w <= self.screen_dim[0] else self.screen_dim[0]
        self.window_size = [wd_w, int(ratio * wd_w)]
        self.window_size[0] = 790
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
        ]

        self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map = {}

        self.padX = 20
        self.padY = 10

        self.load_theme()
        self.update_requests = {}

        self.img_path = f"{qa_functions.Files.icoRoot}\\.png\\ftsra.png"
        self.img_size = (75, 75)
        self.img = None
        self.load_png()

        self.ttk_theme = self.kwargs['ttk_theme']

        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color)

        self.title_box = tk.Frame(self.root)
        self.title_label = tk.Label(self.title_box)
        self.title_icon = tk.Label(self.title_box)

        self.button_frame = tk.Frame(self.root)
        self.bf1 = tk.Frame(self.root)
        self.run_check_btn = ttk.Button(self.bf1, command=self.run_all)

        self.activity_container = tk.LabelFrame(self.root, text="Activity")
        self.activity_box = tk.Listbox(self.activity_container)
        self.activity = []
        self.activity_gsuid = {}

        self.x_sc_bar = ttk.Scrollbar(self.activity_container, orient=tk.HORIZONTAL, style="MyHoriz.TScrollbar")
        self.y_sc_bar = ttk.Scrollbar(self.activity_container, orient=tk.VERTICAL, style="My.TScrollbar")

        self.start()
        self.root.mainloop()

    def close(self):
        sys.stdout.write("ru - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.quit()

    def run(self):
        global DEBUG_NORM, APP_TITLE
        qa_prompts.DEBUG_NORM = DEBUG_NORM
        qa_prompts.TTK_THEME = self.ttk_theme

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.title(APP_TITLE)
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
        self.root.iconbitmap(qa_functions.Files.RU_ico)

        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.title_label.config(text="Recovery Utilities", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=self.img)
        self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX / 8), pady=self.padY, side=tk.LEFT)

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT)
        self.label_formatter(self.title_icon)

        self.button_frame.pack(fill=tk.X, expand=False)

        self.bf1.pack(fill=tk.BOTH, expand=False)

        self.run_check_btn.config(text="Run All Checks")
        self.run_check_btn.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.x_sc_bar.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY), side=tk.BOTTOM)
        self.y_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padY/4, self.padX), pady=(self.padY, 0), side=tk.RIGHT)

        self.activity_container.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.activity_box.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=(self.padY, 0))

        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        self.update_requests[gsuid()] = [self.root, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.title_box, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.button_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.bf1, TUC.BG, [TUV.BG]]

        self.label_formatter(self.activity_container, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)

        self.activity_box.config(yscrollcommand=self.y_sc_bar.set, xscrollcommand=self.x_sc_bar.set)
        self.y_sc_bar.config(command=self.activity_box.yview)
        self.x_sc_bar.config(command=self.activity_box.xview)

        self.update_ui()

    def disable_all_inputs(self):
        self.run_check_btn.config(state=tk.DISABLED)

    def enable_all_inputs(self):
        self.run_check_btn.config(state=tk.NORMAL)
        self.update_ui()

    def load_png(self):
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(i)

    def update_ui(self):
        self.load_theme()

        def tr(com) -> Tuple[bool, str]:
            try:
                com()
                return True, '<no errors>'
            except Exception as E:
                return False, str(E)

        def log_error(com: str, el, reason: str, ind: int):
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.ERROR,
                    f'Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])

            sys.stderr.write(f"[ERROR] {'[SAVED] ' if LOGGER_AVAIL else ''}Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>\n")

        def log_norm(com: str, el):
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.DEBUG,
                    f'Applied command \'{com}\' to {el} successfully <{elID}>',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])

            sys.stdout.write(f"[DEBUG] {'[SAVED] ' if LOGGER_AVAIL else ''}Applied command \'{com}\' to {el} successfully <{elID}>\n")

        for elID, (element, command, args) in self.update_requests.items():
            lCommand = [False]
            cargs = []
            for index, arg in enumerate(args):
                carg = arg
                if arg in ThemeUpdateVars.__members__.values():
                    carg = self.theme_update_map[arg]
                    if isinstance(carg, qa_functions.HexColor):
                        carg = carg.color
                elif type(arg) in (list, tuple):
                    if arg[0] == 'LOAD_ARG':
                        carg = self.activity_gsuid[arg[1]]

                cargs.append(carg)

            if command == ThemeUpdateCommands.BG:  # Background
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(bg=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.FG:  # Foreground
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(fg=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_BG:  # Active Background
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(activebackground=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_FG:  # Active Foreground
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(activeforeground=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_FG:  # BORDER COLOR
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent, highlightbackground=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.BORDER_SIZE:  # BORDER SIZE
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(highlightthickness=cargs[0], bd=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.FONT:  # Font
                if len(cargs) == 2:
                    ok, rs = tr(lambda: element.config(font=(cargs[0], cargs[1])))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.CUSTOM:  # Custom
                if len(cargs) <= 0:
                    lCommand = [True, 'Function not provided', 1]
                elif len(cargs) == 1:
                    ok, rs = tr(cargs[0])
                    if not ok:
                        lCommand = [True, rs, 0]
                elif len(cargs) > 1:
                    ok, rs = tr(lambda: cargs[0](*cargs[1::]))
                    if not ok:
                        lCommand = [True, rs, 0]

            elif command == ThemeUpdateCommands.WRAP_LENGTH:  # WL
                if len(cargs) == 1:
                    ok, rs = tr(lambda: element.config(wraplength=cargs[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            if lCommand[0] is True:
                log_error(command.name, element, lCommand[1], lCommand[2])
            elif DEBUG_NORM:
                log_norm(command.name, element)

            del lCommand, cargs

        # TTK
        self.ttk_style.configure(
            'TMenubutton',
            background=self.theme.background.color,
            foreground=self.theme.accent.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            arrowcolor=self.theme.accent.color,
            borderwidth=0
        )

        self.ttk_style.map(
            'TMenubutton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.background.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color)],
            arrowcolor=[('active', self.theme.background.color), ('disabled', self.theme.gray.color)]
        )

        self.ttk_style.configure(
            'TButton',
            background=self.theme.background.color,
            foreground=self.theme.accent.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            focuscolor=self.theme.accent.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'Err.TButton',
            background=self.theme.background.color,
            foreground=self.theme.error.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            focuscolor=self.theme.error.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Err.TButton',
            background=[('active', self.theme.error.color), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        cb_fg = qa_functions.qa_colors.Functions.calculate_more_contrast(qa_functions.HexColor("#000000"), qa_functions.HexColor("#ffffff"), self.theme.background).color

        self.ttk_style.configure(
            'Contrast.TButton',
            background=self.theme.background.color,
            foreground=cb_fg,
            font=(self.theme.font_face, self.theme.font_main_size),
            focuscolor=self.theme.error.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Contrast.TButton',
            background=[('active', cb_fg), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color)

        self.activity_box.config(
            bg=self.theme.background.color,
            fg=self.theme.foreground.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            selectmode=tk.EXTENDED,
            selectbackground=self.theme.accent.color,
            selectforeground=self.theme.background.color
        )

    def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None, bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, abg=ThemeUpdateVars.ACCENT, afg=ThemeUpdateVars.BG):
        if padding is None:
            padding = self.padX

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BG, [bg if not accent else ThemeUpdateVars.ACCENT]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FG, [fg if not accent else ThemeUpdateVars.BG]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_BG, [abg if not accent else ThemeUpdateVars.BG]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_FG, [afg if not accent else ThemeUpdateVars.ACCENT]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FONT, [font, size]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.CUSTOM, [lambda tbc, tbs: button.configure(
            highlightbackground=tbc,
            bd=tbs,
            highlightcolor=tbc,
            highlightthickness=tbs,
            borderwidth=tbs,
            relief=tk.RIDGE
        ), ThemeUpdateVars.BORDER_COLOR, ThemeUpdateVars.BORDER_SIZE]]

    def label_formatter(self, label: tk.Widget, bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, size=ThemeUpdateVars.FONT_SIZE_MAIN, font=ThemeUpdateVars.DEFAULT_FONT_FACE, padding=None):
        if padding is None:
            padding = self.padX

        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.BG, [bg]]
        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.FG, [fg]]

        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.FONT, [font, size]]
        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

    def load_theme(self):
        self.theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map = {
            ThemeUpdateVars.BG: self.theme.background,
            ThemeUpdateVars.FG: self.theme.foreground,
            ThemeUpdateVars.ACCENT: self.theme.accent,
            ThemeUpdateVars.ERROR: self.theme.error,
            ThemeUpdateVars.WARNING: self.theme.warning,
            ThemeUpdateVars.OKAY: self.theme.okay,
            ThemeUpdateVars.GRAY: self.theme.gray,
            ThemeUpdateVars.DEFAULT_FONT_FACE: self.theme.font_face,
            ThemeUpdateVars.ALT_FONT_FACE: self.theme.font_alt_face,
            ThemeUpdateVars.FONT_SIZE_TITLE: self.theme.font_title_size,
            ThemeUpdateVars.FONT_SIZE_LARGE: self.theme.font_large_size,
            ThemeUpdateVars.FONT_SIZE_MAIN: self.theme.font_main_size,
            ThemeUpdateVars.FONT_SIZE_SMALL: self.theme.font_small_size,
            ThemeUpdateVars.FONT_SIZE_XL_TITLE: self.theme.font_xl_title_size,
            ThemeUpdateVars.BORDER_SIZE: self.theme.border_size,
            ThemeUpdateVars.BORDER_COLOR: self.theme.border_color,
        }

    def run_all(self):
        self.disable_all_inputs()
        self.clear_lb()

        fail_acc = 0
        pass_acc = 0
        warn_acc = 0
        uc_functions = ""
        uc_restart_functions = []
        norm_call_functions = []

        def log(String, level=LoggingLevel.DEBUG):
            global DEBUG_NORM, LOGGER_FUNC, LOGGER_AVAIL, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
            if DEBUG_NORM and level == LoggingLevel.DEBUG:
                print(f'[DEBUG] [SAVED] [{level.name.upper()}] {String}')

                LOGGER_FUNC(
                    [qa_functions.LoggingPackage(
                        level,
                        f'[TEST] {String}',
                        LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                    )]
                )

            elif LOGGER_AVAIL and level != LoggingLevel.DEBUG:
                print(f'[DEBUG] [SAVED] [{level.name.upper()}] {String}')

                LOGGER_FUNC(
                    [qa_functions.LoggingPackage(
                        level,
                        f'[TEST] {String}',
                        LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                    )]
                )

        for test, string in (
            (Diagnostics.app_version, 'Checking for updates'),
            (Diagnostics.default_theme, 'Checking default theme'),
            (Diagnostics.global_check, 'Checking all files')
        ):
            log(string, LoggingLevel.INFO)

            if len(self.activity) > 0:
                self.insert_into_lb("")

            raw_res = RunTest(test)
            self.insert_into_lb(string)
            if raw_res is None:
                self.insert_into_lb("Failed to run test", fg=ThemeUpdateVars.ERROR, sbg=ThemeUpdateVars.ERROR)
                continue

            passed, f_s_strs, wa_data, fix_command = raw_res

            if passed:
                self.insert_into_lb('PASSED', fg=ThemeUpdateVars.OKAY, sbg=ThemeUpdateVars.OKAY)
                log('[RESULT] Test PASSED')

                pass_acc += 1
                if len(f_s_strs) > 0:
                    for st in f_s_strs:
                        self.insert_into_lb(f"    {st}")
                        log(f'[PASS] [MESSAGE]\t\t{st}')

            else:
                self.insert_into_lb('FAILED', fg=ThemeUpdateVars.ERROR, sbg=ThemeUpdateVars.ERROR)
                fail_acc += 1
                log('[RESULT] Test FAILED')

                if len(f_s_strs) > 0:
                    for st in f_s_strs:
                        self.insert_into_lb(f"    Failure: {st}")
                        log(f'[FAIL] [FAILURE]\t\t{st}', LoggingLevel.ERROR)

                if fix_command in qa_functions.qa_diagnostics._UC_FUNC:
                    if fix_command in qa_functions.qa_diagnostics._REQ_RESTART:
                        uc_restart_functions.append(fix_command(re_str=True))
                    else:
                        uc_functions = f"{uc_functions} {fix_command(re_str=True)}"

                else:
                    norm_call_functions.append(fix_command)

            if len(wa_data) > 0:
                for d in wa_data:
                    if isinstance(d, str):
                        self.insert_into_lb(f"    Warning: {d}", fg=ThemeUpdateVars.WARNING, sbg=ThemeUpdateVars.WARNING)
                        warn_acc += 1
                        log(f'[{"PASS" if passed else "FAIL"}] [WARNING]\t\t{d}', LoggingLevel.WARNING)

        self.insert_into_lb("")
        self.insert_into_lb(f"Ran {pass_acc + fail_acc} checks:")
        self.insert_into_lb(f"    > {pass_acc} tests passed", fg=ThemeUpdateVars.OKAY, sbg=ThemeUpdateVars.OKAY)
        self.insert_into_lb(f"    > {fail_acc} tests failed", fg=ThemeUpdateVars.ERROR, sbg=ThemeUpdateVars.ERROR)
        self.insert_into_lb(f"    > {warn_acc} warnings", fg=ThemeUpdateVars.WARNING, sbg=ThemeUpdateVars.WARNING)

        log(f'[ACC. RESULTS] ({pass_acc} Passed) ({fail_acc} Failed) ({warn_acc} Warnings) ', LoggingLevel.INFO)

        if fail_acc > 0:
            log(f'Found {fail_acc} failures; prompting for permission to fix now', LoggingLevel.INFO)

            s_mem = qa_functions.SMem()
            qa_prompts.InputPrompts.ButtonPrompt(s_mem, 'Fix Errors?', ('Yes', 'y'), ('No', 'n'), default='<cancel>', message=f'Found {fail_acc} errors; do you want to fix these errors now?')

            if s_mem.get() == 'y':
                log(f'User agreed to fix errors.', LoggingLevel.INFO)

                self.insert_into_lb("")
                self.insert_into_lb("-"*100)
                self.insert_into_lb("Running FIX commands")

            else:
                log('User denied access to fix errors.', LoggingLevel.INFO)

            del s_mem

        del fail_acc, pass_acc

        self.enable_all_inputs()

    def insert_into_lb(self, string: str, bg: Union[str, ThemeUpdateVars] = ThemeUpdateVars.BG, fg: Union[str, ThemeUpdateVars] = ThemeUpdateVars.FG, sbg: Union[str, ThemeUpdateVars] = ThemeUpdateVars.ACCENT, sfg: Union[str, ThemeUpdateVars] = ThemeUpdateVars.BG):
        self.activity_box.insert(tk.END, string)

        ngsuid = gsuid()
        self.activity_gsuid[ngsuid] = len(self.activity)

        self.update_requests[ngsuid] = [  # For dynamic theming
            self.activity_box, ThemeUpdateCommands.CUSTOM,
            [
                lambda ind, a_bg, a_fg, s_bg, s_fg: self.activity_box.itemconfig(
                    ind, bg=a_bg, fg=a_fg, selectbackground=s_bg, selectforeground=s_fg
                ), ['LOAD_ARG', ngsuid], bg, fg, sbg, sfg
            ]
        ]

        self.activity_box.itemconfig(
            len(self.activity),
            bg=self.theme_update_map[bg].color if bg in self.theme_update_map else bg,
            fg=self.theme_update_map[fg].color if fg in self.theme_update_map else fg,
            selectbackground=self.theme_update_map[sbg].color if sbg in self.theme_update_map else sbg,
            selectforeground=self.theme_update_map[sfg].color if sfg in self.theme_update_map else sfg,
        )

        self.activity.append(string.strip())
        self.activity_box.yview(tk.END)

        self.root.update()

    def clear_lb(self):
        self.activity = []
        self.activity_box.delete(0, tk.END)

        for uid in self.activity_gsuid:
            if uid in self.update_requests:
                self.update_requests.pop(uid)

        self.activity_gsuid = {}

        self.root.update()

    def __del__(self):
        self.thread.join(self, 0)


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    ui_root = tk.Toplevel()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root
