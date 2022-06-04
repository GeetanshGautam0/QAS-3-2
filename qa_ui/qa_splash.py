import tkinter.ttk as ttk, qa_functions, PIL.Image, PIL.ImageTk, math, sys, tkinter as tk
from time import sleep
from typing import *
from qa_functions.qa_theme_loader import Load as LoadTheme


theme = LoadTheme.auto_load_pref_theme()


class Splash(tk.Toplevel):
    def __init__(self, master: tk.Toplevel, title: str, img_src: str, **kw) -> None:
        super().__init__(master, **kw)
        global theme

        self.theme = theme
        self.destroyed = False

        self.root: tk.Toplevel = master
        self.title_string, self.img_path = title, img_src
        self.frame: tk.Frame = tk.Frame(self.root)  # type: ignore
        self.img_size = (60, 60)
        self.img = None

        self.style = ttk.Style()
        self.style.theme_use('default')

        self.geo = "600x250+{}+{}".format(
            int(self.root.winfo_screenwidth() / 2 - 300),
            int(self.root.winfo_screenheight() / 2 - 125)
        )

        self.titleLbl = tk.Label(self.frame, text=title)
        self.imgLbl = tk.Label(self.frame, anchor=tk.E)
        self.pbar = ttk.Progressbar(self.frame, length=100, mode='determinate', orient=tk.HORIZONTAL)
        self.loading_label = tk.Label(self.frame, justify=tk.LEFT, anchor=tk.W, text="Loading\nGeetansh Gautam\nPress\"ALT + F4\" to exit")
        self.infoLbl = tk.Label(self.frame, justify=tk.LEFT, anchor=tk.W, text="")

        self.ac_start = self.theme.foreground.color
        self.ac_end = self.theme.accent.color
        self.loadGrad = True
        self.grad = (self.theme.foreground.color, )
        self.complete = False

        self.run()
        self.root.update()

    def update_loading_lbl(self):
        if self.complete:
            self.loading_label.config(text=f'Done Loading\nGeetansh Gautam\nPress\"ALT + F4\" to exit')
        else:
            c = self.loading_label.cget('text').count('.')
            c = (c+1) if c < 3 else 0
            self.loading_label.config(text=f'Loading{"."*c}\nGeetansh Gautam\nPress\"ALT + F4\" to exit')
            self.root.update()
            self.root.after(500, self.update_loading_lbl)

    def run(self):
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
        self.root.wm_attributes('-topmost', 1)
        self.root.geometry(self.geo)

        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.config(bg=self.theme.background.color, bd='0')

        self.load_png()
        self.imgLbl.configure(
            image=self.img,
            bg=self.theme.background.color,
            bd=0,
            activebackground=self.theme.background.color
        )
        self.imgLbl.image = self.img

        self.loading_label.pack(fill=tk.X, expand=False, padx=5, side=tk.BOTTOM)
        self.infoLbl.pack(fill=tk.X, expand=False, padx=5, side=tk.BOTTOM)
        self.pbar.pack(fill=tk.X, expand=False, side=tk.BOTTOM)

        self.titleLbl.pack(fill=tk.BOTH, expand=True, padx=5, side=tk.RIGHT)
        self.imgLbl.pack(fill=tk.BOTH, expand=False, padx=(5, 0), side=tk.LEFT)

        self.update_ui()
        self.setProgress(0)
        self.update_loading_lbl()

    def showCompletion(self) -> None:
        if self.destroyed:
            return

        self.pbar['value'] = 100

        self.complete = True
        self.update_loading_lbl()
        self.infoLbl.pack_forget()

        self.update_ui()

    def setImg(self, img) -> None:
        if self.destroyed:
            return

        self.img_path = img
        self.load_png()
        self.imgLbl.config(image=self.img)  # type: ignore
        self.imgLbl.image = self.img        # type: ignore
        self.imgLbl.update()                # type: ignore

    def setProgress(self, per: float) -> None:
        if self.destroyed:
            return

        if per >= 100:
            self.complete = True
            self.showCompletion()
            return

        if self.loadGrad:
            self.grad = qa_functions.ColorFunctions.fade(self.ac_start, self.ac_end)
            self.loadGrad = False

        self.pbar.configure(style="Horizontal.TProgressbar")
        self.pbar['value'] = per

        if not self.complete:
            self.style.configure(
                "Horizontal.TProgressbar",
                background=self.grad[int((len(self.grad) - 1) * (per / 100) * 0.8)],
                foreground=self.grad[int((len(self.grad) - 1) * (per / 100) * 0.8)],
                troughcolor=self.theme.background.color
            )
            self.titleLbl.config(fg=self.grad[int((len(self.grad) - 1) * per / 100)])
            self.infoLbl.config(fg=self.grad[int((len(self.grad) - 1) * per / 100)])

        self.root.update()

    def setInfo(self, string) -> None:
        if self.destroyed:
            return

        if self.complete:
            return

        self.infoLbl.config(text=string)
        self.root.update()

    def setTitle(self, string: str) -> None:
        if self.destroyed:
            return

        self.title_string = string.strip()
        self.titleLbl.config(text=self.title_string)
        self.root.update()

    def update_ui(self) -> None:
        if self.destroyed:
            return

        self.root.config(bg=self.theme.background.color)
        self.frame.config(bg=self.theme.background.color)
        self.titleLbl.config(bg=self.theme.background.color, font=(self.theme.font_face, math.floor(self.theme.font_title_size * 1.1)), anchor=tk.W, justify=tk.LEFT)
        self.infoLbl.config(bg=self.theme.background.color, fg=self.theme.foreground.color, font=(self.theme.font_face, self.theme.font_small_size), anchor=tk.W, justify=tk.LEFT)
        self.loading_label.config(bg=self.theme.background.color, fg=self.theme.foreground.color, font=(self.theme.font_face, self.theme.font_small_size), anchor=tk.W, justify=tk.LEFT)

        self.style.configure(
            "Horizontal.TProgressbar",
            foreground=self.grad[0],
            background=self.grad[0],
            troughcolor=self.theme.background.color,
            borderwidth=0,
            thickness=2
        )

        self.root.update()

    def load_png(self):
        if self.destroyed:
            return

        i = PIL.Image.open(self.img_path)
        i = i.resize(self.img_size, PIL.Image.ANTIALIAS)
        self.img = PIL.ImageTk.PhotoImage(i)


