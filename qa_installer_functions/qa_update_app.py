import sys, traceback, click, ctypes, threading, urllib3, tkinter as tk, os, json, appdirs
from tkinter import messagebox, ttk


with open('.\\.config\\main_config.json', 'r') as file:
    d = file.read()
    file.close()
nv_json_data = json.loads(d)

NV_ROOT = f"{appdirs.user_data_dir(nv_json_data['application']['appdata_app_name'], nv_json_data['application']['app_author'], str(nv_json_data['application']['version']), nv_json_data['application']['appdata_roaming'])}\\.nvf"
NV_DELIMITER = "=="
URL_BASE = nv_json_data['application']['root_update_url']

_NV_ROOT = "L_UPDATE"
HTTP = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=1.0, read=1.5),
    retries=False
)
_THEME = {  # DEFAULT.DEFAULT.LIGHT
    "background":     "#FFFFFF",
    "foreground":     "#000000",
    "accent":         "#2db2e7",

    "error":          "#E01A00",
    "warning":        "#D6A630",
    "ok":             "#138811",

    "gray":           "#5C5C5C",

    "font": {
      "font_face":        "Montserrat",
      "alt_font_face":    "Century Gothic",

      "size_small":       10,
      "size_main":        13,
      "size_subtitle":    20,
      "size_title":       28,
      "size_xl_title":    40
    }
}
with open('.config\\update_commands.json', 'r') as file:
    _OC = json.loads(file.read())
    file.close()

_COMMANDS = {}


def load_commands() -> dict:
    global _COMMANDS

    with open('.config\\update_commands.json', 'r') as file2:
        _OC2 = json.loads(file.read())
        file2.close()

    _COMMANDS = {}
    for command2, val2 in _OC2.items():
        _COMMANDS[command2] = []
        for url, dst in val2.items():
            _COMMANDS[command2].append([url, dst])

    return _COMMANDS


