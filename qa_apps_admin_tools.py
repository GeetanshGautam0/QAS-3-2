from threading import Thread
import tkinter as tk, sys
from typing import *
import qa_functions


script_name = "APP_AT"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False


class _UI(Thread):
    def __init__(self, root, ic, ds, **kwargs):
        super().__init__()
        Thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs

        self.start()
        self.root.mainloop()

    def close(self):
        sys.stdout.write("at - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.after(0, self.root.quit)

    def run(self):
        self.root.protocol('WM_DELETE_WINDOW', self.close)


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs):
    ui_root = tk.Tk()
    cls = _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root
