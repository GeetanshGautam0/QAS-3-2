import sys, qa_functions, qa_files, os, traceback, PIL, json, copy, subprocess, tkinter as tk, re, hashlib, random
from . import qa_prompts
from .qa_prompts import gsuid, configure_scrollbar_style
from qa_functions.qa_enum import ThemeUpdateCommands, ThemeUpdateVars, LoggingLevel, FileType
from qa_functions.qa_std import ANSI, AppLogColors
from qa_functions.qa_custom import HexColor
from threading import Thread
from tkinter import ttk, filedialog
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from dataclasses import dataclass
from enum import Enum
from ctypes import windll
from typing import *

script_name = "APP_AT"
APP_TITLE = "Quizzing Application | Admin Tools"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
DEBUG_DEV_FLAG = False
MAX = 50
_Fs = True


class Levels(Enum):
    (NORMAL, OKAY, WARNING, ERROR) = range(4)


@dataclass
class Message:
    LVL: Levels
    MSG: str


class _UI(Thread):
    def __init__(self, root: Union[tk.Toplevel, tk.Tk], ic: Any, ds: Any, **kwargs: Optional[Any]) -> None:
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        (self.SELECT_PAGE, self.EDIT_PAGE, self.CREATE_PAGE) = range(3)

        self.dsb, self.busy = False, False

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs
        self.root.withdraw()

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        wd_w = 1000 if 1000 <= self.screen_dim[0] else self.screen_dim[0]
        wd_h = 900 if 900 <= self.screen_dim[1] else self.screen_dim[1]
        self.window_size = [wd_w, wd_h]
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
        ]

        self.window_size_2 = [670, 475]
        self.screen_pos_2 = [
            int(self.screen_dim[0] / 2 - self.window_size_2[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size_2[1] / 2)
        ]

        self.theme: qa_functions.qa_custom.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]] = {}

        self.padX = 20
        self.padY = 10

        self.gi_cl = True
        self._job: Union[None, str] = None

        self.load_theme()
        tmp = tk.Label(self.root)
        self.update_requests: Dict[str, List[Any]] = {}
        self.late_update_requests: Dict[tk.Widget, List[Any]] = {}
        self.data: Dict[Any, Any] = {}

        self.img_path = qa_functions.Files.AT_png
        self.img_size = (75, 75)
        self.svgs: Dict[str, Any] = {
            'arrow_left': {'accent': '', 'normal': ''},
            'arrow_right': {'accent': '', 'normal': ''},
            'settings_cog': {'accent': '', 'normal': ''},
            'question': {'accent': '', 'normal': ''},
            'checkmark': {'accent': '', 'normal': ''},
            'arrow_left_large': {'accent': '', 'normal': ''},
            'arrow_right_large': {'accent': '', 'normal': ''},
            'settings_cog_large': {'accent': '', 'normal': ''},
            'question_large': {'accent': '', 'normal': ''},
            'checkmark_large': {'accent': '', 'normal': ''},
            'admt': ''
        }
        self.checkmark_src = "./.src/.icons/.progress/checkmark.svg"
        self.cog_src = './.src/.icons/.misc/settings.svg'
        self.arrow_left_src = './.src/.icons/.misc/left_arrow.svg'
        self.question_src = './.src/.icons/.misc/question.svg'
        self.arrow_right_src = './.src/.icons/.misc/right_arrow.svg'
        self.svg_tmp = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup".replace('/', '\\')
        self.load_png()

        self.ttk_theme = cast(str, self.kwargs['ttk_theme'])
        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Admin')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size, 'My')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

        self.page_index = self.SELECT_PAGE
        self.prev_page = self.page_index

        self.title_box = tk.Frame(self.root)
        self.title_label = tk.Label(self.title_box)
        self.title_icon = tk.Label(self.title_box)

        self.menu = tk.Menu(self.root, tearoff=False)
        self.context_menu = tk.Menu(self.root, tearoff=False)
        self.root['menu'] = self.menu
        self.menu_file = tk.Menu(self.menu, tearoff=False)

        self.select_frame = tk.Frame(self.root)
        self.create_frame = tk.Frame(self.root)
        self.db_frame = tk.Frame(self.root)

        self.create_inp1_var = tk.StringVar()
        self.create_inp2_var = tk.StringVar()

        self.select_lbl = tk.Label(self.select_frame, text="Select a database to edit")
        self.select_open = ttk.Button(self.select_frame, text="Open Existing DB", command=self.open_entry)
        self.select_new = ttk.Button(self.select_frame, text="Create New DB", command=self.new_entry)
        self.select_scores = ttk.Button(self.select_frame, text="Score Manager")

        self.create_title = tk.Label(self.create_frame, text="Create New Database")
        self.create_inp1_cont = tk.LabelFrame(self.create_frame, text="Database Name")
        self.create_inp1 = ttk.Entry(self.create_inp1_cont, textvariable=self.create_inp1_var)

        self.create_config_frame = tk.LabelFrame(self.create_frame, text="Database Configuration")
        self.create_inp2_cont = tk.LabelFrame(self.create_config_frame, text="")
        self.create_inp2 = ttk.Entry(self.create_inp2_cont, textvariable=self.create_inp2_var)
        self.create_add_psw_sel = ttk.Button(self.create_config_frame, text="NO password", command=self.psw_sel_click)

        self.create_btn_frame = tk.Frame(self.create_frame)
        self.create_cancel = ttk.Button(self.create_btn_frame, text="Cancel", command=lambda: self.proc_exit(None))
        self.create_create = ttk.Button(self.create_btn_frame, text="Create", command=self.new_main)

        self.general_info_label = tk.Label(self.root, text="")

        # Main elements (Edit page)
        self.edit_sidebar = tk.Frame(self.db_frame)
        self.edit_pic = tk.Label(self.edit_sidebar)
        self.edit_db_name = tk.Label(self.edit_sidebar)
        self.edit_btn_panel = tk.Frame(self.edit_sidebar)
        self.edit_sep = ttk.Separator(self.db_frame)

        # Menu Buttons (Edit page)
        self.edit_configuration_btn = ttk.Button(self.edit_btn_panel, text='Configuration', command=self.edit_configuration)
        self.edit_questions_btn = ttk.Button(self.edit_btn_panel, text='Questions', command=self.edit_questions)

        # Configuration page:: Main Elements (Edit page)
        self.edit_configuration_master_frame = tk.Frame(self.db_frame)
        self.edit_configuration_canvas = tk.Canvas(self.edit_configuration_master_frame)
        self.edit_configuration_vsb = ttk.Scrollbar(self.edit_configuration_master_frame, style='MyAdmin.TScrollbar')
        self.edit_configuration_frame = tk.Frame(self.edit_configuration_canvas)

        # Configuration page:: Elements (Edit page)
        self.edit_configuration_title = tk.Label(self.edit_configuration_frame)

        self.edit_password_container = tk.LabelFrame(self.edit_configuration_frame)
        self.edit_db_psw_container = tk.LabelFrame(self.edit_password_container)
        self.edit_qz_psw_container = tk.LabelFrame(self.edit_password_container)

        self.edit_db_psw_lbl = tk.Label(self.edit_db_psw_container)
        self.edit_db_psw_button = ttk.Button(self.edit_db_psw_container, command=self.db_psw_toggle)
        self.edit_db_psw_reset_btn = ttk.Button(self.edit_db_psw_container, command=self.db_psw_change)

        self.edit_qz_psw_lbl = tk.Label(self.edit_qz_psw_container)
        self.edit_qz_psw_button = ttk.Button(self.edit_qz_psw_container, command=self.qz_psw_toggle)
        self.edit_qz_psw_reset_btn = ttk.Button(self.edit_qz_psw_container, command=self.qz_psw_change)

        self.edit_configuration_save = ttk.Button(self.edit_configuration_frame, text="Save Changes", command=self.save_db)
        self.sb_expand_shrink = ttk.Button(self.edit_sidebar, command=self.expand_click)

        self.edit_config_main_cont = tk.LabelFrame(self.edit_configuration_frame, text='Quiz Configuration')
        self.edit_config_acc_cont = tk.LabelFrame(self.edit_config_main_cont, text="Custom Quiz Configuration")
        self.edit_config_qz_dc = tk.LabelFrame(self.edit_config_main_cont, text="Quiz Distribution Configuration")
        self.edit_config_ddc_cont = tk.LabelFrame(self.edit_config_main_cont, text="Penalty Configuration")

        # Config :: ACC
        self.edit_config_acc_lbl = tk.Label(self.edit_config_acc_cont)
        self.edit_config_acc_btns = tk.Frame(self.edit_config_acc_cont)
        self.edit_config_acc_btn1 = ttk.Button(self.edit_config_acc_btns, command=self._acc_enable)
        self.edit_config_acc_btn2 = ttk.Button(self.edit_config_acc_btns, command=self._acc_disable)

        # Config :: POA
        self.edit_config_poa_lbl = tk.Label(self.edit_config_qz_dc)
        self.edit_config_poa_btns = tk.Frame(self.edit_config_qz_dc)
        self.edit_config_poa_btn1 = ttk.Button(self.edit_config_poa_btns, command=self._poa_part)
        self.edit_config_poa_btn2 = ttk.Button(self.edit_config_poa_btns, command=self._poa_all)

        # Config :: RQO
        self.edit_config_rqo_lbl = tk.Label(self.edit_config_qz_dc)
        self.edit_config_rqo_btns = tk.Frame(self.edit_config_qz_dc)
        self.edit_config_rqo_btn1 = ttk.Button(self.edit_config_rqo_btns, command=self._rqo_enable)
        self.edit_config_rqo_btn2 = ttk.Button(self.edit_config_rqo_btns, command=self._rqo_disable)

        # Config :: SSD
        self.edit_config_ssd_lbl = tk.Label(self.edit_config_qz_dc)
        self.edit_config_ssd_var = tk.StringVar()
        self.edit_config_ssd_field = ttk.Entry(self.edit_config_qz_dc, textvariable=self.edit_config_ssd_var)

        # Config :: DPI
        self.edit_config_dpi_lbl = tk.Label(self.edit_config_ddc_cont)
        self.edit_config_dpi_btns = tk.Frame(self.edit_config_ddc_cont)
        self.edit_config_dpi_btn1 = ttk.Button(self.edit_config_dpi_btns, command=self._dpi_enable)
        self.edit_config_dpi_btn2 = ttk.Button(self.edit_config_dpi_btns, command=self._dpi_disable)

        # Config :: A2D
        self.edit_config_dda_lbl = tk.Label(self.edit_config_ddc_cont)
        self.edit_config_dda_var = tk.StringVar()
        self.edit_config_dda_field = ttk.Entry(self.edit_config_ddc_cont, textvariable=self.edit_config_dda_var)

        self.start()
        self.root.mainloop()

    # -------------------
    # Frame Configurators
    # -------------------

    def configure_create_frame(self) -> None:
        self.create_title.config(justify=tk.LEFT, anchor=tk.W)
        self.create_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.create_inp1.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.create_inp1.config(style='My.TEntry')
        self.create_inp2.config(style='My.TEntry')
        self.create_inp1_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.create_add_psw_sel.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.create_inp2_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=(0, self.padY))
        self.create_config_frame.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.create_btn_frame.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
        self.create_cancel.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, ipady=self.padY / 2)
        self.create_create.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, ipady=self.padY / 2)

        self.update_requests['create_inp10'] = [
            self.create_inp1,
            ThemeUpdateCommands.FONT,
            [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN]
        ]
        self.update_requests['create_inp1_cont0'] = [
            self.create_inp1_cont,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda bg, fg, face, size: self.create_inp1_cont.config(bg=bg, fg=fg, font=(face, size), bd='0'),
                ThemeUpdateVars.BG, ThemeUpdateVars.GRAY,
                ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['create_inp20'] = [
            self.create_inp2,
            ThemeUpdateCommands.FONT,
            [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN]
        ]
        self.update_requests['create_inp2_cont0'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda bg, fg, face, size: self.create_inp2_cont.config(bg=bg, fg=fg, font=(face, size), bd='0'),
                ThemeUpdateVars.BG, ThemeUpdateVars.GRAY,
                ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['create_config_frame0'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda bg, fg, face, size: self.create_config_frame.config(bg=bg, fg=fg, font=(face, size), bd='0'),
                ThemeUpdateVars.BG, ThemeUpdateVars.GRAY,
                ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['create_btn_frame0'] = [self.create_btn_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.create_inp2_var.trace("w", self.inp2_edit)
        self.create_inp1_var.trace("w", self.inp1_edit)

    def configure_sel_frame(self) -> None:
        self.select_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.TOP)
        self.select_open.pack(fill=tk.X, expand=True, padx=self.padX, pady=(self.padY, 0), ipady=self.padY)
        self.select_new.pack(fill=tk.X, expand=True, padx=self.padX, ipady=self.padY)
        self.select_scores.pack(fill=tk.X, expand=False, padx=self.padX, pady=(0, self.padY), side=tk.BOTTOM, ipady=self.padY)

    def configure_edit_frame(self) -> None:
        global DEBUG_NORM

        # Layout
        self.edit_pic.pack(fill=tk.BOTH, expand=False, pady=self.padY * 2, padx=self.padX)
        self.edit_pic.config(text='Admin Tools', image=self.svgs['admt'], compound=tk.TOP)

        self.sb_expand_shrink.pack(fill=tk.X, expand=False, pady=(self.padY * 2, 0), side=tk.BOTTOM)

        self.edit_db_name.pack(fill=tk.X, expand=False, pady=self.padY, padx=self.padX, side=tk.BOTTOM)
        self.edit_btn_panel.pack(fill=tk.X, expand=False, pady=self.padY)

        self.edit_configuration_btn.pack(fill=tk.X, expand=True, ipady=self.padY / 2)
        self.edit_questions_btn.pack(fill=tk.X, expand=True, ipady=self.padY / 2)

        self.edit_sidebar.pack(fill=tk.Y, expand=False, side=tk.LEFT)
        self.edit_sep.pack(fill=tk.Y, expand=False, side=tk.LEFT, pady=(self.padY, 0))

        # Configuration Frame
        self.edit_configuration_vsb.pack(fill=tk.Y, expand=False, padx=(0, self.padX), pady=self.padY, side=tk.RIGHT)
        self.edit_configuration_canvas.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=self.padY)

        self.edit_configuration_title.config(text="Configuration Manager")
        self.edit_configuration_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY * 2, side=tk.TOP)

        self.edit_password_container.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
        self.edit_db_psw_container.pack(fill=tk.X, expand=True, padx=self.padX, pady=(self.padY, 0))
        self.edit_qz_psw_container.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
        self.edit_password_container.config(text="Security")
        self.edit_db_psw_container.config(text="Administrator Password")
        self.edit_qz_psw_container.config(text="Quiz Password")

        self.edit_db_psw_lbl.config(text="This password allows for the restriction of users who can edit this database.", anchor=tk.W, justify=tk.LEFT)
        self.edit_db_psw_lbl.pack(fill=tk.X, expand=False, pady=self.padY, side=tk.TOP)

        self.edit_db_psw_button.pack(fill=tk.X, expand=True, pady=self.padY, side=tk.LEFT)
        self.edit_db_psw_reset_btn.pack(fill=tk.X, expand=True, pady=self.padY, side=tk.RIGHT)

        self.edit_db_psw_button.config(text="")
        self.edit_db_psw_reset_btn.config(text="Reset Password")

        self.edit_qz_psw_lbl.config(text="This password allows for the restriction of users who can access the quiz.", anchor=tk.W, justify=tk.LEFT)
        self.edit_qz_psw_lbl.pack(fill=tk.X, expand=False, pady=self.padY, side=tk.TOP)

        self.edit_qz_psw_button.pack(fill=tk.X, expand=True, pady=self.padY, side=tk.LEFT)
        self.edit_qz_psw_reset_btn.pack(fill=tk.X, expand=True, pady=self.padY, side=tk.RIGHT)

        self.edit_qz_psw_button.config(text="")
        self.edit_qz_psw_reset_btn.config(text="Reset Password")

        self.edit_configuration_save.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY, ipady=self.padY / 2)

        self.edit_configuration_btn.config(compound=tk.LEFT, image=self.svgs['settings_cog_large']['normal'], style='LG.TButton')
        self.edit_questions_btn.config(compound=tk.LEFT, image=self.svgs['question_large']['normal'], style='LG.TButton')

        self.edit_config_main_cont.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_acc_cont.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_acc_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_config_acc_lbl.config(
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1,
            text="Though the default settings will remain the same as the ones below, if the following option is enabled, the user will be prompted to edit the ensuing settings themself prior to taking the quiz. Disabling this option will lock in the settings you choose."
        )

        self.edit_config_acc_btns.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_acc_btn1.pack(fill=tk.X, expand=True, ipady=self.padY/2, side=tk.LEFT)
        self.edit_config_acc_btn2.pack(fill=tk.X, expand=True, ipady=self.padY/2, side=tk.RIGHT)

        self.edit_config_qz_dc.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_poa_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_config_poa_lbl.config(
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1,
            text="\"Part or All\": Should the quiz taker be prompted with ALL the questions or a subset of the questions?"
        )

        self.edit_config_poa_btns.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_poa_btn1.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.LEFT)
        self.edit_config_poa_btn2.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.RIGHT)

        self.edit_config_ssd_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_config_ssd_lbl.config(
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1,
            text="\"Subsample Divisor\": (Applicable when \"Part or All\" is set to \"PART\") the divisor used to find the subsample of the questions.\n\nExample: If there are twenty questions, setting this number to 2 would yield ten questions for the quiz taker to be prompted with (sampled during quiz.)"
        )

        self.edit_config_ssd_field.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_ssd_field.config(style='MyLarge.TEntry')

        self.edit_config_rqo_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_config_rqo_lbl.config(
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1,
            text="\"Randomize Question Order\": Should the question order be randomized?"
        )

        self.edit_config_rqo_btns.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_rqo_btn1.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.LEFT)
        self.edit_config_rqo_btn2.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.RIGHT)

        self.edit_config_ddc_cont.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_dpi_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_config_dpi_lbl.config(
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1,
            text=f"\"Penalize Incorrect Responses\": Should points be subtracted when an incorrect response given?"
        )

        self.edit_config_dpi_btns.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_dpi_btn1.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.LEFT)
        self.edit_config_dpi_btn2.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.RIGHT)

        self.edit_config_dda_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_config_dda_lbl.config(
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1,
            text=f"\"Deduction Amount\": How many points should be deducted on incorrect responses?"
        )

        self.edit_config_dda_field.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
        self.edit_config_dda_field.config(style='MyLarge.TEntry')

        # Scrollbar setup
        self.edit_configuration_vsb.configure(command=self.edit_configuration_canvas.yview)
        self.edit_configuration_canvas.configure(yscrollcommand=self.edit_configuration_vsb.set)

        self.edit_configuration_canvas.create_window(
            0, 0,
            window=self.edit_configuration_frame,
            anchor="nw",
            tags="self.edit_configuration_frame"
        )

        self.edit_configuration_frame.update()
        self.edit_configuration_frame.bind("<Configure>", self.onFrameConfig)
        self.edit_configuration_canvas.bind("<MouseWheel>", self._on_mousewheel)

        COM = ThemeUpdateCommands
        VAR = ThemeUpdateVars

        # Logical Requests
        for el, name in (
                (self.edit_config_acc_lbl, 'acc'),
                (self.edit_config_poa_lbl, 'poa'),
                (self.edit_config_rqo_lbl, 'rqo'),
                (self.edit_config_ssd_lbl, 'ssd'),
                (self.edit_config_dpi_lbl, 'dpi'),
                (self.edit_config_dda_lbl, 'dda')
        ):
            self._config_lbl_wrl(el, name)

        self.edit_config_ssd_var.set('')
        self.edit_config_dda_var.set('')
        self.edit_config_ssd_var.trace('w', self._ssd_inp)
        self.edit_config_dda_var.trace('w', self._dda_inp)

        # Theme Requests
        self.label_formatter(self.edit_db_name, size=VAR.FONT_SIZE_SMALL, uid='edit_db_name')
        self.update_requests['edit_btn_panel0'] = [self.edit_btn_panel, COM.BG, [VAR.BG]]
        self.update_requests['edit_sidebar0'] = [self.edit_sidebar, COM.BG, [VAR.BG]]
        self.update_requests['edit_configuration_master_frame0'] = [self.edit_configuration_master_frame, COM.BG, [VAR.BG]]
        self.update_requests['edit_configuration_frame0'] = [self.edit_configuration_frame, COM.BG, [VAR.BG]]
        self.update_requests['edit_configuration_canvas0'] = [self.edit_configuration_canvas, COM.BG, [VAR.BG]]
        self.update_requests['edit_configuration_canvas1'] = [
            None, COM.CUSTOM,
            [lambda *args: self.edit_configuration_canvas.config(bd=0, highlightthickness=0)]
        ]
        self.update_requests['edit_password_container0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_password_container.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5]
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_db_psw_container0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_db_psw_container.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_qz_psw_container0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_qz_psw_container.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_config_acc_cont0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_acc_cont.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_config_qz_dc0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_qz_dc.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_config_ddc_cont0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_ddc_cont.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_config_main_cont0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_main_cont.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3]), highlightthickness=args[4],
                    highlightbackground=args[5]
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests['edit_db_psw_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_db_psw_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])  # , font=args[2:3]
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_qz_psw_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_qz_psw_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_config_acc_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_acc_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_config_poa_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_poa_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_config_rqo_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_rqo_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_config_ssd_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_ssd_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_config_dpi_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_dpi_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_config_dda_lbl0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_dda_lbl.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests['edit_pic0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_pic.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_LARGE
            ]
        ]
        self.update_requests['edit_configuration_title0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_configuration_title.config(
                    bg=args[0], fg=args[1], font=(args[2], args[3])
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_TITLE
            ]
        ]
        self.update_requests['edit_config_acc_btns0'] = [
            self.edit_config_acc_btns,
            COM.BG,
            [VAR.BG]
        ]
        self.update_requests['edit_config_poa_btns0'] = [
            self.edit_config_poa_btns,
            COM.BG,
            [VAR.BG]
        ]
        self.update_requests['edit_config_dpi_btns0'] = [
            self.edit_config_dpi_btns,
            COM.BG,
            [VAR.BG]
        ]
        self.update_requests['edit_config_rqo_btns0'] = [
            self.edit_config_rqo_btns,
            COM.BG,
            [VAR.BG]
        ]
        self.update_requests['edit_config_dda_field<font>'] = [
            self.edit_config_dda_field,
            COM.FONT,
            [VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_MAIN]
        ]
        self.update_requests['edit_config_ssd_field<font>'] = [
            self.edit_config_ssd_field,
            COM.FONT,
            [VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_MAIN]
        ]
        self.update_requests['UpRule[d]::<db_psw_toggle>0'] = [None, COM.CUSTOM, [lambda: self.db_psw_toggle(nrst=True)]]
        self.update_requests['UpRule[d]::<qz_psw_toggle>0'] = [None, COM.CUSTOM, [lambda: self.qz_psw_toggle(nrst=True)]]

        del COM, VAR

    def configure_edit_controls(self) -> None:
        d = copy.deepcopy(self.data[self.EDIT_PAGE]['db']['CONFIGURATION'])
        if d['acc']:
            self.edit_config_acc_btn1.config(style='Active.TButton', state=tk.DISABLED, text='Enabled')
            self.edit_config_acc_btn2.config(style='TButton', state=tk.NORMAL, text='Disable')
        else:
            self.edit_config_acc_btn2.config(style='Active.TButton', state=tk.DISABLED, text='Disabled')
            self.edit_config_acc_btn1.config(style='TButton', state=tk.NORMAL, text='Enable')

        if d['poa'] == 'p':
            self.edit_config_poa_btn1.config(style='Active.TButton', state=tk.DISABLED, text='Part')
            self.edit_config_poa_btn2.config(style='TButton', state=tk.NORMAL, text='All')
            self.edit_config_ssd_field.config(state=tk.NORMAL)
            self.edit_config_ssd_var.set(str(d['ssd']))
        elif d['poa'] == 'a':
            self.edit_config_poa_btn2.config(style='Active.TButton', state=tk.DISABLED, text='All')
            self.edit_config_poa_btn1.config(style='TButton', state=tk.NORMAL, text='Part')
            self.edit_config_ssd_field.config(state=tk.DISABLED)
            self.edit_config_ssd_var.set('Set POA to "All" to edit.')

        else:
            log(LoggingLevel.ERROR, '[CONFIG_EDIT_CONTROLS]: <POA> - Unexpected edge case [0]')
            raise qa_functions.UnexpectedEdgeCase('Configuration: <POA> - expected value to be `p` or `a`.')

        if d['rqo']:
            self.edit_config_rqo_btn1.config(style='Active.TButton', state=tk.DISABLED, text='Enabled')
            self.edit_config_rqo_btn2.config(style='TButton', state=tk.NORMAL, text='Disable')
        else:
            self.edit_config_rqo_btn2.config(style='Active.TButton', state=tk.DISABLED, text='Disabled')
            self.edit_config_rqo_btn1.config(style='TButton', state=tk.NORMAL, text='Enable')

        if d['dpi']:
            self.edit_config_dpi_btn1.config(style='Active.TButton', state=tk.DISABLED, text='Enabled')
            self.edit_config_dpi_btn2.config(style='TButton', state=tk.NORMAL, text='Disable')
            self.edit_config_dda_field.config(state=tk.NORMAL)
            self.edit_config_dda_var.set(str(d['a2d']))
        else:
            self.edit_config_dpi_btn2.config(style='Active.TButton', state=tk.DISABLED, text='Disabled')
            self.edit_config_dpi_btn1.config(style='TButton', state=tk.NORMAL, text='Enable')
            self.edit_config_dda_field.config(state=tk.DISABLED)
            self.edit_config_dda_var.set('Set "Penalize Errors" to "Enabled" to edit.')

        del d
        return

    # -----------------
    # LL Event Handlers
    # -----------------

    def _on_mousewheel(self, event: Any) -> None:
        """
        Straight out of stackoverflow
        Article: https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        Change: added "int" around the first arg
        """
        if self.page_index != self.EDIT_PAGE:
            return

        self.edit_configuration_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def onFrameConfig(self, _: Any) -> None:
        self.edit_configuration_canvas.configure(scrollregion=self.edit_configuration_canvas.bbox("all"))

    # ------------
    # GEO Handlers
    # ------------

    def geo_large(self) -> None:
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")

    def geo_small(self) -> None:
        self.root.geometry(f"{self.window_size_2[0]}x{self.window_size_2[1]}+{self.screen_pos_2[0]}+{self.screen_pos_2[1]}")

    # -----
    # SETUP
    # -----

    def close(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        sys.stdout.write("at - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.quit()

    def run(self) -> None:
        global DEBUG_NORM, APP_TITLE
        qa_prompts.DEBUG_NORM = DEBUG_NORM
        qa_prompts.TTK_THEME = self.ttk_theme

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.title(APP_TITLE)
        self.root.iconbitmap(qa_functions.Files.AT_ico)

        self.geo_small()

        self.general_info_label.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.BOTTOM, pady=(0, self.padY))

        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.title_label.config(text="Administrator Tools", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=self.svgs['admt'])
        self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX / 8), pady=self.padY, side=tk.LEFT)

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT, uid='title_label')
        self.label_formatter(self.title_icon, uid='title_icon')

        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        self.update_requests['root0'] = [self.root, TUC.BG, [TUV.BG]]
        self.update_requests['title_box0'] = [self.title_box, TUC.BG, [TUV.BG]]

        self.menu.add_cascade(menu=self.menu_file, label='Database')
        self.menu_file.add_command(label='Create New Database', command=self.new_entry)
        self.menu_file.add_command(label='Open Database', command=self.open_entry)
        self.menu_file.add_command(label='Close Database', command=self.close_entry)

        self.context_menu.add_command(label='Create New Database', command=self.new_entry)
        self.context_menu.add_command(label='Open Database', command=self.open_entry)
        self.context_menu.add_command(label='Close Database', command=self.close_entry)

        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=self.close)

        self.update_requests['select_frame0'] = [self.select_frame, TUC.BG, [TUV.BG]]
        self.update_requests['db_frame0'] = [self.db_frame, TUC.BG, [TUV.BG]]
        self.update_requests['create_frame0'] = [self.create_frame, TUC.BG, [TUV.BG]]
        self.label_formatter(self.select_lbl, size=TUV.FONT_SIZE_SMALL, uid='select_lbl')
        self.label_formatter(self.create_title, size=TUV.FONT_SIZE_TITLE, fg=TUV.ACCENT, uid='create_title')
        self.label_formatter(self.general_info_label, size=TUV.FONT_SIZE_SMALL, uid='general_info_label')

        self.root.bind('<3>', self.context_menu_show)
        self.root.bind('<F5>', self.update_ui)
        self.root.bind('<Control-r>', self.update_ui)
        self.root.bind('<MouseWheel>', self._on_mousewheel)

        self.configure_sel_frame()
        self.configure_create_frame()
        self.configure_edit_frame()

        self.ask_db_frame()
        self.update_ui()

        self.root.deiconify()
        self.root.focus_get()

    # ---------------------
    # Custom Event Handlers
    # ---------------------

    def _acc_enable(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['acc'] = True
        self.configure_edit_controls()

    def _acc_disable(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['acc'] = False
        self.configure_edit_controls()

    def _poa_part(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['poa'] = 'p'
        self.configure_edit_controls()

    def _poa_all(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['poa'] = 'a'
        self.configure_edit_controls()

    def _rqo_enable(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['rqo'] = True
        self.configure_edit_controls()

    def _rqo_disable(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['rqo'] = False
        self.configure_edit_controls()

    def _dpi_enable(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['dpi'] = True
        self.configure_edit_controls()

    def _dpi_disable(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['dpi'] = False
        self.configure_edit_controls()

    def _ssd_inp(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        if self.page_index != self.EDIT_PAGE:
            return

        if self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['poa'] != 'p':
            return

        try:
            d_set = self.edit_config_ssd_var.get().strip()
            p = True

            if d_set in ('', None):
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = 1
                return

            if not d_set.isnumeric():
                fx = re.findall(r'[0-9]{1,2}', self.edit_config_ssd_var.get().strip())
                self.edit_config_ssd_var.set(fx[0] if fx else 1)
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = fx[0] if fx else 1
                p = False

            if p and not 1 <= len(d_set) <= 2:
                if len(d_set) == 0:
                    self.edit_config_ssd_var.set('1')
                    self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = 1
                else:
                    fx = re.findall(r'[0-9]{1,2}', d_set)
                    self.edit_config_ssd_var.set(fx[0] if fx else 1)
                    self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = fx[0] if fx else 1

                p = False
            assert p, 'Subsample divisor must be an integer between 1 and 10'

            f = float(d_set)
            if not (1 <= f <= 10):
                self.edit_config_ssd_var.set('1' if f < 1 else '10')
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = '1' if f < 1 else '10'
                assert False, 'Subsample divisor must be between 1 and 10'

            if f != int(f):
                self.edit_config_ssd_var.set(str(int(f)))
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = int(f)
                assert False, 'Subsample divisor cannot contain a decimal'

            self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['ssd'] = int(f)

        except Exception as E:
            self.show_info(
                Message(Levels.ERROR, str(E)),
                3000
            )
            return

    def _dda_inp(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        if self.page_index != self.EDIT_PAGE:
            return

        if not self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['dpi']:
            return

        try:
            d_set = self.edit_config_dda_var.get().strip()
            p = True

            if d_set in ('', None):
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = 1
                return

            if not d_set.isnumeric():
                fx = re.findall(r'[0-9]{1,2}', d_set)
                self.edit_config_dda_var.set(fx[0] if fx else 1)
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = fx[0] if fx else 1
                p = False

            if p and not 1 <= len(d_set) <= 2:
                if len(d_set) == 0:
                    self.edit_config_dda_var.set('1')
                    self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = 1
                else:
                    fx = re.findall(r'[0-9]{1,2}', self.edit_config_dda_var.get().strip())
                    self.edit_config_dda_var.set(fx[0] if fx else 1)
                    self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = fx[0] if fx else 1

                p = False
            assert p, 'Deduction amount must be an integer between 1 and 10'

            f = float(d_set)
            if not (1 <= f <= 10):
                self.edit_config_dda_var.set('1' if f < 1 else '10')
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = '1' if f < 1 else '10'
                assert False, 'Deduction amount must be between 1 and 10'

            if f != int(f):
                self.edit_config_dda_var.set(str(int(f)))
                self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = int(f)
                assert False, 'Deduction amount cannot contain a decimal'

            self.data[self.EDIT_PAGE]['db']['CONFIGURATION']['a2d'] = int(f)

        except Exception as E:
            self.show_info(
                Message(Levels.ERROR, str(E)),
                3000
            )
            return

    def _config_lbl_wrl(self, el: tk.Label, name: str) -> None:
        if el not in self.late_update_requests:
            self.late_update_requests[el] = []

        self.late_update_requests[el].extend(
            [
                [
                    ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *args: el.config(wraplength=args[0] - 2 * args[1]),
                        ('<EXECUTE>', lambda *args: el.winfo_width()),
                        ('<LOOKUP>', 'padX')
                    ]
                ],
                [
                    ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *args: log(LoggingLevel.DEVELOPER, f"[LUpdate[LU][{name}]::Rule_WrLP_Auto] wraplength=({args[0]} - 2*{args[1]}) = {args[0] - 2 * args[1]} {ANSI.RESET}"),
                        ('<EXECUTE>', lambda *args: self.edit_configuration_frame.winfo_width()),
                        ('<LOOKUP>', 'padX'),
                    ] if DEBUG_NORM and qa_functions.App.DEV_MODE else [lambda *args: None]
                ],
                [
                    ThemeUpdateCommands.CUSTOM,
                    [el.update]
                ]
            ]
        )

    def expand_click(self, *_0: Optional[Any], **kwargs: Optional[Any]) -> None:
        try:
            curr = self.data[self.EDIT_PAGE]['_UI']['sb_shrunk']
            self.data[self.EDIT_PAGE]['_UI']['sb_shrunk'] = curr if kwargs.get('do_not_reset') else not curr
        except KeyError:
            self.data[self.EDIT_PAGE]['_UI'] = {'sb_shrunk': False}
            curr = False

        if curr:
            self.edit_configuration_btn.config(text='', compound=tk.CENTER)
            self.edit_questions_btn.config(text='', compound=tk.CENTER)
            self.sb_expand_shrink.config(text='', image=self.svgs['arrow_right_large']['normal'], compound=tk.CENTER)
            self.edit_db_name.config(text='')
            self.edit_pic.config(text='')

        else:
            self.edit_configuration_btn.config(text='Configuration', compound=tk.LEFT)
            self.edit_questions_btn.config(text='Questions', compound=tk.LEFT)
            self.sb_expand_shrink.config(text='Shrink', image=self.svgs['arrow_left_large']['normal'], compound=tk.LEFT)
            self.edit_db_name.config(text=f"Current Database: \"{self.data[self.EDIT_PAGE]['db']['DB']['name']}\"")
            self.edit_pic.config(text="Admin Tools")

    def db_psw_toggle(self, *_0: Optional[Any], **kwargs: Optional[Any]) -> None:
        if self.EDIT_PAGE not in self.data:
            return

        cond = self.data[self.EDIT_PAGE]['db']['DB']['psw'][0]

        if not kwargs.get('nrst'):
            if not cond:
                if cast(Tuple[Any, ...], self.db_psw_change())[1]:
                    self.show_info(Message(Levels.ERROR, "Couldn't set password."))
                    return

            cond = not cond
            self.data[self.EDIT_PAGE]['db']['DB']['psw'][0] = cond

        if cond:
            try:
                self.edit_db_psw_button.image = self.svgs['checkmark']['accent']    # type: ignore
                self.edit_db_psw_button.config(compound=tk.LEFT, image=self.svgs['checkmark']['accent'], style='Active.TButton')
            except Exception as E:
                self.edit_db_psw_button.config(style='Active.TButton')
                log(LoggingLevel.ERROR, f"Failed to add image to <edit_db_psw_button> : {E.__class__.__name__}({E})")
        else:
            self.data[self.EDIT_PAGE]['db']['DB']['psw'][1] = ''
            self.edit_db_psw_button.image = ''                                      # type: ignore
            self.edit_db_psw_button.config(style='TButton', image='')

        self.edit_db_psw_button.config(text=f"{'Not ' if not cond else ''}Protected")

    def db_psw_change(self, *_0: Optional[Any], **_1: Optional[Any]) -> Optional[Tuple[Any, ...]]:
        if self.EDIT_PAGE not in self.data:
            return None

        self.disable_all_inputs()
        self.busy = True

        s_mem = qa_functions.SMem()
        sep = '<!%%QAP_INT_SE!@DB_PSW_CHANGE!?%2112312>'
        qa_prompts.InputPrompts.DEntryPrompt(s_mem, sep, ['Enter a new admin password', 'Re-enter password'])

        res = s_mem.get()
        f = True
        f1 = True

        if isinstance(res, str):
            res = res.strip()
            if res != '':
                c = res.split(sep)
                if len(c) == 2:
                    a, b = c
                    del c
                    f = False

                    if a == b:
                        f1 = False
                        del b
                        s_mem.set('')
                        qa_prompts.InputPrompts.ButtonPrompt(s_mem, 'Reset Admin Password?', ('Yes', 'y'), ("No", 'n'), default='n', message=f'Are you sure you want to reset your password to "{a}"')
                        if s_mem.get() == 'y':
                            hashed = hashlib.sha3_512(a.encode()).hexdigest()
                            self.data[self.EDIT_PAGE]['db']['DB']['psw'] = [True, hashed]
                            self.show_info(Message(Levels.OKAY, 'Successfully reset administrator password'))

                    else:
                        qa_prompts.MessagePrompts.show_error(
                            qa_prompts.InfoPacket('Failed to reset password (passwords don\'t match.)')
                        )

        if f:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket('Failed to reset password (unknown error.)')
            )

        self.enable_all_inputs()
        self.busy = False

        del s_mem
        return f, f1

    def qz_psw_toggle(self, *_0: Optional[Any], **kwargs: Optional[Any]) -> None:
        if self.EDIT_PAGE not in self.data:
            return

        cond = self.data[self.EDIT_PAGE]['db']['DB']['q_psw'][0]

        if not kwargs.get('nrst'):
            if not cond:
                if cast(Tuple[Any, ...], self.qz_psw_change())[1]:
                    self.show_info(Message(Levels.ERROR, "Couldn't set password."))
                    return

            cond = not cond
            self.data[self.EDIT_PAGE]['db']['DB']['q_psw'][0] = cond

        self.edit_qz_psw_button.config(text=f"{'Not ' if not cond else ''}Protected")
        if cond:
            self.edit_qz_psw_button.config(compound=tk.LEFT, image=self.svgs['checkmark']['accent'], style='Active.TButton')
        else:
            self.data[self.EDIT_PAGE]['db']['DB']['q_psw'][1] = ''
            self.edit_qz_psw_button.config(style='TButton', image='')

    def qz_psw_change(self, *_0: Optional[Any], **_1: Optional[Any]) -> Optional[Tuple[Any, ...]]:
        if self.EDIT_PAGE not in self.data:
            return None

        self.disable_all_inputs()
        self.busy = True

        s_mem = qa_functions.SMem()
        sep = '<!%%QAP_INT_SE!@DB_PSW_CHANGE!?%2112312>'
        qa_prompts.InputPrompts.DEntryPrompt(s_mem, sep, ['Enter a new quiz password', 'Re-enter password'])

        res = s_mem.get()
        f = True
        f1 = True

        if isinstance(res, str):
            res = res.strip()
            if res != '':
                c = res.split(sep)
                if len(c) == 2:
                    a, b = c
                    del c
                    f = False

                    if a == b:
                        f1 = False
                        del b
                        s_mem.set('')
                        qa_prompts.InputPrompts.ButtonPrompt(s_mem, 'Reset Quiz Password?', ('Yes', 'y'), ("No", 'n'), default='n', message=f'Are you sure you want to reset your password to "{a}"')
                        if s_mem.get() == 'y':
                            assert isinstance(a, str)
                            hashed = hashlib.sha3_512(a.encode()).hexdigest()
                            self.data[self.EDIT_PAGE]['db']['DB']['q_psw'] = [True, hashed]
                            self.show_info(Message(Levels.OKAY, 'Successfully reset quiz password'))

                    else:
                        qa_prompts.MessagePrompts.show_error(
                            qa_prompts.InfoPacket('Failed to reset quiz access password (passwords don\'t match.)')
                        )

        if f:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket('Failed to reset quiz access password (unknown error.)')
            )

        self.enable_all_inputs()
        self.busy = False

        del s_mem
        return f, f1

    def inp2_edit(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        global MAX

        a = self.create_inp2_var.get()
        if len(a) > MAX:
            self.create_inp2_var.set(a[:MAX:])
            self.show_info(
                Message(Levels.ERROR, f'Password length cannot exceed {MAX} characters ({random.randint(0, 10)})')
            )

    def inp1_edit(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        global MAX

        a = self.create_inp1_var.get()
        if len(a) > MAX:
            self.create_inp1_var.set(a[:MAX:])
            self.show_info(
                Message(Levels.ERROR, f'Name length cannot exceed {MAX} characters ({random.randint(0, 10)})')
            )

    def _clear_info(self) -> None:
        if not self.gi_cl:
            return

        try:
            self.late_update_requests.pop(self.general_info_label)
        except KeyError:
            pass

        self.general_info_label.config(text="")
        self.gi_cl = False
        if self._job is not None:
            self.root.after_cancel(self._job)

    def show_info(self, data: Message, timeout: int = 3000) -> None:
        if timeout < 10:  # Useless
            return

        if 0 >= len(data.MSG) or 100 < len(data.MSG):  # Skip
            return

        self.gi_cl = True

        self.general_info_label.config(text=data.MSG)
        self.late_update_requests[self.general_info_label] = [
            [ThemeUpdateCommands.FG, [{
                                          Levels.ERROR: ThemeUpdateVars.ERROR,
                                          Levels.OKAY: ThemeUpdateVars.OKAY,
                                          Levels.WARNING: ThemeUpdateVars.WARNING,
                                          Levels.NORMAL: ThemeUpdateVars.ACCENT
                                      }[data.LVL]]]
        ]
        self._job = self.root.after(timeout, self._clear_info)
        self.update_ui()

    def ask_db_frame(self) -> None:
        self.prev_page = self.page_index

        self.db_frame.pack_forget()
        self.create_frame.pack_forget()
        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.select_frame.pack(fill=tk.BOTH, expand=True)
        self.menu_file.entryconfig('Close Database', state=tk.DISABLED)
        self.context_menu.entryconfig('Close Database', state=tk.DISABLED)

        self.page_index = self.SELECT_PAGE

        self.geo_small()

    def create_db_frame(self) -> None:
        self.prev_page = self.page_index

        self.db_frame.pack_forget()
        self.select_frame.pack_forget()
        self.title_box.pack_forget()
        self.create_frame.pack(fill=tk.BOTH, expand=True)
        self.menu_file.entryconfig('Close Database', state=tk.DISABLED)
        self.context_menu.entryconfig('Close Database', state=tk.DISABLED)

        self.create_inp1_var.set("")
        self.psw_sel_click(True)

        self.page_index = self.CREATE_PAGE

        self.geo_small()

    def edit_db_frame(self) -> None:
        self.prev_page = self.page_index

        self.select_frame.pack_forget()
        self.create_frame.pack_forget()
        self.title_box.pack_forget()
        self.db_frame.pack(fill=tk.BOTH, expand=True)
        self.menu_file.entryconfig('Close Database', state=tk.NORMAL)
        self.context_menu.entryconfig('Close Database', state=tk.NORMAL)

        self.sb_expand_shrink.config(text='Shrink', image=self.svgs['arrow_left_large']['normal'], compound=tk.LEFT)
        self.page_index = self.EDIT_PAGE

        self.geo_large()
        self.edit_configuration()

    def psw_sel_click(self, reset: bool = False) -> None:
        if self.CREATE_PAGE not in self.data:
            reset = True
        elif 'psw_enb' not in self.data[self.CREATE_PAGE] or 'psw' not in self.data[self.CREATE_PAGE]:
            reset = True

        if reset:
            if self.CREATE_PAGE not in self.data:
                self.data[self.CREATE_PAGE] = {}

            self.create_inp2_cont.config(text="")
            self.data[self.CREATE_PAGE]['psw_enb'] = False
            self.data[self.CREATE_PAGE]['psw'] = ''
            self.create_inp2.pack_forget()
            self.create_inp2_var.set("")
            self.create_add_psw_sel.config(text="NO password")

            return

        self.data[self.CREATE_PAGE]['psw_enb'] = not self.data[self.CREATE_PAGE]['psw_enb']
        enb = self.data[self.CREATE_PAGE]['psw_enb']
        if enb:
            self.create_inp2_cont.config(text="Enter a Password")
            self.data[self.CREATE_PAGE]['psw_enb'] = True
            self.data[self.CREATE_PAGE]['psw'] = ''
            self.create_inp2.pack(fill=tk.X, expand=True)
            self.create_inp2_var.set("")
            self.create_add_psw_sel.config(text="Add a password", image=self.svgs['checkmark']['normal'], compound=tk.LEFT)
        else:
            self.psw_sel_click(True)

    def context_menu_show(self, e: Any, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        if self.page_index == self.EDIT_PAGE:
            self.context_menu.post(e.x_root, e.y_root)

    def proc_exit(self, exit_to_page: Union[None, int]) -> None:
        self.page_index = exit_to_page if exit_to_page is not None else self.prev_page
        self.busy, self.dsb = False, False

        self._clear_info()

        self.data = {}

        if self.page_index == self.EDIT_PAGE:
            self.edit_db_frame()
        elif self.page_index == self.CREATE_PAGE:
            self.create_db_frame()
        elif self.page_index == self.SELECT_PAGE:
            self.ask_db_frame()
        else:
            raise Exception("Edge case not expected (ECnE Error)")

        self.enable_all_inputs()

    def new_entry(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME

        if self.dsb or self.busy:
            return

        self.busy = True
        self.disable_all_inputs()

        try:
            self.create_db_frame()
        except:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('Failed to create database file.'))

            tb = traceback.format_exc()
            sys.stderr.write(f'<NEW>: {tb}\n')
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.ERROR,
                    f'<DB_CREATE_NEW> {tb}',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])

    def close_entry(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME

        if self.dsb or self.busy:
            return

        self.busy = True
        self.disable_all_inputs()

        try:
            if self.page_index == self.EDIT_PAGE:
                if self.data[self.EDIT_PAGE]['db'] != self.data[self.EDIT_PAGE]['db_saved']:
                    s_mem = qa_functions.SMem()
                    qa_prompts.InputPrompts.ButtonPrompt(
                        s_mem, 'Save Changes?', ("Yes", "y"), ("No", 'n'), default='y',
                        message="Changes have been detected in the current database; do you want to save these changes?"
                    )

                    res = s_mem.get()
                    del s_mem
                    if isinstance(res, str):
                        if res == 'y':
                            self.save_db()

            self.proc_exit(self.SELECT_PAGE)

        except Exception as E:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(f'Failed to close database file: {E}'))

            tb = traceback.format_exc()
            sys.stderr.write(f'<CLOSE>: {tb}\n')
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.ERROR,
                    f'<DB_CLOSE> {tb}',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])

    def open_entry(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME

        if self.dsb or self.busy:
            return

        self.busy = True
        self.disable_all_inputs()

        try:
            file_name = filedialog.askopenfilename(filetypes=[('QA File', f'.{qa_files.qa_file_extn}')])
            if os.path.isfile(file_name):
                if file_name.split('.')[-1] != 'aspx':
                    file = qa_functions.File(file_name)
                    raw = qa_functions.OpenFile.load_file(file, qa_functions.OpenFunctionArgs())
                    read, _ = cast(Tuple[bytes, str], qa_files.load_file(FileType.QA_FILE, raw))
                    self.open(file_name, json.loads(read), False)

        except Exception as E:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('Failed to open database file.'))

            tb = traceback.format_exc()
            sys.stderr.write(f'<NEW>: {tb}\n')
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.ERROR,
                    f'<DB_OPEN> {tb}',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])

            self.proc_exit(self.SELECT_PAGE)
            return

        self.busy = False
        self.enable_all_inputs()

    # -----------
    # PAGE CHANGE
    # -----------

    def edit_configuration(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        log(LoggingLevel.DEBUG, 'Entered EDIT::CONFIGURATION page')
        self.edit_configuration_btn.config(style='ActiveLG.TButton', image=self.svgs['settings_cog_large']['accent'])
        self.edit_questions_btn.config(style='LG.TButton', image=self.svgs['question_large']['normal'])

        self.db_psw_toggle(nrst=True)
        self.qz_psw_toggle(nrst=True)

        self.edit_configuration_master_frame.pack(fill=tk.BOTH, expand=True)

        self.update_ui()

    def edit_questions(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        log(LoggingLevel.DEBUG, 'Entered EDIT::QUESTIONS page')
        self.edit_questions_btn.config(style='ActiveLG.TButton', image=self.svgs['question_large']['accent'])
        self.edit_configuration_btn.config(style='LG.TButton', image=self.svgs['settings_cog_large']['normal'])

        self.edit_configuration_master_frame.pack_forget()

        self.update_ui()

    # --------------
    # Main Functions
    # --------------

    def compile_changes(self) -> Tuple[bool, Tuple[List[Tuple[Union[Tuple[str, int], str], Any, Any]], List[str]]]:
        if not qa_functions.data_at_dict_path(f'{self.EDIT_PAGE}/db_saved', self.data)[0]:
            return False, ([], [])

        if self.data[self.EDIT_PAGE]['db_saved'] == self.data[self.EDIT_PAGE]['db']:
            return False, ([], [])

        def rec(og: Any, new: Any, root: str = "") -> Tuple[List[Tuple[Union[Tuple[str, int], str], Any, Any]], List[str]]:
            c: List[Tuple[Union[Tuple[str, int], str], Any, Any]] = []
            f: List[str] = []

            # assert , "[CRITICAL] Failed to compile changes: {DDT}"
            if type(og) is not type(new):
                if isinstance(new, dict):
                    og1 = {k: None for k in new.keys()}
                    c1, f1 = rec(og1, new)
                    c.extend(c1)
                    f.extend(f1)
                    del c1, f1, og1

                else:
                    c.append((root, og, new))

                return c, f

            if isinstance(og, (list, dict, tuple, set)):
                # assert , "[CRITICAL] Failed to compile changes: {LEN}"
                if len(og) != len(new):
                    if isinstance(new, dict):
                        if isinstance(og, dict):
                            tks = {*og.keys(), *new.keys()}
                            og1, new1 = {k: og.get(k) for k in tks}, {k: new.get(k) for k in tks}
                            c1, f1 = rec(og1, new1)
                            c.extend(c1)
                            f.extend(f1)
                            del og1, new1, c1, f1

                        else:
                            og1 = {k: None for k in new.keys()}
                            c1, f1 = rec(og1, new)
                            c.extend(c1)
                            f.extend(f1)
                            del c1, f1, og1

                    else:
                        c.append((root, '<ls>', '<data_added_or_removed>'))

                elif isinstance(og, dict):
                    for (k1, _), (k2, _1) in zip(og.items(), new.items()):
                        if k1 != k2:
                            f.append('[CRITICAL] Failed to compile changes: {KoKt}')
                            continue

                        a, b = rec(og[k1], new[k1], k1)
                        c.extend(a)
                        f.extend(b)
                        del a, b

                else:
                    for i, (a, b) in enumerate(zip(og, new)):
                        if cast(Any, a) != cast(Any, b):
                            c.append(((root, i), a, b))

            else:
                if cast(Union[str, bytes, int, float, bool], og) != cast(Union[str, bytes, int, float, bool], new):
                    c.append((root, og, new))

            return c, f

        changes = rec(self.data[self.EDIT_PAGE]['db_saved'], self.data[self.EDIT_PAGE]['db'])
        return True, changes

    @staticmethod
    def compile_changes_str(changes: List[Tuple[Union[Tuple[str, int], str], Any, Any]]) -> str:
        n_map: Dict[Any, Any] = {
            'psw': {
                0: ['Database Password Protection', True, True],
                1: ['Admin password', False, True]
            },
            'q_psw': {
                0: ['Quiz Password Protection', True, True],
                1: ['Quiz password', False, True]
            },
            'DB': ['Database root configuration', False, False],
            'CONFIGURATION': ['Configuration data', False, False],
            'QUESTIONS': ['Questions list', False, False],

            # CONFIGURATION
            'acc': ['Allow Custom Quiz Configuration', True, True],
            'poa': ['Questions: Part or All', True, True],
            'rqo': ['Randomize Question Order', True, True],
            'ssd': ['POA; Subsample divisor', True, True],
            'dpi': ['Deduct Points When Incorrect', True, True],
            'a2d': ['Num. points to deduct', True, True],
        }

        c = []
        print(changes)
        for n, og, new in changes:
            if isinstance(n, tuple):
                n, ind = n
                name, show, v_trans = n_map[n][ind]
            else:
                name, show, v_trans = n_map[n]

            if v_trans:
                o = False
                if new is None:
                    new = '<REMOVED>'
                    o = True
                elif isinstance(new, bool):
                    new = f"{'En' if new else 'Dis'}abled"

                if og is None:
                    og = '<NON_EXISTENT>'
                    o = True
                elif isinstance(og, bool):
                    og = f"{'En' if og else 'Dis'}abled"

                if n == 'poa' and not o:
                    og = "Part" if og == 'p' else "All"
                    new = "Part" if new == 'p' else "All"

            if show:
                c.append(f"{name}: {og} \u2192 {new}")
            else:
                c.append(f"Changed {name.lower()}")

        return "\n   *" + "\n   *".join(c)

    def save_db(self, _do_not_prompt: bool = False) -> None:
        s_mem = qa_functions.SMem()
        s_mem.set('n')
        changed, [changes, failures] = self.compile_changes()

        if not changed:
            self.show_info(Message(Levels.ERROR, 'No changes found.'))
            return

        if len(failures) > 0:
            Str = "Failed to compile changes made due to the following error(s):\n\t* " + \
                  "\n\t* ".join(f for f in failures)
            log(LoggingLevel.ERROR, f"<SAVE_DB>: {str}")
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(Str))
            return

        if not _do_not_prompt:
            qa_prompts.InputPrompts.ButtonPrompt(
                s_mem, 'Review Changes', ('Yes, save changes', 'y'), ('No', 'n'), default='n',
                message=f"Do you want to save the following changes:\n{self.compile_changes_str(changes)}"
            )

            if s_mem.get() is None:
                return

        r = s_mem.get()
        if r is None:
            return

        if r.strip() == 'y' or _do_not_prompt:
            new_str = json.dumps(self.data[self.EDIT_PAGE]['db'])
            file = qa_functions.File(self.data[self.EDIT_PAGE]['db_path'])
            new, _ = cast(Tuple[bytes, str], qa_files.generate_file(FileType.QA_FILE, new_str))
            qa_functions.SaveFile.secure(file, new, qa_functions.SaveFunctionArgs(False, False, save_data_type=bytes))
            self.data[self.EDIT_PAGE]['db_saved'] = copy.deepcopy(self.data[self.EDIT_PAGE]['db'])
            log(LoggingLevel.SUCCESS, 'Successfully saved new data to database.')
            self.show_info(Message(Levels.OKAY, 'Successfully saved new data'))

        del s_mem

    def new_main(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        global MAX

        log(LoggingLevel.DEBUG, 'Entered new_main proc')

        log(LoggingLevel.INFO, "DB_CREATION: <nm> proc")
        l = len(self.create_inp1_var.get())
        p = 0 < l <= MAX
        log(LoggingLevel.INFO, f"DB_CREATION: <nm>; res: {l} ({'pass' if p else 'fail'})")
        if not p:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(f"Database name's length must be between 1 and {MAX} characters.")
            )
            return

        if self.data[self.CREATE_PAGE]['psw_enb']:
            log(LoggingLevel.INFO, "DB_CREATION: <pr> proc")
            psw = self.create_inp2_var.get()

            if not isinstance(psw, str):  # Shouldn't be needed, but just in case.
                log(LoggingLevel.ERROR, "DB_CREATION: p!=str [prompt*]")
                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket("Please enter a password, or deselect the password option.")
                )
                return

            log(LoggingLevel.INFO, f"DB_CREATION: <pr:len> {len(psw)}")
            hashed_psw = hashlib.sha3_512(psw.encode()).hexdigest()
            log(LoggingLevel.INFO, f"DB_CREATION: <pr:hash> {hashed_psw}")

            if len(psw.strip()) == 0:
                log(LoggingLevel.ERROR, "DB_CREATION: p::strip!>0 [prompt*]")
                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket("Please enter a password, or deselect the password option.")
                )
                return

            if psw != psw.replace(' ', '').replace('\n', '').replace('\t', ''):
                log(LoggingLevel.ERROR, "DB_CREATION: p::n_space!=<p> [prompt*]")
                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket("Password may not contain spaces.")
                )
                return

            log(LoggingLevel.INFO, "DB_CREATION: Password okay; hash stored in screen temp data.")
            self.data[self.CREATE_PAGE]['psw'] = hashed_psw

        log(LoggingLevel.INFO, "DB_CREATION: <sa> proc [prompt*_tk:filedialog]")

        file = filedialog.asksaveasfilename(filetypes=[('QA File', qa_files.qa_file_extn)])
        if file is None:
            self.proc_exit(self.CREATE_PAGE)
            self.show_info(Message(Levels.NORMAL, 'Aborted process.'))
            return
        if not os.path.isdir('\\'.join(file.replace('/', '\\').split('\\')[:-2:])):
            self.proc_exit(self.CREATE_PAGE)
            self.show_info(Message(Levels.NORMAL, 'Aborted process.'))
            return

        psw_ld = self.create_inp2_var.get().strip() if self.data[self.CREATE_PAGE]['psw_enb'] else ''

        file = qa_functions.File(f'{file}.{qa_files.qa_file_extn}' if file.split('.')[-1] != qa_files.qa_file_extn else file)
        db_starter_dict = {
            'DB': {
                'name': self.create_inp1_var.get(),
                'psw': [self.data[self.CREATE_PAGE]['psw_enb'], hashlib.sha3_512(psw_ld.encode()).hexdigest() if len(psw_ld) > 0 else ''],
                'q_psw': [False, '']
            },
            'CONFIGURATION': {

            },
            'QUESTIONS': []
        }
        db_starter = json.dumps(db_starter_dict, indent=4)

        try:
            data, _ = cast(Tuple[bytes, str], qa_files.generate_file(FileType.QA_FILE, db_starter))
            qa_functions.SaveFile.secure(file, data, qa_functions.SaveFunctionArgs(append=False, encrypt=False, save_data_type=bytes))
        except Exception as E:
            log(LoggingLevel.ERROR, f'DB_CREATION: [save proc]: {traceback.format_exc()}')
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(f"""An error occurred whilst creating the new database;
Error: {E}
Error Code: {hashlib.md5(f"{E}".encode()).hexdigest()}

Technical Information: {traceback.format_exc()}"""))

            self.proc_exit(self.CREATE_PAGE)
            return

        self.open(file.file_path, db_starter_dict, True)

    @staticmethod
    def _clean_db(db: Dict[str, Any]) -> Dict[str, Any]:
        assert isinstance(db, dict)
        name_f, name_d = qa_functions.data_at_dict_path('DB/name', db)
        assert name_f

        log(LoggingLevel.INFO, 'Checking database integrity')

        def rs_name() -> None:
            log(LoggingLevel.ERROR, 'Name data corrupted')

            s_mem = qa_functions.SMem()
            s_mem.set('')

            while True:
                qa_prompts.InputPrompts.SEntryPrompt(s_mem, 'The database\'s name data was corrupted; please enter a new name below:', default='')
                res = s_mem.get()
                if res is None:
                    continue
                res = res.strip()

                if len(res) > 0:
                    break

            log(LoggingLevel.ERROR, f'Name reset to \"{res}\"')

            db['DB']['name'] = res
            del res, s_mem

        if not isinstance(name_d, str):
            rs_name()
        elif len(name_d.strip()) <= 0:
            rs_name()

        _, psw_d = qa_functions.data_at_dict_path('DB/psw', db)
        b = isinstance(psw_d, list)
        if b:
            b &= len(psw_d) == 2
            if b:
                b &= isinstance(psw_d[0], bool)
                b &= isinstance(psw_d[1], str)

                if b:
                    b &= not (len(psw_d[1]) != 128 and psw_d[0])  # NAND logic gate

                    # NAND:
                    # <!128> and <!enb>: True
                    # <128> and <!enb>: False
                    # <!128> and <enb>: False
                    # <128> and <enb>: True

        if not b:
            log(LoggingLevel.ERROR, 'DB_PSW corruption; reset.')
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('Administrator password corrupted; protection disabled.'))
            db['DB']['psw'] = [False, '']

        del psw_d

        _, q_psw_d = qa_functions.data_at_dict_path('DB/q_psw', db)
        b = isinstance(q_psw_d, list)
        if b:
            b &= len(q_psw_d) == 2
            if b:
                b &= isinstance(q_psw_d[0], bool)
                b &= isinstance(q_psw_d[1], str)

                if b:
                    b &= not (len(q_psw_d[1]) != 128 and q_psw_d[0])  # NAND logic gate

                    # NAND:
                    # <!128> and <!enb>: True
                    # <128> and <!enb>: False
                    # <!128> and <enb>: False
                    # <128> and <enb>: True

        if not b:
            log(LoggingLevel.ERROR, 'QZ_PSW corruption; reset.')
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('Quiz password corrupted; protection disabled.'))
            db['DB']['q_psw'] = [False, '']

        # Configuration checks
        cr = 'CONFIGURATION'
        cd = db.get(cr)

        if not cd:
            log(LoggingLevel.ERROR, "Configuration data not found; resetting configuration data. ")
            db[cr] = {
                'acc': False,  # Allow custom quiz configuration
                'poa': 'p',  # Part or all
                'rqo': False,  # Randomize question order
                'ssd': 2,  # Subsample divisor
                'dpi': False,  # Deduct points on incorrect (responses)
                'a2d': 1  # Amount of points to deduct
            }
        else:
            f: List[Any] = []
            for k, (tp, default, ln) in (
                    ('acc', (bool, False, None)),
                    ('poa', (str, 'p', 1)),
                    ('rqo', (bool, False, None)),
                    ('ssd', (int, 2, None)),
                    ('dpi', (bool, False, None)),
                    ('a2d', (int, 1, None)),
            ):
                # TODO: Implement test
                pass

        qr = 'QUESTIONS'

        return db

    def open(self, path: str, data: Dict[Any, Any], _bypass_psw: bool = False) -> None:
        assert os.path.isfile(path)
        assert type(data) is dict

        self.enable_all_inputs()

        try:
            O_data = copy.deepcopy(data)
            n_data = self._clean_db(data)

            self.data[self.EDIT_PAGE] = {'db_path': path}
            self.data[self.EDIT_PAGE]['db'] = n_data
            self.data[self.EDIT_PAGE]['db_saved'] = O_data

            changed, (changes, failures) = self.compile_changes()

            if changed:
                s_mem = qa_functions.SMem()
                s_mem.set('')
                qa_prompts.InputPrompts.ButtonPrompt(
                    s_mem,
                    'Corrupted data found.',
                    ('Fix now', 'fn'), ('Exit', 'ex'),
                    default='ex',
                    message='Corrupted data was found in the requested database; the application has compiled the changes needed to fix the database.\n\nDo you want to save the following changes:\n' +
                            self.compile_changes_str(changes)
                )

                if s_mem.get() != 'fn':
                    self.proc_exit(self.SELECT_PAGE)
                    self.show_info(Message(Levels.ERROR, 'Aborted process.'))
                    return

                else:
                    self.save_db(True)

            del changed, changes, failures, O_data
            self.data[self.EDIT_PAGE]['db_saved'] = n_data

            if not _bypass_psw and data['DB']['psw'][0]:
                s_mem = qa_functions.SMem()
                qa_prompts.InputPrompts.SEntryPrompt(s_mem, f'Enter database password for \'{data["DB"]["name"]}\'', '')

                r = s_mem.get()
                if r is None:
                    del s_mem

                    self.proc_exit(self.SELECT_PAGE)
                    return

                if r.strip() == '':
                    del s_mem
                    self.proc_exit(self.SELECT_PAGE)
                    return

                if hashlib.sha3_512(r.encode()).hexdigest() != data['DB']['psw'][1]:
                    s_mem.set('')
                    qa_prompts.InputPrompts.ButtonPrompt(
                        s_mem, 'Security', ('Retry', 'rt'), ('Exit', 'ex'), default='?',
                        message="Couldn't open database: Invalid password. Do you want to retry?"
                    )

                    if s_mem.get() == 'rt':
                        self.open(path, data, False)
                        return

                    del s_mem

                    self.proc_exit(self.SELECT_PAGE)
                    return

                del s_mem

            self.busy = False
            self.edit_db_frame()  # Pack components

            self.edit_db_name.config(text=f"Current Database: \"{data['DB']['name']}\"", anchor=tk.W)
            self.data[self.EDIT_PAGE] = {'db_path': path}
            self.data[self.EDIT_PAGE]['db'] = copy.deepcopy(n_data)
            self.data[self.EDIT_PAGE]['db_saved'] = copy.deepcopy(n_data)
            self.data[self.EDIT_PAGE]['_UI'] = {'sb_shrunk': True}

            self.expand_click(do_not_reset=True)
            self.configure_edit_controls()

        except Exception as E:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(
                    f"""An error occurred whilst opening the database;
Error: {E}
Error Code: {hashlib.md5(f"{E}".encode()).hexdigest()}

Technical Information: {traceback.format_exc()}"""
                )
            )

    # --------------------
    # DEFAULT UI FUNCTIONS
    # --------------------

    def update_ui(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.load_theme()

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
            for index, arg in enumerate(args):
                cleaned_args.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

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
                                rs_b: int = cast(int, {
                                    'padX': self.padX,
                                    'padY': self.padY,
                                    'root_width': self.root.winfo_width(),
                                    'root_height': self.root.winfo_height(),
                                }.get(cast(str, arg[1])))

                                if rs_b is not None:
                                    cleaned_arg = rs_b
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

                if lCommand[0] is True:
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cleaned_args

    def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN,
                         padding: Union[None, int] = None, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, abg: ThemeUpdateVars = ThemeUpdateVars.ACCENT, afg: ThemeUpdateVars = ThemeUpdateVars.BG, uid: Union[str, None] = None) -> None:
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
                font, size,
                self.window_size[0] - 2 * padding
            ]
        ]

    def label_formatter(self, label: Union[tk.Label, tk.LabelFrame], bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN,
                        font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int] = None, uid: Union[str, None] = None) -> None:
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
                bg, fg, font, size, padding
            ] if isinstance(label, tk.Label) else (
                [
                    lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                    bg, fg, font, size, padding
                ] if isinstance(label, tk.LabelFrame) else [
                    lambda *args: None
                ]
            )
        ]

    def load_theme(self) -> None:
        self.theme = qa_functions.qa_theme_loader.Load.auto_load_pref_theme()
        self.rst_theme = False

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
        self.svgs['admt'] = ImageTk.PhotoImage(i)
        
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
        self.dsb = True

        for btn in (self.select_open, self.select_new, self.select_scores,
                    self.edit_questions_btn, self.edit_configuration_btn,
                    self.edit_db_psw_reset_btn, self.edit_db_psw_button,
                    self.edit_qz_psw_reset_btn, self.edit_qz_psw_button):
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        self.dsb = False

        for btn in (self.select_open, self.select_new, self.select_scores,
                    self.edit_questions_btn, self.edit_configuration_btn,
                    self.edit_db_psw_reset_btn, self.edit_db_psw_button,
                    self.edit_qz_psw_reset_btn, self.edit_qz_psw_button):
            if btn not in exclude:
                btn.config(state=tk.NORMAL)

        self.update_ui()

    def __del__(self) -> None:
        self.thread.join(self, 0)


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

    data = f"{AppLogColors.ADMIN_TOOLS}{AppLogColors.EXTRA}[ADMIN_TOOLS]{ANSI.RESET} {data}"

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
    qa_prompts.LOGGER_AVAIL = LOGGER_AVAIL
    qa_prompts.LOGGER_FUNC = LOGGER_FUNC
    qa_prompts.LOGGING_FILE_NAME = LOGGING_FILE_NAME
    qa_prompts.DEBUG_NORM = DEBUG_NORM
    qa_prompts.DEBUG_DEV_FLAG = DEBUG_DEV_FLAG
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
