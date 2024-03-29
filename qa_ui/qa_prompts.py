import threading, traceback, tkinter as tk, qa_functions, sys, os, re, urllib3, PIL.Image, hashlib
from tkinter import messagebox, ttk
from typing import *
from dataclasses import dataclass
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from qa_functions.qa_enum import LoggingLevel, ThemeUpdateVars, ThemeUpdateCommands
from qa_functions.qa_std import ANSI, AppLogColors


LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = 'QA_PROMPTS'
DEBUG_NORM = False
DEBUG_DEV_FLAG = False

TTK_THEME = 'clam'
_SVG_COLOR_REPL_ROOT = "<<<PYTHON__INSERT__COLOR__HERE>>>"

configure_scrollbar_style = qa_functions.TTKTheme.configure_scrollbar_style
configure_button_style = qa_functions.TTKTheme.configure_button_style
configure_entry_style = qa_functions.TTKTheme.configure_entry_style


@dataclass
class InfoPacket:
    msg: str

    button_text: str = "OKAY"
    title: Union[str, None] = None
    long: bool = False


@dataclass
class DownloadPacket:
    output_file: str

    title: str = "Enter URL"
    message: str = ""
    file_extn: Union[str, None] = None


class MessagePrompts:
    # Info Prompt
    @staticmethod
    def show_info(msg: InfoPacket, root: Union[tk.Tk, tk.Toplevel, None] = None, qoc: bool = False) -> None:
        try:
            if root is None:
                root = tk.Toplevel()
            MessagePrompts._CInfo(root, msg, qoc)
        except Exception as E:
            log(LoggingLevel.ERROR, f"Failed to use custom prompt: {E} {traceback.format_exc()}")
            messagebox.showinfo(msg.title, msg.msg)
            if qoc:
                sys.exit('show_info fallback')

    class _CInfo(threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool) -> None:
            global TTK_THEME

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root, self.msg, self.qoc = root, msg, quit_on_close

            self.msg.long = len(self.msg.msg) > 70
            if self.msg.title is None:
                self.msg.title = "Info"

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = (4 if not self.msg.long else 10) / 9
            wd_w = 500 if self.msg.long else 450
            wd_w = wd_w if wd_w <= self.screen_dim[0] else self.screen_dim[0]
            lwdw = 700 if 700 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [lwdw if self.msg.long else wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[qa_functions.HexColor, int, str, float]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.svg_size = (50, 50)
            self.appdata_svg_base = '.info_svg'
            self.svg_src = ".src/.icons/.info/base_icon.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}\\svg.svg".replace('/', '\\')
            self.img = None

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.data_label = tk.Label(self.root)
            self.data_frame = tk.Frame(self.root)
            self.data_txt = tk.Text(self.data_frame, wrap=tk.WORD)
            self.data_sc_bar = ttk.Scrollbar(self.data_frame, style='MyPrompts.TScrollbar')
            self.close_button = tk.Button(self.root, command=self.close)

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            if self.qoc:
                sys.exit()
            else:
                self.thread.join(self, 0)
                self.root.after(0, self.root.quit)
                self.root.withdraw()
                self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_el, _command, _args) in self.update_requests.items():
                element = cast(tk.Label, _el)
                command = cast(ThemeUpdateCommands, _command)
                args = cast(List[Any], _args)
                lCommand = [False, '', -1]
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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.update_svg()
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')

        def svg_set_path(self) -> None:
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            dst_file = self.svg_path

            if not os.path.exists(dst):
                os.makedirs(dst)

            File = qa_functions.File(self.svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.accent.color)
            File = qa_functions.File(dst_file)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        def update_svg(self) -> None:
            self.svg_set_path()
            self.img = get_svg(self.svg_path, self.theme.background.color, self.svg_size)
            self.svg_label.config(image=cast(str, self.img))

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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
                ThemeUpdateVars.BORDER_COLOR: self.theme.border_color,
                ThemeUpdateVars.TITLE_FONT_FACE: self.theme.title_font_face,
            }

        def run(self) -> None:
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title("Quizzing Application | Info")
            # self.root.resizable(False, True)
            self.root.focus_get()
            
            self.update_requests[gsuid('qa_prompts')] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

            self.svg_label.pack(side=tk.LEFT, pady=self.padY, padx=(self.padX, self.padX/8))
            self.svg_size = (50, 50)
            self.svg_label.config(justify=tk.CENTER, anchor=tk.CENTER, width=self.svg_size[0], height=self.svg_size[1])
            self.label_formatter(self.svg_label)

            self.title_label.config(text=cast(str, self.msg.title), justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX/8, self.padX), pady=self.padY, side=tk.RIGHT)

            self.title_frame.pack(fill=tk.X, expand=True)

            if self.msg.long:
                self.data_txt.delete(0.0, tk.END)
                self.data_txt.insert(0.0, self.msg.msg)
                self.data_txt.config(state=tk.DISABLED, width=15, height=8)
                self.data_txt.pack(fill=tk.BOTH, expand=True, padx=(self.padX, self.padX/4), pady=self.padY, side=tk.LEFT)
                self.data_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padX/4, self.padX), pady=self.padY, side=tk.RIGHT)
                self.label_formatter(self.data_txt, size=ThemeUpdateVars.FONT_SIZE_SMALL)
                self.update_requests[gsuid('qa_prompts')] = [self.data_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.data_frame.pack(fill=tk.BOTH, expand=True)
                self.data_txt['yscrollcommand'] = self.data_sc_bar.set
                self.data_sc_bar.config(command=self.data_txt.yview)

            else:
                self.data_label.config(text=self.msg.msg, justify=tk.LEFT, anchor=tk.W)
                self.data_label.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.label_formatter(self.data_label)

            self.close_button.config(text=self.msg.button_text)
            self.close_button.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, ipadx=self.padX, ipady=self.padY)

            self.label_formatter(self.title_label, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE if not self.msg.long else ThemeUpdateVars.FONT_SIZE_TITLE, padding=int(self.padX+self.svg_size[0]/2))
            self.button_formatter(self.close_button, True)

            self.update_ui()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    # Warning Prompt
    @staticmethod
    def show_warning(msg: InfoPacket, root: Union[tk.Tk, tk.Toplevel, None] = None, qoc: bool = False) -> None:
        try:
            if root is None:
                root = tk.Toplevel()
            MessagePrompts._CWarning(root, msg, qoc)

        except Exception as E:
            sys.stderr.write(f"Failed to use custom prompt: {E} {traceback.format_exc()}")
            messagebox.showwarning(msg.title, msg.msg)
            if qoc:
                sys.exit('show_warning fallback')

    class _CWarning(threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool) -> None:
            global TTK_THEME
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
            lwdw = 700 if 700 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [lwdw if self.msg.long else wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[qa_functions.HexColor, str, int, float]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.svg_size = (50, 50)
            self.appdata_svg_base = '.warning_svg'
            self.svg_src = ".src/.icons/.warning/base_icon.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}\\svg.svg".replace('/', '\\')
            self.img = None

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.warning.color, 'Prompts')

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.data_label = tk.Label(self.root)
            self.data_frame = tk.Frame(self.root)
            self.data_txt = tk.Text(self.data_frame, wrap=tk.WORD)
            self.data_sc_bar = ttk.Scrollbar(self.data_frame, style='MyPrompts.TScrollbar')
            self.close_button = tk.Button(self.root, command=self.close)

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            if self.qoc:
                sys.exit()
            else:
                self.thread.join(self, 0)
                self.root.after(0, self.root.quit)
                self.root.withdraw()
                self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.update_svg()
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.warning.color, 'Prompts')

        def svg_set_path(self) -> None:
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            dst_file = self.svg_path

            if not os.path.exists(dst):
                os.makedirs(dst)

            File = qa_functions.File(self.svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.warning.color)
            File = qa_functions.File(dst_file)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        def update_svg(self) -> None:
            self.svg_set_path()
            self.img = get_svg(self.svg_path, self.theme.background.color, self.svg_size)
            self.svg_label.config(image=cast(str, self.img))

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.WARNING]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.WARNING if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.WARNING]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title("Quizzing Application | Warning")
            # self.root.resizable(False, True)
            self.root.focus_get()

            self.update_requests[gsuid('qa_prompts')] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

            self.svg_label.pack(side=tk.LEFT, pady=self.padY, padx=(self.padX, self.padX / 8))
            self.svg_size = (50, 50)
            self.svg_label.config(justify=tk.CENTER, anchor=tk.CENTER, width=self.svg_size[0], height=self.svg_size[1])
            self.label_formatter(self.svg_label)

            self.title_label.config(text=cast(str, self.msg.title), justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)

            self.title_frame.pack(fill=tk.X, expand=True)

            if self.msg.long:
                self.data_txt.delete(0.0, tk.END)
                self.data_txt.insert(0.0, self.msg.msg)
                self.data_txt.config(state=tk.DISABLED, width=15, height=8)
                self.data_txt.pack(fill=tk.BOTH, expand=True, padx=(self.padX, self.padX / 4), pady=self.padY, side=tk.LEFT)
                self.data_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padX / 4, self.padX), pady=self.padY, side=tk.RIGHT)
                self.label_formatter(self.data_txt, size=ThemeUpdateVars.FONT_SIZE_SMALL)
                self.update_requests[gsuid('qa_prompts')] = [self.data_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.data_frame.pack(fill=tk.BOTH, expand=True)
                self.data_txt['yscrollcommand'] = self.data_sc_bar.set
                self.data_sc_bar.config(command=self.data_txt.yview)

            else:
                self.data_label.config(text=self.msg.msg, justify=tk.LEFT, anchor=tk.W)
                self.data_label.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.label_formatter(self.data_label)

            self.close_button.config(text=self.msg.button_text)
            self.close_button.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, ipadx=self.padX, ipady=self.padY)

            self.label_formatter(self.title_label, fg=ThemeUpdateVars.WARNING, size=ThemeUpdateVars.FONT_SIZE_LARGE if not self.msg.long else ThemeUpdateVars.FONT_SIZE_TITLE, padding=int(self.padX+self.svg_size[0]/2))
            self.button_formatter(self.close_button, True)

            self.update_ui()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    # Error Prompt
    @staticmethod
    def show_error(msg: InfoPacket, root: Union[tk.Tk, tk.Toplevel, None] = None, qoc: bool = False) -> None:
        try:
            if root is None:
                root = tk.Toplevel()
            MessagePrompts._CError(root, msg, qoc)
            return

        except Exception as E:
            sys.stderr.write(f"Failed to use custom prompt: {E} {traceback.format_exc()}")
            messagebox.showerror(msg.title, msg.msg)
            if qoc:
                sys.exit('show_error fallback')

    class _CError(threading.Thread):
        def __init__(self, root: Union[tk.Tk, tk.Toplevel], msg: InfoPacket, quit_on_close: bool) -> None:
            global TTK_THEME

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
            large_wd_w = 700 if 700 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [large_wd_w if self.msg.long else wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[qa_functions.HexColor, str, int, float]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.svg_size = (50, 50)
            self.appdata_svg_base = '.error_svg'
            self.svg_src = ".src/.icons/.error/base_icon.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}\\svg.svg".replace('/', '\\')
            self.img = None

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.error.color, 'Prompts')

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.data_label = tk.Label(self.root)
            self.data_frame = tk.Frame(self.root)
            self.data_txt = tk.Text(self.data_frame, wrap=tk.WORD)
            self.data_sc_bar = ttk.Scrollbar(self.data_frame, style='MyPrompts.TScrollbar')
            self.close_button = tk.Button(self.root, command=self.close)

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            if self.qoc:
                sys.exit()
            else:
                self.thread.join(self, 0)
                self.root.after(0, self.root.quit)
                self.root.withdraw()
                self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.update_svg()
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.error.color, 'Prompts')

        def svg_set_path(self) -> None:
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            dst_file = self.svg_path

            if not os.path.exists(dst):
                os.makedirs(dst)

            File = qa_functions.File(self.svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.error.color)
            File = qa_functions.File(dst_file)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        def update_svg(self) -> None:
            self.svg_set_path()
            self.img = get_svg(self.svg_path, self.theme.background.color, self.svg_size)
            self.svg_label.config(image=cast(str, self.img))

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ERROR]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ERROR if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ERROR]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.title("Quizzing Application | Error")
            # self.root.resizable(False, True)
            self.root.focus_get()

            self.update_requests[gsuid('qa_prompts')] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

            self.svg_label.pack(side=tk.LEFT, pady=self.padY, padx=(self.padX, self.padX / 8))
            self.svg_size = (50, 50)
            self.svg_label.config(justify=tk.CENTER, anchor=tk.CENTER, width=self.svg_size[0], height=self.svg_size[1])
            self.label_formatter(self.svg_label)

            self.title_label.config(text=cast(str, self.msg.title), justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)

            self.title_frame.pack(fill=tk.X, expand=True)

            if self.msg.long:
                self.data_txt.delete(0.0, tk.END)
                self.data_txt.insert(0.0, self.msg.msg)
                self.data_txt.config(state=tk.DISABLED, width=15, height=8)
                self.data_txt.pack(fill=tk.BOTH, expand=True, padx=(self.padX, self.padX / 4), pady=self.padY, side=tk.LEFT)
                self.data_sc_bar.pack(fill=tk.Y, expand=False, padx=(self.padX / 4, self.padX), pady=self.padY, side=tk.RIGHT)
                self.label_formatter(self.data_txt, size=ThemeUpdateVars.FONT_SIZE_SMALL)
                self.update_requests[gsuid('qa_prompts')] = [self.data_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.data_frame.pack(fill=tk.BOTH, expand=True)
                self.data_txt['yscrollcommand'] = self.data_sc_bar.set
                self.data_sc_bar.config(command=self.data_txt.yview)

            else:
                self.data_label.config(text=self.msg.msg, justify=tk.LEFT, anchor=tk.W)
                self.data_label.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.label_formatter(self.data_label)

            self.close_button.config(text=self.msg.button_text)
            self.close_button.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, ipadx=self.padX, ipady=self.padY)

            self.label_formatter(self.title_label, fg=ThemeUpdateVars.ERROR, size=ThemeUpdateVars.FONT_SIZE_LARGE if not self.msg.long else ThemeUpdateVars.FONT_SIZE_TITLE, padding=int(self.padX+self.svg_size[0]/2))
            self.button_formatter(self.close_button, True)

            self.update_ui()

        def __del__(self) -> None:
            self.thread.join(self, 0)


