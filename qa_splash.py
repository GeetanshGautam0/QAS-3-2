import tkinter.ttk as ttk, qa_functions, sys, PIL.Image, PIL.ImageTk
from tkinter import *


theme = qa_functions.LoadTheme.auto_load_pref_theme()


class Splash(Toplevel):
    def __init__(self, master, title, img_src):
        global theme
        self.theme = theme

        self.style = ttk.Style()
        self.root, self.title, self.img_path = master, title, img_src
        self.frame = Frame(self.root)
        self.img_size = (50, 50)
        self.img = None

        self.geo = "600x225+{}+{}".format(
            int(self.root.winfo_screenwidth() / 2 - 300),
            int(self.root.winfo_screenheight() / 2 - 125)
        )

        self.titleLbl = Label(self.frame, text=title)
        self.imgLbl = Label(self.frame, anchor=E)
        self.pbar = ttk.Progressbar(self.frame, length=100, mode='determinate', orient=HORIZONTAL)
        self.loading_label = Label(self.frame, justify=LEFT, anchor=W, text="Loading\nGeetansh Gautam\nPress\"ALT + F4\" to exit")
        self.infoLbl = Label(self.frame, justify=LEFT, anchor=W, text="")

        self.ac_start = self.theme.foreground.color
        self.ac_end = self.theme.accent.color
        self.loadGrad = True
        self.grad = ["#000000"]
        self.complete = False

        self.run()
        self.root.update()

    def update_loading_lbl(self):
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

        self.frame.pack(fill=BOTH, expand=True)
        self.frame.config(bg=self.theme.background.color)

        self.load_png()
        self.imgLbl.configure(
            image=self.img,
            bg=self.theme.background.color,
            bd=0,
            activebackground=self.theme.background.color
        )
        self.imgLbl.image = self.img

        self.infoLbl.pack(fill=X, expand=False, padx=5, side=BOTTOM, pady=(5, 0))
        self.loading_label.pack(fill=X, expand=False, padx=5, side=BOTTOM)
        self.pbar.pack(fill=X, expand=False, side=BOTTOM)

        self.titleLbl.pack(fill=BOTH, expand=True, padx=5, side=RIGHT)
        self.imgLbl.pack(fill=BOTH, expand=False, padx=(5, 0), side=LEFT)

        self.update_ui()
        self.update_loading_lbl()

    def completeColor(self) -> None:
        self.complete = True

        self.style.configure(
            "Horizontal.TProgressbar",
            foreground=self.theme.accent.color,
            background=self.theme.accent.color,
            troughcolor=self.theme.background.color
        )
        self.titleLbl.config(
            fg=self.theme.accent.color,
            bg=self.theme.background.color
        )
        self.frame.config(
            bg=self.theme.background.color
        )
        self.infoLbl.config(
            bg=self.theme.background.color,
            fg=self.theme.foreground.color
        )

        self.update_ui()

    def setImg(self, img) -> None:
        self.img_path = img
        self.load_png()
        self.imgLbl.configure(image=self.img)
        self.imgLbl.image = self.img
        self.imgLbl.update()

    def setProgress(self, per: float) -> None:
        if self.loadGrad:
            self.grad = qa_functions.ColorFunctions.fade(self.ac_start, self.ac_end)
            self.loadGrad = False

        self.pbar['value'] = per

        if not self.complete:
            self.style.configure(
                "Horizontal.TProgressbar",
                background=self.grad[int((len(self.grad) - 1) * (per / 100) * 0.8)],
                foreground=self.grad[int((len(self.grad) - 1) * (per / 100) * 0.8)],
                troughcolor=self.theme.background.color
            )
            self.titleLbl.config(fg=self.grad[int((len(self.grad) - 1) * per / 100)])

        self.pbar.update()

    def setInfo(self, text) -> None:
        self.information = text.strip()
        self.infoLbl.config(text=self.information)
        self.root.update()

    def setTitle(self, text: str) -> None:
        # self.title = text.replace(' ', '\n')
        self.title = text.strip()
        self.titleLbl.config(text=self.title)
        self.root.update()

    def update_ui(self) -> None:
        self.root.config(bg=self.theme.background.color)
        self.frame.config(bg=self.theme.background.color)
        self.titleLbl.config(bg=self.theme.background.color, fg=self.theme.accent.color, font=(self.theme.font_face, 36), anchor=W, justify=LEFT)
        self.infoLbl.config(bg=self.theme.background.color, fg=self.theme.foreground.color, font=(self.theme.font_face, self.theme.font_small_size), anchor=W, justify=LEFT)
        self.loading_label.config(bg=self.theme.background.color, fg=self.theme.foreground.color, font=(self.theme.font_face, self.theme.font_small_size), anchor=W, justify=LEFT)

        self.style.configure(
            "Horizontal.TProgressbar",
            foreground=self.grad[0],
            background=self.grad[0],
            troughcolor=self.theme.background.color,
            borderwidth=0,
            thickness=2
        )

        self.pbar.configure(style="Horizontal.TProgressbar")

        self.root.update()

    def load_png(self):
        i = PIL.Image.open(self.img_path)
        i = i.resize(self.img_size, PIL.Image.ANTIALIAS)
        self.img = PIL.ImageTk.PhotoImage(i)


def Pass(): pass


def hide(__inst: Splash):
    __inst.root.overrideredirect(False)
    __inst.root.wm_attributes("-topmost", 0)
    __inst.root.iconify()
    __inst.root.withdraw()
    __inst.root.update()
    return


def show(__inst: Splash = None):
    if __inst is None:
        __inst = Splash(Toplevel(), 'Quizzing Application', qa_functions.Files.QF_ico)

    __inst.root.overrideredirect(True)
    __inst.root.deiconify()
    __inst.root.wm_attributes("-topmost", 1)
    __inst.root.update()
    return __inst


def destroy(__inst: Splash):
    __inst.root.after(0, __inst.root.destroy)
    return
