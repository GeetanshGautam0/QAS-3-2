import sys, qa_functions, os, PIL, subprocess, tkinter as tk, random, traceback
from . import qa_prompts
from .qa_prompts import gsuid, configure_scrollbar_style
from qa_functions.qa_enum import ThemeUpdateCommands, ThemeUpdateVars, LoggingLevel
from qa_functions.qa_std import ANSI, AppLogColors
from qa_functions.qa_custom import HexColor
from threading import Thread
from tkinter import ttk
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from ctypes import windll
from typing import *


AUTO = 3
script_name = "APP_QF"
APP_TITLE = "Quizzing Application | Quizzing Form"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
DEBUG_DEV_FLAG = False


class _UI(Thread):
    def __init__(self, root: Union[tk.Toplevel, tk.Tk], ic: Any, ds: Any, **kwargs: Optional[Any]) -> None:
        super().__init__()
        Thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs
        self.root.withdraw()

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        wd_w = 1000 if 1000 <= self.screen_dim[0] else self.screen_dim[0]
        wd_h = 550 if 550 <= self.screen_dim[1] else self.screen_dim[1]
        self.window_size = [wd_w, wd_h]
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
        ]

        self.theme: qa_functions.qa_custom.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]] = {}  # type: ignore

        self.padX = 20
        self.padY = 10

        self.gi_cl = True
        self._job: Union[None, str] = None

        self.inputs: List[Union[tk.Button, ttk.Button, ttk.Entry, tk.Entry, tk.Text]] = []

        self.load_theme()
        self.update_requests: Dict[str, List[Any]] = {}  # type: ignore
        self.late_update_requests: Dict[tk.Widget, List[Any]] = {}  # type: ignore
        self.data: Dict[Any, Any] = {}  # type: ignore

        self.img_path = qa_functions.Files.QF_png
        self.img_size = (75, 75)
        self.svgs: Dict[str, Any] = {
            'arrow_left': {'accent': '', 'normal': ''},
            'arrow_right': {'accent': '', 'normal': ''},
            'settings_cog': {'accent': '', 'normal': ''},
            'question': {'accent': '', 'normal': ''},
            'checkmark': {'accent': '', 'normal': ''},
            'export': {'accent': '', 'normal': ''},
            'arrow_left_large': {'accent': '', 'normal': ''},
            'arrow_right_large': {'accent': '', 'normal': ''},
            'settings_cog_large': {'accent': '', 'normal': ''},
            'question_large': {'accent': '', 'normal': ''},
            'checkmark_large': {'accent': '', 'normal': ''},
            'export_large': {'accent': '', 'normal': ''},

            'qf': ''
        }
        self.checkmark_src = "./.src/.icons/.progress/checkmark.svg"
        self.cog_src = './.src/.icons/.misc/settings.svg'
        self.arrow_left_src = './.src/.icons/.misc/left_arrow.svg'
        self.question_src = './.src/.icons/.misc/question.svg'
        self.arrow_right_src = './.src/.icons/.misc/right_arrow.svg'
        self.export_src = './.src/.icons/.misc/export.svg'
        self.svg_tmp = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup".replace('/', '\\')
        self.load_png()

        self.ttk_theme = cast(str, self.kwargs['ttk_theme'])
        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'QF')
        self.ttk_style = qa_functions.TTKTheme.configure_button_style(self.ttk_style, self.theme, self.theme.accent.color)
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size, 'My')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')
           
        self.title = tk.Label(self.root)

        self.screen_data: Dict[int, Dict[Any, Any]] = {}
        [self.LOGIN_PAGE, self.CONFIGURATION_PAGE, self.SUMMARY_PAGE] = range(3)
        for i in range(3): self.screen_data[i] = {}
        self.current_page = self.LOGIN_PAGE

        self.login_frame = tk.Frame(self.root)
        self.config_frame = tk.Frame(self.root)
        self.summary_frame = tk.Frame(self.root)

        self.LF_file_frame = tk.Frame(self.login_frame)
        self.LF_file_ttl = tk.Label(self.LF_file_frame)
        self.LF_file_select = ttk.Button(self.LF_file_frame, style='Active.TButton')
        self.LF_file_info = tk.Label(self.LF_file_frame)
        
        self.LF_fields = tk.Frame(self.login_frame)

        self.LF_first_name = ttk.Entry(self.LF_fields, style='MyLarge.TEntry')
        self.LF_last_name = ttk.Entry(self.LF_fields, style='MyLarge.TEntry')
        self.LF_ID = ttk.Entry(self.LF_fields, style='MyLarge.TEntry')

        self.LF_FN_lbl = tk.Label(self.login_frame, text='First Name')
        self.LF_LN_lbl = tk.Label(self.login_frame, text='Last Name')
        self.LF_ID_lbl = tk.Label(self.login_frame, text='Student ID')

        self.inputs.extend([self.LF_first_name, self.LF_last_name, self.LF_ID])

        self.start()
        self.root.deiconify()
        self.root.focus_get()
        self.root.mainloop()

    def close(self) -> None:
        sys.stdout.write("qf - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.after(0, self.root.quit)

    def pageSetup(self, page_index: int, CRfFunc: Union[bool, int] = AUTO) -> bool:
        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        def LoginRf() -> None:
            self.update_requests[gsuid()] = [self.LF_file_frame, TUC.BG, [TUV.ACCENT]]
            self.update_requests[gsuid()] = [self.LF_fields, TUC.BG, [TUV.BG]]
            self.update_requests[gsuid()] = [self.login_frame, TUC.BG, [TUV.BG]]   
            self.update_requests[gsuid()] = [self.LF_file_ttl, TUC.CUSTOM, [
                lambda *args: self.LF_file_ttl.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                TUV.ACCENT, TUV.BG, TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_LARGE
            ]]
            self.update_requests['logText'] = [
                None,
                TUC.CUSTOM,
                [
                    lambda *args: log(LoggingLevel.DEBUG, f'{str(args[0])} {args[2]}'),
                    ('<EXECUTE>', lambda *_: self.LF_file_frame.winfo_width()), 'test', ('<LOOKUP>', 'padX')
            ]]
            self.update_requests[gsuid()] = [self.LF_file_info, TUC.CUSTOM, [
                lambda *args: self.LF_file_ttl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), anchor=tk.W, justify=tk.LEFT, wraplength=args[4]-2*args[5]
                ),
                TUV.ACCENT, TUV.BG, TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_MAIN, 
                ('<EXECUTE>', lambda *_: self.LF_file_frame.winfo_width()), ('<LOOKUP>', 'padX')
            ]]

            self.LF_fields.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)
            self.LF_file_frame.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY, side=tk.LEFT, ipadx=self.padX*2.5)

            self.LF_file_ttl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
            self.LF_file_ttl.config(text='Select a File')
            
            self.LF_file_select.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY*2)
            self.LF_file_select.config(text='Browse...', command=self.LFC_browse)

            self.LF_file_info.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
            self.LF_file_info.config(text='')

            self.screen_data[self.LOGIN_PAGE]['FilePath'] = ''
            self.screen_data[self.LOGIN_PAGE]['RfDone'] = True
           
        def ConfigurationRf() -> None:
            pass

        def SummaryRf() -> None:
            pass
           
        mapper = {
            self.LOGIN_PAGE: (self.login_frame, LoginRf),
            self.CONFIGURATION_PAGE: (self.config_frame, ConfigurationRf),
            self.SUMMARY_PAGE: (self.summary_frame, SummaryRf)
        }

        assert page_index in mapper,                    'QF::_pageSetup: inv. page_index (0x00)'
        assert CRfFunc in (True, False, 0, 1, AUTO),    'QF::_pageSetup: inv. CRfFunc arg (0x01)'

        frame, RfFunc = mapper[page_index]

        if CRfFunc == AUTO:
            CRfFunc = not bool(self.screen_data[page_index].get('RfDone'))
        
        if CRfFunc:
            try:
                RfFunc()
            except Exception as E:
                log(LoggingLevel.ERROR, f'Failed to run RFFunc for index {page_index}.\nError: {E}\n{traceback.format_exc()}')
                return False

        for (oFrame, _) in mapper.values():
            oFrame.pack_forget()

        frame.pack(fill=tk.BOTH, expand=True)
        return True

    def LFC_browse(self) -> None:
        pass

    def run(self) -> None:
        global APP_TITLE

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.iconbitmap(qa_functions.Files.QF_ico)
        self.root.title(APP_TITLE)
        self.root.geometry('%s+%s' % ('x'.join(str(d) for d in self.window_size), '+'.join(str(d) for d in self.screen_pos)))

        self.update_requests['QFRoot'] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleBG'] = [self.title, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleFG'] = [self.title, ThemeUpdateCommands.FG, [ThemeUpdateVars.ACCENT]]
        self.update_requests['QFTitleFont'] = [self.title, ThemeUpdateCommands.FONT, [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_XL_TITLE]]

        self.title.config(text='Quizzing Form', anchor=tk.W, justify=tk.LEFT)
        self.title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.TOP)

        self.pageSetup(self.LOGIN_PAGE)
        self.update_ui()
    def update_ui(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.load_theme()

        self.window_size = [self.root.winfo_width(), self.root.winfo_height()]
        self.screen_pos = [self.root.winfo_x(), self.root.winfo_y()]

        def tr(com: Any, *a: Any, **k: Any) -> Tuple[bool, str]:
            try:
                return True, com(*a, **k)
            except Exception as E:
                return False, f"{E.__class__.__name__}({E})"

        def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
            log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

        def log_norm(com: str, el: tk.Widget) -> None:
            log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

        for elID, (_e, _c, _a) in self.update_requests.items():
            command = cast(ThemeUpdateCommands, _c)
            element = cast(tk.Button, _e)
            args = cast(List[Any], _a)

            lCommand = [False, '', -1]
            cleaned_args = []

            if 'logText' in elID:
                print('UPDATE_UI', 'LOG_TEXT', args)

            for index, arg in enumerate(args):
                cleaned_arg = arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg]

                if isinstance(arg, tuple):
                    if len(arg) >= 2:
                        if arg[0] == '<EXECUTE>':
                            if 'logText' in elID:
                                print('UPDATE_UI LOG_TEXT exec :: ', end='')

                            ps, res = (tr(arg[1]) if len(args) == 2 else tr(arg[1], arg[2::]))
                            if ps:
                                cleaned_arg = res
                                if 'logText' in elID:
                                    print('SUCCESS', f'"{cleaned_arg}"')
                            else:
                                if 'logText' in elID:
                                    print('ERROR')
                                log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

                        elif arg[0] == '<LOOKUP>':
                            if 'logText' in elID:
                                print('UPDATE_UI LOG_TEXT look :: ', end='')

                            rs_b: int = cast(int, {
                                'padX': self.padX,
                                'padY': self.padY,
                                'root_width': self.root.winfo_width(),
                                'root_height': self.root.winfo_height(),
                                'uid': elID,
                                'UI': self,
                                'SELF': element
                            }.get(cast(str, arg[1])))

                            if rs_b is not None:
                                cleaned_arg = rs_b
                                if 'logText' in elID:
                                    print('SUCCESS', f'"{cleaned_arg}"')
                            else:
                                if 'logText' in elID:
                                    print('ERROR')
                                log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

                cleaned_args.append(cleaned_arg)

                if isinstance(cleaned_args[index], qa_functions.HexColor):
                    cleaned_args[index] = cleaned_args[index].color

            if command == ThemeUpdateCommands.BG:  # Background
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(bg=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.FG:  # Foreground
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(fg=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_BG:  # Active Background
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(activebackground=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_FG:  # Active Foreground
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(activeforeground=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_FG:  # BORDER COLOR
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.BORDER_SIZE:  # BORDER SIZE
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(highlightthickness=cleaned_args[0], bd=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.FONT:  # Font
                if len(cleaned_args) == 2:
                    ok, rs = tr(lambda: element.config(font=(cleaned_args[0], cleaned_args[1])))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.CUSTOM:  # Custom
                if len(cleaned_args) <= 0:
                    lCommand = [True, 'Function not provided', 1]
                elif len(cleaned_args) == 1:
                    ok, rs = tr(cleaned_args[0])
                    if not ok:
                        lCommand = [True, rs, 0]
                elif len(cleaned_args) > 1:
                    ok, rs = tr(lambda: cleaned_args[0](*cleaned_args[1::]))
                    if not ok:
                        lCommand = [True, rs, 0]

            elif command == ThemeUpdateCommands.WRAP_LENGTH:  # WL
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(wraplength=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            else:
                lCommand = [True, f'<Err:UnexpectedCommand ({command})>', -2]

            if lCommand[0] is True:
                log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
            elif DEBUG_NORM:
                log_norm(command.name, element)

            del lCommand, cleaned_args

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
            'LG.TButton',
            background=self.theme.background.color,
            foreground=self.theme.accent.color,
            font=(self.theme.font_face, self.theme.font_large_size),
            focuscolor=self.theme.accent.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'LG.TButton',
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

        del cb_fg

        self.ttk_style = qa_functions.TTKTheme.configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Admin')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size)
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

        self.ttk_style.configure(
            'Active.TButton',
            background=self.theme.accent.color,
            foreground=self.theme.background.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            focuscolor=self.theme.background.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Active.TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.accent.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'Accent2.TButton',
            background=self.theme.warning.color,
            foreground=self.theme.background.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            focuscolor=self.theme.background.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Accent2.TButton',
            background=[('active', self.theme.warning.color), ('disabled', self.theme.warning.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'Accent2LG.TButton',
            background=self.theme.warning.color,
            foreground=self.theme.background.color,
            font=(self.theme.font_face, self.theme.font_large_size),
            focuscolor=self.theme.background.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Accent2LG.TButton',
            background=[('active', self.theme.warning.color), ('disabled', self.theme.warning.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'ActiveLG.TButton',
            background=self.theme.accent.color,
            foreground=self.theme.background.color,
            font=(self.theme.font_face, self.theme.font_large_size),
            focuscolor=self.theme.background.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'ActiveLG.TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.accent.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'TSeparator',
            background=self.theme.gray.color
        )

        elID = "<lUP::unknown>"

        for _e, commands in self.late_update_requests.items():
            assert isinstance(commands, (list, tuple, set))
            element = cast(tk.Button, _e)

            for _c, _a in commands:
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False]
                cleaned_args = []
                for index, arg in enumerate(args):
                    cleaned_arg = (arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(arg, tuple):
                        if len(arg) >= 2:
                            if arg[0] == '<EXECUTE>':
                                ps, res = (tr(arg[1]) if len(args) == 2 else tr(arg[1], arg[2::]))
                                if ps:
                                    cleaned_arg = res
                                else:
                                    log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

                            if arg[0] == '<LOOKUP>':
                                rs_ba: int = cast(int, {
                                    'padX': self.padX,
                                    'padY': self.padY,
                                    'root_width': self.root.winfo_width(),
                                    'root_height': self.root.winfo_height()
                                }.get(cast(str, arg[1])))

                                if rs_ba is not None:
                                    cleaned_arg = rs_ba
                                else:
                                    log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

                    cleaned_args.append(cleaned_arg)

                    if isinstance(cleaned_args[index], qa_functions.HexColor):
                        cleaned_args[index] = cleaned_args[index].color

                if command == ThemeUpdateCommands.BG:  # Background
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(bg=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.FG:  # Foreground
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(fg=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_BG:  # Active Background
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(activebackground=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_FG:  # Active Foreground
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(activeforeground=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_FG:  # BORDER COLOR
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.BORDER_SIZE:  # BORDER SIZE
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(highlightthickness=cleaned_args[0], bd=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.FONT:  # Font
                    if len(cleaned_args) == 2:
                        ok, rs = tr(lambda: element.config(font=(cleaned_args[0], cleaned_args[1])))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.CUSTOM:  # Custom
                    if len(cleaned_args) <= 0:
                        lCommand = [True, 'Function not provided', 1]
                    elif len(cleaned_args) == 1:
                        ok, rs = tr(cleaned_args[0])
                        if not ok:
                            lCommand = [True, rs, 0]
                    elif len(cleaned_args) > 1:
                        ok, rs = tr(lambda: cleaned_args[0](*cleaned_args[1::]))
                        if not ok:
                            lCommand = [True, rs, 0]

                elif command == ThemeUpdateCommands.WRAP_LENGTH:  # WL
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(wraplength=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                else:
                    lCommand = [True, f'<Err:UnexpectedCommand ({command})>', -2]

                if lCommand[0] is True:
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cleaned_args

    def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, abg: ThemeUpdateVars = ThemeUpdateVars.ACCENT, afg: ThemeUpdateVars = ThemeUpdateVars.BG, uid: Union[str, None] = None) -> None:
        if padding is None:
            padding = self.padX

        if uid is None:
            uid = qa_prompts.gsuid()
        else:
            uid = f'{uid}<BTN>'

        while uid in self.update_requests:
            uid = f"{uid}[{random.randint(1000, 9999)}]"

        self.update_requests[uid] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda tbc, tbs, *args: button.config(
                    bg=args[0], fg=args[1], activebackground=args[2], activeforeground=args[3],
                    font=(args[4], args[5]),
                    wraplength=args[6],
                    highlightbackground=tbc,
                    bd=tbs,
                    highlightcolor=tbc,
                    highlightthickness=tbs,
                    borderwidth=tbs,
                    relief=tk.RIDGE
                ),
                ThemeUpdateVars.BORDER_COLOR,
                ThemeUpdateVars.BORDER_SIZE,
                (bg if not accent else ThemeUpdateVars.ACCENT),
                (fg if not accent else ThemeUpdateVars.BG),
                (abg if not accent else ThemeUpdateVars.BG),
                (afg if not accent else ThemeUpdateVars.ACCENT),
                font, size,
                self.window_size[0] - 2 * padding
            ] if isinstance(button, tk.Button) else [
                lambda *args: log(LoggingLevel.WARNING, f'{args[0]} : (from ButtonFormatter) !Btn'),
                ('<LOOKUP>', 'uid')
            ]
        ]

    def label_formatter(self, label: Union[tk.Label, tk.LabelFrame], bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int, float] = None, uid: Union[str, None] = None) -> None:
        if padding is None:
            padding = self.padX

        if uid is None:
            uid = qa_prompts.gsuid()
        else:
            uid = f'{uid}<LBL>'

        while uid in self.update_requests:
            uid = f"{uid}[{random.randint(1000, 9999)}]"

        self.update_requests[uid] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=args[5] - 2 * args[4]),
                bg, fg, font, size, padding, ('<LOOKUP>', 'root_width')
            ] if isinstance(label, tk.Label) else (
                [
                    lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                    bg, fg, font, size, padding
                ] if isinstance(label, tk.LabelFrame) else [
                    lambda *args: log(LoggingLevel.WARNING, f'{args[0]} : (from LabelFormatter) !Lbl, !LblF'),
                    ('<LOOKUP>', 'uid')
                ]
            )
        ]

    def load_theme(self) -> None:
        self.theme = qa_functions.qa_theme_loader.Load.auto_load_pref_theme()
        assert self.theme.check(), 'Loaded theme does not comply with all basic restrictions (err. 0x01)'

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

    def load_png(self) -> None:
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.svgs['qf'] = ImageTk.PhotoImage(i)

        ls: Tuple[
            Tuple[str, str, HexColor, HexColor, Union[int, float], Tuple[str, str]],
            ...] = (
            (self.checkmark_src, 'c_mark', self.theme.background, self.theme.accent, self.theme.font_main_size, ('checkmark', 'normal')),
            (self.checkmark_src, 'c_mark_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('checkmark', 'accent')),
            (self.cog_src, 'cog', self.theme.background, self.theme.accent, self.theme.font_main_size, ('settings_cog', 'normal')),
            (self.cog_src, 'cog_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('settings_cog', 'accent')),
            (self.arrow_right_src, 'arrow_right', self.theme.background, self.theme.accent, self.theme.font_main_size, ('arrow_right', 'normal')),
            (self.arrow_right_src, 'arrow_right_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('arrow_right', 'accent')),
            (self.arrow_left_src, 'arrow_left', self.theme.background, self.theme.accent, self.theme.font_main_size, ('arrow_left', 'normal')),
            (self.arrow_left_src, 'arrow_left_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('arrow_left', 'accent')),
            (self.question_src, 'question', self.theme.background, self.theme.accent, self.theme.font_main_size, ('question', 'normal')),
            (self.question_src, 'question_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('question', 'accent')),

            (self.checkmark_src, 'c_mark_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('checkmark_large', 'normal')),
            (self.checkmark_src, 'c_mark_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('checkmark_large', 'accent')),
            (self.cog_src, 'cog_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('settings_cog_large', 'normal')),
            (self.cog_src, 'cog_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('settings_cog_large', 'accent')),
            (self.arrow_right_src, 'arrow_right_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_right_large', 'normal')),
            (self.arrow_right_src, 'arrow_right_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_right_large', 'accent')),
            (self.arrow_left_src, 'arrow_left_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_left_large', 'normal')),
            (self.arrow_left_src, 'arrow_left_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_left_large', 'accent')),
            (self.question_src, 'question_accent', self.theme.background, self.theme.accent, self.theme.font_title_size, ('question_large', 'normal')),
            (self.question_src, 'question_accent_accent', self.theme.accent, self.theme.background, self.theme.font_title_size, ('question_large', 'accent')),
        )

        for src, name, background, foreground, _s, (a, b) in ls:
            size = cast(int, _s)
            try:
                File = qa_functions.File(src)
                tmp = f"{self.svg_tmp}\\{File.file_name}"
                raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
                new_data = raw_data.replace(qa_prompts._SVG_COLOR_REPL_ROOT, foreground.color)
                File = qa_functions.File(tmp)
                qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))
                self.svgs[a][b] = get_svg(tmp, background.color, (size, size), name)

            except Exception as E:
                log(LoggingLevel.ERROR, f'admt::load_png - Failed to load requested svg ({src}): {E}')

    def disable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        for btn in self.inputs:
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        for btn in self.inputs:
            if btn not in exclude:
                btn.config(state=tk.NORMAL)

        self.update_ui()


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

    data = f"{AppLogColors.QUIZZING_FORM}{AppLogColors.EXTRA}[QUIZZING_FORM]{ANSI.RESET} {data}"

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


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs: Any) -> tk.Toplevel:
    transfer_log_info(qa_prompts)

    qa_functions.qa_theme_loader.THEME_LOADER_ENABLE_DEV_DEBUGGING = DEBUG_DEV_FLAG

    subprocess.call('', shell=True)
    if os.name == 'nt':  # Only if we are running on Windows
        k = windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)

    log(LoggingLevel.ERROR, '[USER CHECK] Error message logging available')
    log(LoggingLevel.SUCCESS, '[USER CHECK] Success message logging available')
    log(LoggingLevel.INFO, '[USER CHECK] Info message logging available')
    log(LoggingLevel.WARNING, '[USER CHECK] Warning message logging available')
    log(LoggingLevel.DEBUG, '[USER CHECK] Debug message logging available')
    log(LoggingLevel.DEVELOPER, '[USER CHECK] Developer console logging available')

    ui_root = tk.Toplevel()
    _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root


def get_svg(svg_file: str, bg: Union[str, int], size: Union[None, Tuple[int, int]] = None, name: Union[None, str] = None) -> ImageTk.PhotoImage:
    background = bg
    if isinstance(bg, str):
        background = int(bg.replace("#", '0x'), 0)

    assert isinstance(background, int)

    drawing = svg2rlg(svg_file)
    bytes_png = BytesIO()
    renderPM.drawToFile(drawing, bytes_png, fmt="PNG", bg=background)
    img = Image.open(bytes_png)
    if size is not None:
        img = img.resize(size, PIL.Image.ANTIALIAS)

    p_img = ImageTk.PhotoImage(img, name=name)

    return p_img


def transfer_log_info(script: Any) -> None:
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, DEBUG_NORM, DEBUG_DEV_FLAG

    script.LOGGER_AVAIL = LOGGER_AVAIL  # type: ignore
    script.LOGGER_FUNC = LOGGER_FUNC   # type: ignore
    script.LOGGING_FILE_NAME = LOGGING_FILE_NAME    # type: ignore
    script.DEBUG_NORM = DEBUG_NORM  # type: ignore
    script.DEBUG_DEV_FLAG = DEBUG_DEV_FLAG  # type: ignore
