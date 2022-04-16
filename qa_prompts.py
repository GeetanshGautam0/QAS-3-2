from tkinter import messagebox, ttk

import PIL.Image

from qa_functions.qa_enum import *

import threading, traceback, tkinter as tk, qa_functions, sys, os, shutil
from typing import *
from dataclasses import dataclass


from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
from PIL import Image, ImageTk
from io import BytesIO

LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = ''
DEBUG_NORM = False


_SVG_COLOR_REPL_ROOT = "<<<PYTHON__INSERT__COLOR__HERE>>>"


@dataclass
class InfoPacket:
    msg: str

    button_text: str = "OKAY"
    title: str = None
    long: bool = False


class MessagePrompts:
    # Info Prompt
    @staticmethod
    def show_info(msg: InfoPacket, root: Union[tk.Tk, tk.Toplevel] = None, qoc: bool = False):
        try:
            if root is None:
                root = tk.Tk()
            MessagePrompts._CInfo(root, msg, qoc)
        except Exception as E:
            print(f"Failed to use custom prompt: {E} {traceback.format_exc()}")
            messagebox.showinfo(msg.title, msg.msg)
            if qoc: sys.exit('show_error fallback')

    class _CInfo(threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool):
            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root, self.msg, self.qoc = root, msg, quit_on_close

            self.msg.long = len(self.msg.msg) > 70
            if self.msg.title is None: self.msg.title = "Info"

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = (4 if not self.msg.long else 10) / 9
            wd_w = 500 if self.msg.long else 450
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

            self.svg_size = (50, 50)
            self.appdata_svg_base = '.info_svg'
            self.svg_src = ".src\\.icons\\.info\\base_icon.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}\\svg.svg".replace('/', '\\')
            self.img = None

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.data_label = tk.Label(self.root)
            self.data_frame = tk.Frame(self.root)
            self.data_txt = tk.Text(self.data_frame)
            self.data_sc_bar = ttk.Scrollbar(self.data_frame)
            self.close_button = tk.Button(self.root, command=self.close)

            self.acc = 0

            self.start()
            self.root.mainloop()

        def close(self):
            if self.qoc:
                self.root.after(0, self.root.quit)
            else:
                self.root.after(0, self.root.destroy)

        def create_base(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title(self.msg.title)
            self.root.resizable(False, True)

            self.update_ui()

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

            self.update_svg()

        def svg_set_path(self):
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            dst_file = self.svg_path

            if not os.path.exists(dst):
                os.makedirs(dst)

            File = qa_functions.File(self.svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.accent.color)
            File = qa_functions.File(dst_file)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        def update_svg(self):
            self.svg_set_path()
            self.img = get_svg(self.svg_path, self.theme.background.color, self.svg_size)
            self.svg_label.config(image=self.img)

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
                ThemeUpdateVars.BORDER_SIZE: self.theme.border_size,
                ThemeUpdateVars.BORDER_COLOR: self.theme.border_color
            }

        def run(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title("Quizzing Application | Info")
            # self.root.resizable(False, True)
            self.root.focus_get()
            
            self.update_requests[gsuid()] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.update_requests[gsuid()] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

            self.svg_label.pack(side=tk.LEFT, pady=self.padY, padx=(self.padX, self.padX/8))
            self.svg_size = (50, 50)
            self.svg_label.config(justify=tk.CENTER, anchor=tk.CENTER, width=self.svg_size[0], height=self.svg_size[1])
            self.label_formatter(self.svg_label)

            self.title_label.config(text=self.msg.title, justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX/8, self.padX), pady=self.padY, side=tk.RIGHT)

            self.title_frame.pack(fill=tk.X, expand=True)

            if self.msg.long:
                self.data_txt.delete(0.0, tk.END)
                self.data_txt.insert(0.0, self.msg.msg)
                self.data_txt.config(state=tk.DISABLED, width=15, height=8)
                self.data_txt.pack(fill=tk.BOTH, expand=True, padx=(self.padX, self.padX/4), pady=self.padY, side=tk.LEFT)
                self.data_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padX/4, self.padX), pady=self.padY, side=tk.RIGHT)
                self.label_formatter(self.data_txt, size=ThemeUpdateVars.FONT_SIZE_SMALL)
                self.update_requests[gsuid()] = [self.data_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.data_frame.pack(fill=tk.BOTH, expand=True)
                self.data_txt['yscrollcommand'] = self.data_sc_bar.set
                self.data_sc_bar.config(command=self.data_txt.yview)

            else:
                self.data_label.config(text=self.msg.msg, justify=tk.LEFT, anchor=tk.W)
                self.data_label.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.label_formatter(self.data_label)

            self.close_button.config(text=self.msg.button_text)
            self.close_button.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, ipadx=self.padX, ipady=self.padY)

            self.label_formatter(self.title_label, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE if not self.msg.long else ThemeUpdateVars.FONT_SIZE_TITLE)
            self.button_formatter(self.close_button, True)

            self.update_ui()

        def __del__(self):
            self.thread.join(self, 0)

    # Warning Prompt
    @staticmethod
    def show_warning(msg: InfoPacket, root: Union[tk.Tk, tk.Toplevel] = None, qoc: bool = False):
        try:
            if root is None:
                root = tk.Tk()
            MessagePrompts._CWarning(root, msg, qoc)

        except Exception as E:
            sys.stderr.write(f"Failed to use custom prompt: {E} {traceback.format_exc()}")
            messagebox.showwarning(msg.title, msg.msg)
            if qoc: sys.exit('show_error fallback')

    class _CWarning(threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool):
            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root, self.msg, self.qoc = root, msg, quit_on_close

            self.msg.long = len(self.msg.msg) > 70
            if self.msg.title is None: self.msg.title = "Warning"

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = (4 if not self.msg.long else 10) / 9
            wd_w = 500 if self.msg.long else 450
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

            self.svg_size = (50, 50)
            self.appdata_svg_base = '.warning_svg'
            self.svg_src = ".src\\.icons\\.warning\\base_icon.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}\\svg.svg".replace('/', '\\')
            self.img = None

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.data_label = tk.Label(self.root)
            self.data_frame = tk.Frame(self.root)
            self.data_txt = tk.Text(self.data_frame)
            self.data_sc_bar = ttk.Scrollbar(self.data_frame)
            self.close_button = tk.Button(self.root, command=self.close)

            self.acc = 0

            self.start()
            self.root.mainloop()

        def close(self):
            if self.qoc:
                self.root.after(0, self.root.quit)
            else:
                self.root.after(0, self.root.destroy)

        def create_base(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title(self.msg.title)
            self.root.resizable(False, True)

            self.update_ui()

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

            self.update_svg()

        def svg_set_path(self):
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            dst_file = self.svg_path

            if not os.path.exists(dst):
                os.makedirs(dst)

            File = qa_functions.File(self.svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.warning.color)
            File = qa_functions.File(dst_file)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        def update_svg(self):
            self.svg_set_path()
            self.img = get_svg(self.svg_path, self.theme.background.color, self.svg_size)
            self.svg_label.config(image=self.img)

        def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None):
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.WARNING]]
            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.WARNING if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.WARNING]]
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
                ThemeUpdateVars.BORDER_SIZE: self.theme.border_size,
                ThemeUpdateVars.BORDER_COLOR: self.theme.border_color
            }

        def run(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title("Quizzing Application | Warning")
            # self.root.resizable(False, True)
            self.root.focus_get()

            self.update_requests[gsuid()] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.update_requests[gsuid()] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

            self.svg_label.pack(side=tk.LEFT, pady=self.padY, padx=(self.padX, self.padX / 8))
            self.svg_size = (50, 50)
            self.svg_label.config(justify=tk.CENTER, anchor=tk.CENTER, width=self.svg_size[0], height=self.svg_size[1])
            self.label_formatter(self.svg_label)

            self.title_label.config(text=self.msg.title, justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)

            self.title_frame.pack(fill=tk.X, expand=True)

            if self.msg.long:
                self.data_txt.delete(0.0, tk.END)
                self.data_txt.insert(0.0, self.msg.msg)
                self.data_txt.config(state=tk.DISABLED, width=15, height=8)
                self.data_txt.pack(fill=tk.BOTH, expand=True, padx=(self.padX, self.padX / 4), pady=self.padY, side=tk.LEFT)
                self.data_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padX / 4, self.padX), pady=self.padY, side=tk.RIGHT)
                self.label_formatter(self.data_txt, size=ThemeUpdateVars.FONT_SIZE_SMALL)
                self.update_requests[gsuid()] = [self.data_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.data_frame.pack(fill=tk.BOTH, expand=True)
                self.data_txt['yscrollcommand'] = self.data_sc_bar.set
                self.data_sc_bar.config(command=self.data_txt.yview)

            else:
                self.data_label.config(text=self.msg.msg, justify=tk.LEFT, anchor=tk.W)
                self.data_label.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.label_formatter(self.data_label)

            self.close_button.config(text=self.msg.button_text)
            self.close_button.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, ipadx=self.padX, ipady=self.padY)

            self.label_formatter(self.title_label, fg=ThemeUpdateVars.WARNING, size=ThemeUpdateVars.FONT_SIZE_LARGE if not self.msg.long else ThemeUpdateVars.FONT_SIZE_TITLE)
            self.button_formatter(self.close_button, True)

            self.update_ui()

        def __del__(self):
            self.thread.join(self, 0)

    # Error Prompt
    @staticmethod
    def show_error(msg: InfoPacket, root: Union[tk.Tk, tk.Toplevel] = None, qoc: bool = False):
        try:
            if root is None:
                root = tk.Tk()
            MessagePrompts._CError(root, msg, qoc)

        except Exception as E:
            sys.stderr.write(f"Failed to use custom prompt: {E} {traceback.format_exc()}")
            messagebox.showerror(msg.title, msg.msg)
            if qoc: sys.exit('show_error fallback')

    class _CError(threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool):
            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root, self.msg, self.qoc = root, msg, quit_on_close

            self.msg.long = len(self.msg.msg) > 70
            if self.msg.title is None: self.msg.title = "Error"

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = (4 if not self.msg.long else 10) / 9
            wd_w = 500 if self.msg.long else 450
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

            self.svg_size = (50, 50)
            self.appdata_svg_base = '.error_svg'
            self.svg_src = ".src\\.icons\\.error\\base_icon.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}\\svg.svg".replace('/', '\\')
            self.img = None

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.data_label = tk.Label(self.root)
            self.data_frame = tk.Frame(self.root)
            self.data_txt = tk.Text(self.data_frame)
            self.data_sc_bar = ttk.Scrollbar(self.data_frame)
            self.close_button = tk.Button(self.root, command=self.close)

            self.acc = 0

            self.start()
            self.root.mainloop()

        def close(self):
            if self.qoc:
                self.root.after(0, self.root.quit)
            else:
                self.root.after(0, self.root.destroy)

        def create_base(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title(self.msg.title)
            self.root.resizable(False, True)

            self.update_ui()

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

            self.update_svg()

        def svg_set_path(self):
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            dst_file = self.svg_path

            if not os.path.exists(dst):
                os.makedirs(dst)

            File = qa_functions.File(self.svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.error.color)
            File = qa_functions.File(dst_file)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        def update_svg(self):
            self.svg_set_path()
            self.img = get_svg(self.svg_path, self.theme.background.color, self.svg_size)
            self.svg_label.config(image=self.img)

        def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None):
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ERROR]]
            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ERROR if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ERROR]]
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
                ThemeUpdateVars.BORDER_SIZE: self.theme.border_size,
                ThemeUpdateVars.BORDER_COLOR: self.theme.border_color
            }

        def run(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title("Quizzing Application | Error")
            # self.root.resizable(False, True)
            self.root.focus_get()

            self.update_requests[gsuid()] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.update_requests[gsuid()] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

            self.svg_label.pack(side=tk.LEFT, pady=self.padY, padx=(self.padX, self.padX / 8))
            self.svg_size = (50, 50)
            self.svg_label.config(justify=tk.CENTER, anchor=tk.CENTER, width=self.svg_size[0], height=self.svg_size[1])
            self.label_formatter(self.svg_label)

            self.title_label.config(text=self.msg.title, justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)

            self.title_frame.pack(fill=tk.X, expand=True)

            if self.msg.long:
                self.data_txt.delete(0.0, tk.END)
                self.data_txt.insert(0.0, self.msg.msg)
                self.data_txt.config(state=tk.DISABLED, width=15, height=8)
                self.data_txt.pack(fill=tk.BOTH, expand=True, padx=(self.padX, self.padX / 4), pady=self.padY, side=tk.LEFT)
                self.data_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padX / 4, self.padX), pady=self.padY, side=tk.RIGHT)
                self.label_formatter(self.data_txt, size=ThemeUpdateVars.FONT_SIZE_SMALL)
                self.update_requests[gsuid()] = [self.data_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.data_frame.pack(fill=tk.BOTH, expand=True)
                self.data_txt['yscrollcommand'] = self.data_sc_bar.set
                self.data_sc_bar.config(command=self.data_txt.yview)

            else:
                self.data_label.config(text=self.msg.msg, justify=tk.LEFT, anchor=tk.W)
                self.data_label.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.label_formatter(self.data_label)

            self.close_button.config(text=self.msg.button_text)
            self.close_button.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, ipadx=self.padX, ipady=self.padY)

            self.label_formatter(self.title_label, fg=ThemeUpdateVars.ERROR, size=ThemeUpdateVars.FONT_SIZE_LARGE if not self.msg.long else ThemeUpdateVars.FONT_SIZE_TITLE)
            self.button_formatter(self.close_button, True)

            self.update_ui()

        def __del__(self):
            self.thread.join(self, 0)


class InputPrompts:
    pass


def get_svg(svg_file, background, size=None):

    if isinstance(background, str):
        background = int(background.replace("#", '0x'), 0)

    drawing = svg2rlg(svg_file)
    bytes_png = BytesIO()
    renderPM.drawToFile(drawing, bytes_png, fmt="PNG", bg=background)
    img = Image.open(bytes_png)
    if size is not None:
        img = img.resize(size, PIL.Image.ANTIALIAS)

    p_img = ImageTk.PhotoImage(img)

    return p_img


def gsuid(arg1: str = 'elForm'):
    return qa_functions.gen_short_uid(arg1)

