import tkinter as tk, sys, qa_functions, qa_files, os, traceback, hashlib, json, random, subprocess, math
from threading import Thread
from . import qa_prompts
from tkinter import ttk, filedialog, colorchooser, font
from .qa_prompts import gsuid, configure_scrollbar_style
from PIL import Image, ImageTk
from ctypes import windll
from typing import *
from qa_functions.qa_enum import ThemeUpdateCommands, ThemeUpdateVars, LoggingLevel, FileType
from qa_functions.qa_std import ANSI, AppLogColors
from qa_functions.qa_custom import Theme, UnexpectedEdgeCase
from qa_files.qa_theme import TDB_to_DICT, TDB, ReadData as ReadAsTDB, LATEST_GENERATE_FUNCTION as GenThemeFile


script_name = "APP_TU"
APP_TITLE = "Quizzing Application | Theming Utility"
_THEME_FILE_TYPE = qa_functions.qa_enum.FileType.QA_THEME

LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
DEBUG_DEV_FLAG = False


class _UI(Thread):
    def __init__(self, root: Union[tk.Toplevel, tk.Tk], ic: Any, ds: Any, **kwargs: Optional[Dict[str, Any]]) -> None:
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs
        self.root.withdraw()

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        self.window_size = [int(math.pi/3.14 * .8 * self.screen_dim[1]), int(self.screen_dim[1] * .8)]
        
        if self.window_size[0] > (self.screen_dim[0] * 0.9): 
            self.window_size[0] = int(self.screen_dim[0] * 0.9)
            
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] * .43 - self.window_size[1] / 2)
        ]

        self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map: Dict[ThemeUpdateVars, Union[str, int, float, qa_functions.HexColor]] = {}
        self.tmp_theme: Theme = clone_theme(self.theme)
        self.rst_theme = True

        self.padX = 20
        self.padY = 10

        self.load_theme()
        self.update_requests: Dict[
                str,
                List[Union[Union[tk.Tk, tk.Toplevel, None, tk.Widget, tk.BaseWidget], ThemeUpdateCommands, List[Any]]]
        ] = {}

        self.img_path = f"{qa_functions.Files.icoRoot}\\.png\\themer.png"
        self.img_size = (75, 75)
        self.img = None
        self.load_png()

        self.ttk_theme = cast(str, self.kwargs['ttk_theme'])

        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'TU')

        self.title_box = tk.Frame(self.root)
        self.title_label = tk.Label(self.title_box)
        self.title_icon = tk.Label(self.title_box)

        self.theme_selector_panel = tk.LabelFrame(self.root)
        self.theme_pref = qa_functions.qa_theme_loader.load_pref_data()
        self.select_theme_button = tk.Button(self.theme_selector_panel)
        self.theme_selector_s_var = tk.StringVar(self.root)
        self.theme_selector_options: Dict[str, Union[str, Theme]] = {'No themes loaded; click \'Refresh\' to load themes': ''}
        self.theme_pre_installed_frame = tk.Frame(self.theme_selector_panel)
        self.theme_pre_installed_lbl = tk.Label(self.theme_pre_installed_frame)
        self.theme_selector_dropdown = ttk.OptionMenu(self.theme_pre_installed_frame, self.theme_selector_s_var, *self.theme_selector_options.keys())
        self.theme_selector_s_var.set(self.theme_pref[2])
        self.install_new_frame = tk.Frame(self.theme_selector_panel)
        self.install_new_label = tk.Label(self.install_new_frame)
        self.install_new_button = ttk.Button(self.install_new_frame)
        self.prev_theme_selection = self.theme_selector_s_var.get()
        self.online_theme_button = ttk.Button(self.install_new_frame)
        self.theme_uninstall_frame = tk.Frame(self.theme_selector_panel)
        self.theme_uninstall_lbl = tk.Label(self.theme_uninstall_frame)
        self.theme_uninstall_button = ttk.Button(self.theme_uninstall_frame, style='Err.TButton')
        
        self.showcase_root_frame = tk.LabelFrame(self.root)
        self.showcase_canvas = tk.Canvas(self.showcase_root_frame)
        self.showcase_frame = tk.Frame(self.showcase_canvas)
        self.showcase_vsb = ttk.Scrollbar(self.showcase_root_frame, style='MyTU.TScrollbar')
        self.showcase_xsb = ttk.Scrollbar(self.showcase_root_frame, style='MyHorizTU.TScrollbar', orient=tk.HORIZONTAL)

        self.showcase_f1 = tk.Frame(self.showcase_frame)
        self.showcase_f2 = tk.Frame(self.showcase_frame)
        self.showcase_f3 = tk.Frame(self.showcase_frame)
        self.showcase_f4 = tk.Frame(self.showcase_frame)

        self.showcase_bg = tk.Button(self.showcase_f1)
        self.showcase_fg = tk.Button(self.showcase_f1)
        self.showcase_accent = tk.Button(self.showcase_f2)
        self.showcase_gray = tk.Button(self.showcase_f2)
        self.showcase_error = tk.Button(self.showcase_f3)
        self.showcase_warning = tk.Button(self.showcase_f3)
        self.showcase_okay = tk.Button(self.showcase_f4)
        self.showcase_border_color = tk.Button(self.showcase_f4)

        self.showcase_font_all = tk.Frame(self.showcase_frame)
        self.showcase_primary = tk.LabelFrame(self.showcase_font_all)
        self.showcase_alt = tk.LabelFrame(self.showcase_font_all)

        self.showcase_primary_font = ttk.Button(self.showcase_primary, command=self.prim_font)
        self.showcase_alt_font = ttk.Button(self.showcase_alt, command=self.alt_font)
        self.showcase_title_font = ttk.Button(self.showcase_primary, command=self.title_font)

        self.showcase_fp_1 = tk.Button(self.showcase_primary)
        self.showcase_fp_2 = tk.Button(self.showcase_primary)
        self.showcase_fp_3 = tk.Button(self.showcase_primary)
        self.showcase_fp_4 = tk.Button(self.showcase_primary)
        self.showcase_fp_5 = tk.Button(self.showcase_primary)

        self.showcase_ap_1 = tk.Button(self.showcase_alt)
        self.showcase_ap_2 = tk.Button(self.showcase_alt)
        self.showcase_ap_3 = tk.Button(self.showcase_alt)
        self.showcase_ap_4 = tk.Button(self.showcase_alt)
        self.showcase_ap_5 = tk.Button(self.showcase_alt)

        self.showcase_border_size = ttk.Button(self.showcase_frame, command=self.border_size)

        self.export_button_panel = tk.LabelFrame(self.root)
        self.export_theme_button = ttk.Button(self.export_button_panel, command=self.export_theme)
        self.save_theme_button = ttk.Button(self.export_button_panel, command=self.save_custom_theme)
        self.reset_theme_button = ttk.Button(self.export_button_panel, command=self.reset_theme, style='Contrast.TButton')
        self.preview_button = ttk.Button(self.export_button_panel, command=cast(Callable[[], Any], self.preview_change))

        self.space_filler_1 = tk.Label(self.theme_pre_installed_frame)
        self.space_filler_2 = tk.Label(self.install_new_frame)
        self.space_filler_3 = tk.Label(self.theme_uninstall_frame)

        self.start()
        self.root.mainloop()

    def close(self) -> None:
        sys.stdout.write("tu - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.quit()

    def update_ui(self, theme: Union[None, Theme] = None) -> None:
        self.load_theme(theme)

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

            lCommand = [False, '', 0]
            cargs = []

            for index, arg in enumerate(args):
                cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                if isinstance(cargs[index], qa_functions.qa_custom.HexColor):
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

        self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'TU')

        HC = qa_functions.HexColor
        bw = int(0.025*self.window_size[0])

        self.showcase_bg.config(
            text=f"Background\n{self.theme.background.color}",
            background=self.theme.background.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.background).color,
            width=bw
        )

        self.showcase_fg.config(
            text=f"Foreground\n{self.theme.foreground.color}",
            background=self.theme.foreground.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.foreground).color,
            width=bw
        )

        self.showcase_accent.config(
            text=f"Accent\n{self.theme.accent.color}",
            background=self.theme.accent.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.accent).color,
            width=bw
        )

        self.showcase_gray.config(
            text=f"Gray\n{self.theme.gray.color}",
            background=self.theme.gray.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.gray).color,
            width=bw
        )

        self.showcase_warning.config(
            text=f"Warning\n{self.theme.warning.color}",
            background=self.theme.warning.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.warning).color,
            width=bw
        )

        self.showcase_okay.config(
            text=f"Okay\n{self.theme.okay.color}",
            background=self.theme.okay.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.okay).color,
            width=bw
        )

        self.showcase_error.configure(
            text=f"Error\n{self.theme.error.color}",
            background=self.theme.error.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.error).color,
            width=bw
        )

        self.showcase_border_color.configure(
            text=f"Border\n{self.theme.border_color.color}",
            background=self.theme.border_color.color,
            foreground=qa_functions.qa_colors.Functions.calculate_more_contrast(HC("#ffffff"), HC("#000000"), self.theme.border_color).color,
            width=bw
        )

        self.showcase_border_size.config(
            text=f"Border Size: {self.theme.border_size}"
        )

        self.showcase_primary_font.config(text=f"Primary Font: {self.theme.font_face}")
        self.showcase_title_font.config(text=f"Title Font: {self.theme.title_font_face}")
        self.showcase_alt_font.config(text=f"Alternative Font: {self.theme.font_alt_face}")

        self.showcase_ap_1.config(text=f"Small: {self.theme.font_small_size}")
        self.showcase_fp_1.config(text=f"Small: {self.theme.font_small_size}")

        self.showcase_ap_2.config(text=f"Primary: {self.theme.font_main_size}")
        self.showcase_fp_2.config(text=f"Primary: {self.theme.font_main_size}")

        self.showcase_ap_3.config(text=f"Large: {self.theme.font_large_size}")
        self.showcase_fp_3.config(text=f"Large: {self.theme.font_large_size}")

        self.showcase_ap_4.config(text=f"Title: {self.theme.font_title_size}")
        self.showcase_fp_4.config(text=f"Title: {self.theme.font_title_size}")

        self.showcase_ap_5.config(text=f"Extra Large: {self.theme.font_xl_title_size}")
        self.showcase_fp_5.config(text=f"Extra Large: {self.theme.font_xl_title_size}")

        self.showcase_canvas.config(bd=0, highlightthickness=0)

        # External Update Calls
        self.update_theme_selector_options()

    def button_formatter(self, button: tk.Button, accent: bool = False, font_face: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None,
                         bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, abg: ThemeUpdateVars = ThemeUpdateVars.ACCENT, afg: ThemeUpdateVars = ThemeUpdateVars.BG, uid: Union[str, None] = None) -> None:
        if padding is None:
            padding = self.padX

        if uid is None:
            uid = gsuid()
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
                font_face, size,
                self.window_size[0] - 2 * padding
            ]
        ]

    def label_formatter(self, label: Union[tk.Label, tk.LabelFrame], bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font_face: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[int, None] = None, uid: Union[str, None] = None) -> None:
        if padding is None:
            padding = self.padX

        if uid is None:
            uid = gsuid()
        else:
            uid = f'{uid}<LBL>'

        while uid in self.update_requests:
            uid = f"{uid}[{random.randint(1000, 9999)}]"

        self.update_requests[uid] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=self.window_size[0] - 2 * args[4]),
                bg, fg, font_face, size, padding
            ] if isinstance(label, tk.Label) else (
                [
                    lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                    bg, fg, font_face, size, padding
                ] if isinstance(label, tk.LabelFrame) else [
                    lambda *args: None
                ]
            )
        ]

    def load_theme(self, theme: Union[Theme, None] = None) -> None:
        if theme is None and (gen_cmp_theme_dict(self.tmp_theme) == self.theme or self.rst_theme):
            self.theme = qa_functions.LoadTheme.auto_load_pref_theme()
            self.rst_theme = False
        else:
            sys.stdout.write("[PREVIEW] using provided theme\n")
            if theme is not None:
                self.theme = theme
                self.tmp_theme = theme

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
            ThemeUpdateVars.TITLE_FONT_FACE: self.theme.title_font_face,
        }

    def run(self) -> None:
        global DEBUG_NORM, APP_TITLE
        qa_prompts.DEBUG_NORM = DEBUG_NORM
        qa_prompts.TTK_THEME = self.ttk_theme

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.title(APP_TITLE)
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
        self.root.iconbitmap(qa_functions.Files.TU_ico)

        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.title_label.config(text="Theming Utility", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=cast(str, self.img))
        self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX/8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX/8), pady=self.padY, side=tk.LEFT)

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT, font_face=ThemeUpdateVars.TITLE_FONT_FACE)
        self.label_formatter(self.title_icon)

        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        self.update_requests[gsuid()] = [self.root, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.title_box, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.theme_pre_installed_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.install_new_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.theme_uninstall_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_root_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_canvas, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_f1, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_f2, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_f3, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_f4, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.showcase_font_all, TUC.BG, [TUV.BG]]

        self.theme_selector_panel.config(text="Installed Themes")
        self.theme_selector_panel.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, ipadx=self.padX/2, ipady=self.padY/2)

        for sf in (self.space_filler_2, self.space_filler_1, self.space_filler_3):
            sf.pack(fill=tk.X, expand=True, side=tk.RIGHT)
            self.label_formatter(sf)

        self.theme_pre_installed_frame.pack(fill=tk.X, expand=False)
        self.theme_selector_dropdown.pack(side=tk.RIGHT, padx=(0, self.padX), pady=self.padY, fill=tk.X, expand=False)
        self.theme_pre_installed_lbl.config(text="Select an Installed Theme:", anchor=tk.E, justify=tk.RIGHT)
        self.theme_pre_installed_lbl.pack(side=tk.LEFT, padx=(self.padX, 0), pady=self.padY, fill=tk.X, expand=False)

        self.install_new_frame.pack(fill=tk.X, expand=False)
        self.install_new_label.config(text="Want to try a new theme?")
        self.install_new_label.pack(fill=tk.X, expand=False, padx=(self.padX, 0), pady=(0, self.padY), side=tk.LEFT)
        self.online_theme_button.config(text="Download (Online)", command=self.online_download)
        self.online_theme_button.pack(fill=tk.X, expand=False, padx=(0, self.padX), pady=(0, self.padY), side=tk.RIGHT)
        self.install_new_button.config(text="Install (Local)", command=self.install_new_theme)
        self.install_new_button.pack(fill=tk.X, expand=False, padx=(0, self.padX), pady=(0, self.padY), side=tk.RIGHT)

        self.theme_uninstall_frame.pack(fill=tk.X, expand=False)
        self.theme_uninstall_lbl.config(text="No longer using a theme?")
        self.theme_uninstall_lbl.pack(fill=tk.X, expand=False, padx=(self.padX, 0), pady=(0, self.padY), side=tk.LEFT)
        self.theme_uninstall_button.config(text="Uninstall a Theme", command=self.uninstall)
        self.theme_uninstall_button.pack(fill=tk.X, expand=False, padx=(0, self.padX), pady=(0, self.padY), side=tk.RIGHT)

        self.theme_selector_s_var.trace('w', self.on_theme_drop_change)
        self.label_formatter(self.theme_selector_panel, size=TUV.FONT_SIZE_SMALL)
        self.label_formatter(self.theme_pre_installed_lbl, size=TUV.FONT_SIZE_MAIN)
        self.label_formatter(self.install_new_label, size=TUV.FONT_SIZE_MAIN)
        self.label_formatter(self.theme_uninstall_lbl, size=TUV.FONT_SIZE_MAIN)

        self.showcase_root_frame.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=(0, self.padY), side=tk.LEFT)
        self.showcase_xsb.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
        self.showcase_canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(self.padX/2, 0), pady=self.padY)
        self.showcase_vsb.pack(fill=tk.Y, expand=False, side=tk.RIGHT, padx=(0, self.padX/2), pady=self.padY)
        self.export_button_panel.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=(0, self.padY), side=tk.RIGHT)
        self.showcase_root_frame.config(text="Current theme. Click on any item below to change its value")
        self.export_button_panel.config(text="Custom Theme IO")

        self.export_theme_button.pack(fill=tk.Y, expand=True, padx=self.padX, pady=self.padY)
        self.save_theme_button.pack(fill=tk.Y, expand=True, padx=self.padX, pady=(0, self.padY))
        self.reset_theme_button.pack(fill=tk.Y, expand=True, padx=self.padX, pady=(0, self.padY))
        self.export_theme_button.config(text="Export")
        self.save_theme_button.config(text="Save")
        self.reset_theme_button.config(text="Reset")

        self.label_formatter(self.showcase_root_frame, size=TUV.FONT_SIZE_SMALL)
        self.label_formatter(self.showcase_primary, size=TUV.FONT_SIZE_SMALL)
        self.label_formatter(self.showcase_alt, size=TUV.FONT_SIZE_SMALL)
        self.label_formatter(self.export_button_panel, size=TUV.FONT_SIZE_SMALL)

        self.showcase_vsb.configure(command=self.showcase_canvas.yview)
        self.showcase_xsb.configure(command=self.showcase_canvas.xview)
        self.showcase_canvas.configure(yscrollcommand=self.showcase_vsb.set, xscrollcommand=self.showcase_xsb.set)

        self.showcase_bg.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.showcase_bg.config(command=self.onBGClick)
        self.button_formatter(self.showcase_bg)

        self.showcase_fg.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.showcase_fg.config(command=self.onFGClick)
        self.button_formatter(self.showcase_fg)

        self.showcase_accent.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.showcase_accent.config(command=self.onAccentClick)
        self.button_formatter(self.showcase_accent)

        self.showcase_gray.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.showcase_gray.config(command=self.onGrayClick)
        self.button_formatter(self.showcase_gray)

        self.showcase_error.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.showcase_error.config(command=self.onErrorClick)
        self.button_formatter(self.showcase_error)

        self.showcase_warning.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.showcase_warning.config(command=self.onWarningClick)
        self.button_formatter(self.showcase_warning)

        self.showcase_okay.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.showcase_okay.config(command=self.onOkayClick)
        self.button_formatter(self.showcase_okay)

        self.showcase_border_color.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.showcase_border_color.config(command=self.onBCClick)
        self.button_formatter(self.showcase_border_color)

        self.showcase_f1.pack(fill=tk.X, expand=True)
        self.showcase_f2.pack(fill=tk.X, expand=True)
        self.showcase_f3.pack(fill=tk.X, expand=True)
        self.showcase_f4.pack(fill=tk.X, expand=True)

        self.showcase_border_size.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.showcase_font_all.pack(fill=tk.X, expand=False)
        self.showcase_primary.pack(fill=tk.BOTH, expand=True)
        self.showcase_alt.pack(fill=tk.BOTH, expand=True)

        self.showcase_primary_font.pack(fill=tk.X, expand=False, pady=(self.padY, 0), padx=self.padX)
        self.showcase_title_font.pack(fill=tk.X, expand=False, pady=(self.padY, 0), padx=self.padX)
        self.showcase_alt_font.pack(fill=tk.X, expand=False, pady=(self.padY, 0), padx=self.padX)

        self.showcase_primary.config(text="Primary Font")
        self.showcase_alt.config(text="Alternative Font")

        self.showcase_ap_1.config(command=self.font_size_small)
        self.showcase_ap_1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_ap_2.config(command=self.font_size_medium)
        self.showcase_ap_2.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_ap_3.config(command=self.font_size_large)
        self.showcase_ap_3.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_ap_4.config(command=self.font_size_title)
        self.showcase_ap_4.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_ap_5.config(command=self.font_size_xl)
        self.showcase_ap_5.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.showcase_fp_1.config(command=self.font_size_small)
        self.showcase_fp_1.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_fp_2.config(command=self.font_size_medium)
        self.showcase_fp_2.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_fp_3.config(command=self.font_size_large)
        self.showcase_fp_3.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_fp_4.config(command=self.font_size_title)
        self.showcase_fp_4.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

        self.showcase_fp_5.config(command=self.font_size_xl)
        self.showcase_fp_5.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.button_formatter(self.showcase_fp_1, size=TUV.FONT_SIZE_SMALL)
        self.button_formatter(self.showcase_fp_2, size=TUV.FONT_SIZE_MAIN)
        self.button_formatter(self.showcase_fp_3, size=TUV.FONT_SIZE_LARGE)
        self.button_formatter(self.showcase_fp_4, size=TUV.FONT_SIZE_TITLE)
        self.button_formatter(self.showcase_fp_5, size=TUV.FONT_SIZE_XL_TITLE)
        self.button_formatter(self.showcase_ap_1, size=TUV.FONT_SIZE_SMALL, font_face=TUV.ALT_FONT_FACE)
        self.button_formatter(self.showcase_ap_2, size=TUV.FONT_SIZE_MAIN, font_face=TUV.ALT_FONT_FACE)
        self.button_formatter(self.showcase_ap_3, size=TUV.FONT_SIZE_LARGE, font_face=TUV.ALT_FONT_FACE)
        self.button_formatter(self.showcase_ap_4, size=TUV.FONT_SIZE_TITLE, font_face=TUV.ALT_FONT_FACE)
        self.button_formatter(self.showcase_ap_5, size=TUV.FONT_SIZE_XL_TITLE, font_face=TUV.ALT_FONT_FACE)

        # Final things
        self.showcase_canvas.create_window(0.0, 0.0, window=self.showcase_frame, anchor="nw", tags="self.showcase_frame")

        self.showcase_frame.update()
        self.showcase_frame.bind("<Configure>", self.onFrameConfig)
        self.showcase_canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.update_ui()

        self.root.deiconify()
        self.root.focus_get()

    def _on_mousewheel(self, event: Any) -> None:
        """
        Straight out of stackoverflow
        Article: https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        Change: added "int" around the first arg
        """
        self.showcase_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def onFrameConfig(self, event: Any) -> None:
        self.showcase_canvas.configure(scrollregion=self.showcase_canvas.bbox("all"))

    def load_png(self) -> None:
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(i)

    def update_theme_selector_options(self) -> None:
        og = {**self.theme_selector_options}
        self.theme_selector_options = {}
        for code, tad in qa_functions.LoadTheme.auto_load_all().items():
            name, theme = (*tad.keys(),)[0], (*tad.values(),)[0]

            file_name = theme.theme_file_display_name
            self.theme_selector_options[f'{file_name}: {name}'] = theme

        if og != self.theme_selector_options:
            self.theme_pref = qa_functions.qa_theme_loader.load_pref_data()
            self.theme_selector_s_var.set(self.theme_pref[2])
            self.theme_selector_dropdown['menu'].delete(0, tk.END)
            for option in self.theme_selector_options:
                self.theme_selector_dropdown['menu'].add_radiobutton(
                    label=option, command=tk._setit(self.theme_selector_s_var, option)
                )

    def on_theme_drop_change(self, *args: Optional[Any], **kwargs: Optional[Any]) -> None:
        def nope() -> None:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket("The requested theme wasn't found; refreshing list."),
                qoc=False
            )
            self.update_ui()

        if self.prev_theme_selection != self.theme_selector_s_var.get():
            self.prev_theme_selection = self.theme_selector_s_var.get()
            nt = self.theme_selector_options.get(self.theme_selector_s_var.get())
            if not isinstance(nt, qa_functions.Theme):
                nope()

            new_theme = cast(qa_functions.Theme, nt)
            if not os.path.exists(new_theme.theme_file_path):
                nope()
            else:
                qa_functions.qa_theme_loader.set_pref(
                    new_theme.theme_file_path, new_theme.theme_code, f'{new_theme.theme_file_display_name}: {new_theme.theme_display_name}'
                )
                self.rst_theme = True
                self.update_ui()

    def online_download(self) -> None:
        self.disable_all_inputs()

        tmp_dir = f"{qa_functions.App.appdata_dir}\\.tmp\\.downloads".replace('/', '\\')
        tmp_file_path = f"{tmp_dir}\\{random.randint(1000, 9999)}.qa.tmp.download.qaTheme"
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)
        elif os.path.isdir(tmp_file_path):
            os.remove(tmp_file_path)

        qa_prompts.MessagePrompts.show_warning(
            qa_prompts.InfoPacket("Do not download/install themes from any sources that you do not trust; if you wish to abort the download process, click the \"Cancel\" button on the next screeen. ")
        )

        qa_prompts.InputPrompts.DownloadFile(qa_prompts.DownloadPacket(tmp_file_path))
        if not os.path.isfile(tmp_file_path):
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket('Failed to download theme from requested URL')
            )
            self.enable_all_inputs()
            return

        try:
            file = qa_functions.qa_custom.File(tmp_file_path)
            raw = qa_functions.qa_file_handler.Open.load_file(file, qa_functions.qa_custom.OpenFunctionArgs(bytes))
            _, raw2 = cast(Tuple[bytes, str], qa_files.qa_file_std.load_file(qa_functions.qa_enum.FileType.QA_THEME, raw))
            self.install_new_theme((tmp_file_path, ))
            os.remove(tmp_file_path)

        except Exception as E:
            sys.stderr.write(traceback.format_exc())
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(f'Failed to install theme: {str(E)}')
            )

        self.enable_all_inputs()

    def install_new_theme(self, files: Union[None, Tuple[Any]] = None) -> Union[None, List[str]]:
        self.disable_all_inputs()

        req_files = filedialog.askopenfilenames(
            title="Select Theme File",
            filetypes=[('Quizzing Application Theme', qa_files.qa_theme_extn)]
        ) if not isinstance(files, tuple) else files

        to_install: Dict[str, Tuple[qa_functions.Theme, ...]] = {}  # type: ignore

        if len(req_files) <= 0:
            self.enable_all_inputs()
            return None

        e1 = {**qa_functions.LoadTheme.auto_load_all()}
        e2, e3, e4 = [], [], []
        for k, v in e1.items():
            exs: qa_functions.Theme = (*v.values(),)[0]
            e2.append({
                'bg': exs.background.color,
                'fg': exs.foreground.color,
                'accent': exs.accent.color,
                'error': exs.error.color,
                'warning': exs.warning.color,
                'okay': exs.okay.color,
                'gray': exs.gray.color,
                'ff': exs.font_face,
                'fft': exs.title_font_face,
                'faf': exs.font_alt_face,
                'fss': exs.font_small_size,
                'fms': exs.font_main_size,
                'fls': exs.font_large_size,
                'fts': exs.font_title_size,
                'fxlts': exs.font_xl_title_size,
                'bs': exs.border_size,
                'bc': exs.border_color.color
            })
            e3.append((k, (*v.keys(),)[0], f"{exs.theme_file_display_name}: {exs.theme_display_name}"))
            e4.append(f"{exs.theme_file_display_name}: {exs.theme_display_name}")

        for file in req_files:
            file = file.replace('/', '\\')
            fn = file.split('\\')[-1]

            try:
                if file.split('.')[-1] != qa_files.qa_theme_extn:
                    raise Exception('Invalid file extension')

                file_inst = qa_functions.File(file)
                raw = qa_functions.OpenFile.load_file(file_inst, qa_functions.OpenFunctionArgs(bytes, False))
                js = qa_files.load_file(qa_functions.qa_enum.FileType.QA_THEME, raw)

                # For MyPy
                assert isinstance(js, tuple)
                assert len(js) == 2
                _, string = js
                del js

                theme_json = TDB_to_DICT(ReadAsTDB(string, file), True)
                assert fn not in (qa_functions.Files.ThemePrefFile, qa_functions.Files.ThemeCustomFile), f"Filename '{fn}' is not allowed (system reserved)"
                assert 'file_info' in theme_json, 'File info unavailable'
                assert 'avail_themes' in theme_json['file_info'], 'No themes available'
                assert 'num_themes' in theme_json['file_info']['avail_themes'], 'No themes available'
                assert len(theme_json['file_info']['avail_themes']) == theme_json['file_info']['avail_themes']['num_themes'] + 1, 'Corrupted theme data'
                assert theme_json['file_info']['avail_themes']['num_themes'] > 0, 'No themes available'

                all_theme_data = qa_functions.LoadTheme._load_theme(file, string)

                it, ins = [], []

                for _, td in all_theme_data.items():
                    theme_name, theme_data = ((*td.keys(),)[0], (*td.values(),)[0])

                    comp_theme_dict = gen_cmp_theme_dict(theme_data)

                    dn = f"{theme_data.theme_file_display_name}: {theme_data.theme_display_name}"

                    if dn in e4:
                        ins.append(dn)

                    elif comp_theme_dict in e2:
                        it.append((f"{fn}: {theme_data.theme_code}", e3[e2.index(cast(Dict[str, Union[str, Any]], comp_theme_dict))][0]))

                    else:
                        if fn not in to_install:
                            to_install[fn] = ()

                        to_install[fn] = (*to_install[fn], theme_data)

                if len(it) + len(ins) > 0:
                    raise Exception((("\n\tCouldn't install {} theme(s) from '{}': identical theme(s) already installed.\n\t\tFailed to install the following themes:\n\t\t\t*{}\n".format(str(len(it)), fn, "\n\t\t\t*".join(f"<{a}> = <{b}>" for a, b in it))) if len(it) > 0 else "") + ((("\n" if len(it) > 0 else "") +("\n\tCouldn't install {} theme(s) from '{}': theme with identical names already installed.\n\t\tFailed to install the following themes:\n\t\t\t*{}\n".format(str(len(ins)), fn, "\n\t\t\t*".join(j for j in ins)))) if len(ins) > 0 else ""))

            except Exception as E:
                tb = traceback.format_exc()

                log(LoggingLevel.ERROR, f'QATU-ThemeInstaller: Error x1: {tb}')

                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket(
                        msg=f"""Failed to install theme from file '{fn}'.

Error: {str(E)}
Error Code: {hashlib.md5(str(E).encode()).hexdigest()}

Technical Information:
{tb}""",
                        title="Couldn't Install Theme"
                    )
                )

        install_dir = f"{qa_functions.App.appdata_dir}\\{qa_functions.Files.ad_theme_folder}".replace('/','\\')
        installed = []
        if not os.path.isdir(install_dir):
            os.makedirs(install_dir)

        for filename, _t in to_install.items():
            themes: Tuple[qa_functions.Theme] = cast(Tuple[qa_functions.qa_custom.Theme], _t)

            if len(themes) <= 0:
                continue

            assert len(themes) > 0  # For compiler

            theme_data_dict: Dict[Any, Any] = {
                'file_info':
                    {
                        'name': themes[0].theme_file_name,
                        'display_name': themes[0].theme_file_display_name,
                        'avail_themes': {
                            'num_themes': len(themes)
                        }
                    }
            }

            for theme in themes:
                theme_data_dict['file_info']['avail_themes'][theme.theme_display_name] = theme.theme_code

                nt = {
                    'display_name': theme.theme_display_name,
                    'background': theme.background.color,
                    'foreground': theme.foreground.color,
                    'accent': theme.accent.color,
                    'error': theme.error.color,
                    'warning': theme.warning.color,
                    'ok': theme.okay.color,
                    'gray': theme.gray.color,
                    'font': {
                        'title_font_face': theme.title_font_face,
                        'font_face': theme.font_face,
                        'alt_font_face': theme.font_alt_face,
                        'size_small': theme.font_small_size,
                        'size_main': theme.font_main_size,
                        'size_subtitle': theme.font_large_size,
                        'size_title': theme.font_title_size,
                        'size_xl_title': theme.font_xl_title_size
                    },
                    'border': {
                        'size': theme.border_size,
                        'colour': theme.border_color.color
                    }
                }

                theme_data_dict = {**theme_data_dict, theme.theme_code: nt}

            d2s = json.dumps(theme_data_dict, indent=4)
            d2s2 = qa_files.generate_file(qa_functions.qa_enum.FileType.QA_THEME, d2s)
            File = qa_functions.File(f"{install_dir}\\{filename}")
            qa_functions.SaveFile.secure(
                File, d2s2, qa_functions.SaveFunctionArgs(False, False, delete_backup=False, save_data_type=bytes)
            )
            installed.append(f"{install_dir}\\{filename}")

        self.enable_all_inputs()
        return installed

    def uninstall(self) -> None:
        self.disable_all_inputs()

        all_themes = qa_functions.qa_theme_loader.Load.auto_load_all(False)
        if len(all_themes) <= 0:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('No installed themes found'))
            self.enable_all_inputs()
            return

        ls: Dict[str, Theme] = {f"{(*v.values(),)[0].theme_file_display_name}: {(*v.values(),)[0].theme_display_name}": (*v.values(),)[0] for v in all_themes.values()}
        s_mem = qa_functions.qa_std.SMem()
        qa_prompts.InputPrompts.OptionPrompt(s_mem, set(ls), "Select a theme to uninstall")
        selection = s_mem.get()

        if selection in ['0', None]:
            self.enable_all_inputs()
            return

        chosen_theme: Theme = ls[cast(str, selection)]
        chosen_theme_file = qa_functions.qa_custom.File(chosen_theme.theme_file_path)

        if os.path.isfile(chosen_theme_file.file_path):
            try:
                raw = qa_functions.OpenFile.load_file(chosen_theme_file, qa_functions.OpenFunctionArgs(bytes))
                _, r2 = cast(Tuple[bytes, str], qa_files.load_file(FileType.QA_THEME, raw))
                theme_json = TDB_to_DICT(ReadAsTDB(raw, chosen_theme_file.file_path), True)
                os.remove(chosen_theme_file.file_path)

                theme_json['file_info']['avail_themes']['num_themes'] -= 1
                theme_json.pop(chosen_theme.theme_code)
                theme_json['file_info']['avail_themes'].pop(
                    [*theme_json['file_info']['avail_themes'].keys()][
                        [*theme_json['file_info']['avail_themes'].values()].index(chosen_theme.theme_code)
                    ]
                )

                fn = chosen_theme_file.file_name

                ok = fn not in (qa_functions.Files.ThemePrefFile, qa_functions.Files.ThemeCustomFile)
                ok &= 'file_info' in theme_json
                ok &= 'avail_themes' in theme_json['file_info']
                ok &= 'num_themes' in theme_json['file_info']['avail_themes']
                ok &= len(theme_json['file_info']['avail_themes']) == theme_json['file_info']['avail_themes']['num_themes'] + 1
                ok &= theme_json['file_info']['avail_themes']['num_themes'] > 0

                if ok:
                    nt = json.dumps(theme_json, indent=4)
                    prp = qa_files.generate_file(FileType.QA_THEME, nt)
                    qa_functions.SaveFile.secure(chosen_theme_file, prp, qa_functions.SaveFunctionArgs(False, save_data_type=bytes))

                qa_prompts.MessagePrompts.show_info(
                    qa_prompts.InfoPacket(f'Successfully uninstalled theme "{selection}"')
                )

            except Exception as E:
                sys.stderr.write(f"{traceback.format_exc()}\n")
                os.remove(chosen_theme_file.file_path)

        self.update_theme_selector_options()
        self.enable_all_inputs()

    def disable_all_inputs(self) -> None:
        self.install_new_button.config(state=tk.DISABLED)
        self.online_theme_button.config(state=tk.DISABLED)
        self.theme_selector_dropdown.config(state=tk.DISABLED)
        self.theme_uninstall_button.config(state=tk.DISABLED)
        self.showcase_bg.config(state=tk.DISABLED)
        self.showcase_fg.config(state=tk.DISABLED)
        self.showcase_accent.config(state=tk.DISABLED)
        self.showcase_gray.config(state=tk.DISABLED)
        self.showcase_error.config(state=tk.DISABLED)
        self.showcase_warning.config(state=tk.DISABLED)
        self.showcase_okay.config(state=tk.DISABLED)
        self.export_theme_button.config(state=tk.DISABLED)
        self.save_theme_button.config(state=tk.DISABLED)
        self.showcase_border_color.config(state=tk.DISABLED)

    def enable_all_inputs(self) -> None:
        self.install_new_button.config(state=tk.NORMAL)
        self.online_theme_button.config(state=tk.NORMAL)
        self.theme_selector_dropdown.config(state=tk.NORMAL)
        self.theme_uninstall_button.config(state=tk.NORMAL)
        self.showcase_bg.config(state=tk.NORMAL)
        self.showcase_fg.config(state=tk.NORMAL)
        self.showcase_accent.config(state=tk.NORMAL)
        self.showcase_gray.config(state=tk.NORMAL)
        self.showcase_error.config(state=tk.NORMAL)
        self.showcase_warning.config(state=tk.NORMAL)
        self.showcase_okay.config(state=tk.NORMAL)
        self.export_theme_button.config(state=tk.NORMAL)
        self.save_theme_button.config(state=tk.NORMAL)
        self.showcase_border_color.config(state=tk.NORMAL)
        self.update_ui()

    def export_theme(self) -> None:
        self.disable_all_inputs()
        saved = self.save_custom_theme(True, True)

        if saved:
            new_file_name = filedialog.asksaveasfilename(defaultextension='.qaTheme', filetypes=(('Quizzing App Theme', 'qaTheme'), ))
            if not isinstance(new_file_name, str):
                self.enable_all_inputs()
                return
            
            elif not len(new_file_name) > 0:
                self.enable_all_inputs()
                return

            new_file_name = new_file_name.replace('/', '\\')

            try:
                s_mem = qa_functions.qa_std.SMem()
                sep = ">>%QuizzingApp.ICManager.sep1%2>>"

                qa_prompts.InputPrompts.DEntryPrompt(s_mem, sep, ['File Display Name', 'Theme Display Name'])
                raw = s_mem.get()
                assert isinstance(raw, str)
                if raw.strip() == '0' or sep not in raw:
                    self.enable_all_inputs()
                    return

                fdp, tdn = raw.split(sep)
                self.load_theme()           # "Save" sets the custom theme as the default theme; use it.
                ct = clone_theme(self.theme)

                fdp_tokens, fdp_list = fdp.split(' '), []
                for tok in fdp_tokens:
                    fdp_list.append(f"{tok[0].upper()}" + f"{tok[1::].lower() if len(tok) > 1 else ''}")
                fdp_clean = ' '.join(fdp_list)
                tdp_tokens, tdp_clean_list = tdn.split(' '), []
                for tok in tdp_tokens:
                    tdp_clean_list.append(f"{tok[0].upper()}" + f"{tok[1::].lower() if len(tok) > 1 else ''}")
                tdp_clean_str = ' '.join(i for i in tdp_clean_list)
                del tdp_clean_list

                ct.theme_file_display_name = fdp_clean
                ct.theme_display_name = tdp_clean_str
                ct.theme_file_name = f"QuizzingApp.Community.{fdp_clean.replace(' ', '')}"
                ct.theme_code = f"Themes.Custom.{tdp_clean_str.replace(' ', '')}"
                ct.theme_file_path = new_file_name

                file_data = GenThemeFile(
                    new_file_name, ct.theme_file_name,
                    ct.theme_file_display_name, qa_functions.qa_info.App.version,
                    qa_functions.qa_info.App.build_id, {ct.theme_code: ct}
                )[1]

                file_bytes = qa_files.generate_file(FileType.QA_THEME, file_data)
                file = qa_functions.File(new_file_name)
                assert qa_functions.SaveFile.secure(file, file_bytes, qa_functions.SaveFunctionArgs(False, save_data_type=bytes)), "SaveError"

                nf = cast(List[str], self.install_new_theme((new_file_name,)))[0]
                qa_functions.qa_theme_loader.set_pref(nf, ct.theme_code, f'{ct.theme_file_display_name}: {ct.theme_display_name}')

                qa_prompts.MessagePrompts.show_info(
                    qa_prompts.InfoPacket(
                        f"Your theme was successfully saved and installed; it's called '{ct.theme_file_display_name}: {ct.theme_display_name}' and it has already been selected for you! This theme is now available for use throughout the Quizzing Application Suite. At any time, you may uninstall this theme like any other installed theme.",
                        title="Congratulations!"
                    )
                )

            except Exception as E:
                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket(
f"""Failed to export your theme;
Error: {str(E)}
Error Code: {hashlib.md5(str(E).encode()).hexdigest()}

Technical Information:
{traceback.format_exc()}      
"""
                    )
                )

        self.enable_all_inputs()
        return

    def on_prev_click(self, tp: str, exs: ThemeUpdateVars) -> None:
        self.disable_all_inputs()

        if tp == 'color':
            new_color = colorchooser.askcolor(cast(qa_functions.HexColor, self.theme_update_map[exs]).color)
            if None in new_color:
                self.enable_all_inputs()
                return

            assert isinstance(new_color[1], str)
            self.preview_change(exs, qa_functions.HexColor((new_color[1])))

        self.enable_all_inputs()

    def onBGClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.BG)

    def onFGClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.FG)

    def onAccentClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.ACCENT)

    def onErrorClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.ERROR)

    def onOkayClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.OKAY)

    def onWarningClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.WARNING)

    def onGrayClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.GRAY)

    def onBCClick(self) -> None:
        self.on_prev_click('color', ThemeUpdateVars.BORDER_COLOR)

    def reset_theme(self) -> None:
        self.rst_theme = True
        self.update_ui()

    def save_custom_theme(self, internal_call: bool = False, _bypass_changes_check: bool = False) -> bool:
        self.disable_all_inputs()
        pr_theme_full = qa_functions.LoadTheme.auto_load_pref_theme()
        pr_theme = gen_cmp_theme_dict(pr_theme_full)
        cr_theme = gen_cmp_theme_dict(self.theme)

        if pr_theme == cr_theme and not _bypass_changes_check:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('No changes made to theme'))
            self.enable_all_inputs()
            return False

        nt = {
            'display_name': 'Custom Theme',
            'background': self.theme.background.color,
            'foreground': self.theme.foreground.color,
            'accent': self.theme.accent.color,
            'error': self.theme.error.color,
            'warning': self.theme.warning.color,
            'ok': self.theme.okay.color,
            'gray': self.theme.gray.color,
            'font': {
                'title_font_face': self.theme.title_font_face,
                'font_face': self.theme.font_face,
                'alt_font_face': self.theme.font_alt_face,
                'size_small': self.theme.font_small_size,
                'size_main': self.theme.font_main_size,
                'size_subtitle': self.theme.font_large_size,
                'size_title': self.theme.font_title_size,
                'size_xl_title': self.theme.font_xl_title_size
            },
            'border': {
                'size': self.theme.border_size,
                'colour': self.theme.border_color.color
            }
        }

        passed, failures, warnings = \
            cast(Tuple[bool, List[str], List[str]], qa_functions.TestTheme.check_theme('UserGen', nt, True))

        if not passed:
            string = f"In the following message, an \"AA Contrast\" error means that there is insufficient contrast between the state color and the background color.\n\nCouldn't save your theme as it failed {len(failures)} checks:\n\t*%s\n\nTo reset the theme, click 'Reset Theme'" % "\n\t*".join(failure for failure in failures)
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(string))
            self.enable_all_inputs()
            return False

        elif len(warnings) > 0:
            string = f"In the following message, an \"AAA Contrast\" error means that the contrast between the state color and the background color is merely SATISFACTORY.\n\nYour theme passed the basic tests, but raised warning(s) on {len(warnings)} checks:\n\t*%s" % "\n\t*".join(warning for warning in warnings)
            qa_prompts.MessagePrompts.show_warning(qa_prompts.InfoPacket(string))

        try:
            file_data = {
                'file_info': {
                    'name': 'QuizzingApp.SystemReserved.User.Custom',
                    'display_name': 'User Generated',
                    'avail_themes': {
                        'num_themes': 1,
                        'ugen_cs': 'User.Custom.Theme'
                    }
                },
                'User.Custom.Theme': {
                    **nt
                }
            }

            file_bytes = qa_files.generate_file(FileType.QA_THEME, json.dumps(file_data, indent=4))
            file = qa_functions.File(f"{qa_functions.App.appdata_dir}\\{qa_functions.Files.ad_theme_folder}\\{qa_functions.Files.ThemeCustomFile}".replace('/', '\\'))
            assert qa_functions.SaveFile.secure(file, file_bytes, qa_functions.SaveFunctionArgs(False, save_data_type=bytes)), "SaveError"

        except Exception as E:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(
f"""Failed to save your theme;
Error: {str(E)}
Error Code: {hashlib.md5(str(E).encode()).hexdigest()}

Technical Information:
{traceback.format_exc()}      
"""
                )
            )
            self.enable_all_inputs()
            return False

        # Set as preferred (=> current) theme
        qa_functions.qa_theme_loader.set_pref(
            f"{qa_functions.App.appdata_dir}\\{qa_functions.Files.ad_theme_folder}\\{qa_functions.Files.ThemeCustomFile}".replace('/', '\\'),
            'User.Custom.Theme',
            'User Generated: Custom Theme'
        )

        if not internal_call:
            qa_prompts.MessagePrompts.show_info(
                qa_prompts.InfoPacket(
                    "Your theme was successfully saved; it's called 'User Generated: Custom Theme' and it has already been selected for you! This theme is now available for use throughout the Quizzing Application Suite. At any time, you may uninstall this theme like any other installed theme. To share your theme, click on 'Export.'",
                    title="Congratulations!"
                )
            )

        self.enable_all_inputs()
        return True

    def preview_change(self, change_key: ThemeUpdateVars, change: Union[qa_functions.HexColor, int, float, str]) -> None:
        self.disable_all_inputs()
        TUV = ThemeUpdateVars

        new_theme = clone_theme(self.theme)

        if isinstance(change, qa_functions.HexColor):
            if change_key == TUV.BG:
                new_theme.background = change
            elif change_key == TUV.FG:
                new_theme.foreground = change
            elif change_key == TUV.ACCENT:
                new_theme.accent = change
            elif change_key == TUV.GRAY:
                new_theme.gray = change
            elif change_key == TUV.ERROR:
                new_theme.error = change
            elif change_key == TUV.WARNING:
                new_theme.warning = change
            elif change_key == TUV.OKAY:
                new_theme.okay = change
            elif change_key == TUV.BORDER_COLOR:
                new_theme.border_color = change
            else:
                raise UnexpectedEdgeCase('0xa981')

        elif type(change) in (int, float):
            if change_key == TUV.FONT_SIZE_SMALL:
                new_theme.font_small_size = cast(Union[float, int], change)
            elif change_key == TUV.FONT_SIZE_MAIN:
                new_theme.font_main_size = cast(Union[float, int], change)
            elif change_key == TUV.FONT_SIZE_LARGE:
                new_theme.font_large_size = cast(Union[float, int], change)
            elif change_key == TUV.FONT_SIZE_TITLE:
                new_theme.font_title_size = cast(Union[float, int], change)
            elif change_key == TUV.FONT_SIZE_XL_TITLE:
                new_theme.font_xl_title_size = cast(Union[float, int], change)
            elif change_key == TUV.BORDER_SIZE:
                new_theme.border_size = cast(Union[float, int], change)
            else:
                raise UnexpectedEdgeCase('0xa982')

        elif isinstance(change, str):
            if change_key == TUV.DEFAULT_FONT_FACE:
                new_theme.font_face = change
            elif change_key == TUV.ALT_FONT_FACE:
                new_theme.font_alt_face = change
            elif change_key == TUV.TITLE_FONT_FACE:
                new_theme.title_font_face = change
            else:
                raise UnexpectedEdgeCase('0xa983')

        else:
            raise UnexpectedEdgeCase('0xa980')

        if gen_cmp_theme_dict(new_theme) != gen_cmp_theme_dict(self.theme):
            self.update_ui(new_theme)
        else:
            sys.stderr.write("no changes in theme\n")

        self.enable_all_inputs()

    def font_picker(self) -> Union[None, str]:
        self.disable_all_inputs()

        s_mem = qa_functions.SMem()
        qa_prompts.InputPrompts.OptionPrompt(s_mem, sorted({*font.families()}, key=str.lower), "Pick a font")  # type: ignore
        self.enable_all_inputs()

        raw = s_mem.get()
        assert isinstance(raw, str)
        return None if raw.strip() == '0' else raw

    def title_font(self) -> None:
        new_font = self.font_picker()
        if isinstance(new_font, str):
            self.preview_change(ThemeUpdateVars.TITLE_FONT_FACE, new_font)

    def prim_font(self) -> None:
        new_font = self.font_picker()
        if isinstance(new_font, str):
            self.preview_change(ThemeUpdateVars.DEFAULT_FONT_FACE, new_font)

    def alt_font(self) -> None:
        new_font = self.font_picker()
        if isinstance(new_font, str):
            self.preview_change(ThemeUpdateVars.ALT_FONT_FACE, new_font)

    def font_size_picker(self, current: Union[int, float], var: ThemeUpdateVars, name: str) -> None:
        self.disable_all_inputs()

        s_mem = qa_functions.SMem()
        qa_prompts.InputPrompts.SEntryPrompt(s_mem, f'New size for \'{name}\':', str(current).strip())
        self.enable_all_inputs()

        raw = s_mem.get()
        assert isinstance(raw, str)

        if raw.strip() == str(current).strip():
            return None
        else:
            try:
                f = int(raw)
                if var == ThemeUpdateVars.BORDER_SIZE:
                    assert f <= 10, "Border size must be smaller than 10"
                else:
                    assert 60 >= f >= 3, "Font size must be between size 3 and size 60"
                self.preview_change(var, f)
            except Exception as E:
                qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(f'Invalid font size provided: {E}'))

    def font_size_small(self) -> None:
        self.font_size_picker(self.theme.font_small_size, ThemeUpdateVars.FONT_SIZE_SMALL, 'small')

    def font_size_medium(self) -> None:
        self.font_size_picker(self.theme.font_main_size, ThemeUpdateVars.FONT_SIZE_MAIN, 'primary')

    def font_size_large(self) -> None:
        self.font_size_picker(self.theme.font_large_size, ThemeUpdateVars.FONT_SIZE_LARGE, 'large')

    def font_size_title(self) -> None:
        self.font_size_picker(self.theme.font_title_size, ThemeUpdateVars.FONT_SIZE_TITLE, 'title')

    def font_size_xl(self) -> None:
        self.font_size_picker(self.theme.font_xl_title_size, ThemeUpdateVars.FONT_SIZE_XL_TITLE, 'XL')

    def border_size(self) -> None:
        self.font_size_picker(self.theme.border_size, ThemeUpdateVars.BORDER_SIZE, 'border size')

    def __del__(self) -> None:
        self.thread.join(self, 0)


