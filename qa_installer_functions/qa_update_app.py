import sys, traceback, time, random, click, hashlib, ctypes, threading, urllib3, \
    tkinter as tk, os
from tkinter import messagebox, ttk
from qa_functions import qa_nv_flags as NVF_Handler


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
_COMMANDS = {
    'DEFAULT_THEME': (
        ('https://raw.githubusercontent.com/GeetanshGautam0/QAS-3-2/master/.src/.defaults/.themes/default.json', '.src\\.defaults\\.themes\\default.json'),
        ('https://raw.githubusercontent.com/GeetanshGautam0/QAS-3-2/master/.src/.defaults/.themes/hashes.json', '.src\\.defaults\\.themes\\hashes.json'),
    )
}


class UpdaterUI(threading.Thread):
    def __init__(self, downloads, *args, **kwargs):
        super().__init__()
        self.thread = threading.Thread
        self.thread.__init__(self)

        self.okay_to_close = True

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

    def clear_lb(self):
        self.activity_acc = 0
        self.activity_box.delete(0, tk.END)

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

        self.root.title("Quizzing App | Updater")
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.window_pos[0]}+{self.window_pos[1]}")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        if os.path.isfile('.src\\.icons\\.app_ico\\updater.ico'):
            self.root.iconbitmap('.src\\.icons\\.app_ico\\updater.ico')

        self.error_label.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.BOTTOM)
        self.frame_1.pack(fill=tk.BOTH, expand=True)

        self.title_label.config(text="Updating Scripts", justify=tk.LEFT, anchor=tk.W)
        self.title_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.activity_box.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.close_button.config(text="CLOSE", command=self.close)
        self.close_button.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.update_theme()
        self.start_downloads()

    def start_downloads(self):
        global _THEME, _COMMANDS, _NV_ROOT, HTTP

        if len(self.downloads) <= 0:
            self.insert_item('No download commands provided', _THEME['background'], _THEME['error'], _THEME['error'])
            self.okay_to_close = True
            self.close_button.config(state=tk.NORMAL)
            return

        self.okay_to_close = False
        self.close_button.config(state=tk.DISABLED)

        if 'ReadFlags' in self.downloads:
            self.insert_item('Looking for commands in NVF folder.')
            n_coms = NVF_Handler.yield_all_flags_as_list(_NV_ROOT)
            for nc in n_coms:
                self.insert_item(f"   *{'Valid' if nc in _COMMANDS else 'Invalid'} command found: {nc}")
                if nc in _COMMANDS:
                    self.downloads.append(nc)
                else:
                    NVF_Handler.delete_flag(_NV_ROOT, nc)

            while 'ReadFlags' in self.downloads:
                self.downloads.pop(self.downloads.index('ReadFlags'))

        self.downloads = {*self.downloads}  # Remove duplicates

        for command in self.downloads:
            self.insert_item(f' ')

            if command in _COMMANDS:
                self.insert_item(f'Running command \"{command}\".')
                files = _COMMANDS[command]
                for url, dst_file in files:
                    try:
                        success, result = tr(HTTP.request, 'GET', url)
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
                    NVF_Handler.delete_flag(_NV_ROOT, command)

            else:
                self.insert_item(f"Unknown command \"{command}\"", fg=_THEME['error'], sfg=_THEME['error'])

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
def start(**kwargs):
    if _is_admin():
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


if __name__ == "__main__":
    _cli_handler()