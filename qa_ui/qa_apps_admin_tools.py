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
from . import qa_adv_forms as qa_forms
from fpdf import FPDF  # type: ignore
from datetime import datetime

qa_info = qa_functions.qa_info

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


class CustomText(tk.Text):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # type: ignore
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"  # type: ignore
        self.tk.call("rename", self._w, self._orig)  # type: ignore
        self.tk.createcommand(self._w, self._proxy)  # type: ignore

        self._custom_as_enb = False
        self._custom_stg = False

    def _proxy(self, command: Any, *args: Any) -> Any:
        # avoid error when copying
        if command == 'get' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not self.tag_ranges('sel'):
            return

        # avoid error when deleting
        if command == 'delete' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not self.tag_ranges('sel'):
            return

        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ('insert', 'delete', 'replace'):
            self.event_generate('<<TextModified>>')

        return result

    def clear_all(self) -> None:
        self.delete('1.0', tk.END)

    def enable_auto_size(self) -> None:
        self._custom_as_enb = True
        log(LoggingLevel.INFO, f'(CustomWidget) {self.winfo_name()}: Enabled auto sizing')
        self.bind('<Key>', self._custom_update_size)

    def auto_size(self) -> None:
        if not self._custom_as_enb:
            self.enable_auto_size()

        self._custom_update_size(None)

    def _custom_update_size(self, _: Any) -> None:
        if not self._custom_as_enb:
            return

        widget_width = 0
        widget_height = float(self.index(tk.END))

        for line in self.get("1.0", tk.END).split("\n"):
            if len(line) > widget_width:
                widget_width = len(line) + 1

        self.config(width=widget_width, height=int(widget_height))

    def setup_color_tags(self, theme_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]], tab_len: int = 5) -> None:
        if self._custom_stg:
            return

        self._custom_stg = True

        log(LoggingLevel.INFO, f'(CustomWidget) {self.winfo_name()}: Enabled custom tags')

        self.tag_config("<accent>", selectbackground=theme_map[ThemeUpdateVars.FG].color, foreground=theme_map[ThemeUpdateVars.ACCENT].color)  # type: ignore
        self.tag_config("<error>", foreground=theme_map[ThemeUpdateVars.ERROR].color, selectbackground=theme_map[ThemeUpdateVars.ERROR].color, selectforeground=theme_map[ThemeUpdateVars.BG].color)  # type: ignore
        self.tag_config("<error_bg>", background=theme_map[ThemeUpdateVars.ERROR].color, foreground=theme_map[ThemeUpdateVars.BG].color, selectbackground=theme_map[ThemeUpdateVars.FG].color, selectforeground=theme_map[ThemeUpdateVars.ERROR].color)  # type: ignore
        self.tag_config("<okay>", foreground=theme_map[ThemeUpdateVars.OKAY].color, selectbackground=theme_map[ThemeUpdateVars.OKAY].color, selectforeground=theme_map[ThemeUpdateVars.BG].color)  # type: ignore
        self.tag_config("<okay_bg>", background=theme_map[ThemeUpdateVars.OKAY].color, foreground=theme_map[ThemeUpdateVars.BG].color, selectbackground=theme_map[ThemeUpdateVars.FG].color, selectforeground=theme_map[ThemeUpdateVars.OKAY].color)  # type: ignore
        self.tag_config("<warning>", foreground=theme_map[ThemeUpdateVars.WARNING].color, selectbackground=theme_map[ThemeUpdateVars.WARNING].color, selectforeground=theme_map[ThemeUpdateVars.BG].color)  # type: ignore
        self.tag_config("<warning_bg>", background=theme_map[ThemeUpdateVars.WARNING].color, foreground=theme_map[ThemeUpdateVars.BG].color, selectbackground=theme_map[ThemeUpdateVars.FG].color, selectforeground=theme_map[ThemeUpdateVars.WARNING].color)  # type: ignore
        self.tag_config("<accent_bg>", background=theme_map[ThemeUpdateVars.ACCENT].color, foreground=theme_map[ThemeUpdateVars.BG].color)  # type: ignore
        self.tag_config('<gray_fg>', foreground=theme_map[ThemeUpdateVars.GRAY].color, selectbackground=theme_map[ThemeUpdateVars.GRAY].color, selectforeground=theme_map[ThemeUpdateVars.BG].color)  # type: ignore
        self.tag_config('<gray_bg>', background=theme_map[ThemeUpdateVars.GRAY].color, selectbackground=theme_map[ThemeUpdateVars.FG].color, selectforeground=theme_map[ThemeUpdateVars.GRAY].color)  # type: ignore
        self.tag_config('<underline>', underline=1)  # type: ignore
        self.tag_config('<indented_first>', lmargin1=tab_len)  # type: ignore
        self.tag_config('<indented_body>', lmargin2=tab_len)  # type: ignore


class Levels(Enum):
    """
    Logging Levels (ENUM) for ADMIN TOOLS UI.
        USED BY Message CLASS
    """

    (NORMAL, OKAY, WARNING, ERROR) = range(4)


@dataclass
class Message:
    """
    Data packets to be used for logging in the admin tools UI
    use this dataclass for transferring data.
    """

    LVL: Levels
    MSG: str


