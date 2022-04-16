from threading import Thread
import tkinter as tk, sys, qa_prompts, qa_functions, qa_files, PIL
from typing import *
from tkinter import ttk
from qa_functions.qa_enum import *
from qa_prompts import gsuid
from PIL import Image, ImageTk


script_name = "APP_TU"
APP_TITLE = "Quizzing Application | Theming Utility"
_THEME_FILE_TYPE = qa_functions.qa_enum.FileType.QA_THEME

LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = ''
DEBUG_NORM = False


class _UI(Thread):
    def __init__(self, root, ic, ds, **kwargs):
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        ratio = 4/3
        wd_w = 700
        wd_w = wd_w if wd_w <= self.screen_dim[0] else self.screen_dim[0]
        self.window_size = [wd_w, int(ratio * wd_w)]
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

        self.img_path = f"{qa_functions.Files.icoRoot}\\.png\\themer.png"
        self.img_size = (75, 75)
        self.img = None
        self.load_png()

        self.title_box = tk.Frame(self.root)
        self.title_label = tk.Label(self.title_box)
        self.title_icon = tk.Label(self.title_box)

        self.start()
        self.root.mainloop()

    def close(self):
        sys.stdout.write("tu - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.quit()

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
            else:
                sys.stderr.write(f"[ERROR] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>\n")

        def log_norm(com: str, el):
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.DEBUG,
                    f'Applied command \'{com}\' to {el} successfully <{elID}>',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])
            else:
                print(f"[DEBUG] Applied command \'{com}\' to {el} successfully <{elID}>")

        for elID, (element, command, args) in self.update_requests.items():
            lCommand = [False]
            cargs = []
            for index, arg in enumerate(args):
                cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                if isinstance(cargs[index], qa_functions.HexColor):
                    cargs[index] = cargs[index].color

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
                    print(cargs)
                    ok, rs = tr(lambda: cargs[0](cargs[1::]))
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

        # self.setup_png()

    def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None):
        if padding is None:
            padding = self.padX

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FONT, [font, size]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

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
            ThemeUpdateVars.BORDER_COLOR: self.theme.border_color
        }

    def run(self):
        global DEBUG_NORM, APP_TITLE
        DEBUG_NORM = self.kwargs.get('debug')
        qa_prompts.DEBUG_NORM = DEBUG_NORM

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.title(APP_TITLE)
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
        self.root.iconbitmap(qa_functions.Files.TU_ico)

        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.title_label.config(text="Theming Utility", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=self.img)
        self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX/8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX/8), pady=self.padY, side=tk.LEFT)

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT)
        self.label_formatter(self.title_icon)

        self.update_requests[gsuid()] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gsuid()] = [self.title_box, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.update_ui()

    def load_png(self):
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(i)

    def __del__(self):
        self.thread.join(self, 0)


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    ui_root = tk.Toplevel()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root