class UpdaterUI(threading.Thread):
    def __init__(self, downloads, *args, **kwargs):
        super().__init__()
        self.thread = threading.Thread
        self.thread.__init__(self)

        self.okay_to_close = True

        load_commands()

        self.root = tk.Tk()
        self.downloads, self.args, self.kwargs = downloads, args, kwargs

        self.window_size = [700, 450]
        self.window_pos = [
            int(self.root.winfo_screenwidth()/2 - self.window_size[0]/2),
            int(self.root.winfo_screenheight()/2 - self.window_size[1]/2)
        ]

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.frame_1 = tk.Frame(self.root)
        self.activity_box = tk.Listbox(self.frame_1)
        self.title_label = tk.Label(self.frame_1)
        self.close_button = ttk.Button(self.frame_1)

        self.error_label = tk.Label(self.root)
        self.activity_acc = 0

        self.padX = 20
        self.padY = 10

        self.start()
        self.root.mainloop()

    def err(self):
        global _THEME

        self.okay_to_close = True
        self.close_button.config(state=tk.NORMAL)
        tr(self.insert_item, f'Failed to update file: {traceback.format_exc()}', _THEME['background'], _THEME['error'], _THEME['error'])

    def insert_item(self, text: str, bg: str = _THEME['background'], fg: str = _THEME['foreground'], sfg: str = _THEME['accent']):
        self.activity_box.insert(tk.END, text)
        self.activity_box.itemconfig(self.activity_acc, bg=bg, foreground=fg, selectbackground=sfg, selectforeground=bg)
        self.activity_acc += 1
        self.activity_box.yview(tk.END)
        self.root.update()

    def clear_lb(self):
        self.activity_acc = 0
        self.activity_box.delete(0, tk.END)
        self.activity_box.yview(tk.END)

        self.root.update()

    def update_theme(self):
        global _THEME

        self.root.config(bg=_THEME['background'])
        self.frame_1.config(bg=_THEME['background'])
        self.error_label.config(bg=_THEME['background'], fg=_THEME['error'], font=(_THEME['font']['font_face'], _THEME['font']['size_small']), wraplength=self.window_size[0])
        self.title_label.config(bg=_THEME['background'], fg=_THEME['accent'], font=(_THEME['font']['font_face'], _THEME['font']['size_title']), wraplength=self.window_size[0] - self.padX*2)

        self.style.configure(
            'TButton',
            background=_THEME.get('background'),
            foreground=_THEME.get('accent'),
            font=(_THEME['font']['font_face'], _THEME['font']['size_main']),
            focuscolor=_THEME.get('accent'),
            bordercolor=0
        )

        self.style.map(
            'TButton',
            background=[('active', _THEME.get('accent')), ('disabled', _THEME.get('background')), ('readonly', _THEME.get('gray'))],
            foreground=[('active', _THEME.get('background')), ('disabled', _THEME.get('gray')), ('readonly', _THEME.get('background'))]
        )

        self.activity_box.config(
            bg=_THEME['background'],
            fg=_THEME['foreground'],
            font=(_THEME['font']['font_face'], _THEME['font']['size_small']),
            selectmode=tk.EXTENDED,
            selectbackground=_THEME['accent'],
            selectforeground=_THEME['background']
        )

    def close(self):
        if not self.okay_to_close:
            messagebox.showerror('Quizzing Application | Updater', 'Cannot close updater: update in progress.')
            return

        self.root.quit()

    def run(self):
        tk.Tk.report_callback_exception = self.err

        self.root.title("Quizzing App | Updater v2")
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.window_pos[0]}+{self.window_pos[1]}")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        if os.path.isfile('.src\\.icons\\.app_ico\\updater.ico'):
            self.root.iconbitmap('.src\\.icons\\.app_ico\\updater.ico')

        self.error_label.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.BOTTOM)
        self.frame_1.pack(fill=tk.BOTH, expand=True)

        self.title_label.config(text=self.kwargs['title'], justify=tk.LEFT, anchor=tk.W)
        self.title_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.activity_box.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.close_button.config(text="START", command=self.start_downloads)
        self.close_button.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.update_theme()
        self.load_commands()

    def load_commands(self):
        self.downloads: list

        for command in [*self.downloads]:
            if command == 'ReadFlags':
                self.insert_item('Looking for commands in NVF folder.')
                n_coms = nv_yield_all_flags_as_list(_NV_ROOT)
                for nc in n_coms:
                    if nc in _COMMANDS:
                        self.downloads.append(nc)
                    else:
                        self.insert_item(f"   * Invalid command found in NVF: {nc}")
                        nv_delete_flag(_NV_ROOT, nc)

                while 'ReadFlags' in self.downloads:
                    self.downloads.pop(self.downloads.index('ReadFlags'))

            elif command not in _COMMANDS:
                self.insert_item(f"Invalid command found: {command}", bg=_THEME['background'], fg=_THEME['error'], sfg=_THEME['error'])
                while command in self.downloads:
                    self.downloads.pop(self.downloads.index(command))

        self.insert_item('')
        self.downloads = set(self.downloads)

        if len(self.downloads) >= 1:
            self.insert_item('Updating will run the following commands:')
            for command in self.downloads:
                self.insert_item(f'\t* {command}')
        else:
            self.insert_item(f"No download commands found.", bg=_THEME['background'], fg=_THEME['error'], sfg=_THEME['error'])
            self.close_button.config(text="CLOSE", command=self.close)

    def start_downloads(self):
        global _THEME, _COMMANDS, _NV_ROOT, HTTP, URL_BASE

        self.clear_lb()
        self.insert_item('Checking connection.')

        self.root.update()

        success, _ = tr(HTTP.request, 'GET', 'https://www.google.com')
        if not success:
            self.insert_item('Connection not established')
            self.close_button.config(text="RETRY")
            return

        self.root.update()

        success |= tr(HTTP.request, 'GET', 'https://raw.githubusercontent.com/GeetanshGautam0/QAS-3-2/master/.config/main_config.json')[0]
        if not success:
            self.insert_item('Connection not established (1)')
            self.close_button.config(text="RETRY")
            return

        self.root.update()

        self.insert_item('')
        self.insert_item('Successfully established connection')
        self.insert_item('Starting downloads')

        self.close_button.config(command=self.close, text="CLOSE")

        self.root.update()

        if len(self.downloads) <= 0:
            self.insert_item('No download commands provided', _THEME['background'], _THEME['error'], _THEME['error'])
            self.okay_to_close = True
            self.close_button.config(state=tk.NORMAL)
            return

        self.okay_to_close = False
        self.close_button.config(state=tk.DISABLED)

        self.downloads = {*self.downloads}  # Remove duplicates

        self.root.update()

        for command in self.downloads:
            self.insert_item(f' ')
            if command in _COMMANDS:
                self.insert_item(f'Running command \"{command}\".')
                files = _COMMANDS[command]
                for c_url, dst_file in files:
                    try:
                        success, result = tr(HTTP.request, 'GET', f'{URL_BASE}/{c_url}')
                        if not success:
                            self.insert_item(f'Failed to download file source file: {result}', fg=_THEME['error'], sfg=_THEME['error'])
                            continue

                        dst_dir = "\\".join(folder for folder in dst_file.replace('/', '\\').split('\\')[:-1:])
                        dst_file_name = dst_file.replace('/', '\\').split('\\')[-1]
                        dst_dir = dst_dir.strip('\\')

                        if dst_dir.strip() in ('.', '', '<root>', '.\\', './', '\\.', '/.'):
                            file = dst_file_name
                        else:
                            if not os.path.isdir(dst_dir):
                                os.makedirs(dst_dir)
                            file = dst_file

                        with open(file, 'wb') as dst_f:
                            dst_f.write(result.data)
                            dst_f.close()

                    except Exception as excep:
                        sys.stderr.write(f"{traceback.format_exc()}\n")

                        try:
                            self.insert_item(f'Failed to download \'{dst_file_name}\': {excep}', fg=_THEME['error'], sfg=_THEME['error'])
                        except NameError:
                            self.insert_item(f'Failed to download file for command \'{command}\': {excep}', fg=_THEME['error'], sfg=_THEME['error'])

                        continue

                    self.insert_item(f'Successfully downloaded \'{dst_file_name}\'', fg=_THEME['ok'], sfg=_THEME['ok'])
                    nv_delete_flag(_NV_ROOT, command)

            else:
                self.insert_item(f"Unknown command \"{command}\"", fg=_THEME['error'], sfg=_THEME['error'])

            self.root.update()

        self.okay_to_close = True
        self.close_button.config(state=tk.NORMAL)
        self.insert_item(f' ')
        self.insert_item(f'Executed all commands', fg=_THEME['ok'], sfg=_THEME['ok'])

        return

    def __del__(self):
        self.thread.join(self, 0)


