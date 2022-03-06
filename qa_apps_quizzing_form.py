from threading import Thread
import tkinter as tk, sys
from typing import *


class _UI(Thread):
    def __init__(self, root, ic, ds):
        super().__init__()
        Thread.__init__(self)

        self.root, self.ic, self.ds = root, ic, ds

        self.start()
        self.root.mainloop()

    def close(self):
        sys.stdout.write("qf - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.after(0, self.root.quit)

    def run(self):
        self.root.protocol('WM_DELETE_WINDOW', self.close)


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel]):
    ui_root = tk.Tk()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell)

    return ui_root
