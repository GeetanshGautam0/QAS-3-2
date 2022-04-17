from threading import Thread
import tkinter as tk, sys, qa_prompts, qa_functions, qa_files, os, traceback, hashlib, json
from typing import *
from tkinter import ttk, filedialog
from qa_functions.qa_enum import *
from qa_prompts import gsuid
from PIL import Image, ImageTk


script_name = "APP_TU"
APP_TITLE = "Quizzing Application | Theming Utility"
_THEME_FILE_TYPE = qa_functions.qa_enum.FileType.QA_THEME

LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = ''
DEBUG_NORM = False


class _UI(Thread):
    def __init__(self, root, ic, ds, **kwargs):
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        ratio = 4/3
        wd_w = 700
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

        self.img_path = f"{qa_functions.Files.icoRoot}\\.png\\themer.png"
        self.img_size = (75, 75)
        self.img = None
        self.load_png()

        self.title_box = tk.Frame(self.root)
        self.title_label = tk.Label(self.title_box)
        self.title_icon = tk.Label(self.title_box)
        
        self.IO_panel = tk.LabelFrame(self.root)
        self.install_button = tk.Button(self.IO_panel)
        self.export_button = tk.Button(self.IO_panel)

        self.theme_selector_panel = tk.LabelFrame(self.root)
        self.theme_pref = qa_functions.qa_theme_loader._load_pref_data()
        self.select_theme_button = tk.Button(self.theme_selector_panel)
        self.theme_selector_s_var = tk.StringVar(self.root)
        self.theme_selector_options = {'No themes loaded; click \'Refresh\' to load themes': ''}
        self.theme_pre_installed_frame = tk.Frame(self.theme_selector_panel)
        self.theme_pre_installed_lbl = tk.Label(self.theme_pre_installed_frame)
        self.theme_selector_dropdown = ttk.OptionMenu(self.theme_pre_installed_frame, self.theme_selector_s_var, *self.theme_selector_options.keys())
        self.theme_selector_s_var.set(self.theme_pref[2])
        self.install_new_frame = tk.Frame(self.theme_selector_panel)
        self.install_new_label = tk.Label(self.install_new_frame)
        self.install_new_button = ttk.Button(self.install_new_frame)

        self.prev_theme_selection = self.theme_selector_s_var.get()

        self.space_filler_1 = tk.Label(self.theme_pre_installed_frame)
        self.space_filler_2 = tk.Label(self.install_new_frame)

        self.ttk_theme = 'clam'

        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)

        self.start()
        self.root.mainloop()

    def close(self):
        sys.stdout.write("tu - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.quit()

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
            bordercolor=0
        )

        self.ttk_style.map(
            'TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        # External Update Calls
        self.update_theme_selector_options()

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
            ThemeUpdateVars.FONT_SIZE_XL_TITLE: self.theme.font_xl_title_size,
            ThemeUpdateVars.BORDER_SIZE: self.theme.border_size,
            ThemeUpdateVars.BORDER_COLOR: self.theme.border_color
        }

    def run(self):
        global DEBUG_NORM, APP_TITLE
        DEBUG_NORM = self.kwargs.get('debug')
        qa_prompts.DEBUG_NORM = DEBUG_NORM
        qa_prompts.TTK_THEME = self.ttk_theme

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.title(APP_TITLE)
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
        self.root.iconbitmap(qa_functions.Files.TU_ico)

        self.title_box.pack(fill=tk.X, expand=False, pady=50)
        self.title_label.config(text="Theming Utility", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=self.img)
        self.title_label.pack(fill=tk.X, expand=True, padx=(self.padX/8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX/8), pady=self.padY, side=tk.LEFT)

        self.label_formatter(self.title_label, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT)
        self.label_formatter(self.title_icon)

        TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

        self.update_requests[gsuid()] = [self.root, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.title_box, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.theme_pre_installed_frame, TUC.BG, [TUV.BG]]
        self.update_requests[gsuid()] = [self.install_new_frame, TUC.BG, [TUV.BG]]

        self.theme_selector_panel.config(text="Installed Themes")
        self.theme_selector_panel.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, ipadx=self.padX/2, ipady=self.padY/2)

        self.space_filler_1.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.space_filler_2.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.label_formatter(self.space_filler_1)
        self.label_formatter(self.space_filler_2)

        self.theme_pre_installed_frame.pack(fill=tk.X, expand=False)
        self.theme_selector_dropdown.pack(side=tk.RIGHT, padx=(0, self.padX), pady=self.padY, fill=tk.X, expand=False)
        self.theme_pre_installed_lbl.config(text="Select an Installed Theme:", anchor=tk.E, justify=tk.RIGHT)
        self.theme_pre_installed_lbl.pack(side=tk.LEFT, padx=(self.padX, 0), pady=self.padY, fill=tk.X, expand=False)

        self.install_new_frame.pack(fill=tk.X, expand=False)
        self.install_new_label.config(text="Want to try out a new theme?")
        self.install_new_label.pack(fill=tk.X, expand=False, padx=(self.padX, 0), pady=(0, self.padY), side=tk.LEFT)
        self.install_new_button.config(text="Install a New Theme", command=self.install_new_theme)
        self.install_new_button.pack(fill=tk.X, expand=False, padx=(0, self.padX), pady=(0, self.padY), side=tk.RIGHT)

        self.theme_selector_s_var.trace('w', self.on_theme_drop_change)
        self.label_formatter(self.theme_selector_panel, size=TUV.FONT_SIZE_MAIN)
        self.label_formatter(self.theme_pre_installed_lbl, size=TUV.FONT_SIZE_MAIN)
        self.label_formatter(self.install_new_label, size=TUV.FONT_SIZE_MAIN)

        self.update_ui()

    def load_png(self):
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(i)

    def update_theme_selector_options(self):
        og = {**self.theme_selector_options}
        self.theme_selector_options = {}
        for code, tad in qa_functions.LoadTheme.auto_load_all().items():
            name, theme = (*tad.keys(),)[0], (*tad.values(),)[0]

            file_name = theme.theme_file_display_name
            self.theme_selector_options[f'{file_name}: {name}'] = theme

        if og != self.theme_selector_options:
            self.theme_pref = qa_functions.qa_theme_loader._load_pref_data()
            self.theme_selector_s_var.set(self.theme_pref[2])
            self.theme_selector_dropdown['menu'].delete(0, tk.END)
            for option in self.theme_selector_options:
                self.theme_selector_dropdown['menu'].add_radiobutton(
                    label=option, command=tk._setit(self.theme_selector_s_var, option)
                )

    def on_theme_drop_change(self, *args, **kwargs):
        def nope():
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket("The requested theme wasn't found; refreshing list."),
                qoc=False
            )
            self.update_ui()

        if self.prev_theme_selection != self.theme_selector_s_var.get():
            self.prev_theme_selection = self.theme_selector_s_var.get()
            new_theme: qa_functions.Theme = self.theme_selector_options.get(self.theme_selector_s_var.get())
            if not isinstance(new_theme, qa_functions.Theme):
                nope()
            elif not os.path.exists(new_theme.theme_file_path):
                nope()
            else:
                qa_functions.qa_theme_loader._set_pref(
                    new_theme.theme_file_path, new_theme.theme_code, f'{new_theme.theme_file_display_name}: {new_theme.theme_display_name}'
                )
                self.update_ui()

    def install_new_theme(self):
        self.disable_all_inputs()

        req_files = filedialog.askopenfilenames(
            title="Select Theme File",
            filetypes=[('Quizzing Application Theme', qa_files.qa_theme_extn)]
        )

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

        to_install = {}

        for file in req_files:
            file = file.replace('/', '\\')
            fn = file.split('\\')[-1]

            try:
                if file.split('.')[-1] != qa_files.qa_theme_extn:
                    raise Exception('Invalid file extension')

                file_inst = qa_functions.File(file)
                raw = qa_functions.OpenFile.load_file(file_inst, qa_functions.OpenFunctionArgs(bytes, False))
                _, json_string = qa_files.load_file(qa_functions.qa_enum.FileType.QA_THEME, raw)
                theme_json = json.loads(json_string)
                assert fn != qa_functions.Files.ThemePrefFile, f"Filename '{fn}' is not allowed (system reserved)"
                assert 'file_info' in theme_json, 'File info unavailable'
                assert 'avail_themes' in theme_json['file_info'], 'No themes available'
                assert 'num_themes' in theme_json['file_info']['avail_themes'], 'No themes available'
                assert len(theme_json['file_info']['avail_themes']) == theme_json['file_info']['avail_themes']['num_themes'] + 1, 'Corrupted theme data'
                assert theme_json['file_info']['avail_themes']['num_themes'] > 0, 'No themes available'
                avail_themes = {**theme_json['file_info']['avail_themes']}
                avail_themes.pop('num_themes')

                all_theme_data = qa_functions.LoadTheme._load_theme(file, theme_json, avail_themes)

                it = []
                ins = []

                for _, td in all_theme_data.items():
                    theme_name, theme_data = (*td.keys(),)[0], (*td.values(),)[0]
                    theme_data: qa_functions.Theme

                    comp_theme_dict = {
                        'bg': theme_data.background.color,
                        'fg': theme_data.foreground.color,
                        'accent': theme_data.accent.color,
                        'error': theme_data.error.color,
                        'warning': theme_data.warning.color,
                        'okay': theme_data.okay.color,
                        'gray': theme_data.gray.color,
                        'ff': theme_data.font_face,
                        'faf': theme_data.font_alt_face,
                        'fss': theme_data.font_small_size,
                        'fms': theme_data.font_main_size,
                        'fls': theme_data.font_large_size,
                        'fts': theme_data.font_title_size,
                        'fxlts': theme_data.font_xl_title_size,
                        'bs': theme_data.border_size,
                        'bc': theme_data.border_color.color
                    }

                    dn = f"{theme_data.theme_file_display_name}: {theme_data.theme_display_name}"

                    if dn in e4:
                        ins.append(dn)

                    elif comp_theme_dict in e2:
                        it.append((f"{fn}: {theme_data.theme_code}", e3[e2.index(comp_theme_dict)][0]))

                    else:
                        if fn not in to_install:
                            to_install[fn] = ()

                        to_install[fn] = (*to_install[fn], theme_data)

                if len(it) + len(ins) > 0:
                    raise Exception((("\n\tCouldn't install {} theme(s) from '{}': identical theme(s) already installed.\n\t\tFailed to install the following themes:\n\t\t\t*{}\n".format(str(len(it)), fn, "\n\t\t\t*".join(f"<{a}> = <{b}>" for a, b in it))) if len(it) > 0 else "") + ((("\n" if len(it) > 0 else "") +("\n\tCouldn't install {} theme(s) from '{}': theme with identical names already installed.\n\t\tFailed to install the following themes:\n\t\t\t*{}\n".format(str(len(ins)), fn, "\n\t\t\t*".join(j for j in ins)))) if len(ins) > 0 else ""))

            except Exception as E:
                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket(
                        msg=f"""Failed to install theme from file '{fn}'.

Error: {str(E)}
Error Code: {hashlib.md5(str(E).encode()).hexdigest()}

Technical Information:
{traceback.format_exc()}""",
                        title="Couldn't Install Theme"
                    )
                )

        install_dir = f"{qa_functions.App.appdata_dir}\\{qa_functions.Files.ad_theme_folder}".replace('/','\\')
        if not os.path.isdir(install_dir):
            os.makedirs(install_dir)

        for filename, themes in to_install.items():
            themes: Tuple[qa_functions.Theme]

            if len(themes) <= 0:
                continue

            theme_data_dict = {
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

        self.enable_all_inputs()
        self.update_ui()

    def disable_all_inputs(self):
        self.install_new_button.config(state=tk.DISABLED)
        self.theme_selector_dropdown.config(state=tk.DISABLED)

    def enable_all_inputs(self):
        self.install_new_button.config(state=tk.NORMAL)
        self.theme_selector_dropdown.config(state=tk.NORMAL)

    def __del__(self):
        self.thread.join(self, 0)


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    ui_root = tk.Toplevel()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root