class Install(threading.Thread):
    def __init__(self):
        super().__init__()
        self.thread = threading.Thread
        self.thread.__init__(self)

        self.okay_to_close = True

        self.root = tk.Tk()
        self.downloads = {
            1: ['UPDATE_COMMANDS', 'UPDATE_MANIFEST'],
            2: ['AUTO_INSTALL']
        }

        self.window_size = [700, 450]
        self.window_pos = [
            int(self.root.winfo_screenwidth()/2 - self.window_size[0]/2),
            int(self.root.winfo_screenheight()/2 - self.window_size[1]/2)
        ]

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.frame_1 = tk.Frame(self.root)
        self.activity_box = tk.Listbox(self.frame_1)
        self.title_label = tk.Label(self.frame_1)
        self.close_button = ttk.Button(self.frame_1)

        self.error_label = tk.Label(self.root)
        self.activity_acc = 0

        self.padX = 20
        self.padY = 10

        self.start()
        self.root.mainloop()

    def err(self):
        global _THEME

        self.okay_to_close = True
        self.close_button.config(state=tk.NORMAL)
        tr(self.insert_item, f'Failed to update file: {traceback.format_exc()}', _THEME['background'], _THEME['error'], _THEME['error'])

    def insert_item(self, text: str, bg: str = _THEME['background'], fg: str = _THEME['foreground'], sfg: str = _THEME['accent']):
        self.activity_box.insert(tk.END, text)
        self.activity_box.itemconfig(self.activity_acc, bg=bg, foreground=fg, selectbackground=sfg, selectforeground=bg)
        self.activity_acc += 1
        self.activity_box.yview(tk.END)
        self.root.update()

    def clear_lb(self):
        self.activity_acc = 0
        self.activity_box.delete(0, tk.END)
        self.activity_box.yview(tk.END)

        self.root.update()

    def update_theme(self):
        global _THEME

        self.root.config(bg=_THEME['background'])
        self.frame_1.config(bg=_THEME['background'])
        self.error_label.config(bg=_THEME['background'], fg=_THEME['error'], font=(_THEME['font']['font_face'], _THEME['font']['size_small']), wraplength=self.window_size[0])
        self.title_label.config(bg=_THEME['background'], fg=_THEME['accent'], font=(_THEME['font']['font_face'], _THEME['font']['size_title']), wraplength=self.window_size[0] - self.padX*2)

        self.style.configure(
            'TButton',
            background=_THEME.get('background'),
            foreground=_THEME.get('accent'),
            font=(_THEME['font']['font_face'], _THEME['font']['size_main']),
            focuscolor=_THEME.get('accent'),
            bordercolor=0
        )

        self.style.map(
            'TButton',
            background=[('active', _THEME.get('accent')), ('disabled', _THEME.get('background')), ('readonly', _THEME.get('gray'))],
            foreground=[('active', _THEME.get('background')), ('disabled', _THEME.get('gray')), ('readonly', _THEME.get('background'))]
        )

        self.activity_box.config(
            bg=_THEME['background'],
            fg=_THEME['foreground'],
            font=(_THEME['font']['font_face'], _THEME['font']['size_small']),
            selectmode=tk.EXTENDED,
            selectbackground=_THEME['accent'],
            selectforeground=_THEME['background']
        )

    def close(self):
        if not self.okay_to_close:
            messagebox.showerror('Quizzing Application | Updater', 'Cannot close updater: update in progress.')
            return

        self.root.quit()

    def run(self):
        tk.Tk.report_callback_exception = self.err

        self.root.title("Quizzing App | Updater v2")
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.window_pos[0]}+{self.window_pos[1]}")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        if os.path.isfile('.src\\.icons\\.app_ico\\updater.ico'):
            self.root.iconbitmap('.src\\.icons\\.app_ico\\updater.ico')

        self.error_label.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.BOTTOM)
        self.frame_1.pack(fill=tk.BOTH, expand=True)

        self.title_label.config(text="Install Quizzing App", justify=tk.LEFT, anchor=tk.W)
        self.title_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.activity_box.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.close_button.config(text="START INSTALLATION", command=self.start_downloads)
        self.close_button.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.update_theme()
        self.load_commands()

    def load_commands(self):
        if len(self.downloads) >= 1:
            self.insert_item('Updating will run the following commands:')
            for coms in self.downloads.values():
                for com in coms:
                    self.insert_item(f'\t* {com}')
        else:
            self.insert_item(f"No download commands found.", bg=_THEME['background'], fg=_THEME['error'], sfg=_THEME['error'])
            self.close_button.config(text="CLOSE", command=self.close)

    def start_downloads(self):
        global _THEME, _COMMANDS, _NV_ROOT, HTTP, URL_BASE

        self.clear_lb()
        self.insert_item('Checking connection.')

        self.root.update()

        success, _ = tr(HTTP.request, 'GET', 'https://www.google.com')
        if not success:
            self.insert_item('Connection not established')
            self.close_button.config(text="RETRY")
            return

        self.root.update()

        success |= tr(HTTP.request, 'GET', 'https://raw.githubusercontent.com/GeetanshGautam0/QAS-3-2/master/.config/main_config.json')[0]
        if not success:
            self.insert_item('Connection not established (1)')
            self.close_button.config(text="RETRY")
            return

        self.root.update()

        self.insert_item('')
        self.insert_item('Successfully established connection')
        self.insert_item('Starting downloads')

        self.close_button.config(command=self.close, text="CLOSE")

        self.root.update()

        if len(self.downloads) <= 0:
            self.insert_item('No download commands provided', _THEME['background'], _THEME['error'], _THEME['error'])
            self.okay_to_close = True
            self.close_button.config(state=tk.NORMAL)
            return

        self.okay_to_close = False
        self.close_button.config(state=tk.DISABLED)

        self.root.update()

        for command in self.downloads[1]:
            self.insert_item(f' ')
            if command in _COMMANDS:
                self.insert_item(f'Running command \"{command}\".')
                files = _COMMANDS[command]
                for c_url, dst_file in files:
                    try:
                        success, result = tr(HTTP.request, 'GET', f'{URL_BASE}/{c_url}')
                        if not success:
                            self.insert_item(f'Failed to download file source file: {result}', fg=_THEME['error'], sfg=_THEME['error'])
                            continue

                        dst_dir = "\\".join(folder for folder in dst_file.replace('/', '\\').split('\\')[:-1:])
                        dst_file_name = dst_file.replace('/', '\\').split('\\')[-1]
                        dst_dir = dst_dir.strip('\\')

                        if dst_dir.strip() in ('.', '', '<root>', '.\\', './', '\\.', '/.'):
                            file = dst_file_name
                        else:
                            if not os.path.isdir(dst_dir):
                                os.makedirs(dst_dir)
                            file = dst_file

                        with open(file, 'wb') as dst_f:
                            dst_f.write(result.data)
                            dst_f.close()

                    except Exception as excep:
                        sys.stderr.write(f"{traceback.format_exc()}\n")

                        try:
                            self.insert_item(f'Failed to download \'{dst_file_name}\': {excep}', fg=_THEME['error'], sfg=_THEME['error'])
                        except NameError:
                            self.insert_item(f'Failed to download file for command \'{command}\': {excep}', fg=_THEME['error'], sfg=_THEME['error'])

                        continue

                    self.insert_item(f'Successfully downloaded \'{dst_file_name}\'', fg=_THEME['ok'], sfg=_THEME['ok'])
                    nv_delete_flag(_NV_ROOT, command)

            else:
                self.insert_item(f"Unknown command \"{command}\"", fg=_THEME['error'], sfg=_THEME['error'])

            self.root.update()

        load_commands()

        for command in load_manifest()['secondary']:
            self.insert_item(f' ')
            if command in _COMMANDS:
                self.insert_item(f'Running command \"{command}\".')
                files = _COMMANDS[command]
                for c_url, dst_file in files:
                    try:
                        success, result = tr(HTTP.request, 'GET', f'{URL_BASE}/{c_url}')
                        if not success:
                            self.insert_item(f'Failed to download file source file: {result}', fg=_THEME['error'], sfg=_THEME['error'])
                            continue

                        dst_dir = "\\".join(folder for folder in dst_file.replace('/', '\\').split('\\')[:-1:])
                        dst_file_name = dst_file.replace('/', '\\').split('\\')[-1]
                        dst_dir = dst_dir.strip('\\')

                        if dst_dir.strip() in ('.', '', '<root>', '.\\', './', '\\.', '/.'):
                            file = dst_file_name
                        else:
                            if not os.path.isdir(dst_dir):
                                os.makedirs(dst_dir)
                            file = dst_file

                        with open(file, 'wb') as dst_f:
                            dst_f.write(result.data)
                            dst_f.close()

                    except Exception as excep:
                        sys.stderr.write(f"{traceback.format_exc()}\n")

                        try:
                            self.insert_item(f'Failed to download \'{dst_file_name}\': {excep}', fg=_THEME['error'], sfg=_THEME['error'])
                        except NameError:
                            self.insert_item(f'Failed to download file for command \'{command}\': {excep}', fg=_THEME['error'], sfg=_THEME['error'])

                        continue

                    self.insert_item(f'Successfully downloaded \'{dst_file_name}\'', fg=_THEME['ok'], sfg=_THEME['ok'])
                    nv_delete_flag(_NV_ROOT, command)

            else:
                self.insert_item(f"Unknown command \"{command}\"", fg=_THEME['error'], sfg=_THEME['error'])

            self.root.update()

        self.okay_to_close = True
        self.close_button.config(state=tk.NORMAL)
        self.insert_item(f' ')
        self.insert_item(f'Executed all commands', fg=_THEME['ok'], sfg=_THEME['ok'])

        return

    def __del__(self):
        self.thread.join(self, 0)


