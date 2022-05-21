import tkinter as tk, sys, qa_prompts, qa_functions, qa_files, os, traceback, PIL, hashlib, random, json
from threading import Thread
from typing import *
from tkinter import ttk, filedialog
from qa_functions.qa_enum import *
from qa_prompts import gsuid, configure_scrollbar_style
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from dataclasses import dataclass
from enum import Enum

script_name = "APP_AT"
APP_TITLE = "Quizzing Application | Admin Tools"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
MAX = 50


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
        ratio = 4 / 3
        wd_w = 700
        wd_w = wd_w if wd_w <= self.screen_dim[0] else self.screen_dim[0]
        self.window_size = [wd_w, int(ratio * wd_w)]
        self.window_size[0] = 900 if 900 <= self.screen_dim[0] else self.screen_dim[0]
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
        self.img = None
        self.checkmark = None
        self.checkmark_src = ".src\\.icons\\.progress\\checkmark.svg"
        self.checkmark_tmp = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup".replace('/', '\\') + self.checkmark_src.split("\\")[-1]
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

        self.edit_title = tk.Label(self.db_frame)
        self.edit_btn_panel = tk.Frame(self.db_frame)

        self.edit_configuration_btn = ttk.Button(self.edit_btn_panel, text='Configuration', command=lambda: self.root.focus_get().event_generate('<<EditConfiguration>>'))
        self.edit_questions_btn = ttk.Button(self.edit_btn_panel, text='Questions', command=lambda: self.root.focus_get().event_generate('<<EditQuestions>>'))

        self.edit_configuration_master_frame = tk.Frame(self.db_frame)
        self.edit_configuration_canvas = tk.Canvas(self.edit_configuration_master_frame)
        self.edit_configuration_vsb = ttk.Scrollbar(self.edit_configuration_master_frame, style='MyAdmin.TScrollbar')
        self.edit_configuration_frame = tk.Frame(self.edit_configuration_canvas)

        self.edit_password_container = tk.LabelFrame(self.edit_configuration_frame)
        self.edit_db_psw_container = tk.LabelFrame(self.edit_password_container)
        self.edit_qz_psw_container = tk.LabelFrame(self.edit_password_container)

        self.edit_db_psw_var = tk.StringVar()
        self.edit_db_psw_lbl = tk.Label(self.edit_db_psw_container)
        self.edit_db_psw_button = ttk.Button(self.edit_db_psw_container, command=lambda: self.root.focus_get().event_generate('<<EDIT_DB_PSW_CLICK>>'))
        self.edit_db_psw_reset_btn = ttk.Button(self.edit_db_psw_container, command=lambda: self.root.focus_get().event_generate('<<EDIT_DB_PSW_RESET>>'))
        self.edit_db_psw_entry = ttk.Entry(self.edit_db_psw_container, textvariable=self.edit_db_psw_var)

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

        self.update_requests[gsuid()] = [
            self.create_inp1,
            ThemeUpdateCommands.FONT,
            [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN]
        ]
        self.update_requests[gsuid()] = [
            self.create_inp1_cont,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda bg, fg, face, size: self.create_inp1_cont.config(bg=bg, fg=fg, font=(face, size), bd='0'),
                ThemeUpdateVars.BG, ThemeUpdateVars.GRAY,
                ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gsuid()] = [
            self.create_inp2,
            ThemeUpdateCommands.FONT,
            [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN]
        ]
        self.update_requests[gsuid()] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda bg, fg, face, size: self.create_inp2_cont.config(bg=bg, fg=fg, font=(face, size), bd='0'),
                ThemeUpdateVars.BG, ThemeUpdateVars.GRAY,
                ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gsuid()] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda bg, fg, face, size: self.create_config_frame.config(bg=bg, fg=fg, font=(face, size), bd='0'),
                ThemeUpdateVars.BG, ThemeUpdateVars.GRAY,
                ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gsuid()] = [self.create_btn_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.create_inp2_var.trace("w", self.inp2_edit)
        self.create_inp1_var.trace("w", self.inp1_edit)

    def configure_sel_frame(self):
        self.select_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.TOP)
        self.select_open.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=(0, self.padY), side=tk.LEFT)
        self.select_new.pack(fill=tk.BOTH, expand=True, padx=(0, self.padX), pady=(0, self.padY), side=tk.RIGHT)

    def configure_edit_frame(self):
        # Layout
        self.edit_title.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
        self.edit_btn_panel.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.edit_configuration_btn.pack(fill=tk.X, expand=True, padx=(self.padX, 0), ipady=self.padY/2, side=tk.LEFT)
        self.edit_questions_btn.pack(fill=tk.X, expand=True, padx=(0, self.padX), ipady=self.padY/2, side=tk.RIGHT)

        self.edit_configuration_vsb.pack(fill=tk.Y, expand=False, padx=(0, self.padX), pady=self.padY, side=tk.RIGHT)
        self.edit_configuration_canvas.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=self.padY)

        self.edit_password_container.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
        self.edit_db_psw_container.pack(fill=tk.X, expand=True, padx=self.padX, pady=(self.padY, 0))
        self.edit_qz_psw_container.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
        self.edit_password_container.config(text="Password Management")
        self.edit_db_psw_container.config(text="Administrator Password")
        self.edit_qz_psw_container.config(text="Quiz Password")

        self.edit_db_psw_lbl.config(text="This password allows for the restriction of users who can edit this database.")
        self.edit_db_psw_lbl.pack(fill=tk.X, expand=False, pady=self.padY, side=tk.TOP)

        self.edit_db_psw_button.pack(fill=tk.X, expand=True, pady=self.padY, side=tk.LEFT)
        self.edit_db_psw_reset_btn.pack(fill=tk.X, expand=True, pady=self.padY, side=tk.RIGHT)

        self.edit_db_psw_button.config(text="")
        self.edit_db_psw_reset_btn.config(text="Reset Password")

        # Logical Setup
        self.edit_db_psw_var.set('')

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

        # Theme Requests
        COM = ThemeUpdateCommands
        VAR = ThemeUpdateVars

        self.label_formatter(self.edit_title, size=VAR.FONT_SIZE_SMALL)
        self.update_requests[gsuid()] = [self.edit_btn_panel, COM.BG, [VAR.BG]]
        self.update_requests[gsuid()] = [self.edit_configuration_master_frame, COM.BG, [VAR.BG]]
        self.update_requests[gsuid()] = [self.edit_configuration_frame, COM.BG, [VAR.BG]]
        self.update_requests[gsuid()] = [self.edit_configuration_canvas, COM.BG, [VAR.BG]]
        self.update_requests[gsuid()] = [
            None, COM.CUSTOM,
            [lambda *args: self.edit_configuration_canvas.config(bd=0, highlightthickness=0)]
        ]
        self.update_requests[gsuid()] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_password_container.config(
                    bg=args[0], fg=args[1], font=args[2:3], highlightthickness=args[4],
                    highlightbackground=args[5]
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests[gsuid()] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_db_psw_container.config(
                    bg=args[0], fg=args[1], font=args[2:3], highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests[gsuid()] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_qz_psw_container.config(
                    bg=args[0], fg=args[1], font=args[2:3], highlightthickness=args[4],
                    highlightbackground=args[5], bd='0'
                ),
                VAR.BG, VAR.ACCENT, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL, VAR.BORDER_SIZE, VAR.BORDER_COLOR
            ]
        ]
        self.update_requests[gsuid()] = [
            None, COM.CUSTOM,
            [
                lambda *args: self.edit_db_psw_lbl.config(
                    bg=args[0], fg=args[1], font=args[2:3]
                ),
                VAR.BG, VAR.FG, VAR.DEFAULT_FONT_FACE, VAR.FONT_SIZE_SMALL
            ]
        ]

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

        self.general_info_label.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.BOTTOM)

        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.title_label.config(text="Administrator Tools", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=self.img)
        self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX / 8), pady=self.padY, side=tk.LEFT)

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT)
        self.label_formatter(self.title_icon)

        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        self.update_requests[gsuid()] = [self.root, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.title_box, TUC.BG, [TUV.BG]]

        self.menu.add_cascade(menu=self.menu_file, label='Database')
        self.menu_file.add_command(label='Create New Database', command=lambda: self.root.focus_get().event_generate('<<NewDB>>'))
        self.menu_file.add_command(label='Open Database', command=lambda: self.root.focus_get().event_generate('<<OpenDB>>'))
        self.menu_file.add_command(label='Close Database', command=lambda: self.root.focus_get().event_generate('<<CloseDB>>'))

        self.context_menu.add_command(label='Create New Database', command=lambda: self.root.focus_get().event_generate('<<NewDB>>'))
        self.context_menu.add_command(label='Open Database', command=lambda: self.root.focus_get().event_generate('<<OpenDB>>'))
        self.context_menu.add_command(label='Close Database', command=lambda: self.root.focus_get().event_generate('<<CloseDB>>'))

        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=lambda: self.root.focus_get().event_generate('<<ExitCall>>'))

        self.update_requests[gsuid()] = [self.select_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.db_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.create_frame, TUC.BG, [TUV.BG]]
        self.label_formatter(self.select_lbl, size=TUV.FONT_SIZE_SMALL)
        self.label_formatter(self.create_title, size=TUV.FONT_SIZE_TITLE, fg=TUV.ACCENT)
        self.label_formatter(self.general_info_label, size=TUV.FONT_SIZE_SMALL)

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
        # self.root.bind('<Configure>', self._onConfig)

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
        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.db_frame.pack(fill=tk.BOTH, expand=True)
        self.menu_file.entryconfig('Close Database', state=tk.NORMAL)
        self.context_menu.entryconfig('Close Database', state=tk.NORMAL)

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
            self.create_add_psw_sel.config(text="Add a password", image=self.checkmark, compound=tk.LEFT)
        else:
            self.psw_sel_click(True)

    def context_menu_show(self, e, *_0, **_1):
        if self.page_index == self.EDIT_PAGE:
            self.context_menu.post(e.x_root, e.y_root)

    def proc_exit(self, exit_to_page):
        self.page_index = exit_to_page if exit_to_page is not None else self.prev_page
        self.busy, self.dsb = False, False

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
            self.proc_exit(self.SELECT_PAGE)
            raise Exception
        except:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket('Failed to close database file.'))

            tb = traceback.format_exc()
            sys.stderr.write(f'<NEW>: {tb}\n')
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
                    self.open(json.loads(read))

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
        self.edit_configuration_btn.config(style='Active.TButton')
        self.edit_questions_btn.config(style='TButton')

        cond = self.data[self.EDIT_PAGE]['db']['DB']['psw'][0]

        self.edit_db_psw_button.config(text=f"{'Not ' if not cond else ''}Protected")
        if cond:
            self.edit_db_psw_button.config(compound=tk.LEFT, image=self.checkmark)

        self.edit_configuration_master_frame.pack(fill=tk.BOTH, expand=True)

    def edit_questions(self, *_0, **_1):
        log(LoggingLevel.DEBUG, 'Entered EDIT::QUESTIONS page')
        self.edit_questions_btn.config(style='Active.TButton')
        self.edit_configuration_btn.config(style='TButton')

        self.edit_configuration_master_frame.pack_forget()

    # --------------
    # Main Functions
    # --------------

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

        file = qa_functions.File(f'{file}.{qa_files.qa_file_extn}' if file.split('.')[-1] != qa_files.qa_file_extn else file)
        db_starter_dict = {
            'DB': {
                'name': self.create_inp1_var.get(),
                'psw': [self.data[self.CREATE_PAGE]['psw_enb'], hashlib.sha3_512(self.create_inp2_var.get().encode()).hexdigest()]
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

        self.open(db_starter_dict, True)

    def open(self, data: dict, _bypass_psw: bool = False):
        self.enable_all_inputs()
        assert type(data) is dict

        try:
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
                        self.open(data, False)

                    del s_mem

                    self.proc_exit(self.SELECT_PAGE)
                    return

                del s_mem

            self.busy = False
            self.enable_all_inputs()

            self.edit_db_frame()

            self.edit_title.config(text=f"Current Database: \"{data['DB']['name']}\"", anchor=tk.W)
            self.data[self.EDIT_PAGE] = {
                'db': data
            }

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

            sys.stderr.write(f"[ERROR] {'[SAVED] ' if LOGGER_AVAIL else ''}[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>\n")

        def log_norm(com: str, el):
            if LOGGER_AVAIL:
                LOGGER_FUNC([qa_functions.LoggingPackage(
                    LoggingLevel.DEBUG,
                    f'Applied command \'{com}\' to {el} successfully <{elID}>',
                    LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
                )])

            sys.stdout.write(f"[DEBUG] {'[SAVED] ' if LOGGER_AVAIL else ''}[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>\n")

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

        elID = "<lUP::unknown>"

        for element, commands in self.late_update_requests.items():
            for command, args in commands:
                lCommand = [False]
                cargs = []
                for index, arg in enumerate(args):
                    cargs.append(arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])
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

    def button_formatter(self, button: tk.Button, accent=False, font=ThemeUpdateVars.DEFAULT_FONT_FACE, size=ThemeUpdateVars.FONT_SIZE_MAIN, padding=None, bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, abg=ThemeUpdateVars.ACCENT, afg=ThemeUpdateVars.BG):
        if padding is None:
            padding = self.padX

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BG, [bg if not accent else ThemeUpdateVars.ACCENT]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FG, [fg if not accent else ThemeUpdateVars.BG]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_BG, [abg if not accent else ThemeUpdateVars.BG]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.ACTIVE_FG, [afg if not accent else ThemeUpdateVars.ACCENT]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BORDER_SIZE, [ThemeUpdateVars.BORDER_SIZE]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.BORDER_COLOR, [ThemeUpdateVars.BORDER_COLOR]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.FONT, [font, size]]
        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

        self.update_requests[gsuid()] = [button, ThemeUpdateCommands.CUSTOM, [lambda tbc, tbs: button.configure(
            highlightbackground=tbc,
            bd=tbs,
            highlightcolor=tbc,
            highlightthickness=tbs,
            borderwidth=tbs,
            relief=tk.RIDGE
        ), ThemeUpdateVars.BORDER_COLOR, ThemeUpdateVars.BORDER_SIZE]]

    def label_formatter(self, label: tk.Widget, bg=ThemeUpdateVars.BG, fg=ThemeUpdateVars.FG, size=ThemeUpdateVars.FONT_SIZE_MAIN, font=ThemeUpdateVars.DEFAULT_FONT_FACE, padding=None):
        if padding is None:
            padding = self.padX

        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.BG, [bg]]
        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.FG, [fg]]

        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.FONT, [font, size]]
        self.update_requests[gsuid()] = [label, ThemeUpdateCommands.WRAP_LENGTH, [self.window_size[0] - 2 * padding]]

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
        self.img = ImageTk.PhotoImage(i)

        File = qa_functions.File(self.checkmark_src)
        raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
        new_data = raw_data.replace(qa_prompts._SVG_COLOR_REPL_ROOT, self.theme.accent.color)
        File = qa_functions.File(self.checkmark_tmp)
        qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))

        self.checkmark = get_svg(self.checkmark_tmp, self.theme.background.color, (self.theme.font_main_size, self.theme.font_main_size))

    def disable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button]]):
        self.dsb = True

        for btn in (self.select_open, self.select_new):
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self):
        self.dsb = False

        for btn in (self.select_open, self.select_new):
            btn.config(state=tk.NORMAL)

        self.update_ui()

    def __del__(self):
        self.thread.join(self, 0)


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


def log(level: LoggingLevel, data: str):
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME, DEBUG_NORM

    if level == LoggingLevel.DEBUG and not DEBUG_NORM:
        return

    if LOGGER_AVAIL:
        if level == LoggingLevel.ERROR:
            sys.stderr.write(f'[{level.name.upper()}] [SAVED] {data}\n')
        else:
            sys.stdout.write(f'[{level.name.upper()}] [SAVED] {data}\n')

        LOGGER_FUNC([qa_functions.LoggingPackage(
            level, data,
            LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME
        )])
    else:
        if level == LoggingLevel.ERROR:
            sys.stderr.write(f'[{level.name.upper()}] {data}\n')
        else:
            sys.stdout.write(f'[{level.name.upper()}] {data}\n')


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    ui_root = tk.Toplevel()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root
