import tkinter as tk
from tkinter import messagebox

import qa_functions, qa_files
from qa_functions.qa_enum import *

import threading
from typing import *
from dataclasses import dataclass


LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = ''
DEBUG_NORM = False


@dataclass
class InfoPacket:
    title: str
    msg: str
    long: bool = False


class MessagePrompts:
    class Info (threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool = False):

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root: Union[tk.Tk, tk.Toplevel] = root
            self.qoc = quit_on_close
            self.msg = msg

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 10/9
            wd_w = 900 if msg.long else 450
            wd_w = wd_w if wd_w <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio*wd_w)]
            self.screen_pos = [int(self.screen_dim[0]/2 - self.window_size[0]/2),
                               int(self.screen_dim[1]/2 - self.window_size[1]/2)]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests = {}
            # ID: [element, 'COMMAND_ID', ['for_normal: [args]', 'for_custom: [command, args]']]

            self.title_label = tk.Label(self.root)

            self.start()
            self.root.mainloop()

        def close(self):
            if self.qoc:
                self.root.after(0, self.root.quit)
            else:
                self.root.after(0, self.root.destroy)

        def run(self):
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title(self.msg.title)
            self.root.resizable(False, True)

            self.update_requests[qa_functions.gen_short_uid('elForm')] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.label_formatter(self.title_label, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_TITLE)

            self.title_label.config(text=self.msg.title)
            self.title_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

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
                    print(f"[ERROR] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>")

            def log_norm(com: str, el):
                if not DEBUG_NORM:
                    return

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

                if command == ThemeUpdateCommands.BG:                   # Background
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(bg=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.FG:                 # Foreground
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(fg=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_BG:          # Active Background
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(activebackground=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_FG:          # Active Foreground
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(activeforeground=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_FG:          # BORDER COLOR
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent, highlightbackground=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.BORDER_SIZE:        # BORDER SIZE
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(highlightthickness=cargs[0], bd=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.FONT:               # Font
                    if len(cargs) == 2:
                        ok, rs = tr(lambda: element.config(font=(cargs[0], cargs[1])))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.CUSTOM:             # Custom
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

                elif command == ThemeUpdateCommands.WRAP_LENGTH:        # WL
                    if len(cargs) == 1:
                        ok, rs = tr(lambda: element.config(wraplength=cargs[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                if lCommand[0] is True:
                    log_error(command.name, element, lCommand[1], lCommand[2])
                else:
                    log_norm(command.name, element)

                del lCommand, cargs

        def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None):
            if padding is None:
                padding = self.padX

            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, size=ThemeUpdateVars.FONT_SIZE_MAIN, font=ThemeUpdateVars.DEFAULT_FONT_FACE, padding=None):
            if padding is None:
                padding = self.padX

            self.update_requests[qa_functions.gen_short_uid('elForm')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[qa_functions.gen_short_uid('elForm')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[qa_functions.gen_short_uid('elForm')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

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

        def __del__(self):
            self.thread.join(self, 0)


class InputPrompts:
    pass