@click.group()
def _cli_handler():
    pass


@_cli_handler.command()
@click.option('--ReadFlags', help='find commands in .nvf folder', is_flag=True)
@click.option('--Update', help="specify command", is_flag=False)
@click.option('--Console', help="open debugging console", is_flag=True)
@click.option('--Title', help="title to be displayed on the UI", is_flag=False, default="Updating App")
@click.option('--noAdmin', help='do not ask for UAC elevation', is_flag=True)
def start(**kwargs):
    if _is_admin() or kwargs['noadmin']:
        try:
            commands = []
            if kwargs.get('readflags'):
                commands = ['ReadFlags']
            if kwargs.get('update') is not None:
                commands.append(kwargs['update'])

            UpdaterUI(commands, **kwargs)

        except Exception:
            if kwargs['console']:
                sys.stderr.write(f"{traceback.format_exc()}\n")
                while True:
                    pass

    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, int(kwargs['console']))


def _is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def tr(command, *args, **kwargs):
    try:
        return True, command(*args, **kwargs)
    except Exception as excep:
        return False, excep


def nv_check_flag(script: str, name: str):
    global NV_ROOT, NV_DELIMITER

    name = name.replace(NV_DELIMITER, '__')
    return os.path.exists(f"{NV_ROOT}\\{script}{NV_DELIMITER}{name}")