def clone_theme(theme_data: qa_functions.Theme) -> qa_functions.Theme:
    return qa_functions.Theme(
        theme_data.theme_file_name, theme_data.theme_file_display_name, theme_data.theme_display_name, theme_data.theme_code,
        theme_file_path=theme_data.theme_file_path,
        background=theme_data.background, foreground=theme_data.foreground, accent=theme_data.accent,
        gray=theme_data.gray, error=theme_data.error, warning=theme_data.warning, okay=theme_data.okay,
        font_face=theme_data.font_face, font_alt_face=theme_data.font_alt_face, font_small_size=theme_data.font_small_size,
        font_main_size=theme_data.font_main_size, font_large_size=theme_data.font_large_size, font_title_size=theme_data.font_title_size,
        font_xl_title_size=theme_data.font_xl_title_size, border_size=theme_data.border_size, border_color=theme_data.border_color,
        title_font_face=theme_data.title_font_face
    )


def gen_cmp_theme_dict(theme_data: Theme) -> Dict[str, Union[int, float, str]]:
    return {
        'background': theme_data.background.color.upper(),
        'foreground': theme_data.foreground.color.upper(),
        'accent': theme_data.accent.color.upper(),
        'error': theme_data.error.color.upper(),
        'warning': theme_data.warning.color.upper(),
        'okay': theme_data.okay.color.upper(),
        'gray': theme_data.gray.color.upper(),
        'fft': theme_data.title_font_face.upper(),
        'ff': theme_data.font_face.upper(),
        'faf': theme_data.font_alt_face.upper(),
        'fss': theme_data.font_small_size,
        'fms': theme_data.font_main_size,
        'fls': theme_data.font_large_size,
        'fts': theme_data.font_title_size,
        'fxlts': theme_data.font_xl_title_size,
        'bs': theme_data.border_size,
        'bc': theme_data.border_color.color.upper()
    }


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

    data = f"{AppLogColors.THEMING_UTILITY}{AppLogColors.EXTRA}[THEMING_UTILITY]{ANSI.RESET} {data}"

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


def transfer_log_info(script: Any) -> None:
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, DEBUG_NORM, DEBUG_DEV_FLAG

    script.LOGGER_AVAIL = LOGGER_AVAIL  # type: ignore
    script.LOGGER_FUNC = LOGGER_FUNC   # type: ignore
    script.LOGGING_FILE_NAME = LOGGING_FILE_NAME    # type: ignore
    script.DEBUG_NORM = DEBUG_NORM  # type: ignore
    script.DEBUG_DEV_FLAG = DEBUG_DEV_FLAG  # type: ignore
