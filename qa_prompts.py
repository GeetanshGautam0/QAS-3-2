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

            self.load_theme()

            self.update_requests = {}
            # element: ['COMMAND_ID', ['for_normal: [args]', 'for_custom: [command, [args]]']]
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

            self.update_requests[self.root] = [ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

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
                        f'Failed to apply command \'{com}\' to {el}: {reason} ({ind})',
                        LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                    )])
                else:
                    print(f"[ERROR] Failed to apply command \'{com}\' to {el}: {reason} ({ind})")

            def log_norm(com: str, el):
                if not DEBUG_NORM: return

                if LOGGER_AVAIL:
                    LOGGER_FUNC([qa_functions.LoggingPackage(
                        LoggingLevel.DEBUG,
                        f'Applied command \'{com}\' to {el} successfully',
                        LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                    )])
                else:
                    print(f"[DEBUG] Applied command \'{com}\' to {el} successfully")

            for element, (command, args) in self.update_requests.items():
                print(element, command, args)

                lCommand = [False]
                if command == ThemeUpdateCommands.BG:
                    if len(args) >= 1:
                        carg = args[0] if args[0] not in ThemeUpdateVars else self.theme_update_map[args[0]]
                        ok, rs = tr(lambda: element.config(bg=carg.color))
                        if not ok:
                            lCommand = [True, rs, 1]

                    else:
                        lCommand = [True, 'Insufficient args', 0]

                    if lCommand[0] is True:
                        log_error(command.name, element, lCommand[1], lCommand[2])
                    else:
                        log_norm(command.name, element)

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
                ThemeUpdateVars.BORDER_COLOUR: self.theme.border_color
            }

        def __del__(self):
            self.thread.join(self, 0)


class InputPrompts:
    pass