def update_step(inst: Splash, ind: int, steps: Union[list, tuple, Dict[int, Any]], resolution=100):
    inst.setInfo(steps[ind])

    ind -= 1  # 0 >> Max
    prev = ind - 1 if ind > 0 else ind

    for i in range(prev * resolution, ind * resolution):
        for j in range(20):
            pass  # < 0.01 sec delay

        inst.setProgress((i / len(steps)) / (resolution / 100))


def show_completion(inst: Splash, steps: Union[list, tuple, dict, set], resolution=100):
    ind = len(steps) - 1

    inst.showCompletion()
    for i in range(ind * resolution, len(steps) * resolution):
        for j in range(20):
            pass  # < 0.01 sec delay

        inst.setProgress((i / len(steps)) / (resolution / 100))

    sleep(.1)
    destroy(inst)


def hide(inst: Splash):
    inst.root.overrideredirect(False)
    inst.root.wm_attributes("-topmost", 0)
    inst.root.iconify()
    inst.root.withdraw()
    inst.root.update()
    return


def show(inst: Splash = None):
    if inst is None:
        inst = Splash(tk.Toplevel(), 'Quizzing Application', qa_functions.Files.QF_ico)

    inst.root.overrideredirect(True)
    inst.root.deiconify()
    inst.root.wm_attributes("-topmost", 1)
    inst.root.update()
    return inst


def destroy(inst: Splash):
    inst.destroyed = True
    inst.root.after(0, inst.root.destroy)
    return
