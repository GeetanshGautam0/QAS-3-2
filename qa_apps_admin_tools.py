from threading import Thread
import tkinter as tk, sys
from typing import *


title_base = "Administrator Tools"
script_name = "APP_ADMT"


class _UI(Thread):
    def __init__(self, root, ic, ds, **kwargs):
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs

        self.start()
        self.root.mainloop()

    def close(self):
        sys.stdout.write("at - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.after(0, self.root.quit)

    def run(self):
        global title_base

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.title(title_base)

    def __del__(self):
        self.thread.join(self, 0)


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    ui_root = tk.Tk()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root