def nv_delete_flag(script: str, name: str):
    global NV_ROOT, NV_DELIMITER

    name = name.replace(NV_DELIMITER, '__')

    if nv_check_flag(script, name):
        os.remove(f"{NV_ROOT}\\{script}{NV_DELIMITER}{name}")


def nv_yield_all_flags_as_list(script: str):
    global NV_ROOT, NV_DELIMITER

    acc = []

    if os.path.isdir(NV_ROOT):
        for item in os.listdir(NV_ROOT):
            if isinstance(script, type):
                if script is any:
                    acc.append(item.replace('__', NV_DELIMITER))

                continue

            if item.split(NV_DELIMITER)[0].lower().strip() == script.lower().strip():
                acc.append(item.split(NV_DELIMITER)[1].replace('__', NV_DELIMITER))

    return acc


def nv_create_flag(script: str, name: str):
    global NV_ROOT, NV_DELIMITER

    if not os.path.isdir(NV_ROOT):
        os.makedirs(NV_ROOT)

    name = name.replace(NV_DELIMITER, '__')

    if not nv_check_flag(script, name):
        with open(f"{NV_ROOT}\\{script}{NV_DELIMITER}{name}", 'w') as flag:
            flag.close()


def nv_clear_all_app_flags(script: str):
    global NV_ROOT, NV_DELIMITER

    if os.path.isdir(NV_ROOT):
        for item in os.listdir(NV_ROOT):
            if item.split(NV_DELIMITER)[0].lower().strip() == script.lower().strip():
                os.remove(f"{NV_ROOT}\\{item}")


def load_manifest() -> dict:
    with open('.config\\update_manifest.json', 'r') as manifest_file:
        o = json.loads(manifest_file.read())
        manifest_file.close()

    return o


if __name__ == "__main__":
    if 'start' in sys.argv:
        _cli_handler()
    else:
        Install()