class PDF(FPDF):
    def __init__(self, accent_color: HexColor, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.cVar_accent_color = accent_color

    def header(self) -> None:
        self.image('./.src/.icons/.app_ico/.png/admin_tools.png', 10, 10, w=10, h=10)
        self.set_font("Courier", "B", 15)

        self.cell(10)

        if qa_functions.check_hex_contrast(HexColor('#ffffff'), self.cVar_accent_color, 3)[0]:
            self.set_text_color(*qa_functions.qa_colors.Convert.HexToRGB(self.cVar_accent_color.color))
        else:
            self.set_text_color(0, 0, 0)

        self.text(25, 16.5, "QA Administrator Tools | Database Dump")
        self.ln(20)

        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Courier", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


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
        
        width_to_height_ratio = 10/9
        
        wd_h = int(self.screen_dim[1] * 0.85)
        wd_w = int(wd_h * width_to_height_ratio)
        
        self.window_size = [wd_w, wd_h]
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] * .43 - self.window_size[1] / 2)
        ]

        self.window_size_2 = [670, 475]
        self.screen_pos_2 = [
            int(self.screen_dim[0] / 2 - self.window_size_2[0] / 2),
            int(self.screen_dim[1] * .43 - self.window_size_2[1] / 2)
        ]

        self.theme: qa_functions.qa_custom.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]] = {}  # type: ignore

        self.padX = 20
        self.padY = 10

        self.gi_cl = True
        self._job: Union[None, str] = None

        self.load_theme()
        self.update_requests: Dict[str, List[Any]] = {}  # type: ignore
        self.late_update_requests: Dict[tk.Widget, List[Any]] = {}  # type: ignore
        self.data: Dict[Any, Any] = {}  # type: ignore

        self.img_path = qa_functions.Files.AT_png
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

            'admt': ''
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
        self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Admin')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size, 'My')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

        self.page_index = self.SELECT_PAGE
        self.prev_page = self.page_index
        self.edit_on_config_page = True

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
        self.edit_export_btn = ttk.Button(self.edit_btn_panel, text='Export', command=self.edit_export)

        # Configuration page:: Main Elements (Edit page)
        self.edit_configuration_master_frame = tk.Frame(self.db_frame)
        self.edit_configuration_canvas = tk.Canvas(self.edit_configuration_master_frame)
        self.edit_configuration_vsb = ttk.Scrollbar(self.edit_configuration_master_frame, style='MyAdmin.TScrollbar')
        self.edit_configuration_frame = tk.Frame(self.edit_configuration_canvas)

        # Configuration page:: Elements (Edit page)
        self.edit_configuration_title = tk.Label(self.edit_configuration_master_frame)

        self.edit_password_container = tk.LabelFrame(self.edit_configuration_frame)
        self.edit_db_psw_container = tk.LabelFrame(self.edit_password_container)
        self.edit_qz_psw_container = tk.LabelFrame(self.edit_password_container)

        self.edit_db_psw_lbl = tk.Label(self.edit_db_psw_container)
        self.edit_db_psw_button = ttk.Button(self.edit_db_psw_container, command=self.db_psw_toggle)
        self.edit_db_psw_reset_btn = ttk.Button(self.edit_db_psw_container, command=self.db_psw_change)

        self.edit_qz_psw_lbl = tk.Label(self.edit_qz_psw_container)
        self.edit_qz_psw_button = ttk.Button(self.edit_qz_psw_container, command=self.qz_psw_toggle)
        self.edit_qz_psw_reset_btn = ttk.Button(self.edit_qz_psw_container, command=self.qz_psw_change)

        self.edit_configuration_save = ttk.Button(self.edit_configuration_master_frame, text="Save Changes", command=self.save_db)
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

        # Question Page :: Main Elements (Edit page)
        self.edit_question_master_frame = tk.Frame(self.db_frame)
        self.edit_question_canvas = tk.Canvas(self.edit_question_master_frame)
        self.edit_question_vsb = ttk.Scrollbar(self.edit_question_master_frame, style='MyAdmin.TScrollbar')
        self.edit_question_xsb = ttk.Scrollbar(self.edit_question_master_frame, orient=tk.HORIZONTAL, style='MyHorizAdmin.TScrollbar')
        self.edit_question_frame = tk.Frame(self.edit_question_canvas)

        self.edit_question_title = tk.Label(self.edit_question_master_frame)
        self.question_map: Dict[str, Any] = {}  # type: ignore  # qId : (ParentLblFrame, [update UIDs], {qData})

        self.edit_question_btn_frame = tk.Frame(self.edit_question_master_frame)
        self.edit_question_add_new_btn = ttk.Button(self.edit_question_btn_frame, text='Add New Question', command=self._ad_q)
        self.edit_questions_save_btn = ttk.Button(self.edit_question_btn_frame, text='Save Changes', command=self.save_db)

        # Export
        self.edit_export_master_frame = tk.Frame(self.db_frame)
        self.edit_export_ttl = tk.Label(self.edit_export_master_frame)
        self.edit_export_pdf = ttk.Button(self.edit_export_master_frame, text='Export as PDF', command=self.export_pdf)
        self.edit_export_pdf_txt = tk.Label(self.edit_export_master_frame)
        self.edit_export_qz = ttk.Button(self.edit_export_master_frame, text='Export as QuizzingForm Database', command=self.export_qz)
        self.edit_export_qz_txt = tk.Label(self.edit_export_master_frame)

        # Final calls
        self.start()
        self.root.mainloop()

    # -------------------
    # Frame Configurators
    # -------------------

    def configure_create_frame(self) -> None:
        """
        Configure Create Frame

        Places UI elements into the "CREATE" frame.
        Creates the appropriate UI update requests.

        :return: None
        """
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

    def configure_question_frame(self) -> None:
        self.edit_question_title.config(text='Question Manager')
        self.edit_question_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY * 2, side=tk.TOP)

        self.edit_question_btn_frame.pack(fill=tk.X, expand=False, side=tk.BOTTOM)

        self.edit_question_add_new_btn.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
        self.edit_question_add_new_btn.config(style='LG.TButton')

        self.edit_questions_save_btn.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
        self.edit_questions_save_btn.config(style='LG.TButton')

        self.edit_question_vsb.pack(fill=tk.Y, expand=False, side=tk.RIGHT, pady=self.padY, padx=(0, self.padX))
        self.edit_question_xsb.pack(fill=tk.X, expand=False, side=tk.BOTTOM, pady=(0, self.padY), padx=(self.padX, 0))
        self.edit_question_canvas.pack(fill=tk.BOTH, expand=True, pady=(self.padY, 0), padx=(self.padX, 0))

        # Scrollbar setup
        self.edit_question_vsb.configure(command=self.edit_question_canvas.yview)
        self.edit_question_xsb.configure(command=self.edit_question_canvas.xview)
        self.edit_question_canvas.configure(
            yscrollcommand=self.edit_question_vsb.set,
            xscrollcommand=self.edit_question_xsb.set,
        )

        self.edit_question_canvas.create_window(
            0, 0,
            window=self.edit_question_frame,
            anchor="nw",
            tags="self.edit_question_frame"
        )

        self.edit_question_frame.update()
        self.edit_question_frame.bind("<Configure>", self.on_frame_config)
        self.edit_question_canvas.bind("<MouseWheel>", self._on_mousewheel)

        TUC = ThemeUpdateCommands
        TUV = ThemeUpdateVars

        self.update_requests[gsuid()] = [self.edit_question_master_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.edit_question_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.edit_question_btn_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [
            self.edit_question_canvas,
            TUC.CUSTOM,
            [
                lambda *args: self.edit_question_canvas.config(bg=args[0], bd=0, highlightthickness=0),
                TUV.BG
            ]
        ]
        self.update_requests[gsuid()] = [
            None,
            TUC.CUSTOM,
            [
                lambda *args: self.edit_question_title.config(
                    bg=args[1], fg=args[0], font=(args[2], args[3])
                ),
                TUV.BG, TUV.ACCENT, TUV.TITLE_FONT_FACE, TUV.FONT_SIZE_TITLE
            ]
        ]

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
        self.edit_export_btn.pack(fill=tk.X, expand=True, ipady=self.padY / 2)

        self.edit_sidebar.pack(fill=tk.Y, expand=False, side=tk.LEFT)
        self.edit_sep.pack(fill=tk.Y, expand=False, side=tk.LEFT, pady=(self.padY, 0))

        # Configuration Frame
        self.edit_configuration_title.config(text="Configuration Manager")
        self.edit_configuration_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY * 2)

        self.edit_configuration_save.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
        self.edit_configuration_save.config(style='LG.TButton')

        self.edit_configuration_vsb.pack(fill=tk.Y, expand=False, padx=(0, self.padX), pady=self.padY, side=tk.RIGHT)
        self.edit_configuration_canvas.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=self.padY)

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

        self.edit_configuration_btn.config(compound=tk.LEFT, image=self.svgs['settings_cog_large']['normal'], style='LG.TButton')
        self.edit_questions_btn.config(compound=tk.LEFT, image=self.svgs['question_large']['normal'], style='LG.TButton')
        self.edit_export_btn.config(compound=tk.LEFT, image=self.svgs['export_large']['normal'], style='LG.TButton')

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
        self.edit_config_acc_btn1.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.LEFT)
        self.edit_config_acc_btn2.pack(fill=tk.X, expand=True, ipady=self.padY / 2, side=tk.RIGHT)

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
        self.edit_configuration_frame.bind("<Configure>", self.on_frame_config)
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
                    bg=args[1], fg=args[0], font=(args[2], args[3])
                ),
                VAR.BG, VAR.ACCENT, VAR.TITLE_FONT_FACE, VAR.FONT_SIZE_TITLE
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

    def configure_export_frame(self) -> None:
        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        self.edit_export_ttl.config(text='Export Manager')
        self.edit_export_ttl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY * 2, side=tk.TOP)

        self.edit_export_pdf.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_export_pdf_txt.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_export_qz.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.edit_export_qz_txt.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.edit_export_pdf_txt.config(
            text="""Click the 'Export as PDF' button to export ALL question data as a PDF file.

NOTE: This files is only for admin-use ONLY; this file CANNOT be read by any QuizzingApp application.""")
        self.edit_export_qz_txt.config(
            text="""Click the 'Export as QuizzingForm Database' button to export the data required by the QuizzingApp QuizzingForm application. This file can then be distributed for usage by quiz-takers.

NOTE: This file is REQUIRED to use the QuizzingApp QuizzingForm application; the raw database file (this database) cannot be accessed by QuizzingForm.
NOTE: This file is NOT human-readable
NOTE: This file cannot be read by any app other than the QuizzingApp QuizzingForm"""
        )

        self.update_requests[gsuid()] = [
            None,
            TUC.CUSTOM,
            [
                lambda *args: self.edit_export_ttl.config(
                    bg=args[1], fg=args[0], font=(args[2], args[3])
                ),
                TUV.BG, TUV.ACCENT, TUV.TITLE_FONT_FACE, TUV.FONT_SIZE_TITLE
            ]
        ]
        self.update_requests[gsuid()] = [self.edit_export_master_frame, TUC.BG, [TUV.BG]]
        self.late_update_requests[self.edit_export_pdf_txt] = [
            [
                TUC.CUSTOM,
                [
                    lambda *args: self.edit_export_pdf_txt.config(bg=args[3], fg=args[4], justify=tk.LEFT, anchor=tk.W, wraplength=qa_functions.clamp(1, args[0] - args[1], args[2])),
                    ('<EXECUTE>', lambda *args: self.edit_export_master_frame.winfo_width()),
                    self.padX * 2,
                    ('<LOOKUP>', 'root_width'),
                    TUV.BG, TUV.GRAY
                ]
            ]
        ]

        self.late_update_requests[self.edit_export_qz_txt] = [
            [
                TUC.CUSTOM,
                [
                    lambda *args: self.edit_export_qz_txt.config(bg=args[3], fg=args[4], justify=tk.LEFT, anchor=tk.W, wraplength=qa_functions.clamp(1, args[0] - args[1], args[2])),
                    ('<EXECUTE>', lambda *args: self.edit_export_master_frame.winfo_width()),
                    self.padX * 2,
                    ('<LOOKUP>', 'root_width'),
                    TUV.BG, TUV.GRAY
                ]
            ]
        ]

    def _rm_q(self, qid: str) -> None:
        """
        Remove Question
            alias history:
            * _rm_q

        USED BY     QuestionFrame

        Removes a specific question from the database.

        :param qid: Question Unique ID
        :return:    None
        """

        if self.dsb:
            return

        try:
            PLF, IDs, QData = self.question_map[qid]
            QN = qid.split('::')[0]
            if self.data[self.EDIT_PAGE]['db']['QUESTIONS'].get(QN) == QData:
                self.data[self.EDIT_PAGE]['db']['QUESTIONS'].pop(QN)

                for ID in IDs:
                    self.question_map.pop(ID)

            else:
                log(LoggingLevel.ERROR, f'_rm_q failed: invalid data')
                assert False, f"_rm-q invalid data {QN} :: {QData}, {self.data[self.EDIT_PAGE]['db']['QUESTIONS'].get(QN)}"

        except Exception:
            log(LoggingLevel.DEBUG, f'_rm_q failed: {qid=} {traceback.format_exc()}')
            self.show_info(Message(Levels.ERROR, 'Failed to remove question; please try again'))

        else:
            log(LoggingLevel.INFO, f'_rm_q: removed {qid}')
            self.show_info(Message(Levels.OKAY, 'Successfully removed question'))

        self.update_questions()

    def _ed_q(self, qid: str) -> None:
        """
        Edit Question
            alias history:
            * _ed_q

        USED BY     QuestionFrame

        Edits a specific question in the database.

        :param qid: Unique Question ID
        :return:    None
        """

        if self.dsb:
            return

        self.disable_all_inputs()

        try:
            QN = qid.split('::')[0]
            _, _0, QData = self.question_map[qid]
            assert QData == self.data[self.EDIT_PAGE]['db']['QUESTIONS'].get(QN), 'invalid data'
            eSMem = qa_functions.SMem(8192)

            T, Q, A, Data0 = QData['0'], QData['1'], QData['2'], QData['d']
            if T[:2] == 'mc':
                assert T[2] == Data0[sum([a.size for a in qa_forms.question_editor_form.Data0.entries])]
                A = json.dumps(A)

            else:
                T += '0'

            for v in (T, Q, A, Data0): assert isinstance(v, str)

            d0Size = sum([a.size for a in qa_forms.question_editor_form.Data0.entries])
            exEntSize = sum([e.size for e in qa_forms.question_editor_form.Data1.exEntries])
            Data0 = Data0[:d0Size]  # Trim data1 ex values from data0

            index = qa_forms.question_editor_form.SMemInd
            sp = qa_forms.question_editor_form.S_MEM_VAL_OFFSET

            eSMem.set(Q, index.QUESTION.value * sp)
            eSMem.set(A, index.ANSWER.value * sp)
            eSMem.set(Data0, index.DATA0.value * sp)
            eSMem.set(T, index.DATA1.value * sp)

            qa_forms.question_editor_form.QEditUI(log, eSMem, True, **self.kwargs)

            nQ = eSMem.get(index.QUESTION.value * sp).strip()  # type: ignore
            nA = eSMem.get(index.ANSWER.value * sp).strip()  # type: ignore
            nD = eSMem.get(index.DATA0.value * sp).strip()  # type: ignore
            nT = eSMem.get(index.DATA1.value * sp).strip()  # type: ignore

            c = False
            for vO, vE in ((Q, nQ), (A, nA), (Data0, nD), (T, nT)):
                assert isinstance(vE, str)
                assert vE.strip() != eSMem.NullStr.strip(), 'nullStr'
                c |= (vO != vE)

            del Q, A, Data0, T, index, sp, eSMem

            if not c:
                log(LoggingLevel.WARNING, '_ed_q: no changes made; returning')
                self.enable_all_inputs()
                self.show_info(Message(Levels.ERROR, 'No changes made to question'))
                return

            nT = nT if nT[:2] == 'mc' else nT[:2]
            assert nT in ('mc0', 'mc1', 'nm', 'tf'), nT

            if len(nD) == d0Size:
                if len(nT) == 3:
                    nD += nT[-1]
                else:
                    nD += '0'

            assert len(nD) == d0Size + exEntSize, len(nD)

            if nT[:2] == 'mc':
                nA = json.loads(nA.strip())

            self.data[self.EDIT_PAGE]['db']['QUESTIONS'][QN] = {'0': nT.strip(), '1': nQ.strip(), '2': nA.strip() if isinstance(nA, str) else nA, 'd': nD.strip()}

        except Exception as E:
            log(LoggingLevel.ERROR, f'_ed_q: failed: {E}')
            log(LoggingLevel.DEBUG, f'_ed_q: failed: {traceback.format_exc()}')
            self.show_info(Message(Levels.ERROR, 'Failed to edit question; please try again'))

        else:
            log(LoggingLevel.SUCCESS, 'Edited question')
            self.show_info(Message(Levels.OKAY, 'Successfully edited question'))
            self.update_questions()

        self.enable_all_inputs()

    def _ad_q(self) -> None:
        """
        Add Question

            alias_history:
            * _ad_q

        USED BY     QuestionFrame

        Wrapper to add a new question to the database.

        :return: None
        """

        if self.dsb:
            return

        self.disable_all_inputs()

        try:
            eSMem = qa_functions.SMem(8192)
            qa_forms.question_editor_form.QEditUI(log, eSMem, False, **self.kwargs)

            d0Size = sum([a.size for a in qa_forms.question_editor_form.Data0.entries])
            exEntSize = sum([e.size for e in qa_forms.question_editor_form.Data1.exEntries])
            index = qa_forms.question_editor_form.SMemInd
            sp = qa_forms.question_editor_form.S_MEM_VAL_OFFSET

            nQ = eSMem.get(index.QUESTION.value * sp).strip()  # type: ignore
            nA = eSMem.get(index.ANSWER.value * sp).strip()  # type: ignore
            nD = eSMem.get(index.DATA0.value * sp).strip()  # type: ignore
            nT = eSMem.get(index.DATA1.value * sp).strip()  # type: ignore

            for vN in (nQ, nA, nD, nT):
                assert isinstance(vN, str), type(vN)
                assert vN != eSMem.NullStr, 'nullStr'

            del index, sp, eSMem

            nT = nT if nT[:2] == 'mc' else nT[:2]
            assert nT in ('mc0', 'mc1', 'nm', 'tf'), nT

            if len(nD) == d0Size:
                if len(nT) == 3:
                    # If it is a multiple choice question, then add the type of MCq to the end of the Data0 var. 
                    nD += nT[-1]
                    
                else:
                    nD += '0'

            assert len(nD) == d0Size + exEntSize, len(nD)

            if nT[:2] == 'mc':
                nA = json.loads(nA.strip())

            QN = str(len(self.data[self.EDIT_PAGE]['db']['QUESTIONS']))
            self.data[self.EDIT_PAGE]['db']['QUESTIONS'][QN] = {'0': nT.strip(), '1': nQ.strip(), '2': nA.strip() if isinstance(nA, str) else nA, 'd': nD.strip()}

        except Exception as E:
            log(LoggingLevel.ERROR, f'_ad_q: failed: {E}')
            log(LoggingLevel.DEBUG, f'_ad_q: failed: {traceback.format_exc()}')
            self.show_info(Message(Levels.ERROR, 'Failed to add question; please try again'))

        else:
            log(LoggingLevel.SUCCESS, 'Added question')
            self.show_info(Message(Levels.OKAY, 'Successfully added question'))
            self.update_questions()

        self.enable_all_inputs()

    def _aq(self, uid: str, data: dict) -> None:  # type: ignore
        """
        Add Question to AdminTools

            alias history:
            * _aq

        Adds a question to the admin tools question page.
        Displays the appropriate information.

        :param uid:     Unique Question ID
        :param data:    Question Data
        :return:        None
        """

        try:
            QN = uid
            QData = data

            TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

            QId = gsuid(QN)
            PLF = tk.LabelFrame(self.edit_question_frame, text=f"Question #{int(QN) + 1}")
            C = CustomText(PLF)

            RBId = f"E{gsuid('qUpdate<tmpEl>')}"
            RB = ttk.Button(PLF, command=lambda: self._rm_q(QId), style='Err.TButton', text='Remove')

            EBId = f"E{gsuid('qUpdate<tmpEl>')}"
            EB = ttk.Button(PLF, command=lambda: self._ed_q(QId), text='Edit')

            CId = f"E{gsuid('qUpdate<tmpEl>')}"
            C.auto_size()
            C.setup_color_tags(self.theme_update_map)

            C.delete('1.0', 'end')
            C.insert('end', 'Question Type: ')
            C.insert(
                'end',
                {
                    'nm': 'Written Response',
                    'mc0': "Multiple Choice",
                    'mc1': "Multiple Choice",
                    'tf': 'True/False'
                }[QData['0']],
                '<accent>'
            )
            C.insert('end', '\nQuestion: "')
            C.insert('end', QData['1'], '<accent>')
            if QData['0'] == 'nm':
                C.insert('end', f'"\n\nAnswer: "')
                C.insert('end', QData['2'], '<accent>')
                C.insert('end', '"')

                d0 = qa_forms.question_editor_form.Data0
                d0_opts = {}
                d0_acc = 0

                for d0_opt in d0.entries:
                    d0_opts[d0_opt.name] = QData['d'][d0_acc:d0_acc + d0_opt.size]
                    d0_acc += d0_opt.size

                opt_autoMark = int(d0_opts['auto_mark'])
                opt_fuzzy = int(d0_opts['fuzzy'])
                opt_fuzzyT = int(d0_opts['fuzzy:threshold'])

                C.insert('end', '\n\nFlags:')
                C.insert('end', '\t\u2022 AutoMark: ')
                C.insert('end', 'ENABLED' if opt_autoMark else 'DISABLED', '<accent>')

                if opt_autoMark:
                    C.insert('end', '\n\t\u2022 Marking Mode: ')
                    C.insert('end', 'Approximate Match' if opt_fuzzy else 'Exact Match', '<accent>')

                    if opt_fuzzy:
                        C.insert('end', '\n\t\u2022 % Match Required: ')
                        C.insert('end', f'{opt_fuzzyT}%', '<accent>')

            elif QData['0'] == 'tf':
                C.insert('end', f'"\n\nAnswer: ')
                C.insert('end', 'TRUE' if int(QData['2']) else 'FALSE', '<accent>')

            elif QData['0'][:2] == 'mc':
                C.insert('end', '\n\nOptions:\n')

                assert isinstance(QData['2'], dict)
                corr, N = QData['2']['C'].split('/'), QData['2']['N']
                NQData = copy.deepcopy(QData)
                NQData['2'].pop('C')
                NQData['2'].pop('N')
                assert len(NQData['2']) >= 2
                assert len(corr) > 0
                fn = qa_forms.question_editor_form.mc_label_gen

                opt_rnd = int(NQData['0'][2])

                for nIdentifier, v in NQData['2'].items():
                    identifier = fn(int(nIdentifier) + 1)
                    C.insert('end', '\t\u2022 Option ')
                    C.insert('end', identifier, '<error>' if nIdentifier not in corr else '<okay>')
                    C.insert('end', f') {v.strip()}\n')

                C.insert('end', '\nCorrect answer(s): ')
                C.insert('end', ', '.join([fn(int(cA) + 1) for cA in corr]), '<okay>')

                C.insert('end', '\n\nFlags:\n\t\u2022 ')
                C.insert('end', f'{"" if opt_rnd else "DO NOT "}Randomize Options', '<accent>')

            else:
                raise qa_functions.UnexpectedEdgeCase('_aq::!mc, !tf, !nm')

            C.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
            C.config(bd=0, highlightthickness=0, wrap=tk.WORD, state=tk.DISABLED)

            RB.pack(fill=tk.X, expand=True, padx=self.padX, pady=(0, self.padY), side=tk.LEFT)
            EB.pack(fill=tk.X, expand=True, padx=self.padX, pady=(0, self.padY), side=tk.RIGHT)

            self.question_map[CId] = C
            self.question_map[RBId] = RB
            self.question_map[EBId] = EB
            self.question_map[QId] = (PLF, [CId, RBId, EBId], QData)

            PLF.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

            self.late_update_requests[PLF] = [
                [
                    TUC.CUSTOM,
                    [
                        lambda *args: cast(tk.LabelFrame, args[0][0]).config(
                            bg=args[1], fg=args[2], font=(args[3], args[4]),
                            width=args[5] - args[6] * 3
                        ),
                        ('<LOOKUP>', 'QMap', QId),
                        TUV.BG, TUV.ACCENT, TUV.DEFAULT_FONT_FACE, TUV.FONT_SIZE_SMALL,
                        ('<LOOKUP>', 'root_width'), self.padX
                    ]
                ],
                [
                    TUC.CUSTOM,
                    [
                        lambda *args: cast(CustomText, args[0]).auto_size(),
                        ('<LOOKUP>', 'QMap', CId)
                    ]
                ],
                [
                    TUC.CUSTOM,
                    [
                        lambda *args, **kwargs: cast(CustomText, args[5]).config(
                            bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                            relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0]
                        ),
                        ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                        ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN,
                        ('<LOOKUP>', 'QMap', CId)
                    ]
                ]
            ]

        except Exception as E:
            log(LoggingLevel.ERROR, f'_aq failed: {E}')
            log(LoggingLevel.DEBUG, f'_aq failed: {uid=} {traceback.format_exc()}')

    def update_questions(self) -> None:
        """
        Update Questions in AdminTools

        alias history:
            * update_questions

        Updates the list of questions in the Admin Tools
        UI.

        :return:    None
        """

        self.disable_all_inputs()

        for QId, D in self.question_map.items():
            if QId[0] == 'E':  # extra data key
                continue

            cast(tk.LabelFrame, D[0]).pack_forget()
            try:
                self.late_update_requests.pop(cast(tk.LabelFrame, D[0]))
                assert D[0] not in self.late_update_requests
            except KeyError as K:
                log(LoggingLevel.DEBUG, f'_uq: KeyError ({K})')
            except AssertionError as A:
                log(LoggingLevel.DEBUG, f'_uq: AE ({A})')

        # Fix index errors
        Qs = list(self.data[self.EDIT_PAGE]['db']['QUESTIONS'].values())
        self.data[self.EDIT_PAGE]['db']['QUESTIONS'] = {}
        for ind, v in enumerate(Qs):
            self.data[self.EDIT_PAGE]['db']['QUESTIONS'][str(ind)] = v

        self.question_map = {}
        self.edit_question_canvas.pack_forget()

        for QN, QData in self.data[self.EDIT_PAGE]['db']['QUESTIONS'].items():
            self._aq(QN, QData)
            self.edit_question_canvas.yview_moveto(1.0)

        self.edit_question_canvas.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=(self.padY, 0))

        self.late_update_requests[self.edit_question_canvas] = [
            [
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: self.edit_question_canvas.config(width=args[0] - 4 * args[2]),
                    ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                    self.padX
                ]
            ],
            [
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: self.edit_question_frame.config(width=args[0] - 4 * args[2]),
                    ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                    self.padX
                ]
            ]
        ]

        self.enable_all_inputs()

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

        if self.edit_on_config_page:
            self.edit_configuration_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        else:
            self.edit_question_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_frame_config(self, _: Any) -> None:
        if self.edit_on_config_page:
            self.edit_configuration_canvas.configure(scrollregion=self.edit_configuration_canvas.bbox("all"))

        else:
            self.edit_question_canvas.configure(scrollregion=self.edit_question_canvas.bbox("all"))

    # ------------
    # Geometry Handlers
    # ------------

    def geo_large(self) -> None:
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")

    def geo_small(self) -> None:
        self.root.geometry(f"{self.window_size_2[0]}x{self.window_size_2[1]}+{self.screen_pos_2[0]}+{self.screen_pos_2[1]}")

    # -----
    # SETUP
    # -----

    def close(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.save_db()

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

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT, uid='title_label', font=ThemeUpdateVars.TITLE_FONT_FACE)
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
        self.label_formatter(self.select_lbl, size=TUV.FONT_SIZE_SMALL, uid='select_lbl', font=ThemeUpdateVars.TITLE_FONT_FACE)
        self.label_formatter(self.create_title, size=TUV.FONT_SIZE_TITLE, fg=TUV.ACCENT, uid='create_title', font=ThemeUpdateVars.TITLE_FONT_FACE)
        self.label_formatter(self.general_info_label, size=TUV.FONT_SIZE_SMALL, uid='general_info_label', font=ThemeUpdateVars.TITLE_FONT_FACE)

        self.root.bind('<3>', self.context_menu_show)
        self.root.bind('<F5>', self.update_ui)
        self.root.bind('<Control-r>', self.update_ui)
        self.root.bind('<MouseWheel>', self._on_mousewheel)

        self.configure_sel_frame()
        self.configure_create_frame()
        self.configure_edit_frame()
        self.configure_question_frame()
        self.configure_export_frame()

        self.ask_db_frame()
        self.update_ui()

        self.root.deiconify()
        self.root.focus_get()

    # ---------------------
    # Custom Event Handlers
    # ---------------------

    def export_pdf(self) -> None:
        """

        Export as PDF

        alias history:
            * export_pdf

        Exports the database as a PDF file.

        :return:    None
        """
        if self.dsb:
            return

        self.disable_all_inputs()
        self.show_info(Message(Levels.NORMAL, 'Please select where to save the file'))

        output_file = filedialog.asksaveasfilename(filetypes=(('.pdf', '.pdf'),), defaultextension='.pdf')

        try:
            assert isinstance(output_file, str), 'Output filename not provided (0xC1)'
            output_file = output_file.strip()
            assert output_file not in ['None', ''], 'Output filename not provided (0xC2)'

            pdf = PDF(self.theme_update_map[ThemeUpdateVars.ACCENT])  # type: ignore
            pdf.add_page()

            fSize = 12
            fSizeHdn = 15

            pdf.set_font("Courier", size=fSize)
            pdf.write(5, 'The following is the information stored in the ')
            pdf.set_font("Courier", 'B', size=fSize)
            pdf.write(5, f'"{self.data[self.EDIT_PAGE]["db_saved"]["DB"]["name"]}"')
            pdf.set_font("Courier", size=fSize)
            pdf.write(5, f' database.')
            pdf.ln()

            pdf.write(5, 'NOTE: Unsaved changes are NOT shown in this document.')

            for _ in range(18):
                pdf.ln()

            pdf.set_font('Courier', 'BI', size=24)
            pdf.write(10, 'WARNING: The information in this document is UNENCRYPTED; make sure to keep this file secure.')

            pdf.add_page()

            def add_point(txt: str, dt: str, bullet: str = '*', indent: int = 0) -> None:
                pdf.set_font("Courier", size=fSize)
                pdf.write(5, f'%s{bullet} {txt}: ' % ("\t" * indent))
                pdf.set_font("Courier", 'B', size=fSize)
                pdf.write(5, dt)
                pdf.ln()

            def add_heading(hdn: str, a2: bool = True) -> None:
                if a2:
                    pdf.ln()
                    pdf.ln()

                pdf.set_font("Courier", 'B', size=fSizeHdn)
                pdf.write(8, hdn)
                pdf.ln()

            add_point('Time when file was created', datetime.now().strftime('%a, %d %b %Y - %H:%M:%S'))

            add_heading('[i] Security Configuration')

            psw = self.data[self.EDIT_PAGE]['db_saved']['DB']['psw'][0]
            add_point('Database (admin) password', f'{"EN" if psw else "DIS"}ABLED')

            qpsw = self.data[self.EDIT_PAGE]['db_saved']['DB']['q_psw'][0]
            add_point('Quiz (access) password', f'{"EN" if qpsw else "DIS"}ABLED')

            add_heading('[ii] Quiz Configuration')

            acc = self.data[self.EDIT_PAGE]['db_saved']['CONFIGURATION']['acc']
            add_point('Allow custom quiz configuration', f'{"EN" if acc else "DIS"}ABLED')

            poa = self.data[self.EDIT_PAGE]['db_saved']['CONFIGURATION']['poa']
            add_point('Ask a subset of all questions, or with all questions', 'SUBSET' if poa == 'p' else 'ALL')

            ssd = self.data[self.EDIT_PAGE]['db_saved']['CONFIGURATION']['ssd']
            add_point('Percentage of questions to include', '1/1 (100%)' if poa != 'p' else f'1/{ssd} (~{1 / float(ssd)}%)')

            rqo = self.data[self.EDIT_PAGE]['db_saved']['CONFIGURATION']['rqo']
            add_point('Randomize Question Order', 'TRUE (RANDOMIZE)' if rqo else 'FALSE (DON\'T RANDOMIZE)')

            dpi = self.data[self.EDIT_PAGE]['db_saved']['CONFIGURATION']['dpi']
            a2d = self.data[self.EDIT_PAGE]['db_saved']['CONFIGURATION']['a2d']
            add_point('Points to be deducted per incorrect response', str(a2d) if dpi else '0')

            add_heading('WARNING: The next page(s) contains ALL questions and answers in PLAIN TEXT. Make sure to keep this document secure.')

            pdf.add_page()

            qs = self.data[self.EDIT_PAGE]['db_saved']['QUESTIONS']

            for ind, question in enumerate(qs.values()):
                t, q, a, d = question['0'], question['1'], question['2'], question['d']
                ts = {
                    'nm': 'Written Response',
                    'tf': 'True/False',
                    'mc0': 'Multiple Choice',
                    'mc1': 'Multiple Choice'
                }[t]

                add_heading(f'Question {ind + 1}', bool(ind))
                add_point('Question type', ts)
                add_point('Question', f'"{q}"')

                if t == 'nm':
                    add_point('Answer', f'"{a}"')

                    add_point('Flags', '')
                    d = d[:sum(e.size for e in qa_forms.question_editor_form.Data0.entries)]
                    dm = {}
                    da = 0

                    for e in qa_forms.question_editor_form.Data0.entries:
                        dd = d[da:da + e.size]
                        dm[e.name] = {
                            qa_forms.question_editor_form.DataType.integer: lambda x: int(x),
                            qa_forms.question_editor_form.DataType.string: lambda x: x,
                            qa_forms.question_editor_form.DataType.boolean: lambda x: bool(int(x))
                        }[e.type](dd)

                        da += e.size

                    add_point('AutoMark', f'{"EN" if dm["auto_mark"] else "DIS"}ABLED', bullet='-', indent=4)
                    if dm["auto_mark"]:
                        add_point('%% match required (100%% = exact match)', '100%' if not dm['fuzzy'] else f'{dm["fuzzy:threshold"]}%', bullet='-', indent=8)

                    del dm, da

                elif t == 'tf':
                    add_point('Answer', 'TRUE' if int(a) else 'FALSE')

                else:
                    assert isinstance(a, dict)
                    c = copy.deepcopy(a)

                    C = c['C'].split('/')
                    c.pop('C')
                    c.pop('N')

                    add_point('Options', '')

                    for index, v in c.items():
                        ident = qa_forms.qa_form_q_edit.mc_label_gen(int(index) + 1)
                        add_point(f'{ident})', v, bullet='', indent=4)

                        if index in C:
                            add_point(f'This option ("{ident}") is', 'CORRECT', indent=8)

                    del c, C

            del psw, qpsw, acc, poa, rqo, ssd, qs

            pdf.output(output_file)

        except PermissionError as PE:
            log(LoggingLevel.ERROR, f'[OS::PE] Failed to export PDF: {PE}')
            log(LoggingLevel.DEBUG, f'[OS::PE] Failed to export PDF: {traceback.format_exc()}')
            qa_prompts.MessagePrompts.show_warning(
                qa_prompts.InfoPacket(
                    'A "PermissionError" occurred when exporting the database. To make sure that this does not happen again, ensure the following:\n\n\u2022 Make sure that the destination folder is not write-protected.\n\u2022 If overwriting an existing file, make sure that that file is not open in/by any program\n\nIf this error persists, please reach out to the developer at https://geetanshgautam.wixsite.com/home.'
                )
            )
            self.show_info(Message(Levels.ERROR, 'Failed to export database dump as PDF'))

        except Exception as E:
            log(LoggingLevel.ERROR, f'Failed to export PDF: {E}')
            log(LoggingLevel.DEBUG, f'Failed to export PDF: {traceback.format_exc()}')
            self.show_info(Message(Levels.ERROR, 'Failed to export database dump as PDF'))

        else:
            self.show_info(Message(Levels.OKAY, 'Successfully exported database dump as PDF'))
            os.system(output_file)

        finally:
            self.enable_all_inputs()

    def export_qz(self) -> None:
        """
        Export Quizzing Database

        alias history:
            * export_qz

        Exports database as a Quizzing Form database.

        Note: Uses qa_files.QZ_GEN_LATEST

        :return:    None
        """

        self.save_db()
        nDB = copy.deepcopy(self.data[self.EDIT_PAGE]['db_saved'])
        
        sDB = qa_files.QZ_GEN_LATEST(
            ['QZDB', f'QZDB.R2<{qa_files.QZ_FRMT.QZDB_R2.value}>', *nDB['DB'].get('FLAGS', [])],
            nDB['DB']['q_psw'],
            nDB['DB']['psw'],
            nDB['DB']['name'],
            qa_functions.qa_info.App.build_id,
            qa_functions.qa_info.App.version,
            nDB['CONFIGURATION'],
            nDB['QUESTIONS']
        )[-1]
        
        self.show_info(Message(Levels.NORMAL, 'Please select where to save the file'))

        fl = filedialog.asksaveasfilename(filetypes=(('Quiz File', f'.{qa_files.qa_quiz_extn}'), )).strip()
        if len(fl) != 0:
            if fl.split('.')[-1] == qa_files.qa_quiz_extn:
                fl = fl[:-(len(qa_files.qa_quiz_extn) + 1)]

            qa_functions.SaveFile.secure(
                qa_functions.File(f'{fl}.{qa_files.qa_quiz_extn}'.replace('/', '\\')),
                qa_files.generate_file(qa_functions.FileType.QA_QUIZ, sDB)[0] + qa_files.C_QZ_TRAILING_ID.encode(),  # type: ignore
                qa_functions.SaveFunctionArgs(
                    False,
                    True,
                    qa_files.qa_quiz_enck,
                    True,
                    True,
                    save_data_type=bytes
                )
            )
            self.show_info(Message(Levels.OKAY, 'Successfully saved quiz file'))

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
            self.edit_export_btn.config(text='', compound=tk.CENTER)
            self.sb_expand_shrink.config(text='', image=self.svgs['arrow_right_large']['normal'], compound=tk.CENTER)
            self.edit_db_name.config(text='')
            self.edit_pic.config(text='')

        else:
            self.edit_configuration_btn.config(text='Configuration', compound=tk.LEFT)
            self.edit_questions_btn.config(text='Questions', compound=tk.LEFT)
            self.edit_export_btn.config(text='Export', compound=tk.LEFT)
            self.sb_expand_shrink.config(text='Shrink', image=self.svgs['arrow_left_large']['normal'], compound=tk.LEFT)
            self.edit_db_name.config(text=f"Current Database: \"{self.data[self.EDIT_PAGE]['db']['DB']['name']}\"")
            self.edit_pic.config(text="Admin Tools")

    def db_psw_toggle(self, *_0: Optional[Any], **kwargs: Optional[Any]) -> None:
        if self.EDIT_PAGE not in self.data:
            return

        cond = self.data[self.EDIT_PAGE]['db']['DB']['psw'][0]

        if not kwargs.get('nrst'):
            if not cond:
                if not cast(Tuple[Any, ...], self.db_psw_change())[2]:
                    self.show_info(Message(Levels.ERROR, "Couldn't set password."))
                    return

            cond = not cond
            self.data[self.EDIT_PAGE]['db']['DB']['psw'][0] = cond

        if cond:
            try:
                self.edit_db_psw_button.image = self.svgs['checkmark']['accent']  # type: ignore
                self.edit_db_psw_button.config(compound=tk.LEFT, image=self.svgs['checkmark']['accent'], style='Active.TButton')
            except Exception as E:
                self.edit_db_psw_button.config(style='Active.TButton')
                log(LoggingLevel.ERROR, f"Failed to add image to <edit_db_psw_button> : {E.__class__.__name__}({E})")
        else:
            self.data[self.EDIT_PAGE]['db']['DB']['psw'][1] = ''
            self.edit_db_psw_button.image = ''  # type: ignore
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
        rst = False

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
                            rst = True

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
        return f, f1, rst

    def qz_psw_toggle(self, *_0: Optional[Any], **kwargs: Optional[Any]) -> None:
        if self.EDIT_PAGE not in self.data:
            return

        cond = self.data[self.EDIT_PAGE]['db']['DB']['q_psw'][0]

        if not kwargs.get('nrst'):
            if not cond:
                if not cast(Tuple[Any, ...], self.qz_psw_change())[2]:
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
        rst = False

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
                            rst = True

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
        return f, f1, rst

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
        """
        Open Database Entry Point

        :param _0:      ARGS
        :param _1:      KWARGS
        :return:        None
        """

        global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME

        if self.dsb or self.busy:
            return

        self.busy = True
        self.disable_all_inputs()

        try:
            file_name = filedialog.askopenfilename(filetypes=[('QA File', f'.{qa_files.qa_file_extn}')])
            if os.path.isfile(file_name):
                if file_name.split('.')[-1] == qa_files.qa_file_extn:
                    file = qa_functions.File(file_name)
                    raw = qa_functions.OpenFile.load_file(file, qa_functions.OpenFunctionArgs())
                    self.open(file_name, qa_files.QADB_ReadData(raw)[0], False)

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
        self.edit_on_config_page = True
        log(LoggingLevel.DEBUG, 'Entered EDIT::CONFIGURATION page')
        self.edit_configuration_btn.config(style='ActiveLG.TButton', image=self.svgs['settings_cog_large']['accent'])
        self.edit_questions_btn.config(style='LG.TButton', image=self.svgs['question_large']['normal'])
        self.edit_export_btn.config(style='LG.TButton', image=self.svgs['export_large']['normal'])

        self.db_psw_toggle(nrst=True)
        self.qz_psw_toggle(nrst=True)

        self.edit_question_master_frame.pack_forget()
        self.edit_export_master_frame.pack_forget()
        self.edit_configuration_master_frame.pack(fill=tk.BOTH, expand=True)

        self.update_ui()

    def edit_questions(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.edit_on_config_page = False
        log(LoggingLevel.DEBUG, 'Entered EDIT::QUESTIONS page')
        self.edit_questions_btn.config(style='ActiveLG.TButton', image=self.svgs['question_large']['accent'])
        self.edit_configuration_btn.config(style='LG.TButton', image=self.svgs['settings_cog_large']['normal'])
        self.edit_export_btn.config(style='LG.TButton', image=self.svgs['export_large']['normal'])

        self.edit_configuration_master_frame.pack_forget()
        self.edit_export_master_frame.pack_forget()
        self.edit_question_master_frame.pack(fill=tk.BOTH, expand=True)

        self.update_questions()
        self.update_ui()

    def edit_export(self, *_: Any, **_1: Any) -> None:
        self.edit_on_config_page = False
        log(LoggingLevel.DEBUG, 'Entered EDIT::EXPORT page')
        self.edit_questions_btn.config(style='LG.TButton', image=self.svgs['question_large']['normal'])
        self.edit_configuration_btn.config(style='LG.TButton', image=self.svgs['settings_cog_large']['normal'])
        self.edit_export_btn.config(style='ActiveLG.TButton', image=self.svgs['export_large']['accent'])

        self.edit_question_master_frame.pack_forget()
        self.edit_configuration_master_frame.pack_forget()
        self.edit_export_master_frame.pack(fill=tk.BOTH, expand=True)

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
                            if '0x' in k1 and k2 in k1:
                                # "<INT>" -> "0x...<INT>" (for questions)
                                log(LoggingLevel.WARNING, f'FCC (KoKt) (+BYP) - "{k1}" vs "{k2}"')
                                new[k1] = og[k1]
                                new.pop(k2)
                            else:
                                log(LoggingLevel.ERROR, f'FCC (KoKt) - "{k1}" vs "{k2}"')
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
        if len(changes[0]) == 0:
            changes = ([('<QA::int_code:comp_ch::LL>', None, None)], changes[1])

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

            '<QA::int_code:comp_ch::LL>': [
                'Low-Level (Technical) Items (may include questions). This may occur when the file\'s version is upgraded automatically.',
                False,
                False
            ],
        }

        c = []
        for n, og, new in changes:
            if isinstance(n, tuple):
                n, ind = n
                nf, nd = qa_functions.data_at_dict_path(f'{n}\\{ind}', n_map)
            else:
                nf, nd = qa_functions.data_at_dict_path(str(n), n_map)

            if nf:
                name, show, v_trans = nd
            else:
                name, show, v_trans = 'Un-indexed items (may involve questions)', False, False

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

        c = list(set(c))
        return "\n   \u2022 " + "\n   \u2022 ".join(c)

    def save_db(self, _do_not_prompt: bool = False, **kwargs: Any) -> None:
        """

        :keyword _force_save:   DO NOT CHECK FOR CHANGES WHEN SAVING. TYPE: BOOL

        :param _do_not_prompt:  DO NOT PROMPT USER (DEF FALSE)
        :param kwargs:          KEYWORD ARGUMENTS
        :return:                NONE
        """

        kwargs['_force_save'] = kwargs.get('_force_save', False)
        assert isinstance(kwargs['_force_save'], bool)

        s_mem = qa_functions.SMem()
        s_mem.set('n')

        if not kwargs['_force_save']:
            changed, [changes, failures] = self.compile_changes()

            if not changed:
                self.show_info(Message(Levels.ERROR, 'No changes found'))
                return

            if len(failures) > 0:
                Str = "Failed to compile changes made due to the following error(s):\n\t\u2022 " + \
                      "\n\t\u2022 ".join(f for f in failures)
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

        else:
            _do_not_prompt = True

        r = s_mem.get()

        if r is None and not _do_not_prompt:
            return

        assert isinstance(r, str)

        if r.strip() == 'y' or _do_not_prompt:

            def _to_questions(questions: Dict[str, Any]) -> List[qa_files.qa_file.Question]:
                return \
                    [
                        qa_files.qa_file.Question(
                            D0=question[qa_files.qa_file.ALPHA_ONE.L2_QBANK_D0],
                            question=question[qa_files.qa_file.ALPHA_ONE.L2_QBANK_Q],
                            answer=question[qa_files.qa_file.ALPHA_ONE.L2_QBANK_A],
                            D1=question[qa_files.qa_file.ALPHA_ONE.L2_QBANK_D1]
                        )
                        for question in questions.values()
                    ]

            file = qa_functions.File(self.data[self.EDIT_PAGE]['db_path'])
            new_str = qa_files.QA_GEN_LATEST(
                str(qa_info.App.version),
                qa_info.App.build_id,
                int(qa_info.App.version),
                qa_info.App.build_name,
                qa_info.App.DEV_MODE,
                self.data[self.EDIT_PAGE]['db']['DB']['name'],
                qa_files.qa_file.Configuration(
AllowCustomQuizConfiguration=self.data[self.EDIT_PAGE]['db']['CONFIGURATION'][qa_files.qa_file.ALPHA_ONE.L2_CONFIG_ACC[0]],
DS_SubsetMode=(self.data[self.EDIT_PAGE]['db']['CONFIGURATION'][qa_files.qa_file.ALPHA_ONE.L2_CONFIG_POA[0]] == 'p'),
DS_SubsetDiv=self.data[self.EDIT_PAGE]['db']['CONFIGURATION'][qa_files.qa_file.ALPHA_ONE.L2_CONFIG_SSD[0]],
DS_RandomizeQuestionOrder=self.data[self.EDIT_PAGE]['db']['CONFIGURATION'][qa_files.qa_file.ALPHA_ONE.L2_CONFIG_RQO[0]],
RM_Deduct=self.data[self.EDIT_PAGE]['db']['CONFIGURATION'][qa_files.qa_file.ALPHA_ONE.L2_CONFIG_DPI[0]],
RM_DeductionAmount=self.data[self.EDIT_PAGE]['db']['CONFIGURATION'][qa_files.qa_file.ALPHA_ONE.L2_CONFIG_A2D[0]],
                ),
                _to_questions(self.data[self.EDIT_PAGE]['db']['QUESTIONS']),
                self.data[self.EDIT_PAGE]['db']['DB']['q_psw'],
                self.data[self.EDIT_PAGE]['db']['DB']['psw'],
            )[-1]

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

        file_name = filedialog.asksaveasfilename(filetypes=[('QA File', qa_files.qa_file_extn)])
        if file_name is None:
            self.proc_exit(self.CREATE_PAGE)
            self.show_info(Message(Levels.NORMAL, 'Aborted process.'))
            return
        if not os.path.isdir('\\'.join(file_name.replace('/', '\\').split('\\')[:-2:])):
            self.proc_exit(self.CREATE_PAGE)
            self.show_info(Message(Levels.NORMAL, 'Aborted process.'))
            return

        psw_ld = self.create_inp2_var.get().strip() if self.data[self.CREATE_PAGE]['psw_enb'] else ''

        file = qa_functions.File(f'{file_name}.{qa_files.qa_file_extn}' if file_name.split('.')[-1] != qa_files.qa_file_extn else file_name)
        db_starter_dict = {
            'DB': {
                'name': self.create_inp1_var.get(),
                'psw': [self.data[self.CREATE_PAGE]['psw_enb'], hashlib.sha3_512(psw_ld.encode()).hexdigest() if len(psw_ld) > 0 else ''],
                'q_psw': [False, '']
            },
            'CONFIGURATION': None,
            'QUESTIONS': None
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

        self.open(file.file_path, db_starter_dict, True, True)

    @staticmethod
    def _clean_db(db: Dict[str, Any]) -> Dict[str, Any]:
        assert isinstance(db, dict)
        name_f, name_d = qa_functions.data_at_dict_path('DB/name', db)
        assert name_f

        log(LoggingLevel.INFO, '_clean_db - Checking database integrity')

        def rs_name() -> None:
            log(LoggingLevel.ERROR, '_clean_db::DBCleaner - Name data corrupted')

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

            log(LoggingLevel.ERROR, f'_clean_db::DBCleaner - Name reset to \"{res}\"')

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
            log(LoggingLevel.ERROR, '_clean_db::DBCleaner - DB_PSW corruption; reset.')
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
            log(LoggingLevel.ERROR, '_clean_db::DBCleaner - QZ_PSW corruption; reset.')
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('Quiz password corrupted; protection disabled.'))
            db['DB']['q_psw'] = [False, '']

        # Configuration checks
        cr = 'CONFIGURATION'
        cd = db.get(cr)

        if not cd:
            log(LoggingLevel.ERROR, "_clean_db::ConfigurationCleaner - Configuration data not found; resetting configuration data. ")
            db[cr] = {
                'acc': False,  # Allow custom quiz configuration
                'poa': 'p',  # Part or all
                'rqo': False,  # Randomize question order
                'ssd': 2,  # Subsample divisor
                'dpi': False,  # Deduct points on incorrect (responses)
                'a2d': 1  # Amount of points to deduct
            }
        elif isinstance(cd, dict):
            f: List[Any] = []

            for k, (tp, default, opts) in (
                    ('acc', (bool, False, [])),
                    ('poa', (str, 'p', ['p', 'a'])),
                    ('rqo', (bool, False, [])),
                    ('ssd', (int, 2, [])),
                    ('dpi', (bool, False, [])),
                    ('a2d', (int, 1, [])),
            ):
                assert isinstance(k, str)
                assert isinstance(opts, (list, tuple, set))

                if not isinstance(cd.get(k), tp):
                    f.append(f'"{k}": tp_check failed; restoring value to "{default}"')
                    cd[k] = default
                    continue

                if len(cast(Sized, opts)) > 0:
                    if cd.get(k) not in opts:
                        f.append(f'"{k}": opt_check failed; restoring value to "{default}"')
                        cd[k] = default
                        continue

                log(LoggingLevel.SUCCESS, f'_clean_db::ConfigurationCleaner - Value for "{k}" is okay (tp, opt).')

            for failure in f:
                log(LoggingLevel.ERROR, f'_clean_db::ConfigurationCleaner - {failure}')

            db[cr] = cd

        else:
            raise qa_functions.UnexpectedEdgeCase('_clean_db::?ConfigurationData (cd) :: !dict, !NoneType')

        qr = 'QUESTIONS'
        qd = db.get(qr)
        cQAcc = 0
        cQN = []

        if qd is None:
            log(LoggingLevel.ERROR, "_clean_db::QuestionCleaner - Question data not found; resetting.")
            db[qr] = {}

        elif isinstance(qd, dict):
            if not qd:
                log(LoggingLevel.WARNING, '_clean_db::QuestionCleaner - No questions in database')

            for k, v in qd.items():
                try:
                    assert isinstance(k, str), f'Question key must be of type STRING; got {type(k)} (qTe::tpT1)'
                    # try:
                    #     int(k)
                    # except Exception as e1:
                    #     raise AssertionError('Question key MUST be able to be translated to an integer (qTe::tpT2)')

                    assert isinstance(v, dict), 'Invalid answer data (aTe::tpT1)'
                    assert len(v.values()) == 4, 'Invalid answer data (aTe::vv2)'
                    assert min([vk in v for vk in ('0', '1', '2', 'd')]), f'Data key(s) not found in answer data (aTe::vk3)'

                    t, q, a, d = v['0'], v['1'], v['2'], v['d']
                    assert t in ('nm', 'tf', 'mc0', 'mc1'), f'Answer type data is invalid (aTe::aTp4)'
                    assert isinstance(q, str), 'Question type is invalid (qTe::TpF)'
                    assert isinstance(d, str), '"Data0" type is invalid (dTe::Tp1)'
                    assert isinstance(a, str if t[:2] != 'mc' else dict), 'Answer type is invalid (aTe::TpF)'

                    dSize = sum([d0.size for d0 in qa_forms.question_editor_form.Data0.entries]) + \
                            sum([d1.size for d1 in qa_forms.question_editor_form.Data1.exEntries])

                    assert len(d) == dSize, f'"Data0" size is invalid (expected {dSize}, got {len(d)}) (dTe::Ln2)'
                    if t[:2] == 'mc':
                        assert t[2] == d[sum([d0.size for d0 in qa_forms.question_editor_form.Data0.entries])], \
                            '"Data0" + MCR bit do not match (dTe+tTe::m1)'
                        assert len(cast(Dict[str, Union[int, str]], a)) >= 4, \
                            'MC question does not contain enough options (Min. = 2 options) (aTe::mc1)'

                except Exception as E:
                    cQAcc += 1
                    log(LoggingLevel.DEBUG, traceback.format_exc())
                    log(LoggingLevel.ERROR, f'cQAcc+ :: {E}')

                    cQN.append(k)

                    qa_prompts.MessagePrompts.show_error(
                        qa_prompts.InfoPacket(
                            f'A question in the database had a fatal error and must be removed from the database.\n\n    \u2022 Error: {E}\n    \u2022 E. Code: {hashlib.md5(str(E).encode()).hexdigest()}\n\n\nYOU WILL BE PROMPTED FOR PERMISSION TO REMOVE QUESTION AFTER ALL QUESTIONS HAVE BEEN CHECKED.'
                        )
                    )

            for k in cQN:
                db[qr].pop(k)
                log(LoggingLevel.WARNING, f'Marked question "{k}" for removal')

            # Fix any erroneous labels
            nLs = list(db[qr].values())
            db[qr] = {}
            for ind, v in enumerate(nLs):
                db[qr][('0x' + qa_functions.clamp(0, 12 - len(hex(ind)), 9e9) * '0' + hex(ind)[2::])] = v  # type: ignore

        else:
            raise qa_functions.UnexpectedEdgeCase('_clean_db::?QuestionData (qd) :: !dict, !NoneType')

        if cQAcc:
            log(LoggingLevel.ERROR, f'_clean_db::QuestionCleaner - {cQAcc} questions corrupted')
        else:
            log(LoggingLevel.SUCCESS, f'_clean_db::QuestionCleaner - Successfully loaded questions (no errors found)')

        return db

    def open_d(self, path: str, data: Dict[Any, Any], _bypass_psw: bool = False, _no_prompt: bool = False, **kwargs: Any) -> None:
        """

        :key _force_new_version:    FORCE USER TO SAVE DB AS PER THE LATEST SPECIFICATION. TYPE: BOOL

        :param path:                PATH TO DB
        :param data:                DATA IN DB (DICT)
        :param _bypass_psw:         BYPASS PASSWORD PROTECTION (DEF FALSE)
        :param _no_prompt:          DO NOT PROMPT USER (DEF FALSE)
        :param kwargs:              KEYWORD ARGUMENTS
        :return:                    NONE
        """
        assert os.path.isfile(path)
        assert type(data) is dict

        kwargs['_force_new_version'] = kwargs.get('_force_new_version', False)
        assert isinstance(kwargs['_force_new_version'], bool)

        self.enable_all_inputs()

        try:
            if isinstance(data['DB'].get('FLAGS'), (tuple, list, set)):
                assert 'QZDB' not in data['DB']['FLAGS']  # Do not want to open a Qzdb file
            
            O_data = copy.deepcopy(data)
            n_data = self._clean_db(data)

            self.data[self.EDIT_PAGE] = {'db_path': path}
            self.data[self.EDIT_PAGE]['db'] = n_data
            self.data[self.EDIT_PAGE]['db_saved'] = O_data

            changed, (changes, failures) = self.compile_changes()

            for failure in failures:
                log(LoggingLevel.ERROR, f'open::comp_c::Failure - {failure}')

            if changed:
                if not _no_prompt:
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

                else:
                    self.save_db(True)

            elif kwargs['_force_new_version']:
                s_mem = qa_functions.SMem()
                s_mem.set('')
                qa_prompts.InputPrompts.ButtonPrompt(
                    s_mem,
                    'New Database Version Available.',
                    ('Update now', 'un'), ('Exit', 'ex'),
                    default='ex',
                    message='The app has detected that you\'re using an outdated version of the QA_FILE format.' +
                            '\n\nTo continue, you must first update the file to the latest specification.'
                )

                if s_mem.get() != 'un':
                    self.proc_exit(self.SELECT_PAGE)
                    self.show_info(Message(Levels.ERROR, 'Aborted process.'))
                    return

                else:
                    self.save_db(True, _force_save=True)

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

    def open_n(self, path: str, data: qa_files.QADB, _bypass_psw: bool = False, _no_prompt: bool = False) -> None:
        """
        Open database

        Overload variant
        Uses question answer database for its data input.
        Is backwards compatible as QADB should be generated by qa_files.qa_file

        NOTE:                   Calls _UI.open variant with DB-1 COMPLIANT dict
                                Passes all other arguments to that function without any
                                changes.

        NOTE:                   Adds KEYWORD-ARG '_force_new_format' to data_d call as
                                per the result of the expr 'not data.LatestFileMode'

        :param path:            path to db
        :param data:            data
        :param _bypass_psw:     bypass password protection
        :param _no_prompt:      do not prompt user for any reason.

        :return:                None
        """

        assert os.path.isfile(path)
        assert type(data) is qa_files.QADB

        self.open_d(
            path,
            qa_files.QA_ToAlphaOne(data),
            _bypass_psw,
            _no_prompt,
            _force_new_version=(not data.LatestFileMode)
        )

        return

    def open(
            self,
            path: str,
            data: qa_files.QADB | Dict[Any, Any],
            _bypass_psw: bool = False,
            _no_prompt: bool = False
    ) -> None:
        match str(type(data)):
            case "<class 'dict'>":
                log(LoggingLevel.WARNING, 'USING DEPRECATED OPEN_D FUNCTION USING DIRECT CALL.')
                return self.open_d(path, cast(Dict[Any, Any], data), _bypass_psw, _no_prompt)
            case "<class 'qa_files.qa_file.QuestionAnswerDB'>":
                log(LoggingLevel.INFO, 'Using OPEN_N function.')
                return self.open_n(path, cast(qa_files.QADB, data), _bypass_psw, _no_prompt)
            case other:
                raise qa_functions.UnexpectedEdgeCase

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
        try:
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

        except RuntimeError as E:
            log(LoggingLevel.ERROR, str(E))

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
        try:
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
                                        'QMap': self.question_map.get(arg[2]) if len(arg) >= 3 else None,
                                        'El': element
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

        except RuntimeError as E:
            log(LoggingLevel.ERROR, str(E))

    def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN,
                         padding: Union[None, int] = None, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, abg: ThemeUpdateVars = ThemeUpdateVars.ACCENT, afg: ThemeUpdateVars = ThemeUpdateVars.BG,
                         uid: Union[str, None] = None) -> None:
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
            ThemeUpdateVars.TITLE_FONT_FACE: self.theme.title_font_face,
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
            (self.export_src, 'export_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('export', 'accent')),
            (self.export_src, 'export', self.theme.background, self.theme.accent, self.theme.font_main_size, ('export', 'normal')),

            (self.checkmark_src, 'c_mark_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('checkmark_large', 'normal')),
            (self.checkmark_src, 'c_mark_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('checkmark_large', 'accent')),
            (self.cog_src, 'cog_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('settings_cog_large', 'normal')),
            (self.cog_src, 'cog_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('settings_cog_large', 'accent')),
            (self.arrow_right_src, 'arrow_right_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_right_large', 'normal')),
            (self.arrow_right_src, 'arrow_right_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_right_large', 'accent')),
            (self.arrow_left_src, 'arrow_left_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_left_large', 'normal')),
            (self.arrow_left_src, 'arrow_left_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_left_large', 'accent')),
            (self.question_src, 'question_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('question_large', 'normal')),
            (self.question_src, 'question_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('question_large', 'accent')),
            (self.export_src, 'export_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('export_large', 'normal')),
            (self.export_src, 'export_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('export_large', 'accent')),
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
                    self.edit_qz_psw_reset_btn, self.edit_qz_psw_button,
                    self.edit_question_add_new_btn, self.edit_questions_save_btn,
                    self.edit_export_btn, self.edit_export_qz, self.edit_export_pdf):
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        self.dsb = False

        for btn in (self.select_open, self.select_new, self.select_scores,
                    self.edit_questions_btn, self.edit_configuration_btn,
                    self.edit_db_psw_reset_btn, self.edit_db_psw_button,
                    self.edit_qz_psw_reset_btn, self.edit_qz_psw_button,
                    self.edit_question_add_new_btn, self.edit_questions_save_btn,
                    self.edit_export_btn, self.edit_export_qz, self.edit_export_pdf):
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
    transfer_log_info(qa_prompts)
    transfer_log_info(qa_forms.question_editor_form)

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
    script.LOGGER_FUNC = LOGGER_FUNC  # type: ignore
    script.LOGGING_FILE_NAME = LOGGING_FILE_NAME  # type: ignore
    script.DEBUG_NORM = DEBUG_NORM  # type: ignore
    script.DEBUG_DEV_FLAG = DEBUG_DEV_FLAG  # type: ignore
