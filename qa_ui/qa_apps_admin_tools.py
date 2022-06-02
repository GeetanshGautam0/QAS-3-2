import sys, qa_functions, qa_files, os, traceback, PIL, json, copy, subprocess
from . import qa_prompts
from threading import Thread
from tkinter import ttk, filedialog
from qa_functions.qa_std import *
from .qa_prompts import gsuid, configure_scrollbar_style
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from dataclasses import dataclass
from enum import Enum
from ctypes import windll


script_name = "APP_AT"
APP_TITLE = "Quizzing Application | Admin Tools"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
MAX = 50
_Fs = True


class Levels(Enum):
    (NORMAL, OKAY, WARNING, ERROR) = range(4)


@dataclass
class Message:
    LVL: Levels
    MSG: str


class _UI(Thread):
    def __init__(self, root, ic, ds, **kwargs):
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

        self.theme: qa_functions.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map = {}

        self.padX = 20
        self.padY = 10

        self.gi_cl = True
        self._job = None

        self.load_theme()
        self.update_requests = {}
        self.late_update_requests = {}
        self.data = {}

        self.img_path = qa_functions.Files.AT_png
        self.img_size = (75, 75)
        self.svgs = {
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

        self.ttk_theme = self.kwargs['ttk_theme']

        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Admin')

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
        self.select_open = ttk.Button(self.select_frame, text="Open Existing DB", command=lambda: self.root.focus_get().event_generate('<<OpenDB>>'))
        self.select_new = ttk.Button(self.select_frame, text="Create New DB", command=lambda: self.root.focus_get().event_generate('<<NewDB>>'))
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
        self.create_create = ttk.Button(self.create_btn_frame, text="Create", command=lambda: self.root.focus_get().event_generate('<<CreateDB_MAIN>>'))

        self.general_info_label = tk.Label(self.root, text="")

        # Main elements (Edit page)
        self.edit_sidebar = tk.Frame(self.db_frame)
        self.edit_pic = tk.Label(self.edit_sidebar)
        self.edit_db_name = tk.Label(self.edit_sidebar)
        self.edit_btn_panel = tk.Frame(self.edit_sidebar)
        self.edit_sep = ttk.Separator(self.db_frame)

        # Menu Buttons (Edit page)
        self.edit_configuration_btn = ttk.Button(self.edit_btn_panel, text='Configuration', command=lambda: self.root.focus_get().event_generate('<<EditConfiguration>>'))
        self.edit_questions_btn = ttk.Button(self.edit_btn_panel, text='Questions', command=lambda: self.root.focus_get().event_generate('<<EditQuestions>>'))

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
        self.edit_db_psw_button = ttk.Button(self.edit_db_psw_container, command=lambda: self.root.focus_get().event_generate('<<EDIT_DB_PSW_CLICK>>'))
        self.edit_db_psw_reset_btn = ttk.Button(self.edit_db_psw_container, command=lambda: self.root.focus_get().event_generate('<<EDIT_DB_PSW_RESET>>'))

        self.edit_qz_psw_lbl = tk.Label(self.edit_qz_psw_container)
        self.edit_qz_psw_button = ttk.Button(self.edit_qz_psw_container, command=lambda: self.root.focus_get().event_generate('<<EDIT_QZ_PSW_CLICK>>'))
        self.edit_qz_psw_reset_btn = ttk.Button(self.edit_qz_psw_container, command=lambda: self.root.focus_get().event_generate('<<EDIT_QZ_PSW_RESET>>'))

        self.edit_configuration_save = ttk.Button(self.edit_configuration_frame, text="Save Changes", command=self.save_db)
        self.sb_expand_shrink = ttk.Button(self.edit_sidebar, command=lambda: self.root.focus_get().event_generate('<<SideBar_Expand_Shrink>>'))

        self.edit_config_main_cont = tk.LabelFrame(self.edit_configuration_frame, text='Quiz Configuration')
        self.edit_config_acc_cont = tk.LabelFrame(self.edit_config_main_cont, text="Custom Quiz Configuration")
        self.edit_config_poa_cont = tk.LabelFrame(self.edit_config_main_cont, text="Quiz Distribution Settings")
        self.edit_config_ddc_cont = tk.LabelFrame(self.edit_config_main_cont, text="Penalty Configuration")

        # Config::ACC
        self.edit_config_acc_lbl = tk.Label(self.edit_config_acc_cont)

        self.start()
        self.root.mainloop()

    # -------------------
    # Frame Configurators
    # -------------------

    def configure_create_frame(self):
        self.create_title.config(justify=tk.LEFT, anchor=tk.W)
        self.create_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.create_inp1.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.create_inp1_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.create_add_psw_sel.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.create_inp2_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=(0, self.padY))
        self.create_config_frame.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.create_btn_frame.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY)
        self.create_cancel.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, ipady=self.padY/2)
        self.create_create.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, ipady=self.padY/2)

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

    def configure_sel_frame(self):
        self.select_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.TOP)
        self.select_open.pack(fill=tk.X, expand=True, padx=self.padX, pady=(self.padY, 0), ipady=self.padY)
        self.select_new.pack(fill=tk.X, expand=True, padx=self.padX, ipady=self.padY)
        self.select_scores.pack(fill=tk.X, expand=False, padx=self.padX, pady=(0, self.padY), side=tk.BOTTOM, ipady=self.padY)

    def configure_edit_frame(self):
        global DEBUG_NORM

        # Layout
        self.edit_pic.pack(fill=tk.BOTH, expand=False, pady=self.padY*2, padx=self.padX)
        self.edit_pic.config(text='Admin Tools', image=self.svgs['admt'], compound=tk.TOP)

        self.sb_expand_shrink.pack(fill=tk.X, expand=False, pady=(self.padY*2, 0), side=tk.BOTTOM)

        self.edit_db_name.pack(fill=tk.X, expand=False, pady=self.padY, padx=self.padX, side=tk.BOTTOM)
        self.edit_btn_panel.pack(fill=tk.X, expand=False, pady=self.padY)

        self.edit_configuration_btn.pack(fill=tk.X, expand=True, ipady=self.padY/2)
        self.edit_questions_btn.pack(fill=tk.X, expand=True, ipady=self.padY/2)

        self.edit_sidebar.pack(fill=tk.Y, expand=False, side=tk.LEFT)
        self.edit_sep.pack(fill=tk.Y, expand=False, side=tk.LEFT, pady=(self.padY, 0))

        # Configuration Frame
        self.edit_configuration_vsb.pack(fill=tk.Y, expand=False, padx=(0, self.padX), pady=self.padY, side=tk.RIGHT)
        self.edit_configuration_canvas.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=self.padY)

        self.edit_configuration_title.config(text="Configuration Manager")
        self.edit_configuration_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY*2, side=tk.TOP)

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

        self.edit_configuration_save.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX, pady=self.padY, ipady=self.padY/2)

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

        # Scrollbar setup
        self.edit_configuration_vsb.configure(command=self.edit_configuration_canvas.yview)
        self.edit_configuration_canvas.configure(yscrollcommand=self.edit_configuration_vsb.set)

        self.edit_configuration_canvas.create_window(
            (0, 0),
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
        if self.edit_config_acc_lbl not in self.late_update_requests:
            self.late_update_requests[self.edit_config_acc_lbl] = []

        self.late_update_requests[self.edit_config_acc_lbl].extend(
            [
                [
                    COM.CUSTOM,
                    [
                        lambda *args: self.edit_config_acc_lbl.config(wraplength=args[0]-2*args[1]),
                        ('<EXECUTE>', lambda *args: self.edit_config_acc_lbl.winfo_width()),
                        ('<LOOKUP>', 'padX')
                    ]
                ],
                [
                    COM.CUSTOM,
                    [
                        lambda *args: log(LoggingLevel.DEVELOPER, f"[LUpdate[LU]::Rule_WrLP_Auto] wraplength=({args[0]} - 2*{args[1]}) = {args[0] - 2 * args[1]} {ANSI.RESET}"),
                        ('<EXECUTE>', lambda *args: self.edit_configuration_frame.winfo_width()),
                        ('<LOOKUP>', 'padX'),
                    ] if DEBUG_NORM and qa_functions.App.DEV_MODE else [lambda *args: None]
                 ],
                [
                    COM.CUSTOM,
                    [self.edit_config_acc_lbl.update]
                ]
            ]
        )

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
        self.update_requests['edit_config_poa_cont0'] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_config_poa_cont.config(
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
                    bg=args[0], fg=args[1], font=(args[2], args[3]) #, font=args[2:3]
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
        self.update_requests['UpRule[d]::<db_psw_toggle>0'] = [None, COM.CUSTOM, [lambda: self.db_psw_toggle(nrst=True)]]
        self.update_requests['UpRule[d]::<qz_psw_toggle>0'] = [None, COM.CUSTOM, [lambda: self.qz_psw_toggle(nrst=True)]]

        del COM, VAR

    # -----------------
    # LL Event Handlers
    # -----------------

    def _on_mousewheel(self, event):
        """
        Straight out of stackoverflow
        Article: https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        Change: added "int" around the first arg
        """
        self.edit_configuration_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def onFrameConfig(self, event):
        self.edit_configuration_canvas.configure(scrollregion=self.edit_configuration_canvas.bbox("all"))

    # ------------
    # GEO Handlers
    # ------------

    def geo_large(self):
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")

    def geo_small(self):
        self.root.geometry(f"{self.window_size_2[0]}x{self.window_size_2[1]}+{self.screen_pos_2[0]}+{self.screen_pos_2[1]}")

    # -----
    # SETUP
    # -----

    def close(self, *_0, **_1):
        sys.stdout.write("at - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.quit()

    def run(self):
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
        self.menu_file.add_command(label='Create New Database', command=lambda: self.root.focus_get().event_generate('<<NewDB>>'))
        self.menu_file.add_command(label='Open Database', command=lambda: self.root.focus_get().event_generate('<<OpenDB>>'))
        self.menu_file.add_command(label='Close Database', command=lambda: self.root.focus_get().event_generate('<<CloseDB>>'))

        self.context_menu.add_command(label='Create New Database', command=lambda: self.root.focus_get().event_generate('<<NewDB>>'))
        self.context_menu.add_command(label='Open Database', command=lambda: self.root.focus_get().event_generate('<<OpenDB>>'))
        self.context_menu.add_command(label='Close Database', command=lambda: self.root.focus_get().event_generate('<<CloseDB>>'))

        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=lambda: self.root.focus_get().event_generate('<<ExitCall>>'))

        self.update_requests['select_frame0'] = [self.select_frame, TUC.BG, [TUV.BG]]
        self.update_requests['db_frame0'] = [self.db_frame, TUC.BG, [TUV.BG]]
        self.update_requests['create_frame0'] = [self.create_frame, TUC.BG, [TUV.BG]]
        self.label_formatter(self.select_lbl, size=TUV.FONT_SIZE_SMALL, uid='select_lbl')
        self.label_formatter(self.create_title, size=TUV.FONT_SIZE_TITLE, fg=TUV.ACCENT, uid='create_title')
        self.label_formatter(self.general_info_label, size=TUV.FONT_SIZE_SMALL, uid='general_info_label')

        self.root.bind('<<ExitCall>>', self.close)
        self.root.bind('<<NewDB>>', self.new_entry)
        self.root.bind('<<CloseDB>>', self.close_entry)
        self.root.bind('<<OpenDB>>', self.open_entry)
        self.root.bind('<<CreateDB_MAIN>>', self.new_main)
        self.root.bind('<3>', self.context_menu_show)
        self.root.bind('<F5>', self.update_ui)
        self.root.bind('<Control-r>', self.update_ui)
        self.root.bind('<<EditConfiguration>>', self.edit_configuration)
        self.root.bind('<<EditQuestions>>', self.edit_questions)
        self.root.bind('<<EDIT_DB_PSW_CLICK>>', self.db_psw_toggle)
        self.root.bind('<<EDIT_DB_PSW_RESET>>', self.db_psw_change)
        self.root.bind('<<EDIT_QZ_PSW_CLICK>>', self.qz_psw_toggle)
        self.root.bind('<<EDIT_QZ_PSW_RESET>>', self.qz_psw_change)
        self.root.bind('<<SideBar_Expand_Shrink>>', self.expand_click)

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

    def expand_click(self, *args, **kwargs):
        try:
            curr = not self.data[self.EDIT_PAGE]['_UI']['sb_shrunk']
            self.data[self.EDIT_PAGE]['_UI']['sb_shrunk'] = curr
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

    def db_psw_toggle(self, *args, **kwargs):
        if self.EDIT_PAGE not in self.data:
            return

        cond = self.data[self.EDIT_PAGE]['db']['DB']['psw'][0]

        if not kwargs.get('nrst'):
            if not cond:
                if self.db_psw_change()[1]:
                    self.show_info(Message(Levels.ERROR, "Couldn't set password."))
                    return

            cond = not cond
            self.data[self.EDIT_PAGE]['db']['DB']['psw'][0] = cond

        if cond:
            try:
                self.edit_db_psw_button.image = self.svgs['checkmark']['accent']
                self.edit_db_psw_button.config(compound=tk.LEFT, image=self.svgs['checkmark']['accent'], style='Active.TButton')
            except Exception as E:
                self.edit_db_psw_button.config(style='Active.TButton')
                log(LoggingLevel.ERROR, f"Failed to add image to <edit_db_psw_button> : {E.__class__.__name__}({E})")
        else:
            self.data[self.EDIT_PAGE]['db']['DB']['psw'][1] = ''
            self.edit_db_psw_button.image = ''
            self.edit_db_psw_button.config(style='TButton', image='')

        self.edit_db_psw_button.config(text=f"{'Not ' if not cond else ''}Protected")

    def db_psw_change(self, *args, **kwargs):
        if self.EDIT_PAGE not in self.data:
            return

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
                a = res.split(sep)
                if len(a) == 2:
                    a, b = a
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

    def qz_psw_toggle(self, *args, **kwargs):
        if self.EDIT_PAGE not in self.data:
            return

        cond = self.data[self.EDIT_PAGE]['db']['DB']['q_psw'][0]

        if not kwargs.get('nrst'):
            if not cond:
                if self.qz_psw_change()[1]:
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

    def qz_psw_change(self, *args, **kwargs):
        if self.EDIT_PAGE not in self.data:
            return

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
                a = res.split(sep)
                if len(a) == 2:
                    a, b = a
                    f = False

                    if a == b:
                        f1 = False
                        del b
                        s_mem.set('')
                        qa_prompts.InputPrompts.ButtonPrompt(s_mem, 'Reset Quiz Password?', ('Yes', 'y'), ("No", 'n'), default='n', message=f'Are you sure you want to reset your password to "{a}"')
                        if s_mem.get() == 'y':
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

    def inp2_edit(self, *args, **kwargs):
        global MAX

        a = self.create_inp2_var.get()
        if len(a) > MAX:
            self.create_inp2_var.set(a[:MAX:])
            self.show_info(
                Message(Levels.ERROR, f'Password length cannot exceed {MAX} characters ({random.randint(0, 10)})')
            )

    def inp1_edit(self, *args, **kwargs):
        global MAX

        a = self.create_inp1_var.get()
        if len(a) > MAX:
            self.create_inp1_var.set(a[:MAX:])
            self.show_info(
                Message(Levels.ERROR, f'Name length cannot exceed {MAX} characters ({random.randint(0, 10)})')
            )

    def _clear_info(self):
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

    def show_info(self, data: Message, timeout=3000):
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

    def ask_db_frame(self):
        self.prev_page = self.page_index

        self.db_frame.pack_forget()
        self.create_frame.pack_forget()
        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.select_frame.pack(fill=tk.BOTH, expand=True)
        self.menu_file.entryconfig('Close Database', state=tk.DISABLED)
        self.context_menu.entryconfig('Close Database', state=tk.DISABLED)

        self.page_index = self.SELECT_PAGE

        self.geo_small()

    def create_db_frame(self):
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

    def edit_db_frame(self):
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

    def psw_sel_click(self, reset=False):
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

    def context_menu_show(self, e, *_0, **_1):
        if self.page_index == self.EDIT_PAGE:
            self.context_menu.post(e.x_root, e.y_root)

    def proc_exit(self, exit_to_page):
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

    def new_entry(self, *_0, **_1):
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

    def close_entry(self, *_0, **_1):
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

    def open_entry(self, *_0, **_1):
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
                    read, _ = qa_files.load_file(qa_functions.FileType.QA_FILE, raw)
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

    def edit_configuration(self, *_0, **_1):
        log(LoggingLevel.DEBUG, 'Entered EDIT::CONFIGURATION page')
        self.edit_configuration_btn.config(style='ActiveLG.TButton', image=self.svgs['settings_cog_large']['accent'])
        self.edit_questions_btn.config(style='LG.TButton', image=self.svgs['question_large']['normal'])

        self.db_psw_toggle(nrst=True)
        self.qz_psw_toggle(nrst=True)

        self.edit_configuration_master_frame.pack(fill=tk.BOTH, expand=True)

        self.update_ui()

    def edit_questions(self, *_0, **_1):
        log(LoggingLevel.DEBUG, 'Entered EDIT::QUESTIONS page')
        self.edit_questions_btn.config(style='ActiveLG.TButton', image=self.svgs['question_large']['accent'])
        self.edit_configuration_btn.config(style='LG.TButton', image=self.svgs['settings_cog_large']['normal'])

        self.edit_configuration_master_frame.pack_forget()

        self.update_ui()

    # --------------
    # Main Functions
    # --------------

    def compile_changes(self):
        if not qa_functions.data_at_dict_path(f'{self.EDIT_PAGE}/db_saved', self.data)[0]:
            return False, ([], [])

        if self.data[self.EDIT_PAGE]['db_saved'] == self.data[self.EDIT_PAGE]['db']:
            return False, ([], [])

        def rec(og: any, new: any, root="") -> Tuple[List[Tuple], List[str]]:
            c: List[Tuple] = []
            f: List[str] = []

            # assert , "[CRITICAL] Failed to compile changes: {DDT}"
            if type(og) is not type(new):
                if isinstance(new, dict):
                    og1 = {k: None for k in cast(dict, new).keys()}
                    c1, f1 = rec(og1, new)
                    c.extend(c1)
                    f.extend(f1)
                    del c1, f1, og1

                else:
                    c.append((root, og, new))

                return c, f

            tp = type(og)

            if tp in [list, dict, tuple, set]:
                # assert , "[CRITICAL] Failed to compile changes: {LEN}"
                if len(og) != len(new):
                    if isinstance(new, dict):
                        if isinstance(og, dict):
                            tks = {*cast(dict, og).keys(), *cast(dict, new).keys()}
                            og1, new1 = {k: cast(dict, og).get(k) for k in tks}, {k: cast(dict, new).get(k) for k in tks}
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

                elif tp is dict:
                    for (k1, _), (k2, _1) in zip(cast(dict, og).items(), cast(dict, new).items()):
                        if k1 != k2:
                            f.append('[CRITICAL] Failed to compile changes: {KoKt}')
                            continue

                        a, b = rec(cast(dict, og)[k1], cast(dict, new)[k1], k1)
                        c.extend(a)
                        f.extend(b)
                        del a, b

                else:
                    for i, (a, b) in enumerate(zip(og, new)):
                        if cast(Union[str, bytes, int, float, bool], a) != cast(Union[str, bytes, int, float, bool], b):
                            c.append(((root, i), a, b))

            else:
                if cast(Union[str, bytes, int, float, bool], og) != cast(Union[str, bytes, int, float, bool], new):
                    c.append((root, og, new))

            del tp
            return c, f

        changes = rec(self.data[self.EDIT_PAGE]['db_saved'], self.data[self.EDIT_PAGE]['db'])
        return True, changes

    @staticmethod
    def compile_changes_str(changes):
        n_map = {
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

    def save_db(self, _do_not_prompt: bool = False):
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

        if s_mem.get().strip() == 'y' or _do_not_prompt:
            new = json.dumps(self.data[self.EDIT_PAGE]['db'])
            file = qa_functions.File(self.data[self.EDIT_PAGE]['db_path'])
            new, _ = cast(Tuple, qa_files.generate_file(FileType.QA_FILE, new))
            qa_functions.SaveFile.secure(file, new, qa_functions.SaveFunctionArgs(False, False, save_data_type=bytes))
            self.data[self.EDIT_PAGE]['db_saved'] = self.data[self.EDIT_PAGE]['db']
            log(LoggingLevel.SUCCESS, 'Successfully saved new data to database.')
            self.show_info(Message(Levels.OKAY, 'Successfully saved new data'))

        del s_mem

    def new_main(self, *_0, **_1):
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
            data, _ = qa_files.generate_file(FileType.QA_FILE, db_starter)
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
    def _clean_db(db: dict) -> dict:
        assert isinstance(db, dict)
        name_f, name_d = qa_functions.data_at_dict_path('DB/name', db)
        assert name_f

        log(LoggingLevel.INFO, 'Checking database integrity')

        def rs_name():
            log(LoggingLevel.ERROR, 'Name data corrupted')

            s_mem = qa_functions.SMem()
            s_mem.set('')

            while True:
                qa_prompts.InputPrompts.SEntryPrompt(s_mem, 'The database\'s name data was corrupted; please enter a new name below:', default='')
                res = s_mem.get().strip()
                if res is None:
                    continue
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
                'acc': False,               # Allow custom quiz configuration
                'poa': 'p',                 # Part or all
                'rqo': False,               # Randomize question order
                'ssd': 2,                   # Subsample divisor
                'dpi': False,               # Deduct points on incorrect (responses)
                'a2d': 1                    # Amount of points to deduct
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
                pass

        qr = 'QUESTIONS'

        return db

    def open(self, path: str, data: dict, _bypass_psw: bool = False):
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

                if s_mem.get() is None:
                    del s_mem

                    self.proc_exit(self.SELECT_PAGE)
                    return

                if s_mem.get().strip() == '':
                    del s_mem

                    self.proc_exit(self.SELECT_PAGE)
                    return

                if hashlib.sha3_512(s_mem.get().encode()).hexdigest() != data['DB']['psw'][1]:
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
            self.data[self.EDIT_PAGE]['_UI'] = {'sb_shrunk': False}

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

    def update_ui(self, *_9, **_1):
        self.load_theme()

        def tr(com, *args, **kwargs) -> Tuple[bool, str]:
            try:
                return True, com(*args, **kwargs)
            except Exception as E:
                return False, f"{E.__class__.__name__}({E})"

        def log_error(com: str, el, reason: str, ind: int):
            log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

        def log_norm(com: str, el):
            log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

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
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme)

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
            background=[('active', self.theme.accent.color), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
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
            background=[('active', self.theme.accent.color), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'TSeparator',
            background=self.theme.gray.color
        )

        elID = "<lUP::unknown>"

        for element, commands in self.late_update_requests.items():
            assert type(commands) in [list, tuple, set]
            commands: Union[list, tuple, set]

            for command, args in commands:
                lCommand = [False]
                cargs = []
                for index, arg in enumerate(args):
                    carg = (arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(arg, tuple):
                        if len(arg) >= 2:
                            if arg[0] == '<EXECUTE>':
                                ps, res = (tr(arg[1]) if len(args) == 2 else tr(arg[1], arg[2::]))
                                if ps:
                                    carg = res
                                else:
                                    log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

                            if arg[0] == '<LOOKUP>':
                                rs = {
                                    'padX': self.padX,
                                    'padY': self.padY,
                                    'root_width': self.root.winfo_width(),
                                    'root_height': self.root.winfo_height(),
                                }.get(arg[1])

                                if rs is not None:
                                    carg = rs
                                else:
                                    log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

                    cargs.append(carg)
                    cargs: list

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

    def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None, bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, abg=ThemeUpdateVars.ACCENT, afg=ThemeUpdateVars.BG, uid=None):
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

    def label_formatter(self, label: Union[tk.Label, tk.LabelFrame], bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, size=ThemeUpdateVars.FONT_SIZE_MAIN, font=ThemeUpdateVars.DEFAULT_FONT_FACE, padding=None, uid=None):
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

    def load_theme(self):
        self.theme = qa_functions.LoadTheme.auto_load_pref_theme()
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

    def load_png(self):
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.svgs['admt'] = ImageTk.PhotoImage(i)

        for src, name, background, foreground, size, (a, b) in [
            [self.checkmark_src, 'c_mark', self.theme.background, self.theme.accent, self.theme.font_main_size, ('checkmark', 'normal')],
            [self.checkmark_src, 'c_mark_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('checkmark', 'accent')],
            [self.cog_src, 'cog', self.theme.background, self.theme.accent, self.theme.font_main_size, ('settings_cog', 'normal')],
            [self.cog_src, 'cog_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('settings_cog', 'accent')],
            [self.arrow_right_src, 'arrow_right', self.theme.background, self.theme.accent, self.theme.font_main_size, ('arrow_right', 'normal')],
            [self.arrow_right_src, 'arrow_right_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('arrow_right', 'accent')],
            [self.arrow_left_src, 'arrow_left', self.theme.background, self.theme.accent, self.theme.font_main_size, ('arrow_left', 'normal')],
            [self.arrow_left_src, 'arrow_left_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('arrow_left', 'accent')],
            [self.question_src, 'question', self.theme.background, self.theme.accent, self.theme.font_main_size, ('question', 'normal')],
            [self.question_src, 'question_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('question', 'accent')],
            
            [self.checkmark_src, 'c_mark_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('checkmark_large', 'normal')],
            [self.checkmark_src, 'c_mark_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('checkmark_large', 'accent')],
            [self.cog_src, 'cog_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('settings_cog_large', 'normal')],
            [self.cog_src, 'cog_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('settings_cog_large', 'accent')],
            [self.arrow_right_src, 'arrow_right_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_right_large', 'normal')],
            [self.arrow_right_src, 'arrow_right_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_right_large', 'accent')],
            [self.arrow_left_src, 'arrow_left_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_left_large', 'normal')],
            [self.arrow_left_src, 'arrow_left_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_left_large', 'accent')],
            [self.question_src, 'question_accent', self.theme.background, self.theme.accent, self.theme.font_title_size, ('question_large', 'normal')],
            [self.question_src, 'question_accent_accent', self.theme.accent, self.theme.background, self.theme.font_title_size, ('question_large', 'accent')],
        ]:
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

    def disable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button]]):
        self.dsb = True

        for btn in (self.select_open, self.select_new, self.select_scores,
                    self.edit_questions_btn, self.edit_configuration_btn,
                    self.edit_db_psw_reset_btn, self.edit_db_psw_button,
                    self.edit_qz_psw_reset_btn, self.edit_qz_psw_button):
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self, *exclude):
        self.dsb = False

        for btn in (self.select_open, self.select_new, self.select_scores,
                    self.edit_questions_btn, self.edit_configuration_btn,
                    self.edit_db_psw_reset_btn, self.edit_db_psw_button,
                    self.edit_qz_psw_reset_btn, self.edit_qz_psw_button):
            if btn not in exclude:
                btn.config(state=tk.NORMAL)

        self.update_ui()

    def __del__(self):
        self.thread.join(self, 0)


def get_svg(svg_file, background, size=None, name=None):
    if isinstance(background, str):
        background = int(background.replace("#", '0x'), 0)

    drawing = svg2rlg(svg_file)
    bytes_png = BytesIO()
    renderPM.drawToFile(drawing, bytes_png, fmt="PNG", bg=background)
    img = Image.open(bytes_png)
    if size is not None:
        img = img.resize(size, PIL.Image.ANTIALIAS)

    p_img = ImageTk.PhotoImage(img, name=name)

    return p_img


def log(level: LoggingLevel, data: str):
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME, DEBUG_NORM
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
    elif level == LoggingLevel.DEVELOPER and (not qa_functions.App.DEV_MODE or not DEBUG_NORM):
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


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    qa_prompts.LOGGER_AVAIL = LOGGER_AVAIL
    qa_prompts.LOGGER_FUNC = LOGGER_FUNC
    qa_prompts.LOGGING_FILE_NAME = LOGGING_FILE_NAME
    qa_prompts.DEBUG_NORM = DEBUG_NORM

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