class InputPrompts:
    class DownloadFile(threading.Thread):
        def __init__(self, data: DownloadPacket, url: Union[None, str] = None) -> None:
            global TTK_THEME

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root = tk.Toplevel()
            self.data = data

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 2/3
            wd_w = 700 if 700 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}

            self.padX = 20
            self.padY = 10
            self.url = url
            self.download_queued = False

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.svg_size = (20, 20)
            self.appdata_svg_base = '.prog_svg'
            self.ok_svg_src = ".src/.icons/.progress/checkmark.svg"
            self.error_svg_src = ".src/.icons/.progress/exclamation.svg"
            self.blank_svg_src = ".src/.icons/.progress/blank.svg"
            self.title_svg_src = ".src/.icons/.misc/www.svg"
            self.svg_path = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup\\{self.appdata_svg_base}".replace('/', '\\')
            self.img_ok = None
            self.img_error = None
            self.img_blank = None
            self.title_img = None
            self.title_img_size = (50, 50)

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            self.page_input = tk.Frame(self.root)
            self.page_loading = tk.Frame(self.root)

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.svg_label = tk.Label(self.title_frame)
            self.msg_lbl = tk.Label(self.page_input)
            self.button_panel = tk.Frame(self.page_input)
            self.download_button = ttk.Button(self.button_panel, command=self.start_download)
            self.close_button = ttk.Button(self.button_panel, command=self.close)
            self.url_entry_frame = tk.Frame(self.page_input)
            self.url_entry_lbl = tk.Label(self.url_entry_frame)
            self.url_entry = ttk.Entry(self.url_entry_frame, style='My.TEntry')
            self.err_acc = 0
            self.error_label = tk.Label(self.root)

            self.downloading = False
            self.success = False
            self.loading_step1_m = tk.Frame(self.page_loading)
            self.loading_step1_L = tk.Label(self.loading_step1_m)
            self.loading_step1_I = tk.Label(self.loading_step1_m)

            self.loading_step2_m = tk.Frame(self.page_loading)
            self.loading_step2_L = tk.Label(self.loading_step2_m)
            self.loading_step2_I = tk.Label(self.loading_step2_m)

            self.loading_step3_m = tk.Frame(self.page_loading)
            self.loading_step3_L = tk.Label(self.loading_step3_m)
            self.loading_step3_I = tk.Label(self.loading_step3_m)

            self.loading_step4_m = tk.Frame(self.page_loading)
            self.loading_step4_L = tk.Label(self.loading_step4_m)
            self.loading_step4_I = tk.Label(self.loading_step4_m)

            self.ok_icon_reqs: List[tk.Label] = []
            self.error_icon_reqs: List[tk.Label] = []
            self.blank_icon_reqs: List[tk.Label] = [self.loading_step4_I, self.loading_step3_I, self.loading_step2_I, self.loading_step1_I]

            self.http = urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=1.0, read=1.5),
                retries=False
            )

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            if self.downloading:
                return

            self.root.after(0, self.root.quit)
            self.thread.join(self, 0)

            try:
                self.root.withdraw()
                self.root.title('Quizzing Application | Closed Prompt')
            except: pass

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(cargs[index], qa_functions.HexColor):
                        cargs[index] = cargs[index].color

                if command in self.theme_update_map:
                    sys.stderr.write(
                        "[WARNING] {}: Provided ThemeUpdateVars member instead of ThemeUpdateCommands member\n".format(element)
                    )
                    continue

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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.update_svg()
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme, self.theme.accent.color if not self.success else self.theme.okay.color)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            if self.download_queued:
                self.start_download()

            if self.success:
                self.title_label.config(fg=self.theme.okay.color)

        def svg_set_path(self) -> None:
            dst = os.path.join(qa_functions.App.appdata_dir, '.tmp/.icon_setup', self.appdata_svg_base).replace('\\', '/')
            ok_fn = self.ok_svg_src.split('\\')[-1]
            err_fn = self.error_svg_src.split('\\')[-1]
            bl_fn = self.blank_svg_src.split('\\')[-1]
            ttl_fn = self.title_svg_src.split('\\')[-1]
            dst_file_ok = f"{self.svg_path}\\{ok_fn}"
            dst_file_err = f"{self.svg_path}\\{err_fn}"
            dst_file_bl = f"{self.svg_path}\\{bl_fn}"
            dst_file_ttl = f"{self.svg_path}\\{ttl_fn}"

            if not os.path.exists(dst):
                os.makedirs(dst)

            # OK
            File = qa_functions.File(self.ok_svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.okay.color)
            File = qa_functions.File(dst_file_ok)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

            # Error
            File = qa_functions.File(self.error_svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.error.color)
            File = qa_functions.File(dst_file_err)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

            # Blank
            File = qa_functions.File(self.blank_svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.accent.color)
            File = qa_functions.File(dst_file_bl)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

            # Title
            File = qa_functions.File(self.title_svg_src)
            raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
            new_data = raw_data.replace(f"{_SVG_COLOR_REPL_ROOT}2", self.theme.foreground.color)
            new_data = new_data.replace(_SVG_COLOR_REPL_ROOT, self.theme.accent.color if not self.success else self.theme.okay.color)
            File = qa_functions.File(dst_file_ttl)
            qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

            del File

        def update_svg(self) -> None:
            self.svg_set_path()

            ok_fn = self.ok_svg_src.split('\\')[-1]
            err_fn = self.error_svg_src.split('\\')[-1]
            bl_fn = self.blank_svg_src.split('\\')[-1]
            ttl_fn = self.title_svg_src.split('\\')[-1]
            file_ok = f"{self.svg_path}\\{ok_fn}"
            file_err = f"{self.svg_path}\\{err_fn}"
            file_bl = f"{self.svg_path}\\{bl_fn}"
            file_ttl = f"{self.svg_path}\\{ttl_fn}"

            self.img_ok = get_svg(file_ok, self.theme.background.color, self.svg_size)
            self.img_error = get_svg(file_err, self.theme.background.color, self.svg_size)
            self.img_blank = get_svg(file_bl, self.theme.background.color, self.svg_size)
            self.title_img = get_svg(file_ttl, self.theme.background.color, self.title_img_size)

            for label in self.ok_icon_reqs:
                label.config(image=cast(str, self.img_ok))
            for label in self.error_icon_reqs:
                label.config(image=cast(str, self.img_error))
            for label in self.blank_icon_reqs:
                label.config(image=cast(str, self.img_blank))

            self.svg_label.config(image=cast(str, self.title_img))

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.title("Quizzing Application | URL Input")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.focus_get()
            self.update_requests[gsuid('qa_prompts')] = [self.root, TUC.BG, [TUV.BG]]

            self.title_frame.pack(fill=tk.X, expand=False)
            self.title_label.config(text=self.data.title, justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX/4, self.padX), pady=self.padY, side=tk.RIGHT)
            self.svg_label.pack(fill=tk.X, expand=False, padx=(self.padX, 0), pady=self.padY, side=tk.LEFT)

            self.button_panel.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
            self.close_button.config(text="Cancel")
            self.download_button.config(text="Download")
            self.loading_failed_button = ttk.Button(self.page_loading)
            self.close_button.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, self.padX/4))
            self.download_button.pack(fill=tk.X, expand=True, side=tk.RIGHT)

            self.error_label.config(text="")
            self.error_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY/2, side=tk.BOTTOM)

            self.url_entry_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, self.padY/2))
            self.url_entry.pack(fill=tk.X, expand=False, padx=self.padX, pady=(0, self.padY))
            self.url_entry_lbl.config(text="Enter URL:", anchor=tk.W, justify=tk.LEFT)

            self.url_entry_frame.pack(fill=tk.BOTH, expand=True)

            self.msg_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
            self.msg_lbl.config(
                text=("Warning: Only download files from sources that you trust." + (
                    f"\n{self.data.message}" if len(self.data.message) > 0 else ""
                ))
            )

            self.label_formatter(self.title_label, fg=TUV.ACCENT, size=TUV.FONT_SIZE_TITLE)
            self.label_formatter(self.svg_label)
            self.label_formatter(self.msg_lbl, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.url_entry_lbl, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.error_label, size=TUV.FONT_SIZE_SMALL, fg=TUV.ERROR)
            self.label_formatter(self.loading_step1_I, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step1_L, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step2_I, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step2_L, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step3_I, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step3_L, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step4_I, size=TUV.FONT_SIZE_MAIN)
            self.label_formatter(self.loading_step4_L, size=TUV.FONT_SIZE_MAIN)

            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.button_panel, TUC.BG, [TUV.BG]]

            self.update_requests[gsuid('qa_prompts')] = [self.loading_step1_m, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.loading_step2_m, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.loading_step3_m, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.loading_step4_m, TUC.BG, [TUV.BG]]

            self.update_requests[gsuid('qa_prompts')] = [self.page_input, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.page_loading, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.url_entry_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.url_entry, TUC.FONT, [TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_SMALL]]

            self.page_input.pack(fill=tk.BOTH, expand=True)

            if isinstance(self.url, str):
                self.url_entry.config(state=tk.DISABLED)
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, self.url.strip())
                self.download_queued = True

            self.update_requests[gsuid('qa_prompts')] = [self.url_entry, TUC.FONT, [TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_MAIN]]

            self.update_ui()

        def start_download(self) -> bool:
            self.download_queued = False

            if self.downloading:
                return False

            self.close_button.config(state=tk.DISABLED)
            self.download_button.config(state=tk.DISABLED)
            self.url_entry.config(state=tk.DISABLED)

            raw = self.url_entry.get().strip() if not isinstance(self.url, str) else self.url.strip()
            urls = check_url_regex(raw)
            if len(urls) != 1:
                sys.stderr.write(f'{raw},\n\t{urls}\n')
                self.err_acc += 1
                self.error_label.config(text=f"Invalid URL provided ({self.err_acc})")
                self.close_button.config(state=tk.NORMAL)
                self.url_entry.config(state=tk.NORMAL)
                self.download_button.config(state=tk.NORMAL)
                return False

            self.error_label.config(text="")
            self.downloading = True
            self.page_input.pack_forget()
            self.page_loading.pack(fill=tk.BOTH, expand=True)

            self.load_file()
            if not self.success and os.path.isfile(self.data.output_file):
                os.remove(self.data.output_file)

            return self.success and os.path.isfile(self.data.output_file)

        def load_file(self) -> None:
            def tr(com: Any, *args: Optional[Any]) -> Tuple[bool, Any]:
                try:
                    return True, com(*args)
                except Exception as E:
                    log(LoggingLevel.ERROR, traceback.format_exc())
                    return False, str(E)

            url = self.url_entry.get().strip() if not isinstance(self.url, str) else self.url.strip()

            self.title_label.config(text="Downloading File")
            self.loading_step1_m.pack(fill=tk.BOTH, expand=False)
            self.loading_step2_m.pack(fill=tk.BOTH, expand=False)
            self.loading_step3_m.pack(fill=tk.BOTH, expand=False)
            self.loading_step4_m.pack(fill=tk.BOTH, expand=False)

            self.loading_step1_I.pack(fill=tk.X, expand=False, side=tk.LEFT, padx=(self.padX, self.padX/2), pady=self.padY/2)
            self.loading_step2_I.pack(fill=tk.X, expand=False, side=tk.LEFT, padx=(self.padX, self.padX/2), pady=self.padY/2)
            self.loading_step3_I.pack(fill=tk.X, expand=False, side=tk.LEFT, padx=(self.padX, self.padX/2), pady=self.padY/2)
            self.loading_step4_I.pack(fill=tk.X, expand=False, side=tk.LEFT, padx=(self.padX, self.padX/2), pady=self.padY/2)

            self.loading_step1_L.pack(fill=tk.X, expand=True, side=tk.RIGHT, padx=(0, self.padX), pady=self.padY/2)
            self.loading_step2_L.pack(fill=tk.X, expand=True, side=tk.RIGHT, padx=(0, self.padX), pady=self.padY/2)
            self.loading_step3_L.pack(fill=tk.X, expand=True, side=tk.RIGHT, padx=(0, self.padX), pady=self.padY/2)
            self.loading_step4_L.pack(fill=tk.X, expand=True, side=tk.RIGHT, padx=(0, self.padX), pady=self.padY/2)

            self.loading_step1_L.config(text="Requesting File", justify=tk.LEFT, anchor=tk.W)
            self.loading_step2_L.config(text="Reading Data", justify=tk.LEFT, anchor=tk.W)
            self.loading_step3_L.config(text="Saving Data", justify=tk.LEFT, anchor=tk.W)
            self.loading_step4_L.config(text="Verifying Data", justify=tk.LEFT, anchor=tk.W)

            self.loading_failed_button.config(text="EXIT", state=tk.DISABLED, command=self.exit_download)
            self.loading_failed_button.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)

            self.root.update()
            self.update_svg()
            if self.loading_step1_I in self.blank_icon_reqs:
                self.blank_icon_reqs.pop(self.blank_icon_reqs.index(self.loading_step1_I))

            # Request
            p, r = tr(self.http.request, 'GET', url)
            if not p:
                sys.stderr.write(f"{r}\n")
                self.error_label.config(text='Server did not respond')
                self.loading_failed_button.config(state=tk.NORMAL)
                self.title_label.config(text='Download Failed')
                self.error_icon_reqs.append(self.loading_step1_I)
                self.update_svg()
                return

            self.ok_icon_reqs.append(self.loading_step1_I)
            self.update_svg()
            if self.loading_step2_I in self.blank_icon_reqs:
                self.blank_icon_reqs.pop(self.blank_icon_reqs.index(self.loading_step2_I))
            p, r2 = tr(r.data.decode)
            p &= isinstance(r2, str)
            if p:
                p &= 100000 >= len(r2) > 0
                r2 = r2.strip()

            if not p:
                sys.stderr.write(f"{r2}\n")
                self.error_label.config(text='Received invalid data')
                self.loading_failed_button.config(state=tk.NORMAL)
                self.title_label.config(text='Download Failed')
                self.error_icon_reqs.append(self.loading_step2_I)
                self.update_svg()
                return

            self.ok_icon_reqs.append(self.loading_step2_I)
            self.update_svg()

            if self.loading_step3_I in self.blank_icon_reqs:
                self.blank_icon_reqs.pop(self.blank_icon_reqs.index(self.loading_step3_I))
            p, r3 = tr(qa_functions.File, self.data.output_file)
            if p:
                p, r3 = tr(qa_functions.SaveFile.secure, r3, r2, qa_functions.SaveFunctionArgs(False, save_data_type=bytes))
                if isinstance(r3, bool):
                    p &= r3

            if not p:
                sys.stderr.write(f"{r3}\n")
                self.error_label.config(text='Failed to save data')
                self.loading_failed_button.config(state=tk.NORMAL)
                self.title_label.config(text='Download Failed')
                self.error_icon_reqs.append(self.loading_step3_I)
                self.update_svg()
                return

            self.ok_icon_reqs.append(self.loading_step3_I)
            self.update_svg()
            if self.loading_step4_I in self.blank_icon_reqs:
                self.blank_icon_reqs.pop(self.blank_icon_reqs.index(self.loading_step4_I))
            ogh = hashlib.sha3_512(r2.encode()).hexdigest()
            p, file = tr(qa_functions.File, self.data.output_file)
            nfh = None
            if p:
                p, rw = tr(qa_functions.OpenFile.load_file, file, qa_functions.OpenFunctionArgs())
                if p:
                    p, nfh = tr(hashlib.sha3_512, rw.strip())

            if not p or nfh is None:
                self.error_label.config(text='Failed to verify data (0)')
                self.loading_failed_button.config(state=tk.NORMAL)
                self.title_label.config(text='Download Failed')
                self.error_icon_reqs.append(self.loading_step4_I)
                self.update_svg()
                return

            if nfh.hexdigest() != ogh:
                sys.stderr.write(f"{nfh.hexdigest()}\n\t!=\n{ogh}\n")
                self.error_label.config(text='Failed to verify data (1)')
                self.loading_failed_button.config(state=tk.NORMAL)
                self.title_label.config(text='Download Failed')
                self.error_icon_reqs.append(self.loading_step4_I)
                self.update_svg()
                return

            self.ok_icon_reqs.append(self.loading_step4_I)
            self.update_svg()
            self.title_label.config(text="Successfully Downloaded File")
            self.loading_failed_button.config(text="DONE", state=tk.NORMAL)
            self.downloading = False
            self.success = True
            self.error_label.config(text="")
            self.update_ui()
            self.root.update()
            if isinstance(self.url, str):
                self.exit_download()
            else:
                return

        def exit_download(self) -> None:
            self.downloading = False
            self.close()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    class OptionPrompt(threading.Thread):
        def __init__(self, s_mem: qa_functions.SMem, options: Set[str], title: str, msg: str = "") -> None:
            global TTK_THEME

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root = tk.Toplevel()
            self.s_mem = s_mem
            self.msg = msg
            self.title = title

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 2 / 3
            wd_w = 500 if 500 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.msg_lbl = tk.Label(self.root)
            self.button_panel = tk.Frame(self.root)
            self.select_button = ttk.Button(self.button_panel, command=self.select)
            self.close_button = ttk.Button(self.button_panel, command=self.close)
            self.error_label = tk.Label(self.root)

            self.drpd_var = tk.StringVar()
            self.def_val = "<Select>"
            self.drpd_var.set(self.def_val)
            self.options = [*options]
            self.dropdown = ttk.OptionMenu(self.root, self.drpd_var, self.def_val, *self.options)

            self.err_acc = 0

            self.head_label = tk.Label(self.root)

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            self.thread.join(self, 0)
            self.root.after(0, self.root.quit)
            self.root.withdraw()
            self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            global DEBUG_NORM

            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(cargs[index], qa_functions.HexColor):
                        cargs[index] = cargs[index].color

                if command in self.theme_update_map:
                    sys.stderr.write(
                        "[WARNING] {}: Provided ThemeUpdateVars member instead of ThemeUpdateCommands member\n".format(element)
                    )
                    continue

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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

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

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.title("Quizzing Application | Options")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.focus_get()
            self.update_requests[gsuid('qa_prompts')] = [self.root, TUC.BG, [TUV.BG]]

            self.title_frame.pack(fill=tk.X, expand=False)
            self.title_label.config(text="Select an Item", justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

            self.button_panel.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
            self.close_button.config(text="Cancel", command=self.exit)
            self.select_button.config(text="Confirm", command=self.select)
            self.close_button.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, self.padX / 4))
            self.select_button.pack(fill=tk.X, expand=True, side=tk.RIGHT)

            self.error_label.config(text="")
            self.error_label.pack(fill=tk.X, padx=self.padX, pady=0, expand=False, side=tk.BOTTOM)

            self.head_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, self.padY/4))
            self.dropdown.pack(fill=tk.X, expand=False, padx=self.padX)
            self.head_label.config(text=self.title, justify=tk.LEFT, anchor=tk.W)

            self.msg_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
            self.msg_lbl.config(text=self.msg)

            self.label_formatter(self.title_label, fg=TUV.ACCENT, size=TUV.FONT_SIZE_TITLE)
            self.label_formatter(self.msg_lbl, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.head_label, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.error_label, fg=TUV.ERROR, size=TUV.FONT_SIZE_SMALL)

            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.button_panel, TUC.BG, [TUV.BG]]

            self.update_ui()

        def select(self) -> None:
            self.select_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.DISABLED)
            self.dropdown.config(state=tk.DISABLED)

            if self.drpd_var.get().strip() == self.def_val.strip():
                self.err_acc += 1
                self.error_label.config(text=f"Please select an item ({self.err_acc})")
                self.select_button.config(state=tk.NORMAL)
                self.close_button.config(state=tk.NORMAL)
                self.dropdown.config(state=tk.NORMAL)
                return

            self.error_label.config(text="")

            self.s_mem.set(self.drpd_var.get())
            self.close()

        def exit(self) -> None:
            self.s_mem.set(str(0))
            self.close()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    class DEntryPrompt(threading.Thread):
        def __init__(self, s_mem: qa_functions.SMem, ans_sep: str, labels_text: List[str]) -> None:
            global TTK_THEME

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root = tk.Toplevel()
            self.s_mem = s_mem
            self.ans_sep = ans_sep
            self.labels = labels_text

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 2 / 3
            wd_w = 500 if 500 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.lbl1 = tk.Label(self.root)
            self.lbl2 = tk.Label(self.root)
            self.button_panel = tk.Frame(self.root)
            self.select_button = ttk.Button(self.button_panel, command=self.select)
            self.close_button = ttk.Button(self.button_panel, command=self.close)
            self.error_label = tk.Label(self.root)

            self.entry1 = ttk.Entry(self.root, style='My.TEntry')
            self.entry2 = ttk.Entry(self.root, style='My.TEntry')

            self.err_acc = 0

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            self.thread.join(self, 0)
            self.root.after(0, self.root.quit)
            self.root.withdraw()
            self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(cargs[index], qa_functions.HexColor):
                        cargs[index] = cargs[index].color

                if command in self.theme_update_map:
                    sys.stderr.write(
                        "[WARNING] {}: Provided ThemeUpdateVars member instead of ThemeUpdateCommands member\n".format(element)
                    )
                    continue

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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

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

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.title("Quizzing Application | Prompt")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.focus_get()
            self.update_requests[gsuid('qa_prompts')] = [self.root, TUC.BG, [TUV.BG]]

            self.title_frame.pack(fill=tk.X, expand=False)
            self.title_label.config(text="Information Required", justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

            self.button_panel.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
            self.close_button.config(text="Cancel", command=self.exit)
            self.select_button.config(text="Confirm", command=self.select)
            self.close_button.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, self.padX / 4))
            self.select_button.pack(fill=tk.X, expand=True, side=tk.RIGHT)

            self.error_label.config(text="")
            self.error_label.pack(fill=tk.X, padx=self.padX, pady=0, expand=False, side=tk.BOTTOM)

            self.lbl1.config(text=self.labels[0], justify=tk.LEFT, anchor=tk.W)
            self.lbl1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

            self.entry1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))
            self.entry1.delete(0, tk.END)

            self.lbl2.config(text=self.labels[1], justify=tk.LEFT, anchor=tk.W)
            self.lbl2.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

            self.entry2.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY / 4, self.padY))
            self.entry2.delete(0, tk.END)

            self.label_formatter(self.title_label, fg=TUV.ACCENT, size=TUV.FONT_SIZE_TITLE)
            self.label_formatter(self.lbl1, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.lbl2, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.error_label, fg=TUV.ERROR, size=TUV.FONT_SIZE_SMALL)

            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.button_panel, TUC.BG, [TUV.BG]]

            self.update_requests[gsuid('qa_prompts')] = [self.entry1, TUC.FONT, [TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_MAIN]]
            self.update_requests[gsuid('qa_prompts')] = [self.entry2, TUC.FONT, [TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_MAIN]]

            self.update_ui()

        def select(self) -> None:
            self.select_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.DISABLED)
            self.entry1.config(state=tk.DISABLED)
            self.entry2.config(state=tk.DISABLED)

            if "" in (self.entry1.get().strip(), self.entry2.get().strip()):
                self.err_acc += 1
                self.error_label.config(text=f"Please fill out all of the information ({self.err_acc})")
                self.select_button.config(state=tk.NORMAL)
                self.close_button.config(state=tk.NORMAL)
                self.entry1.config(state=tk.DISABLED)
                self.entry2.config(state=tk.DISABLED)
                return

            self.error_label.config(text="")

            self.s_mem.set(f"{self.entry1.get().strip()}{self.ans_sep}{self.entry2.get().strip()}")
            self.close()

        def exit(self) -> None:
            self.s_mem.set(str(0))
            self.close()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    class SEntryPrompt(threading.Thread):
        def __init__(self, s_mem: qa_functions.SMem, label_text: str, default: str) -> None:
            global TTK_THEME

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root = tk.Toplevel()
            self.s_mem = s_mem
            self.label = label_text
            self.default = default

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 2 / 3
            wd_w = 500 if 500 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.lbl1 = tk.Label(self.root)
            self.button_panel = tk.Frame(self.root)
            self.select_button = ttk.Button(self.button_panel, command=self.select)
            self.close_button = ttk.Button(self.button_panel, command=self.close)
            self.error_label = tk.Label(self.root)

            self.entry1 = ttk.Entry(self.root, style='My.TEntry')

            self.err_acc = 0

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            self.thread.join(self, 0)
            self.root.after(0, self.root.quit)
            self.root.withdraw()
            self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(cargs[index], qa_functions.HexColor):
                        cargs[index] = cargs[index].color

                if command in self.theme_update_map:
                    sys.stderr.write(
                        "[WARNING] {}: Provided ThemeUpdateVars member instead of ThemeUpdateCommands member\n".format(element)
                    )
                    continue

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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

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

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.title("Quizzing Application | Prompt")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.focus_get()
            self.update_requests[gsuid('qa_prompts')] = [self.root, TUC.BG, [TUV.BG]]

            self.title_frame.pack(fill=tk.X, expand=False)
            self.title_label.config(text="Information Required", justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

            self.button_panel.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
            self.close_button.config(text="Cancel", command=self.exit)
            self.select_button.config(text="Confirm", command=self.select)
            self.close_button.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, self.padX / 4))
            self.select_button.pack(fill=tk.X, expand=True, side=tk.RIGHT)

            self.error_label.config(text="")
            self.error_label.pack(fill=tk.X, padx=self.padX, pady=0, expand=False, side=tk.BOTTOM)

            self.lbl1.config(text=self.label, justify=tk.LEFT, anchor=tk.W)
            self.lbl1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

            self.entry1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))
            self.entry1.delete(0, tk.END)
            self.entry1.insert(0, self.default)

            self.label_formatter(self.title_label, fg=TUV.ACCENT, size=TUV.FONT_SIZE_TITLE)
            self.label_formatter(self.lbl1, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.error_label, fg=TUV.ERROR, size=TUV.FONT_SIZE_SMALL)

            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.button_panel, TUC.BG, [TUV.BG]]

            self.update_requests[gsuid('qa_prompts')] = [self.entry1, TUC.FONT, [TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_MAIN]]

            self.update_ui()

        def select(self) -> None:
            self.select_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.DISABLED)
            self.entry1.config(state=tk.DISABLED)

            if "" == self.entry1.get().strip():
                self.err_acc += 1
                self.error_label.config(text=f"Please fill out all of the information ({self.err_acc})")
                self.select_button.config(state=tk.NORMAL)
                self.close_button.config(state=tk.NORMAL)
                self.entry1.config(state=tk.NORMAL)
                return

            self.error_label.config(text="")

            self.s_mem.set(self.entry1.get().strip())
            self.close()

        def exit(self) -> None:
            self.s_mem.set(self.default)
            self.close()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    class ButtonPrompt(threading.Thread):
        def __init__(self, s_mem: qa_functions.SMem, title: str, *buttons: Tuple[str, str], default: str = '<default>', message: str = "") -> None:
            global TTK_THEME
            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            self.root = tk.Toplevel()
            self.s_mem = s_mem
            self.buttons = buttons
            self.message = message
            self.default = default
            self.title = title

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 2 / 3
            wd_w = 500 if 500 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.lbl1 = tk.Label(self.root)
            self.button_panel = tk.Frame(self.root)
            self.close_button = ttk.Button(self.button_panel, command=self.close)
            self.error_label = tk.Label(self.root)

            self.err_acc = 0

            self.button_dict: Dict[str, List[Union[tk.Button, ttk.Button, str]]] = {}

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            self.thread.join(self, 0)
            self.root.after(0, self.root.quit)
            self.root.withdraw()
            self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            global DEBUG_NORM

            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(cargs[index], qa_functions.HexColor):
                        cargs[index] = cargs[index].color

                if command in self.theme_update_map:
                    sys.stderr.write(
                        "[WARNING] {}: Provided ThemeUpdateVars member instead of ThemeUpdateCommands member\n".format(element)
                    )
                    continue

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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

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

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.title("Quizzing Application | Options")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.focus_get()
            self.update_requests[gsuid('qa_prompts')] = [self.root, TUC.BG, [TUV.BG]]

            self.title_frame.pack(fill=tk.X, expand=False)
            self.title_label.config(text=self.title, justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

            self.button_panel.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
            self.close_button.config(text="Cancel", command=self.exit)
            self.close_button.pack(fill=tk.X, expand=True, side=tk.RIGHT, padx=(0, self.padX / 4))

            self.error_label.config(text="")
            self.error_label.pack(fill=tk.X, padx=self.padX, pady=0, expand=False, side=tk.BOTTOM)

            self.lbl1.config(text=self.message, justify=tk.LEFT, anchor=tk.W)
            self.lbl1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

            self.label_formatter(self.title_label, fg=TUV.ACCENT, size=TUV.FONT_SIZE_TITLE)
            self.label_formatter(self.lbl1, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.error_label, fg=TUV.ERROR, size=TUV.FONT_SIZE_SMALL)

            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.button_panel, TUC.BG, [TUV.BG]]

            for text, code in cast(Iterable[Tuple[str, str]], self.buttons):
                uid = gsuid('qa_prompts')
                btn = ttk.Button(self.button_panel, text=text)
                btn.pack(side=tk.LEFT)

                self.conf(btn, uid, code)

            self.update_ui()

        def conf(self, btn: Union[ttk.Button, tk.Button], uid: str, code: str) -> None:
            self.button_dict[uid] = [btn, code]
            btn.config(command=lambda: self.clicked(uid))

        def clicked(self, uid: str) -> None:
            self.close_button.config(state=tk.DISABLED)
            for btn in self.button_dict.values():
                cast(tk.Button, btn[0]).config(state=tk.DISABLED)

            self.s_mem.set(cast(str, self.button_dict[uid][1]))
            self.close()

        def exit(self) -> None:
            self.s_mem.set(self.default)
            self.close()

        def __del__(self) -> None:
            self.thread.join(self, 0)

    class MCInp(threading.Thread):
        def __init__(self, s_mem: qa_functions.SMem, label_text: str, default: Union[None, str] = None, is_correct: bool = False) -> None:
            global TTK_THEME

            super().__init__()
            self.thread = threading.Thread
            self.thread.__init__(self)

            assert isinstance(s_mem, qa_functions.SMem)
            assert isinstance(label_text, str)

            self.root = tk.Toplevel()
            self.s_mem = s_mem
            self.label = label_text
            self.default: str = default if isinstance(default, str) else self.s_mem.NullStr

            self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
            ratio = 2 / 3
            wd_w = 500 if 500 <= self.screen_dim[0] else self.screen_dim[0]
            self.window_size = [wd_w, int(ratio * wd_w)]
            self.screen_pos = [
                int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
                int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
            ]

            self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}

            self.padX = 20
            self.padY = 10

            self.load_theme()
            self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
            ] = {}

            self.ttk_style = ttk.Style()
            self.ttk_style.theme_use(TTK_THEME)
            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

            self.title_frame = tk.Frame(self.root)
            self.title_label = tk.Label(self.title_frame)
            self.lbl1 = tk.Label(self.root)
            self.button_panel = tk.Frame(self.root)
            self.select_button = ttk.Button(self.button_panel, command=self.select)
            self.close_button = ttk.Button(self.button_panel, command=self.close)
            self.error_label = tk.Label(self.root)

            self.cVar = tk.IntVar()
            self.cVar.set(int(is_correct))
            self.is_correct = tk.Checkbutton(self.root, text='This is a correct answer', var=self.cVar)  # type: ignore

            self.entry1 = ttk.Entry(self.root, style='My.TEntry')

            self.err_acc = 0

            self.start()
            self.root.mainloop()

        def close(self) -> None:
            self.thread.join(self, 0)
            self.root.after(0, self.root.quit)
            self.root.withdraw()
            self.root.title('Quizzing Application | Closed Prompt')

        def update_ui(self) -> None:
            self.load_theme()

            def tr(com: Callable[[], Any]) -> Tuple[bool, str]:
                try:
                    com()
                    return True, '<no errors>'
                except Exception as E:
                    log(LoggingLevel.DEVELOPER, traceback.format_exc())
                    return False, str(E)

            def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
                log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

            def log_norm(com: str, el: tk.Widget) -> None:
                log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

            for elID, (_e, _c, _a) in self.update_requests.items():
                element = cast(tk.Button, _e)
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False, '', -1]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(cargs[index], qa_functions.HexColor):
                        cargs[index] = cargs[index].color

                if command in self.theme_update_map:
                    sys.stderr.write(
                        "[WARNING] {}: Provided ThemeUpdateVars member instead of ThemeUpdateCommands member\n".format(element)
                    )
                    continue

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
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cargs[0]))
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
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cargs

            self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Prompts')
            self.ttk_style = configure_button_style(self.ttk_style, self.theme)
            self.ttk_style = configure_entry_style(self.ttk_style, self.theme)

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

        def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FG, [ThemeUpdateVars.FG if not accent else ThemeUpdateVars.BG]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_BG, [ThemeUpdateVars.ACCENT if not accent else ThemeUpdateVars.BG]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.ACTIVE_FG, [ThemeUpdateVars.BG if not accent else ThemeUpdateVars.ACCENT]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def label_formatter(self, label: tk.Widget, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None) -> None:
            if padding is None:
                padding = self.padX

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.BG, [bg]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FG, [fg]]

            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.FONT, [font, size]]
            self.update_requests[gsuid('qa_prompts')] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        def load_theme(self) -> None:
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

        def run(self) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
            self.root.title("Quizzing Application | Prompt")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            self.root.focus_get()
            self.update_requests[gsuid('qa_prompts')] = [self.root, TUC.BG, [TUV.BG]]

            self.title_frame.pack(fill=tk.X, expand=False)
            self.title_label.config(text="Information Required", justify=tk.LEFT, anchor=tk.W)
            self.title_label.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

            self.button_panel.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
            self.close_button.config(text="Cancel", command=self.exit)
            self.select_button.config(text="Confirm", command=self.select)
            self.close_button.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, self.padX / 4))
            self.select_button.pack(fill=tk.X, expand=True, side=tk.RIGHT)

            self.error_label.config(text="")
            self.error_label.pack(fill=tk.X, padx=self.padX, pady=0, expand=False, side=tk.BOTTOM)

            self.lbl1.config(text=self.label, justify=tk.LEFT, anchor=tk.W)
            self.lbl1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

            self.entry1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))
            self.entry1.delete(0, tk.END)
            if self.default != self.s_mem.NullStr:
                self.entry1.insert(0, self.default)

            self.is_correct.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)

            self.label_formatter(self.title_label, fg=TUV.ACCENT, size=TUV.FONT_SIZE_TITLE)
            self.label_formatter(self.lbl1, fg=TUV.GRAY, size=TUV.FONT_SIZE_SMALL)
            self.label_formatter(self.error_label, fg=TUV.ERROR, size=TUV.FONT_SIZE_SMALL)

            self.update_requests[gsuid('qa_prompts')] = [self.title_frame, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.button_panel, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid('qa_prompts')] = [self.entry1, TUC.FONT, [TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_MAIN]]

            self._onClk(False)
            self.update_ui()

        def _onClk(self, up: bool = True) -> None:
            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            self.update_requests['is_correct<tk::CheckButton>'] = [
                None,
                TUC.CUSTOM,
                [
                    lambda *args: self.is_correct.config(
                        activebackground=args[0], activeforeground=args[1],
                        bg=args[2], bd=(args[3] if args[3] > 0 else 1),
                        font=(args[4], args[5]), highlightthickness=args[3],
                        highlightcolor=args[6], selectcolor=args[7], state=tk.NORMAL,
                        anchor=tk.W, command=self._onClk, fg=args[8]
                    ),
                    TUV.ACCENT, TUV.BG, TUV.BG, TUV.BORDER_SIZE, TUV.DEFAULT_FONT_FACE,
                    TUV.FONT_SIZE_SMALL, TUV.BORDER_COLOR, TUV.ACCENT if self.cVar.get() != 0 else TUV.BG,
                    TUV.FG
                ]
            ]

            if up:
                self.update_ui()

        def select(self) -> None:
            self.select_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.DISABLED)
            self.entry1.config(state=tk.DISABLED)

            if "" == self.entry1.get().strip():
                self.err_acc += 1
                self.error_label.config(text=f"Please fill out all of the information ({self.err_acc})")
                self.select_button.config(state=tk.NORMAL)
                self.close_button.config(state=tk.NORMAL)
                self.entry1.config(state=tk.NORMAL)
                return

            self.error_label.config(text="")

            self.s_mem.set(f"{self.cVar.get()}{self.entry1.get().strip()}")
            self.close()

        def exit(self) -> None:
            self.s_mem.set(self.default)
            self.close()

        def __del__(self) -> None:
            self.thread.join(self, 0)


def get_svg(svg_file: str, bg: str, size: Union[Tuple[int, int], None] = None) -> ImageTk.PhotoImage:
    if isinstance(bg, str):
        background = int(bg.replace("#", '0x'), 0)
    else:
        background = bg

    drawing = svg2rlg(svg_file)
    bytes_png = BytesIO()
    renderPM.drawToFile(drawing, bytes_png, fmt="PNG", bg=background)
    img = Image.open(bytes_png)
    if size is not None:
        img = img.resize(size, PIL.Image.ANTIALIAS)

    p_img = ImageTk.PhotoImage(img)

    return p_img


def check_url_regex(url: str) -> List[str]:
    # yes, I copied the regex.
    # no, i don't have any regrets.

    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    urls = re.findall(regex, url)
    return [x[0] for x in urls]


def gsuid(arg1: str = 'elForm') -> str:
    return qa_functions.gen_short_uid(arg1)


def log(level: LoggingLevel, data: str) -> None:
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME, DEBUG_NORM, DEBUG_DEV_FLAG
    assert isinstance(data, str)

    if level == LoggingLevel.ERROR:
        data = f'{ANSI.FG_BRIGHT_RED}{ANSI.BOLD}[{level.name.upper()}] {"[SAVED] " if LOGGER_AVAIL else ""}{data}{ANSI.RESET}\n'
    elif level == LoggingLevel.SUCCESS:
        data = f'{ANSI.FG_BRIGHT_GREEN}{ANSI.BOLD}[{level.name.upper()}] {"[SAVED] " if LOGGER_AVAIL else ""}{data}{ANSI.RESET}\n'
    elif level == LoggingLevel.WARNING:
        data = f'{ANSI.FG_BRIGHT_YELLOW}[{level.name.upper()}] {"[SAVED] " if LOGGER_AVAIL else ""}{data}{ANSI.RESET}\n'
    elif level == LoggingLevel.DEVELOPER:
        data = f'{ANSI.FG_BRIGHT_BLUE}{ANSI.BOLD}[{level.name.upper()}]{ANSI.RESET} {"[SAVED] " if LOGGER_AVAIL else ""}{data}\n'
    elif level == LoggingLevel.DEBUG:
        data = f'{ANSI.FG_BRIGHT_MAGENTA}[{level.name.upper()}]{ANSI.RESET} {"[SAVED] " if LOGGER_AVAIL else ""}{data}\n'
    else:
        data = f'[{level.name.upper()}] {"[SAVED] " if LOGGER_AVAIL else ""}{data}\n'

    data = f"{AppLogColors.QA_PROMPTS}{AppLogColors.EXTRA}[PROMPT]{ANSI.RESET} {data}"

    if level == LoggingLevel.DEBUG and not DEBUG_NORM:
        return
    elif level == LoggingLevel.DEVELOPER and (not (qa_functions.App.DEV_MODE and DEBUG_DEV_FLAG) or not DEBUG_NORM):
        return

    if level == LoggingLevel.ERROR:
        sys.stderr.write(data)
    else:
        sys.stdout.write(data)

    if LOGGER_AVAIL:
        LOGGER_FUNC([qa_functions.LoggingPackage(
            level, data,
            LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
        )])

