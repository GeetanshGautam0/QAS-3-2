import json, qa_functions, sys, PIL, tkinter as tk, random, re, traceback, math  # , os, qa_files
from enum import Enum
from tkinter import ttk
from threading import Thread
from qa_functions.qa_custom import ThemeUpdateVars, ThemeUpdateCommands, LoggingLevel, HexColor, UnexpectedEdgeCase
from qa_functions.qa_std import gen_short_uid, ANSI, AppLogColors
from qa_ui import qa_prompts
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from typing import *
from dataclasses import dataclass


script_name = "APP_AT::QEdit"
APP_TITLE = "Quizzing Application | Editing Question"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
DEBUG_DEV_FLAG = False


class Levels(Enum):
    (NORMAL, OKAY, WARNING, ERROR) = range(4)


class DataType(Enum):
    (boolean, integer, string) = range(3)


class Codes:
    (FALSE, TRUE) = (str(a) for a in range(2))

    valMap = {
        True: TRUE,
        False: FALSE,
        None: qa_functions.SMem().NullStr
    }

    @staticmethod
    def substitute(value):
        return Codes.valMap[value] if value in Codes.valMap else value


@dataclass
class DataEntry:
    name: str
    index: int
    size: int
    type: DataType


class Data0:
    # Entries
    AutoMark  = DataEntry('auto_mark', 0, 1, DataType.boolean)
    Fuzzy     = DataEntry('fuzzy', 1, 1, DataType.boolean)
    FuzzyThrs = DataEntry('fuzzy:threshold', 2, 2, DataType.integer)

    entries = [AutoMark, Fuzzy, FuzzyThrs]


class Data1:
    QuestionType = DataEntry('qType', 0, 2, DataType.boolean)

    entries = [QuestionType]


@dataclass
class Message:
    LVL: Levels
    MSG: str


class SMemInd(Enum):
    (QUESTION, ANSWER, DATA0, DATA1) = range(4)


class CustomText(tk.Text):
    def __init__(self, logger: object, *args: Any, **kwargs: Any) -> None:
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"  # type: ignore
        self.tk.call("rename", self._w, self._orig)  # type: ignore
        self.tk.createcommand(self._w, self._proxy)  # type: ignore

        self._custom_as_enb = False
        self._custom_stg = False
        self.log = logger

    def _proxy(self, command: Any, *args: Any) -> Any:
        # avoid error when copying
        if command == 'get' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not self.tag_ranges('sel'):
            return

        # avoid error when deleting
        if command == 'delete' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not self.tag_ranges('sel'):
            return

        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ('insert', 'delete', 'replace'):
            self.event_generate('<<TextModified>>')

        return result

    def clear_all(self) -> None:
        self.delete('1.0', tk.END)

    def enable_auto_size(self) -> None:
        self._custom_as_enb = True
        self.log(LoggingLevel.INFO, f'(CustomWidget) {self.winfo_name()}: Enabled auto sizing')  # type: ignore
        self.bind('<Key>', self._custom_update_size)

    def auto_size(self) -> None:
        if not self._custom_as_enb:
            self.enable_auto_size()

        self._custom_update_size(None)

    def _custom_update_size(self, _: Any) -> None:
        if not self._custom_as_enb:
            return

        widget_width = 0
        widget_height = float(self.index(tk.END))

        for line in self.get("1.0", tk.END).split("\n"):
            if len(line) > widget_width:
                widget_width = len(line) + 1
            widget_height += 1

        self.config(width=widget_width, height=widget_height)

    def setup_color_tags(self, theme_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]], tab_len: int = 5) -> None:
        if self._custom_stg:
            return

        self._custom_stg = True

        self.log(LoggingLevel.INFO, f'(CustomWidget) {self.winfo_name()}: Enabled custom tags')  # type: ignore

        self.tag_config("<accent>", foreground=theme_map[ThemeUpdateVars.ACCENT].color)
        self.tag_config("<error>", foreground=theme_map[ThemeUpdateVars.ERROR].color)
        self.tag_config("<error_bg>", background=theme_map[ThemeUpdateVars.ERROR].color, foreground=theme_map[ThemeUpdateVars.BG].color)
        self.tag_config("<okay>", foreground=theme_map[ThemeUpdateVars.OKAY].color)
        self.tag_config("<okay_bg>", background=theme_map[ThemeUpdateVars.OKAY].color, foreground=theme_map[ThemeUpdateVars.BG].color)
        self.tag_config("<warning>", foreground=theme_map[ThemeUpdateVars.WARNING].color)
        self.tag_config("<warning_bg>", background=theme_map[ThemeUpdateVars.WARNING].color, foreground=theme_map[ThemeUpdateVars.BG].color)
        self.tag_config("<accent_bg>", background=theme_map[ThemeUpdateVars.ACCENT].color, foreground=theme_map[ThemeUpdateVars.BG].color)
        self.tag_config('<gray_fg>', foreground=theme_map[ThemeUpdateVars.GRAY].color)
        self.tag_config('<gray_bg>', background=theme_map[ThemeUpdateVars.GRAY].color)
        self.tag_config('<underline>', underline=1)
        self.tag_config('<indented_first>', lmargin1=tab_len)
        self.tag_config('<indented_body>', lmargin2=tab_len)


S_MEM_VAL_OFFSET = 512
S_MEM_M_VAL_MAX_SIZE = 2048  # Major Value (Question / Answer)
S_MEM_D_VAL_MAX_SIZE = 1024  # Data Value (Data0 / Data1)


class QEditUI(Thread):
    def __init__(self, logger: object, shared_mem_obj: qa_functions.SMem, edit_mode: bool = False, **kwargs: Any) -> None:
        super().__init__()
        self.thread = Thread
        self.thread.__init__(self)

        # TODO: Remove the following declarations
        global DEBUG_DEV_FLAG, DEBUG_NORM
        DEBUG_DEV_FLAG = kwargs['debug_dev']
        DEBUG_NORM = kwargs['debug'] or kwargs['debug_all']

        self.log = log
        self.s_mem, self.edit_mode, self.kwargs = shared_mem_obj, edit_mode, kwargs

        self.theme: qa_functions.qa_custom.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]] = {}

        self.root = tk.Toplevel()

        self.gi_cl = True
        self._job: Union[None, str] = None

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        wd_w = 850 if 850 <= self.screen_dim[0] else self.screen_dim[0]
        wd_h = 900 if 900 <= self.screen_dim[1] else self.screen_dim[1]
        self.window_size = [wd_w, wd_h]
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
        ]

        self.update_requests: Dict[str, List[Any]] = {}
        self.late_update_requests: Dict[tk.Widget, List[Any]] = {}
        self.data: Dict[Any, Any] = {}

        self.img_path = qa_functions.Files.AT_png
        self.img_size = (75, 75)
        self.svgs: Dict[str, Any] = {
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

        self.padX = 20
        self.padY = 10

        self.checkmark_src = "./.src/.icons/.progress/checkmark.svg"
        self.cog_src = './.src/.icons/.misc/settings.svg'
        self.arrow_left_src = './.src/.icons/.misc/left_arrow.svg'
        self.question_src = './.src/.icons/.misc/question.svg'
        self.arrow_right_src = './.src/.icons/.misc/right_arrow.svg'
        self.svg_tmp = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup".replace('/', '\\')
        self.load_png()

        self.ttk_theme = cast(str, self.kwargs['ttk_theme'])
        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = qa_functions.TTKTheme.configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Admin')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size, 'My')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

        # IMPORTANT NOTE:
        # The order of items in the following tuple dictates the order in which
        # the pages will be presented
        (self.QFrameInd, self.OptFrameInd, self.AnsFrameInd, self.RFrameInd) = range(4)

        self.screen_data: Dict[int, Dict[Any, Any]] = {
            self.QFrameInd: {},
            self.OptFrameInd: {},
            self.AnsFrameInd: {},
            self.RFrameInd: {},
        }

        # -------------------------------------------
        # TKINTER ELEMENT DECLARATIONS
        # -------------------------------------------

        # Global
        self.message_label = tk.Label(self.root)

        # Frames
        self.title_frame = tk.Frame(self.root)
        self.main_frame = tk.Frame(self.root)
        self.question_frame = tk.Frame(self.main_frame)
        self.options_frame = tk.Frame(self.main_frame)
        self.answer_frame = tk.Frame(self.main_frame)
        self.review_frame = tk.Frame(self.main_frame)

        self.frameMap: Dict[int, Tuple[tk.Frame, Any, bool]] = {
            self.QFrameInd: (self.question_frame, self.qf_setup, False),
            self.AnsFrameInd: (self.answer_frame, self.af_setup, False),
            self.OptFrameInd: (self.options_frame, self.of_setup, False),
            self.RFrameInd: (self.review_frame, self.rf_setup, False)
        }

        self.currentFrame: Union[None, int] = None

        # Title
        self.title_icon = tk.Label(self.title_frame)
        self.title_text = tk.Label(self.title_frame)

        # Navigation
        self.navbar = tk.Frame(self.root)
        self.next_btn = ttk.Button(self.navbar)
        self.prev_btn = ttk.Button(self.navbar)

        # Question Frame
        self.qf_ttl_lbl = tk.Label(self.question_frame)
        self.qf_inf_lbl = tk.Label(self.question_frame)
        self.qf_inp_box = CustomText(self.log, self.question_frame)
        self.qf_chr_cnt = tk.Label(self.question_frame)

        # Option Frame
        self.of_ttl_lbl = tk.Label(self.options_frame)
        self.of_ans_tp_cont = tk.LabelFrame(self.options_frame)
        self.of_ans_mc = ttk.Button(self.of_ans_tp_cont)
        self.of_ans_tf = ttk.Button(self.of_ans_tp_cont)
        self.of_ans_nm = ttk.Button(self.of_ans_tp_cont)

        self.of_nm_options = tk.LabelFrame(self.options_frame)
        self.of_nm_opt_fuz_ent_sv = tk.StringVar()
        self.of_nm_opt_fuz_ent_sv.set('50')
        self.of_nm_opt_fuz_ent_sv.trace('w', lambda *args, **kwargs: self.SVCallback(*args, **kwargs))

        self.of_nm_opt_canv = tk.Canvas(self.of_nm_options)
        self.of_nm_opt_vsb = ttk.Scrollbar(self.of_nm_options)

        self.of_nm_opt_main_frame = tk.Frame(self.of_nm_opt_canv)

        self.of_nm_opt_auto_cont = tk.LabelFrame(self.of_nm_opt_main_frame, text='Automatic v.s. Manual')
        self.of_nm_opt_auto_lbl = tk.Label(self.of_nm_opt_auto_cont)
        self.of_nm_opt_auto_enb = ttk.Button(self.of_nm_opt_auto_cont)

        self.of_nm_opt_fuzzy_cont = tk.LabelFrame(self.of_nm_opt_main_frame, text='Exact v.s. Approximate Match')
        self.of_nm_opt_fuzzy_enb = ttk.Button(self.of_nm_opt_fuzzy_cont)
        self.of_nm_opt_fuzzy_lbl = tk.Label(self.of_nm_opt_fuzzy_cont)

        self.of_nm_opt_fuzzy_thrs_cont = tk.LabelFrame(self.of_nm_opt_fuzzy_cont, text='Threshold')
        self.of_nm_opt_fuzzy_thrs_lbl = tk.Label(self.of_nm_opt_fuzzy_thrs_cont)
        self.of_nm_opt_fuzzy_thrs_ent = ttk.Entry(self.of_nm_opt_fuzzy_thrs_cont, textvariable=self.of_nm_opt_fuz_ent_sv)

        # Answer Frame
        self.af_ttl_lbl = tk.Label(self.answer_frame)

        self.af_tp_lbl = tk.Label(self.answer_frame)

        self.af_tf_sel_T = ttk.Button(self.answer_frame)
        self.af_tf_sel_F = ttk.Button(self.answer_frame)

        self.af_nm_ent = CustomText(self.log, self.answer_frame)
        self.af_nm_chr_cnt = tk.Label(self.answer_frame)

        self.af_mc_main_frame = tk.Frame(self.answer_frame)
        self.af_mc_btn_add_new = ttk.Button(self.af_mc_main_frame)
        self.af_mc_canv = tk.Canvas(self.af_mc_main_frame)
        self.af_mc_frame = tk.Frame(self.af_mc_canv)
        self.af_mc_vsb = ttk.Scrollbar(self.af_mc_main_frame, style='MyAdmin.TScrollbar')
        self.af_mc_xsb = ttk.Scrollbar(self.af_mc_main_frame, style='MyHorizAdmin.TScrollbar', orient=tk.HORIZONTAL)

        self.af_mc_cl_warn_lbl = tk.Label(self.af_mc_frame, text='WARNING: Changing the question-type and returning to this step WILL clear all options')

        self.af_mc_data = {}

        # Review Frame
        self.rf_ttl_lbl = tk.Label(self.review_frame)

        self.rf_main_frame = tk.Frame(self.review_frame)
        self.rf_canv = tk.Canvas(self.rf_main_frame)
        self.rf_vsb = ttk.Scrollbar(self.rf_main_frame, style='MyAdmin.TScrollbar')
        self.rf_xsb = ttk.Scrollbar(self.rf_main_frame, orient=tk.HORIZONTAL, style='MyHorizAdmin.TScrollbar')
        self.rf_frame = tk.Frame(self.rf_canv)

        self.rf_questions = tk.LabelFrame(self.rf_frame, text='Review Question')
        self.rf_options = tk.LabelFrame(self.rf_frame, text='Review Options')
        self.rf_answers = tk.LabelFrame(self.rf_frame, text='Review Answer')

        self.rf_q_lbl = CustomText(self.log, self.rf_questions)
        self.rf_o_lbl = CustomText(self.log, self.rf_options)
        self.rf_a_lbl = CustomText(self.log, self.rf_answers)

        self.start()
        self.root.mainloop()

    def __del__(self) -> None:
        self.thread.join(self, 0)

    def close(self) -> None:
        self.thread.join(self, 0)
        self.root.after(0, self.root.quit)
        self.root.withdraw()
        self.root.title('Quizzing Application | Closed Form')

    def run(self) -> None:
        global APP_TITLE

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.title(APP_TITLE)
        self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}")
        self.root.iconbitmap(qa_functions.Files.AT_ico)

        self.update_requests[gen_short_uid()] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.question_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.answer_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.options_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.review_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.main_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.navbar, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gen_short_uid()] = [self.title_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.update_requests[gen_short_uid()] = [self.title_icon, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.label_formatter(self.title_text, size=ThemeUpdateVars.FONT_SIZE_XL_TITLE, fg=ThemeUpdateVars.ACCENT, uid='title_label')
        self.label_formatter(self.title_icon, uid='title_icon')

        self.prev_btn.config(command=self.prev_page)
        self.next_btn.config(command=self.next_page)

        self.configure_main_frame()
        self.set_frame(self.QFrameInd)

        self.of_nm_opt_vsb.config(command=self.of_nm_opt_canv.yview)
        self.of_nm_opt_canv.configure(yscrollcommand=self.of_nm_opt_vsb.set)
        self.of_nm_opt_canv.create_window((0, 0), window=self.of_nm_opt_main_frame, anchor=tk.NW, tags='self.of_nm_opt_main_frame')  # type: ignore

        self.of_nm_opt_main_frame.bind("<Configure>", self.onFrameConfig)
        self.of_nm_opt_canv.bind("<MouseWheel>", self._on_mousewheel)
        self.of_nm_opt_vsb.bind("<MouseWheel>", self._on_mousewheel)

        self.rf_vsb.config(command=self.rf_canv.yview)
        self.rf_xsb.config(command=self.rf_canv.xview)
        self.rf_canv.configure(yscrollcommand=self.rf_vsb.set, xscrollcommand=self.rf_xsb.set)
        self.rf_canv.create_window((0, 0), window=self.rf_frame, anchor=tk.NW, tags='rf_frame')  # type: ignore

        self.rf_frame.bind("<Configure>", self.RF_onFrameConfig)
        self.rf_canv.bind("<MouseWheel>", self._RF_on_mousewheel)
        self.rf_vsb.bind("<MouseWheel>", self._RF_on_mousewheel)
        self.rf_xsb.bind("<MouseWheel>", self._RF_on_x_mousewheel)

        self.af_mc_vsb.config(command=self.af_mc_canv.yview)
        self.af_mc_xsb.config(command=self.af_mc_canv.xview)
        self.af_mc_canv.configure(yscrollcommand=self.af_mc_vsb.set, xscrollcommand=self.af_mc_xsb.set)
        self.af_mc_canv.create_window((0, 0), window=self.af_mc_frame, anchor=tk.NW, tags='af_mc_frame')  # type: ignore

        self.af_mc_frame.bind("<Configure>", self.AF_MC_onFrameConfig)
        self.af_mc_canv.bind("<MouseWheel>", self._AF_MC_on_mousewheel)
        self.af_mc_vsb.bind("<MouseWheel>", self._AF_MC_on_mousewheel)
        self.af_mc_xsb.bind("<MouseWheel>", self._AF_MC_on_x_mousewheel)

        self.setup_smem()
        self.update_ui()

    def RF_onFrameConfig(self, *_: Any, **_1: Any) -> None:
        self.rf_canv.configure(scrollregion=self.rf_canv.bbox("all"))

    def _RF_on_mousewheel(self, event: Any, *_: Any, **_1: Any) -> None:
        self.rf_canv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _RF_on_x_mousewheel(self, event: Any, *_: Any, **_1: Any) -> None:
        self.rf_canv.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def AF_MC_onFrameConfig(self, *_: Any, **_1: Any) -> None:
        self.af_mc_canv.configure(scrollregion=self.af_mc_canv.bbox("all"))

    def _AF_MC_on_mousewheel(self, event: Any, *_: Any, **_1: Any) -> None:
        self.af_mc_canv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _AF_MC_on_x_mousewheel(self, event: Any, *_: Any, **_1: Any) -> None:
        self.af_mc_canv.xview_scroll(int(-1 * (event.delta / 120)), "units")

    @staticmethod
    def get_children(widget: tk.Widget) -> List[tk.Widget]:
        def rc(_w: tk.Widget) -> List[tk.Widget]:
            el: List[tk.Widget] = []

            for child in _w.winfo_children():
                if child.winfo_children():
                    el.append(child)
                    el.extend(rc(child))
                else:
                    el.append(child)

            return el

        return rc(widget)

    def _on_mousewheel(self, event: Any) -> None:
        """
        Straight out of stackoverflow
        Article: https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        Change: added "int" around the first arg
        """
        self.of_nm_opt_canv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def onFrameConfig(self, _: Any) -> None:
        self.of_nm_opt_canv.configure(scrollregion=self.of_nm_opt_canv.bbox("all"))

    def SVCallback(self, *_0: Any, **_1: Any) -> None:
        v = self.of_nm_opt_fuz_ent_sv.get()
        c = ''.join(re.findall(r'\d+', v.strip()))
        try:
            integralVal = int(c)
        except ValueError:
            integralVal = 0

        if 1 <= integralVal <= 99:
            if c != v:
                self.of_nm_opt_fuz_ent_sv.set(c)
            else:
                return

        elif integralVal < 1:
            self.of_nm_opt_fuz_ent_sv.set('')

        elif integralVal >= 100:
            self.of_nm_opt_fuz_ent_sv.set(str(integralVal)[:2])

        else:
            raise UnexpectedEdgeCase(f'SVCallback (!1le, 99le ++ !1l, !100ge) : {integralVal}')

    def qf_setup(self) -> None:
        global S_MEM_M_VAL_MAX_SIZE

        self.disable_all_inputs()

        self.qf_ttl_lbl.config(text=f"Step {cast(int, self.currentFrame) + 1}: Question", anchor=tk.W, justify=tk.LEFT)
        self.qf_ttl_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.qf_inf_lbl.config(text="Enter the question in the text field below. Whenever you're done, click on 'Next Page' to proceed.", anchor=tk.W, justify=tk.LEFT)
        self.qf_inf_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)

        self.qf_chr_cnt.pack(fill=tk.X, expand=False, side=tk.BOTTOM, padx=self.padX)
        self.qf_chr_cnt.config(anchor=tk.W, justify=tk.LEFT)

        self.qf_inp_box.pack(fill=tk.BOTH, expand=True, padx=self.padX)

        self.label_formatter(self.qf_inf_lbl)
        self.label_formatter(self.qf_ttl_lbl, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE, padding=self.padX, uid='qf_ttl_lbl')
        self.label_formatter(self.qf_chr_cnt, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL, padding=self.padX, uid="qfTextCharCountLBL")
        self.update_requests[gen_short_uid()] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.qf_inp_box.config(
                    bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                    relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0],
                    wrap=tk.WORD, highlightthickness=args[5], highlightcolor=args[6],
                    bd=(args[5] if args[5] > 0 else 1)
                ),
                ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN,
                ThemeUpdateVars.BORDER_SIZE, ThemeUpdateVars.BORDER_COLOR
            ]
        ]

        self.qf_inp_box.bind('<<TextModified>>', self.onQfInpMod)
        self.onQfInpMod()  # setup character count

        # self.frameMap[self.QFrameInd] = (*self.frameMap[self.QFrameInd][:1], True)
        self.frameMap[self.QFrameInd] = (self.frameMap[self.QFrameInd][0], self.frameMap[self.QFrameInd][1], True)
        self.enable_all_inputs()

        return

    def onQfInpMod(self, *_: Any, **_1: Any) -> None:
        global S_MEM_M_VAL_MAX_SIZE

        text = self.qf_inp_box.get("1.0", "end-1c").strip()
        chars = len(text)
        self.qf_chr_cnt.config(text=f"{chars}/{S_MEM_M_VAL_MAX_SIZE} characters")

        if chars > S_MEM_M_VAL_MAX_SIZE:
            self.qf_inp_box.delete('1.0', tk.END)
            self.qf_inp_box.insert('1.0', text[:S_MEM_M_VAL_MAX_SIZE])

    def configNavButtons(self) -> None:
        if self.currentFrame == 0:
            self.prev_btn.config(state=tk.DISABLED, style="LG.TButton")

        if self.currentFrame == len(self.frameMap) - 1:
            self.next_btn.config(text="Submit Question", style="Accent2LG.TButton", command=self.submit_question, state=tk.NORMAL)
        else:
            self.next_btn.config(text="Next Step", style="LG.TButton", command=self.next_page, state=tk.NORMAL)

    def af_setup(self) -> None:
        self.disable_all_inputs()

        # Housekeeping, prep
        for widget in self.get_children(self.answer_frame):
            try:
                widget.pack_forget()
            except Exception as E:
                self.log(LoggingLevel.ERROR, f'<internalError> [af_setup] failed to pack_forget widget {widget} : {E}')

        assert self.screen_data[self.OptFrameInd].get('qType') in ('nm', 'tf', 'mc'), 'AnsFSetup: <!err;> OptF not setup properly'
        self.screen_data[self.AnsFrameInd]['qType'] = self.screen_data[self.OptFrameInd]['qType']

        self.screen_data[self.AnsFrameInd]['A::final'] = None
        self.screen_data[self.AnsFrameInd]['NM'] = {}
        self.screen_data[self.AnsFrameInd]['MC'] = {}
        self.screen_data[self.AnsFrameInd]['TF'] = {}

        # Setup
        self.af_ttl_lbl.config(text=f"Step {cast(int, self.currentFrame) + 1}: Answer", anchor=tk.W, justify=tk.LEFT)
        self.label_formatter(self.af_ttl_lbl, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE, padding=self.padX, uid='af_ttl_lbl')
        self.af_ttl_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.af_tp_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        if self.screen_data[self.AnsFrameInd]['qType'] == 'tf':
            self.af_tp_lbl.config(text='Select whether the correct response is TRUE or FALSE', anchor=tk.W, justify=tk.LEFT)

            self.af_tf_sel_T.config(text='The answer is TRUE', command=self.aF_tf_T_clk)
            self.af_tf_sel_F.config(text='The answer is FALSE', command=self.aF_tf_F_clk)

            self.af_tf_sel_T.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
            self.af_tf_sel_F.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        elif self.screen_data[self.AnsFrameInd]['qType'] == 'nm':
            self.af_tp_lbl.config(text='Please enter the correct answer below', anchor=tk.W, justify=tk.LEFT)
            self.af_nm_chr_cnt.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.BOTTOM)
            self.af_nm_chr_cnt.config(anchor=tk.W, justify=tk.LEFT)
            self.af_nm_ent.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        elif self.screen_data[self.AnsFrameInd]['qType'] == 'mc':
            if isinstance(self.af_mc_data.get('opt'), (list, tuple, set)):
                for uid in self.af_mc_data['opt']:
                    try:
                        self.update_requests.pop(f'{uid}[C]')
                    except:
                        pass

                    try:
                        self.update_requests.pop(f'{uid}[M]')
                    except:
                        pass

            self.af_mc_data = {
                # Key    [var?  [value, type, (Tuple[checks])]]
                'mc::N': [True, [0, int, ((lambda arg: int(arg) if int(arg) >= 0 else 0), )]],
            }  # Clear old MC data
            self.log(LoggingLevel.INFO, '[af_setup] Flushed MC_DATA dict (refr)')

            self.af_tp_lbl.config(text='Add AT LEAST two options below', anchor=tk.W, justify=tk.LEFT)

            self.af_mc_btn_add_new.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
            self.af_mc_btn_add_new.config(text='Add new option', command=self.AF_MC_addNew)

            self.af_mc_main_frame.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
            self.af_mc_vsb.pack(fill=tk.Y, expand=False, side=tk.RIGHT)
            self.af_mc_xsb.pack(fill=tk.X, expand=False, side=tk.BOTTOM)
            self.af_mc_canv.pack(fill=tk.BOTH, expand=True)

            self.af_mc_cl_warn_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

            self.label_formatter(self.af_mc_cl_warn_lbl, fg=ThemeUpdateVars.BG, bg=ThemeUpdateVars.WARNING, size=ThemeUpdateVars.FONT_SIZE_MAIN)
            self.update_requests['af_mc_main_frame-0'] = [
                self.af_mc_main_frame,
                ThemeUpdateCommands.BG,
                [ThemeUpdateVars.BG]
            ]
            self.update_requests['af_mc_frame-0'] = [
                self.af_mc_frame,
                ThemeUpdateCommands.BG,
                [ThemeUpdateVars.BG]
            ]
            self.update_requests['af_mc_canv-0'] = [
                self.af_mc_canv,
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: self.af_mc_canv.config(bg=args[0], bd='0', highlightthickness='0'),
                    ThemeUpdateVars.BG
                ]
            ]
            self.update_requests['AfFr::(MC):Canv{Dim}{a}'] = [
                None,
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: self.af_mc_canv.config(width=args[0] - args[2], height=args[1] - args[3]),
                    ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                    ('<LOOKUP>', 'padX'), ('<LOOKUP>', 'padY')
                ]
            ]

        else:
            raise UnexpectedEdgeCase('AnsSetup : <internal ERR> - qType <!nm, !mc, !tf>')

        self.frameMap[self.AnsFrameInd] = (self.frameMap[self.AnsFrameInd][0], self.frameMap[self.AnsFrameInd][1], True)
        self.label_formatter(self.af_tp_lbl, size=ThemeUpdateVars.FONT_SIZE_MAIN)

        self.update_requests[gen_short_uid()] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.af_nm_ent.config(
                    bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                    relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0],
                    wrap=tk.WORD, highlightthickness=args[5], highlightcolor=args[6],
                    bd=(args[5] if args[5] > 0 else 1)
                ),
                ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN,
                ThemeUpdateVars.BORDER_SIZE, ThemeUpdateVars.BORDER_COLOR
            ]
        ]

        self.af_nm_ent.bind('<<TextModified>>', self.onAfInpMod)
        self.onAfInpMod()  # setup character count

        self.label_formatter(self.af_nm_chr_cnt, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL, padding=self.padX, uid="aFNmTextCharCountLBL")

        self.enable_all_inputs()
        return

    def get_mc_data(self, key: str) -> Any:
        if key not in self.af_mc_data:
            return None
        V, val = self.af_mc_data[key]
        if V:
            nVal, tp, funcs = val
            assert isinstance(nVal, tp)
            if isinstance(funcs, (tuple, list, set)):
                for func in funcs:
                    nVal = func(nVal)
            return nVal

        else:
            return val

    def set_mc_data(self, key: str, data: Any) -> None:
        assert key in self.af_mc_data, 'Hint: manually add configuration for variable/data before using set_mc_data method'
        V, val = self.af_mc_data[key]

        if V:
            _, tp, funcs = val
            if isinstance(funcs, (tuple, list, set)):
                for func in funcs:
                    data = func(data)

            assert isinstance(data, tp)
            self.af_mc_data[key][1][0] = data

        else:
            self.af_mc_data[key][1] = data

    def AF_MC_addNew(self) -> None:
        try:
            SMem = qa_functions.SMem()
            index = cast(int, self.get_mc_data('mc::N')) + 1
            ident = mc_label_gen(index)
            qa_prompts.InputPrompts.MCInp(SMem, f'Please enter the text for option "{ident}"')

            if SMem.get() == SMem.NullStr:
                del SMem
                return

            else:
                cor = bool(int(SMem.get()[0]))
                val = SMem.get()[1::].strip()
                del SMem

                if self._add_ident(index, ident, val, cor):
                    self.show_message(Message(Levels.OKAY, 'Successfully added question'))
                else:
                    self.show_message(Message(Levels.ERROR, 'Failed to add question'))

        except Exception as E:
            self.show_message(Message(Levels.ERROR, 'Failed to add question'))
            self.log(LoggingLevel.ERROR, f"Failed to add question: {E}")
            self.log(LoggingLevel.DEBUG, traceback.format_exc())

    def _edit_ident(self, uid: str) -> None:
        SMem = qa_functions.SMem()
        ident, val, isCorr = self.af_mc_data['el'][uid]
        qa_prompts.InputPrompts.MCInp(SMem, f'Please enter the text for option "{ident}"', val, isCorr)

        if SMem.get() == SMem.NullStr:
            del SMem
            return

        else:
            cor = bool(int(SMem.get()[0]))
            nVal = SMem.get()[1::].strip()
            del SMem

            m = cast(CustomText, self.af_mc_data['el'][f'{uid}[M]'])

            m.config(state=tk.NORMAL)
            m.delete('1.0', 'end')
            m.insert('1.0', 'Value: "')
            m.insert('end', nVal, '<accent>')
            m.insert('end', '"\nFlags:')
            m.insert('end', '\n    \u2022 is_correct: ')
            m.insert('end', str(cor), '<okay>' if cor else '<error>')
            m.insert('end', '\n    \u2022 identifier: ')
            m.insert('end', ident, '<accent>')
            m.config(state=tk.DISABLED)

            self.af_mc_data['el'][uid] = [ident, nVal, cor]
            if not isinstance(self.af_mc_data.get('corr'), list):
                self.af_mc_data['corr'] = []

            if cor:
                self.af_mc_data['corr'].append(uid)
            else:
                if uid in self.af_mc_data['corr']:
                    self.af_mc_data['corr'].pop(self.af_mc_data['corr'].index(uid))

        self.update_ui()

    def _del_ident(self, uid: str) -> None:
        bSMem = qa_functions.SMem()
        ident, _, _1 = self.af_mc_data['el'][uid]
        qa_prompts.InputPrompts.ButtonPrompt(bSMem, 'Confirm Deletion', ('Delete', 'y'), ('Don\'t Delete', 'n'), default='n', message=f'Are you sure you want to delete option "{ident}"')

        if bSMem.get() is None:
            del bSMem
            return

        elif cast(str, bSMem.get()) != 'y':
            del bSMem
            return

        cont = self.af_mc_data['el'][f'{uid}[C]']
        cont.pack_forget()
        del cont, bSMem

        for rt, nm in (('el', uid), ('el', f'{uid}[C]'), ('el', f'{uid}[C]'), ('opt', uid), ('corr', uid)):
            if nm in self.af_mc_data[rt]:
                if isinstance(self.af_mc_data[rt], list):
                    self.af_mc_data[rt].pop(self.af_mc_data[rt].index(nm))
                elif isinstance(self.af_mc_data[rt], dict):
                    self.af_mc_data[rt].pop(nm)
                else:
                    pass  # Cannot pop

        self.update_requests.pop(f'{uid}[C]')
        self.update_requests.pop(f'{uid}[M]')

        qa_prompts.MessagePrompts.show_info(
            qa_prompts.InfoPacket(
                'The identifiers (labels) may be messed up in the list (i.e., "A" may be followed up by "C" if you delete "B", etc.) Note, however, that these identifiers are re-generated later and will therefore be fixed automatically AFTER the question is submitted.'
            )
        )

        self.update_ui()

    def _add_ident(self, index: int, identifier: str, value: str, is_correct: bool, inc: bool = True) -> bool:
        self.log(LoggingLevel.DEBUG, f'{identifier} ({is_correct}) :: {value}')

        try:
            UID = gen_short_uid()

            cont = tk.LabelFrame(self.af_mc_frame, text=f'Option {identifier}')
            m = CustomText(self.log, cont)
            eB = ttk.Button(cont, text='Edit', command=lambda: self._edit_ident(UID))
            dB = ttk.Button(cont, text='Delete', command=lambda: self._del_ident(UID))

            m.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
            cont.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)
            eB.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
            dB.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

            m.setup_color_tags(self.theme_update_map)
            m.delete('1.0', 'end')
            m.insert('1.0', 'Value: "')
            m.insert('end', value, '<accent>')
            m.insert('end', '"\nFlags:')
            m.insert('end', '\n    \u2022 is_correct: ')
            m.insert('end', str(is_correct), '<okay>' if is_correct else '<error>')
            m.insert('end', '\n    \u2022 identifier: ')
            m.insert('end', identifier, '<accent>')

            m.auto_size()

            if not isinstance(self.af_mc_data.get('corr'), list):
                self.af_mc_data['corr'] = []

            if is_correct:
                self.af_mc_data['corr'].append(UID)

            if 'el' not in self.af_mc_data:
                self.af_mc_data['el'] = {
                    f"{UID}[C]": cont,
                    f"{UID}[M]": m,
                    UID: [identifier, value, is_correct]
                }
            else:
                self.af_mc_data['el'][f"{UID}[C]"] = cont
                self.af_mc_data['el'][f"{UID}[M]"] = m
                self.af_mc_data['el'][UID] = [identifier, value, is_correct]

            if 'opt' not in self.af_mc_data:
                self.af_mc_data['opt'] = [UID]
            else:
                cast(List[str], self.af_mc_data['opt']).append(UID)

            self.update_requests[f"{UID}[C]"] = [
                None,
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: cast(tk.LabelFrame, self.af_mc_data['el'][args[0]]).config(
                        bg=args[1], fg=args[2], font=(args[3], args[4])
                    ),
                    ('<LOOKUP>', 'uid'),
                    ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
                ]
            ]

            self.update_requests[f'{UID}[M]'] = [
                None,
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: cast(CustomText, self.af_mc_data['el'][args[0]]).config(
                        state=tk.DISABLED, bd=0, highlightthickness=0, bg=args[1],
                        fg=args[2], font=(args[3], args[4])
                    ),
                    ('<LOOKUP>', 'uid'), ThemeUpdateVars.BG, ThemeUpdateVars.FG,
                    ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN
                ]
            ]

            if inc:
                self.set_mc_data('mc::N', index)

        except Exception as E:
            self.log(LoggingLevel.DEBUG, traceback.format_exc())
            self.log(LoggingLevel.ERROR, f"_add_ident: {E}")
            return False

        else:
            self.update_ui()
            return True

    def onAfInpMod(self, *_: Any, **_1: Any) -> None:
        global S_MEM_M_VAL_MAX_SIZE

        if self.screen_data[self.AnsFrameInd]['qType'] != 'nm': return

        text = self.af_nm_ent.get("1.0", "end-1c").strip()
        chars = len(text)
        self.af_nm_chr_cnt.config(text=f"{chars}/{S_MEM_M_VAL_MAX_SIZE} characters")

        if chars > S_MEM_M_VAL_MAX_SIZE:
            self.af_nm_ent.delete('1.0', tk.END)
            self.af_nm_ent.insert('1.0', text[:S_MEM_M_VAL_MAX_SIZE])

    def configure_aF_tf_btns(self) -> None:
        if self.screen_data[self.AnsFrameInd].get('qType') != 'tf':
            return

        if self.screen_data[self.AnsFrameInd]['TF'].get('sel') is None:
            return

        selection = self.screen_data[self.AnsFrameInd]['TF']['sel']

        if selection:
            self.af_tf_sel_T.config(style='Active.TButton')
            self.af_tf_sel_F.config(style='')
        else:
            self.af_tf_sel_F.config(style='Active.TButton')
            self.af_tf_sel_T.config(style='')

        self.screen_data[self.AnsFrameInd]['A::final'] = selection

    def aF_tf_T_clk(self) -> None:
        if self.screen_data[self.AnsFrameInd].get('qType') != 'tf':
            return

        self.screen_data[self.AnsFrameInd]['TF']['sel'] = True
        self.configure_aF_tf_btns()

    def aF_tf_F_clk(self) -> None:
        if self.screen_data[self.AnsFrameInd].get('qType') != 'tf':
            return

        self.screen_data[self.AnsFrameInd]['TF']['sel'] = False
        self.configure_aF_tf_btns()

    def of_setup(self) -> None:
        self.disable_all_inputs()

        self.of_ttl_lbl.config(text=f"Step {cast(int, self.currentFrame) + 1}: Options", anchor=tk.W, justify=tk.LEFT)
        self.label_formatter(self.of_ttl_lbl, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE, padding=self.padX, uid='of_ttl_lbl')
        self.of_ttl_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.of_ans_tp_cont.config(text="Question Type")
        self.of_ans_mc.config(
            text="Multiple Choice",
            command=lambda: self.root.focus_get().event_generate('<<MultipleChoice>>')  # type: ignore
        )
        self.of_ans_tf.config(
            text="True/False",
            command=lambda: self.root.focus_get().event_generate('<<TrueFalse>>')  # type: ignore
        )
        self.of_ans_nm.config(
            text="Written Response",
            command=lambda: self.root.focus_get().event_generate('<<Written>>')  # type: ignore
        )

        self.of_ans_mc.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
        self.of_ans_tf.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
        self.of_ans_nm.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.RIGHT)

        self.of_ans_tp_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.update_requests[gen_short_uid()] = [
            self.of_ans_tp_cont,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.of_ans_tp_cont.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]

        self.root.bind('<<MultipleChoice>>', self.mc_tp_sel)
        self.root.bind('<<TrueFalse>>', self.tf_tp_sel)
        self.root.bind('<<Written>>', self.nm_tp_sel)

        self.frameMap[self.OptFrameInd] = (self.frameMap[self.OptFrameInd][0], self.frameMap[self.OptFrameInd][1], True)
        self.enable_all_inputs()
        return

    def configure_tp_btns(self) -> None:
        self.of_ans_mc.configure(style='')
        self.of_ans_nm.configure(style='')
        self.of_ans_tf.configure(style='')

        if self.screen_data[self.OptFrameInd].get('qType') not in ('mc', 'tf', 'nm'):
            return

        ttk.Button, {
            'mc': self.of_ans_mc,
            'tf': self.of_ans_tf,
            'nm': self.of_ans_nm
        }[self.screen_data[self.OptFrameInd]['qType']].configure(style='Active.TButton')

    def configure_nm_options(self) -> None:
        self.of_nm_options.config(text="More Options")
        self.of_nm_options.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.of_nm_opt_vsb.pack(fill=tk.Y, expand=False, side=tk.RIGHT)
        self.of_nm_opt_vsb.configure(style='MyAdmin.TScrollbar')
        self.of_nm_opt_canv.pack(fill=tk.BOTH, expand=True)

        self.of_nm_opt_auto_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_auto_lbl.config(text="Should the application mark the response automatically, or require the administrator to mark it manually? (Automatic marks can be overridden by admin afterwards)", anchor=tk.W, justify=tk.LEFT)
        self.of_nm_opt_auto_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_auto_enb.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_auto_enb.config(command=self.nm_aut_cl)

        self.of_nm_opt_fuzzy_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_fuzzy_lbl.config(text="Should the application look for an exact match when marking, or an approximate match? (Applicable only when question set to 'Automatic Marking')", anchor=tk.W, justify=tk.LEFT)
        self.of_nm_opt_fuzzy_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_fuzzy_enb.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)

        self.of_nm_opt_fuzzy_thrs_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
        self.of_nm_opt_fuzzy_thrs_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_fuzzy_thrs_ent.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.of_nm_opt_fuzzy_thrs_lbl.config(text='Enter the threshold percentage (integral values between 1% and 99% (inclusive)) for similarities between the provided answer and the expected answer for a mark to be granted.\n\nNOTE: Do NOT include the \'%\' sign\n\nNOTE: For 100% match, use \'Exact Match\' mode.', anchor=tk.W, justify=tk.LEFT)

        self.of_nm_opt_fuzzy_enb.config(command=self.nm_fuz_cl)
        self.of_nm_opt_fuzzy_thrs_ent.configure(style='MyLarge.TEntry')

        self.label_formatter(self.of_nm_opt_fuzzy_lbl, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL, padding=self.padX*3)
        self.label_formatter(self.of_nm_opt_auto_lbl, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL, padding=self.padX*3)
        self.label_formatter(self.of_nm_opt_fuzzy_thrs_lbl, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL, padding=self.padX*4)
        self.update_requests[gen_short_uid()] = [
            self.of_nm_options,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.of_nm_options.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gen_short_uid()] = [
            self.of_nm_opt_fuzzy_cont,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.of_nm_opt_fuzzy_cont.config(bd='0', bg=args[0], fg=args[1], font=(args[2], args[3])),
                ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gen_short_uid()] = [
            self.of_nm_opt_auto_cont,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.of_nm_opt_auto_cont.config(bd='0', bg=args[0], fg=args[1], font=(args[2], args[3])),
                ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gen_short_uid()] = [
            self.of_nm_opt_fuzzy_thrs_cont,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.of_nm_opt_fuzzy_thrs_cont.config(bd='0', bg=args[0], fg=args[1], font=(args[2], args[3])),
                ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
            ]
        ]
        self.update_requests[gen_short_uid()] = [
            self.of_nm_opt_fuzzy_thrs_ent,
            ThemeUpdateCommands.FONT,
            [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN]
        ]
        self.update_requests[gen_short_uid()] = [
            self.of_nm_opt_canv,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: self.of_nm_opt_canv.config(bg=args[0], bd=0, highlightthickness=0),
                ThemeUpdateVars.BG
            ]
        ]
        self.update_requests[gen_short_uid()] = [self.of_nm_opt_main_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.screen_data[self.OptFrameInd]['conf::nm_options'] = True
        self.screen_data[self.OptFrameInd]['nm::autoMark'] = True
        self.screen_data[self.OptFrameInd]['nm::fuzzy'] = True

        self.update_requests['OptFr(NM):Canv{Dim}{a}'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: self.of_nm_options.config(width=args[0] - args[2], height=args[1] - args[3]),
                ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                ('<LOOKUP>', 'padX'), ('<LOOKUP>', 'padY')
            ]
        ]
        self.update_requests['OptFr(NM):Canv{Dim}{b}'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: self.of_nm_opt_canv.config(width=args[0] - args[2] * 2, height=args[1] - args[3]),
                ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                ('<LOOKUP>', 'padX'), ('<LOOKUP>', 'padY')
            ]
        ]

    def configure_options(self) -> None:
        if self.screen_data[self.OptFrameInd].get('qType') not in ('mc', 'tf', 'nm'):
            return

        if self.screen_data[self.AnsFrameInd].get('qType') in ('mc', 'tf', 'nm'):
            if self.screen_data[self.AnsFrameInd]['qType'] != self.screen_data[self.OptFrameInd]['qType']:
                self.frameMap[self.AnsFrameInd] = (self.frameMap[self.AnsFrameInd][0], self.frameMap[self.AnsFrameInd][1], False)

        if self.screen_data[self.OptFrameInd]['qType'] == 'mc':
            self.of_nm_options.pack_forget()

        elif self.screen_data[self.OptFrameInd]['qType'] == 'tf':
            self.of_nm_options.pack_forget()

        elif self.screen_data[self.OptFrameInd]['qType'] == 'nm':
            self.of_nm_options.pack()
            if self.screen_data[self.OptFrameInd].get('conf::nm_options') in (None, False):
                self.configure_nm_options()

            self.of_nm_opt_fuzzy_cont.pack_forget()
            self.of_nm_opt_fuzzy_thrs_cont.pack_forget()

            if self.screen_data[self.OptFrameInd]['nm::autoMark']:
                self.of_nm_opt_auto_enb.config(text="Mark Automatically", style='Active.TButton')
                self.of_nm_opt_fuzzy_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

                if self.screen_data[self.OptFrameInd]['nm::fuzzy']:
                    self.of_nm_opt_fuzzy_enb.config(text="Approximate Match Required", style='Active.TButton')
                    self.of_nm_opt_fuzzy_thrs_ent.config(state=tk.NORMAL)
                    self.of_nm_opt_fuzzy_thrs_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
                else:
                    self.of_nm_opt_fuzzy_enb.config(text="Exact Match Required", style='')
                    self.of_nm_opt_fuzzy_thrs_ent.config(state=tk.DISABLED)

            else:
                self.of_nm_opt_auto_enb.config(text="Mark Manually", style='')

        else:
            raise UnexpectedEdgeCase('configure_options<?!asserted, + !mc, !tf, !nm : assertion passed??>')

        self.update_ui()

    def nm_aut_cl(self) -> None:
        if self.screen_data[self.OptFrameInd].get('nm::autoMark') is None:
            self.screen_data[self.OptFrameInd]['nm::autoMark'] = True
        else:
            self.screen_data[self.OptFrameInd]['nm::autoMark'] = not self.screen_data[self.OptFrameInd]['nm::autoMark']

        self.configure_options()

    def nm_fuz_cl(self) -> None:
        if self.screen_data[self.OptFrameInd].get('nm::fuzzy') is None:
            self.screen_data[self.OptFrameInd]['nm::fuzzy'] = True
        else:
            self.screen_data[self.OptFrameInd]['nm::fuzzy'] = not self.screen_data[self.OptFrameInd]['nm::fuzzy']

        self.configure_options()

    def mc_tp_sel(self, *_: Any, **_0: Any) -> None:
        self.screen_data[self.OptFrameInd]['qType'] = 'mc'
        self.configure_tp_btns()
        self.configure_options()

    def tf_tp_sel(self, *_: Any, **_0: Any) -> None:
        self.screen_data[self.OptFrameInd]['qType'] = 'tf'
        self.configure_tp_btns()
        self.configure_options()

    def nm_tp_sel(self, *_: Any, **_0: Any) -> None:
        self.screen_data[self.OptFrameInd]['qType'] = 'nm'
        self.configure_tp_btns()
        self.configure_options()

    def rf_setup(self) -> None:
        self.disable_all_inputs()

        for widget in self.get_children(self.review_frame):
            try:
                if widget not in [self.rf_vsb, self.rf_xsb]:
                    widget.pack_forget()
            except Exception as E:
                self.log(LoggingLevel.ERROR, f'<internalError> [rf_setup] failed to pack_forget widget {widget} : {E}')

        self.rf_ttl_lbl.config(text=f"Step {cast(int, self.currentFrame) + 1}: Review", anchor=tk.W, justify=tk.LEFT)
        self.label_formatter(self.rf_ttl_lbl, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE, padding=self.padX, uid='rf_ttl_lbl')
        self.rf_ttl_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)

        self.rf_main_frame.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)

        self.rf_xsb.pack(fill=tk.X, expand=False, side=tk.BOTTOM)
        self.rf_vsb.pack(fill=tk.Y, expand=False, side=tk.RIGHT)
        self.rf_canv.pack(fill=tk.BOTH, expand=True)

        self.rf_questions.pack(fill=tk.BOTH, expand=True)
        self.rf_options.pack(fill=tk.BOTH, expand=True)
        self.rf_answers.pack(fill=tk.BOTH, expand=True)

        self.rf_q_lbl.config(state=tk.NORMAL)
        self.rf_a_lbl.config(state=tk.NORMAL)
        self.rf_o_lbl.config(state=tk.NORMAL)

        self.rf_q_lbl.clear_all()
        self.rf_a_lbl.clear_all()
        self.rf_o_lbl.clear_all()

        self.rf_q_lbl.setup_color_tags(self.theme_update_map)
        self.rf_o_lbl.setup_color_tags(self.theme_update_map)
        self.rf_a_lbl.setup_color_tags(self.theme_update_map)

        self.rf_q_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)
        self.rf_q_lbl.insert('1.0', 'Question: "')
        self.rf_q_lbl.insert('end', self.qf_inp_box.get("1.0", "end-1c").strip(), '<accent>')
        self.rf_q_lbl.insert('end', '"')

        self.rf_o_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)
        Options_qTp, OQT_err = {
            'nm': ('Written Response', False),
            'tf': ('True/False', False),
            'mc': ('Multiple Choice', False),
            None: ('QUESTION TYPE NOT SELECTED', True),
        }[self.screen_data[self.OptFrameInd].get('qType')]

        self.rf_o_lbl.insert('1.0', f"Selected Question Type: ")
        self.rf_o_lbl.insert('end', Options_qTp, '<error>' if OQT_err else '<okay>')

        if Options_qTp == 'Written Response':
            self.rf_o_lbl.insert('end', '\n\n')
            self.rf_o_lbl.insert('end', 'Question-type-specific options:', 'accent')
            self.rf_o_lbl.insert('end', '\n\u2022 Automatic Marking: ', ('<indent_first>', '<indent_body>'))
            self.rf_o_lbl.insert('end', 'Enabled' if self.screen_data[self.OptFrameInd]['nm::autoMark'] else 'Disabled (manual marking selected)', ('<okay>', '<indent_body>'))

            if self.screen_data[self.OptFrameInd]['nm::autoMark']:
                self.rf_o_lbl.insert('end', f'\n\u2022 Auto Mark: Exact v/s Approximate Match: ')
                self.rf_o_lbl.insert('end', 'Approximate match required' if self.screen_data[self.OptFrameInd]['nm::fuzzy'] else 'Exact match required', ('<okay>', '<indent_body>'))
                if self.screen_data[self.OptFrameInd]['nm::fuzzy']:
                    self.rf_o_lbl.insert('end', f'\n\u2022 Auto Mark: Approximate Match: % Similarity Required: ')
                    self.rf_o_lbl.insert('end', f"{self.of_nm_opt_fuz_ent_sv.get().strip()}% match required", ('<okay>', '<indent_body>'))
                else:
                    self.rf_o_lbl.insert('end', '\n\u2022 Auto Mark: Approximate Match: % Similarity Required: <Option Unavailable>', ('<gray_fg>', '<indent_body>'))
            else:
                self.rf_o_lbl.insert('end', '\n\u2022 Auto Mark: Exact v/s Approximate Match: <Option Unavailable>', ('<gray_fg>', '<indent_body>'))
                self.rf_o_lbl.insert('end', '\n\u2022 Auto Mark: Approximate Match: % Similarity Required: <Option Unavailable>', ('<gray_fg>', '<indent_body>'))

            # Written answer
            self.rf_a_lbl.insert('1.0', 'Correct Answer: "')
            self.rf_a_lbl.insert('end', self.screen_data[self.AnsFrameInd]['A::final'], '<accent>')
            self.rf_a_lbl.insert('end', '"')

        elif Options_qTp == 'True/False':
            self.rf_a_lbl.insert('1.0', 'Correct Answer: "')
            self.rf_a_lbl.insert('end', str(self.screen_data[self.AnsFrameInd]['A::final']), '<accent>')
            self.rf_a_lbl.insert('end', '"')

        elif Options_qTp == 'Multiple Choice':
            self.rf_a_lbl.insert('1.0', 'NOTE: The labels (A, B, C, etc.) in this list and the ones listed in the answer entry\npage MAY be different; the following labels are the ones that will be used', '<warning_bg>')
            self.rf_a_lbl.insert('end', '\n\n')

            ind = 0
            for k, v in self.af_mc_data['el'].items():
                if k[-3::] not in ('[M]', '[C]'):
                    ind += 1
                    ident = mc_label_gen(ind)
                    _, val, corr = cast(Tuple[str, str, bool], v)

                    self.rf_a_lbl.insert('end', 'Option ')
                    self.rf_a_lbl.insert('end', ident, '<accent>')
                    self.rf_a_lbl.insert('end', f') {val.strip()}', '<indent_body>')
                    if corr:
                        self.rf_a_lbl.insert('end', f'\n    \u2022 This option is correct\n\n', '<okay>')
                    else:
                        self.rf_a_lbl.insert('end', f'\n    \u2022 This option is incorrect\n\n', '<error>')
        else:
            raise UnexpectedEdgeCase('[rf_setup] :: oqtp <!mc, !nm, !tf>')

        self.rf_a_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)

        self.update_requests[gen_short_uid()] = [
            self.rf_canv,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: self.rf_canv.config(bg=args[0], bd=0, highlightthickness=0),
                ThemeUpdateVars.BG
            ]
        ]
        self.update_requests['ReviewFr(NM):Canv{Dim}{a}'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: self.rf_canv.config(width=args[0] - args[2], height=args[1] - args[3]),
                ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                ('<LOOKUP>', 'padX'), ('<LOOKUP>', 'padY')
            ]
        ]
        self.update_requests['ReviewFr(NM):Canv{Dim}{b}'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: self.rf_canv.config(width=args[0] - args[2] * 2, height=args[1] - args[3]),
                ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'root_height'),
                ('<LOOKUP>', 'padX'), ('<LOOKUP>', 'padY')
            ]
        ]

        for frame in (self.rf_questions, self.rf_options, self.rf_answers):
            self.label_formatter(frame, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_SMALL)

        self.rf_q_lbl.auto_size()
        self.rf_o_lbl.auto_size()
        self.rf_a_lbl.auto_size()

        self.rf_q_lbl.config(state=tk.DISABLED)
        self.rf_o_lbl.config(state=tk.DISABLED)
        self.rf_a_lbl.config(state=tk.DISABLED)

        self.update_requests['rf_q_lbl'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.rf_q_lbl.config(
                    bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                    relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0],
                    wrap=tk.WORD, highlightthickness=0, bd='0'
                ),
                ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN
            ]
        ]
        self.update_requests['rf_a_lbl'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.rf_a_lbl.config(
                    bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                    relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0],
                    wrap=tk.WORD, highlightthickness=0, bd='0'
                ),
                ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN
            ]
        ]
        self.update_requests['rf_o_lbl'] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args, **kwargs: self.rf_o_lbl.config(
                    bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                    relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0],
                    wrap=tk.WORD, highlightthickness=0, bd='0'
                ),
                ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN
            ]
        ]

        # self.frameMap[self.RFrameInd] = (self.frameMap[self.RFrameInd][0], self.frameMap[self.RFrameInd][1], True)
        # (need to reset the review page everytime to keep information up to date)

        self.enable_all_inputs()
        return

    def _clear_info(self) -> None:
        if not self.gi_cl:
            return

        try:
            self.late_update_requests.pop(self.message_label)
        except KeyError:
            pass

        self.message_label.config(text="")
        self.gi_cl = False
        if self._job is not None:
            self.root.after_cancel(self._job)

    def show_message(self, data: Message, timeout: Union[int, None] = 3000) -> None:
        if isinstance(timeout, int):
            if timeout < 10:  # Useless
                return

        if 0 >= len(data.MSG) or 100 < len(data.MSG):  # Skip
            return

        self.gi_cl = True

        self.message_label.config(text=data.MSG)
        self.late_update_requests[self.message_label] = [
            [
                ThemeUpdateCommands.FG,
                [
                    {
                        Levels.ERROR: ThemeUpdateVars.ERROR,
                        Levels.OKAY: ThemeUpdateVars.OKAY,
                        Levels.WARNING: ThemeUpdateVars.WARNING,
                        Levels.NORMAL: ThemeUpdateVars.ACCENT
                    }[data.LVL]
                ]
            ]
        ]
        if isinstance(timeout, int):
            self._job = self.root.after(timeout, self._clear_info)

        self.update_ui()

    def submit_question(self) -> None:
        if self.screen_data[self.AnsFrameInd]['qType'] == 'mc':
            nAf = {
                'C': self.af_mc_data['corr'],
                'N': self.get_mc_data('mc::N')
            }

            uidMap = {}
            for opt in self.af_mc_data['opt']:
                uidMap[opt] = len(uidMap)

            for k, v in self.af_mc_data['el'].items():
                if k[-3::] not in ('[M]', '[C]'):
                    nAf[uidMap[k]] = v[1].strip()

            nC = [uidMap[uid] for uid in nAf['C']]
            nAf['C'] = nC
            del nC, uidMap

            self.screen_data[self.AnsFrameInd]['A::final'] = json.dumps(nAf).strip()
            log(LoggingLevel.DEBUG, f'nAf (af::MC) -> {ANSI.BOLD}{ANSI.FG_BRIGHT_CYAN}{self.screen_data[self.AnsFrameInd]["A::final"]}{ANSI.RESET}')

        # Vars
        global S_MEM_M_VAL_MAX_SIZE, S_MEM_VAL_OFFSET
        question = self.qf_inp_box.get("1.0", "end-1c").strip()

        # Checks
        try:
            # assert 0 < len(question) <= S_MEM_M_VAL_MAX_SIZE
            assert 0 < len(question), "No question found"
            assert len(question) <= S_MEM_M_VAL_MAX_SIZE, f"Question cannot contain more than {S_MEM_M_VAL_MAX_SIZE} characters"
            if self.screen_data[self.OptFrameInd]['qType'] == 'nm':
                assert isinstance(self.screen_data[self.OptFrameInd]['nm::autoMark'], (bool, int)), 'Please select either AUTOMATIC marking or MANUAL marking (Options Page)'
                assert isinstance(self.screen_data[self.OptFrameInd]['nm::fuzzy'], (bool, int)), 'Please select whether to look for an APPROXIMATE or EXACT match when marking (Options Page)'

                if self.screen_data[self.OptFrameInd]['nm::fuzzy']:
                    try:
                        v = int(self.of_nm_opt_fuz_ent_sv.get().strip())
                    except:
                        assert False, 'Please enter an integral value for match threshold (Options Page)'
                    else:
                        assert 1 <= v <= 99, 'Please enter an integral value for match threshold between 1 and 99 (Options Page)'
            
            assert self.screen_data[self.AnsFrameInd]['A::final'] is not None, 'Please provide an answer before submitting the question'
            
        except Exception as E:
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(
                    f'Failed to submit question; please resolve the following error and try again: {E}',
                    "GO BACK",
                    "Question Entry Error"
                )
            )

        try:
            self.set_data(SMemInd.QUESTION, question)
            self.set_data(SMemInd.ANSWER, Codes.substitute(self.screen_data[self.AnsFrameInd]['A::final']))

            data1: List[Union[int, str]] = ['' for _ in Data1.entries]
            data0: List[Union[int, str]] = ['' for _ in Data0.entries]

            data1[Data1.QuestionType.index] = self.screen_data[self.OptFrameInd]['qType']

            if data1[Data1.QuestionType.index] == 'nm':  # Written
                data0[Data0.AutoMark.index] = int(self.screen_data[self.OptFrameInd]['nm::autoMark'])
                if data0[Data0.AutoMark.index] == 1:
                    data0[Data0.Fuzzy.index] = int(self.screen_data[self.OptFrameInd]['nm::fuzzy'])
                    if data0[Data0.Fuzzy.index]:
                        threshold = self.of_nm_opt_fuz_ent_sv.get().strip()
                        if len(threshold) == 1:
                            threshold = '0%s' % threshold
                        elif len(threshold) == 2:
                            pass
                        else:
                            raise UnexpectedEdgeCase(f'!threshold:: <!1, !2; aftCheck> ({threshold})')

                        data0[Data0.FuzzyThrs.index] = threshold
                    else:
                        data0[Data0.FuzzyThrs.index] = '00'

                else:
                    data0[Data0.Fuzzy.index] = 0
                    data0[Data0.FuzzyThrs.index] = '00'

            else:
                data0[Data0.AutoMark.index] = 1
                data0[Data0.Fuzzy.index] = 0
                data0[Data0.FuzzyThrs.index] = '00'

            assert len(str(data0[Data0.AutoMark.index])) == Data0.AutoMark.size
            assert len(str(data0[Data0.Fuzzy.index])) == Data0.Fuzzy.size
            assert len(str(data0[Data0.FuzzyThrs.index])) == Data0.FuzzyThrs.size

            assert len(str(data1[Data1.QuestionType.index])) == Data1.QuestionType.size

            self.set_data(SMemInd.DATA0, ''.join(str(i) for i in data0))
            self.set_data(SMemInd.DATA1, ''.join(str(i) for i in data1))

        except Exception as E:
            self.log(LoggingLevel.ERROR, traceback.format_exc())
            qa_prompts.MessagePrompts.show_error(
                qa_prompts.InfoPacket(
                    f'Failed to submit question (internal error)',
                    "GO BACK",
                    "Question Entry Error (System)"
                )
            )

        else:
            # All good
            self.show_message(Message(Levels.OKAY, 'Successfully submitted question'), None)
            self.close()

    def _pp(self) -> None:
        if not isinstance(self.currentFrame, int):
            return

        self.set_frame(self.currentFrame - 1)

    def _np(self) -> None:
        global S_MEM_M_VAL_MAX_SIZE

        if not isinstance(self.currentFrame, int):
            self.set_frame(0)
            return

        if self.currentFrame == self.RFrameInd:  # Submit
            raise UnexpectedEdgeCase('qEditUI.nextPg(fn)::<RFrame?Call>')

        if self.currentFrame == self.QFrameInd:
            if len(self.qf_inp_box.get("1.0", "end-1c").strip()) <= 0:
                self.show_message(Message(Levels.ERROR, 'You must enter a question to proceed'))
                return

        elif self.currentFrame == self.OptFrameInd:
            if self.screen_data[self.OptFrameInd].get('qType') not in ('mc', 'tf', 'nm'):
                self.show_message(Message(Levels.ERROR, 'You must select a question type to proceed'))
                return

            if self.screen_data[self.OptFrameInd].get('nm::autoMark') and self.screen_data[self.OptFrameInd]['nm::fuzzy']:
                try:
                    if not (1 <= int(self.of_nm_opt_fuz_ent_sv.get()) <= 99):
                        self.show_message(Message(Levels.ERROR, 'Please enter a threshold percentage to proceed'))
                        return
                except Exception as E:
                    log(
                        LoggingLevel.ERROR,
                        f'_np:OptF, autoMark + fuzzy :: !{E}'
                    )
                    self.show_message(Message(Levels.ERROR, 'Please enter a threshold percentage to proceed {deCL:1}'))
                    return

        elif self.currentFrame == self.AnsFrameInd:
            qType = self.screen_data[self.AnsFrameInd]['qType']
            if qType == 'tf':
                try:
                    assert self.screen_data[self.AnsFrameInd]['TF'].get('sel') in (True, False), 'strA'

                except Exception as _:
                    log(
                        LoggingLevel.ERROR,
                        f'_np:AnsF, TF :: !selection not apparent'
                    )
                    self.show_message(Message(Levels.ERROR, 'Please select either TRUE or FALSE to continue'))
                    return

            elif qType == 'nm':
                try:
                    chrCount = len(self.af_nm_ent.get("1.0", "end-1c").strip())
                    assert isinstance(chrCount, int) and (0 < chrCount <= S_MEM_M_VAL_MAX_SIZE)

                except Exception as _:
                    log(
                        LoggingLevel.ERROR,
                        f'_np:AnsF, NM :: !no answer'
                    )
                    self.show_message(Message(Levels.ERROR, 'Please enter an answer in the provided text area to continue'))
                    return

                else:
                    self.screen_data[self.AnsFrameInd]['A::final'] = self.af_nm_ent.get("1.0", "end-1c").strip()

            elif qType == 'mc':
                if self.get_mc_data('mc::N') < 2:
                    self.show_message(Message(Levels.ERROR, 'You must enter AT LEAST two options to continue'))
                    log(LoggingLevel.ERROR, f'_np:AnsF, MC :: !insuf opt')
                    return

                elif not isinstance(self.af_mc_data.get('corr'), list):
                    self.show_message(Message(Levels.ERROR, 'AT LEAST one of the options must be correct to continue'))
                    log(LoggingLevel.ERROR, f'_np:AnsF, MC :: !insuf corr opt')
                    return

                elif len(self.af_mc_data.get('corr')) < 1:
                    self.show_message(Message(Levels.ERROR, 'AT LEAST one of the options must be correct to continue'))
                    log(LoggingLevel.ERROR, f'_np:AnsF, MC :: !insuf corr opt')
                    return

            else:
                raise UnexpectedEdgeCase(f'_np (currF == AnsF) : qType <!nm, !mn, !tf>; ({qType})')

        assert isinstance(self.currentFrame, int)

        self.set_frame(self.currentFrame + 1)

    def prev_page(self) -> None:
        self._pp()
        self.configNavButtons()
        self.update_ui()

    def next_page(self) -> None:
        self._np()
        self.configNavButtons()
        self.update_ui()

    def set_frame(self, frame_index: int) -> None:
        assert frame_index in self.frameMap

        if self.currentFrame is not None:
            self.frameMap[self.currentFrame][0].pack_forget()

        frame, setup_function, setup = self.frameMap[frame_index]
        frame.pack(fill=tk.BOTH, expand=True)
        self.currentFrame = frame_index

        if self.currentFrame == 0:
            self.prev_btn.config(state=tk.DISABLED)
        else:
            self.prev_btn.config(state=tk.NORMAL)

        if self.currentFrame == len(self.frameMap) - 1:
            self.next_btn.config(state=tk.DISABLED)
        else:
            self.next_btn.config(state=tk.NORMAL)

        if not setup:
            cast(Any, setup_function)()

    def configure_main_frame(self) -> None:
        self.message_label.config(text='')
        self.message_label.pack(fill=tk.X, side=tk.BOTTOM, expand=False, padx=self.padX, pady=(0, self.padY/2))

        self.label_formatter(self.message_label, size=ThemeUpdateVars.FONT_SIZE_SMALL)

        self.title_text.config(text="Question Editor", anchor=tk.W)
        self.title_icon.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_icon.config(image=self.svgs['admt'])
        self.title_text.pack(fill=tk.X, expand=True, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.RIGHT)
        self.title_icon.pack(fill=tk.X, expand=True, padx=(self.padX, self.padX / 8), pady=self.padY, side=tk.LEFT)

        self.title_frame.pack(fill=tk.X, expand=False, pady=50)
        self.navbar.pack(fill=tk.X, expand=False, side=tk.BOTTOM)
        self.main_frame.pack(fill=tk.BOTH, expand=False)

        self.next_btn.pack(fill=tk.X, expand=True, side=tk.RIGHT, pady=(self.padY/2, 0), padx=self.padX)
        self.next_btn.configure(text="Next Step")

        self.prev_btn.pack(fill=tk.X, expand=True, side=tk.LEFT, pady=(self.padY/2, 0), padx=self.padX)
        self.prev_btn.config(text="Previous Step")

        self.configNavButtons()

    def set_data(self, index: Union[int, SMemInd], data: str) -> None:
        global S_MEM_VAL_OFFSET, S_MEM_M_VAL_MAX_SIZE, S_MEM_D_VAL_MAX_SIZE

        assert isinstance(data, str)
        assert len(data) <= (S_MEM_D_VAL_MAX_SIZE if index in (SMemInd.DATA0, SMemInd.DATA1) else S_MEM_M_VAL_MAX_SIZE)

        if isinstance(index, int):
            assert 0 <= index <= 3
            self.s_mem.set(data, index * S_MEM_VAL_OFFSET)
        elif isinstance(index, SMemInd):
            self.s_mem.set(data, index.value * S_MEM_VAL_OFFSET)
        else:
            raise UnexpectedEdgeCase("qEdit::set_data - index (!int, !SMemInd)")

    def setup_smem(self) -> None:
        global S_MEM_VAL_OFFSET

        assert self.s_mem.size >= 8192, "S_MEM size invalid; min size: 8192"

        for i in range(4):
            self.set_data(i, self.s_mem.NullStr)
            assert self.s_mem.get(S_MEM_VAL_OFFSET*i) == self.s_mem.NullStr

        self.log(LoggingLevel.SUCCESS, f"Successfully configured SharedMemory Object \"{self.s_mem.name}\"")

    def update_ui(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.load_theme()

        self.window_size = [self.root.winfo_width(), self.root.winfo_height()]
        self.screen_pos = [self.root.winfo_x(), self.root.winfo_y()]

        def tr(com: Any, *a: Any, **k: Any) -> Tuple[bool, str]:
            try:
                return True, com(*a, **k)
            except Exception as E:
                return False, f"{E.__class__.__name__}({E})"

        def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
            self.log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

        def log_norm(com: str, el: tk.Widget) -> None:
            self.log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

        for elID, (_e, _c, _a) in self.update_requests.items():
            command = cast(ThemeUpdateCommands, _c)
            element = cast(tk.Button, _e)
            args = cast(List[Any], _a)

            lCommand = [False, '', -1]
            cleaned_args = []
            for index, arg in enumerate(args):
                cleaned_arg = (arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                if isinstance(arg, tuple):
                    if len(arg) >= 2:
                        if arg[0] == '<EXECUTE>':
                            ps, res = (tr(arg[1]) if len(args) == 2 else tr(arg[1], arg[2::]))
                            if ps:
                                cleaned_arg = res
                            else:
                                self.log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

                        if arg[0] == '<LOOKUP>':
                            rs_b: int = cast(int, {
                                'padX': self.padX,
                                'padY': self.padY,
                                'root_width': self.root.winfo_width(),
                                'root_height': self.root.winfo_height(),
                                'uid': elID
                            }.get(cast(str, arg[1])))

                            if rs_b is not None:
                                cleaned_arg = rs_b
                            else:
                                self.log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

                cleaned_args.append(cleaned_arg)

                if isinstance(cleaned_args[index], qa_functions.HexColor):
                    cleaned_args[index] = cleaned_args[index].color

            if command == ThemeUpdateCommands.BG:  # Background
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(bg=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.FG:  # Foreground
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(fg=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_BG:  # Active Background
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(activebackground=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_FG:  # Active Foreground
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(activeforeground=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.ACTIVE_FG:  # BORDER COLOR
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.BORDER_SIZE:  # BORDER SIZE
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(highlightthickness=cleaned_args[0], bd=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.FONT:  # Font
                if len(cleaned_args) == 2:
                    ok, rs = tr(lambda: element.config(font=(cleaned_args[0], cleaned_args[1])))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            elif command == ThemeUpdateCommands.CUSTOM:  # Custom
                if len(cleaned_args) <= 0:
                    lCommand = [True, 'Function not provided', 1]
                elif len(cleaned_args) == 1:
                    ok, rs = tr(cleaned_args[0])
                    if not ok:
                        lCommand = [True, rs, 0]
                elif len(cleaned_args) > 1:
                    ok, rs = tr(lambda: cleaned_args[0](*cleaned_args[1::]))
                    if not ok:
                        lCommand = [True, rs, 0]

            elif command == ThemeUpdateCommands.WRAP_LENGTH:  # WL
                if len(cleaned_args) == 1:
                    ok, rs = tr(lambda: element.config(wraplength=cleaned_args[0]))
                    if not ok:
                        lCommand = [True, rs, 0]

                else:
                    lCommand = [True, 'Invalid args provided', 2]

            else:
                lCommand = [True, f'<Err:UnexpectedCommand ({command})>', -2]

            if lCommand[0] is True:
                log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
            elif DEBUG_NORM:
                log_norm(command.name, element)

            del lCommand, cleaned_args

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
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size)
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

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
            background=[('active', self.theme.accent.color), ('disabled', self.theme.accent.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'Accent2.TButton',
            background=self.theme.warning.color,
            foreground=self.theme.background.color,
            font=(self.theme.font_face, self.theme.font_main_size),
            focuscolor=self.theme.background.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Accent2.TButton',
            background=[('active', self.theme.warning.color), ('disabled', self.theme.warning.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'Accent2LG.TButton',
            background=self.theme.warning.color,
            foreground=self.theme.background.color,
            font=(self.theme.font_face, self.theme.font_large_size),
            focuscolor=self.theme.background.color,
            bordercolor=self.theme.border_color.color,
            borderwidth=self.theme.border_size,
            highlightcolor=self.theme.border_color.color,
            highlightthickness=self.theme.border_size
        )

        self.ttk_style.map(
            'Accent2LG.TButton',
            background=[('active', self.theme.warning.color), ('disabled', self.theme.warning.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
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
            background=[('active', self.theme.accent.color), ('disabled', self.theme.accent.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'TSeparator',
            background=self.theme.gray.color
        )

        elID = "<lUP::unknown>"

        for _e, commands in self.late_update_requests.items():
            assert isinstance(commands, (list, tuple, set))
            element = cast(tk.Button, _e)

            for _c, _a in commands:
                command = cast(ThemeUpdateCommands, _c)
                args = cast(List[Any], _a)

                lCommand = [False]
                cleaned_args = []
                for index, arg in enumerate(args):
                    cleaned_arg = (arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg])

                    if isinstance(arg, tuple):
                        if len(arg) >= 2:
                            if arg[0] == '<EXECUTE>':
                                ps, res = (tr(arg[1]) if len(args) == 2 else tr(arg[1], arg[2::]))
                                if ps:
                                    cleaned_arg = res
                                else:
                                    self.log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

                            if arg[0] == '<LOOKUP>':
                                rs_ba: int = cast(int, {
                                    'padX': self.padX,
                                    'padY': self.padY,
                                    'root_width': self.root.winfo_width(),
                                    'root_height': self.root.winfo_height()
                                }.get(cast(str, arg[1])))

                                if rs_ba is not None:
                                    cleaned_arg = rs_ba
                                else:
                                    self.log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

                    cleaned_args.append(cleaned_arg)

                    if isinstance(cleaned_args[index], qa_functions.HexColor):
                        cleaned_args[index] = cleaned_args[index].color

                if command == ThemeUpdateCommands.BG:  # Background
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(bg=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.FG:  # Foreground
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(fg=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_BG:  # Active Background
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(activebackground=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_FG:  # Active Foreground
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(activeforeground=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.ACTIVE_FG:  # BORDER COLOR
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(highlightcolor=self.theme.accent.color, highlightbackground=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.BORDER_SIZE:  # BORDER SIZE
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(highlightthickness=cleaned_args[0], bd=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.FONT:  # Font
                    if len(cleaned_args) == 2:
                        ok, rs = tr(lambda: element.config(font=(cleaned_args[0], cleaned_args[1])))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                elif command == ThemeUpdateCommands.CUSTOM:  # Custom
                    if len(cleaned_args) <= 0:
                        lCommand = [True, 'Function not provided', 1]
                    elif len(cleaned_args) == 1:
                        ok, rs = tr(cleaned_args[0])
                        if not ok:
                            lCommand = [True, rs, 0]
                    elif len(cleaned_args) > 1:
                        ok, rs = tr(lambda: cleaned_args[0](*cleaned_args[1::]))
                        if not ok:
                            lCommand = [True, rs, 0]

                elif command == ThemeUpdateCommands.WRAP_LENGTH:  # WL
                    if len(cleaned_args) == 1:
                        ok, rs = tr(lambda: element.config(wraplength=cleaned_args[0]))
                        if not ok:
                            lCommand = [True, rs, 0]

                    else:
                        lCommand = [True, 'Invalid args provided', 2]

                else:
                    lCommand = [True, f'<Err:UnexpectedCommand ({command})>', -2]

                if lCommand[0] is True:
                    log_error(command.name, element, cast(str, lCommand[1]), cast(int, lCommand[2]))
                elif DEBUG_NORM:
                    log_norm(command.name, element)

                del lCommand, cleaned_args

    def button_formatter(self, button: tk.Button, accent: bool = False, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, padding: Union[None, int] = None, bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, abg: ThemeUpdateVars = ThemeUpdateVars.ACCENT, afg: ThemeUpdateVars = ThemeUpdateVars.BG, uid: Union[str, None] = None) -> None:
        if padding is None:
            padding = self.padX

        if uid is None:
            uid = qa_prompts.gsuid()
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
            ] if isinstance(button, tk.Button) else [
                lambda *args: self.log(LoggingLevel.WARNING, f'{args[0]} : (from ButtonFormatter) !Btn'),
                ('<LOOKUP>', 'uid')
            ]
        ]

    def label_formatter(self, label: Union[tk.Label, tk.LabelFrame], bg: ThemeUpdateVars = ThemeUpdateVars.BG, fg: ThemeUpdateVars = ThemeUpdateVars.FG, size: ThemeUpdateVars = ThemeUpdateVars.FONT_SIZE_MAIN, font: ThemeUpdateVars = ThemeUpdateVars.DEFAULT_FONT_FACE, padding: Union[None, int, float] = None, uid: Union[str, None] = None) -> None:
        if padding is None:
            padding = self.padX

        if uid is None:
            uid = qa_prompts.gsuid()
        else:
            uid = f'{uid}<LBL>'

        while uid in self.update_requests:
            uid = f"{uid}[{random.randint(1000, 9999)}]"

        self.update_requests[uid] = [
            None,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=args[5] - 2 * args[4]),
                bg, fg, font, size, padding, ('<LOOKUP>', 'root_width')
            ] if isinstance(label, tk.Label) else (
                [
                    lambda *args: label.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                    bg, fg, font, size, padding
                ] if isinstance(label, tk.LabelFrame) else [
                    lambda *args: self.log(LoggingLevel.WARNING, f'{args[0]} : (from LabelFormatter) !Lbl, !LblF'),
                    ('<LOOKUP>', 'uid')
                ]
            )
        ]

    def load_theme(self) -> None:
        self.theme = qa_functions.qa_theme_loader.Load.auto_load_pref_theme()
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

    def load_png(self) -> None:
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.svgs['admt'] = ImageTk.PhotoImage(i)

        ls: Tuple[
            Tuple[str, str, HexColor, HexColor, Union[int, float], Tuple[str, str]],
            ...] = (
            (self.checkmark_src, 'c_mark', self.theme.background, self.theme.accent, self.theme.font_main_size, ('checkmark', 'normal')),
            (self.checkmark_src, 'c_mark_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('checkmark', 'accent')),
            (self.cog_src, 'cog', self.theme.background, self.theme.accent, self.theme.font_main_size, ('settings_cog', 'normal')),
            (self.cog_src, 'cog_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('settings_cog', 'accent')),
            (self.arrow_right_src, 'arrow_right', self.theme.background, self.theme.accent, self.theme.font_main_size, ('arrow_right', 'normal')),
            (self.arrow_right_src, 'arrow_right_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('arrow_right', 'accent')),
            (self.arrow_left_src, 'arrow_left', self.theme.background, self.theme.accent, self.theme.font_main_size, ('arrow_left', 'normal')),
            (self.arrow_left_src, 'arrow_left_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('arrow_left', 'accent')),
            (self.question_src, 'question', self.theme.background, self.theme.accent, self.theme.font_main_size, ('question', 'normal')),
            (self.question_src, 'question_accent', self.theme.accent, self.theme.background, self.theme.font_main_size, ('question', 'accent')),

            (self.checkmark_src, 'c_mark_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('checkmark_large', 'normal')),
            (self.checkmark_src, 'c_mark_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('checkmark_large', 'accent')),
            (self.cog_src, 'cog_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('settings_cog_large', 'normal')),
            (self.cog_src, 'cog_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('settings_cog_large', 'accent')),
            (self.arrow_right_src, 'arrow_right_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_right_large', 'normal')),
            (self.arrow_right_src, 'arrow_right_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_right_large', 'accent')),
            (self.arrow_left_src, 'arrow_left_large', self.theme.background, self.theme.accent, self.theme.font_title_size, ('arrow_left_large', 'normal')),
            (self.arrow_left_src, 'arrow_left_accent_large', self.theme.accent, self.theme.background, self.theme.font_title_size, ('arrow_left_large', 'accent')),
            (self.question_src, 'question_accent', self.theme.background, self.theme.accent, self.theme.font_title_size, ('question_large', 'normal')),
            (self.question_src, 'question_accent_accent', self.theme.accent, self.theme.background, self.theme.font_title_size, ('question_large', 'accent')),
        )

        for src, name, background, foreground, _s, (a, b) in ls:
            size = cast(int, _s)
            try:
                File = qa_functions.File(src)
                tmp = f"{self.svg_tmp}\\{File.file_name}"
                raw_data = qa_functions.OpenFile.read_file(File, qa_functions.OpenFunctionArgs(str, False), b'', qa_functions.ConverterFunctionArgs())
                new_data = raw_data.replace(qa_prompts._SVG_COLOR_REPL_ROOT, foreground.color)
                File = qa_functions.File(tmp)
                qa_functions.SaveFile.secure(File, new_data, qa_functions.SaveFunctionArgs(False, False, b'', True, True, save_data_type=str))
                self.svgs[a][b] = get_svg(tmp, background.color, (size, size), name)

            except Exception as E:
                self.log(LoggingLevel.ERROR, f'admt::load_png - Failed to load requested svg ({src}): {E}')

    def disable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        for btn in (self.next_btn, self.prev_btn):
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        for btn in (self.next_btn, self.prev_btn):
            if btn not in exclude:
                btn.config(state=tk.NORMAL)

        self.configNavButtons()
        self.update_ui()


def get_svg(svg_file: str, bg: Union[str, int], size: Union[None, Tuple[int, int]] = None, name: Union[None, str] = None) -> ImageTk.PhotoImage:
    background = bg
    if isinstance(bg, str):
        background = int(bg.replace("#", '0x'), 0)

    assert isinstance(background, int)

    drawing = svg2rlg(svg_file)
    bytes_png = BytesIO()
    renderPM.drawToFile(drawing, bytes_png, fmt="PNG", bg=background)
    img = Image.open(bytes_png)
    if size is not None:
        img = img.resize(size, PIL.Image.ANTIALIAS)

    p_img = ImageTk.PhotoImage(img, name=name)

    return p_img


def log(level: LoggingLevel, data: str) -> None:
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, LOGGING_SCRIPT_NAME, DEBUG_NORM, DEBUG_DEV_FLAG
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

    data = f"{AppLogColors.ADMIN_TOOLS}{AppLogColors.EXTRA}[QA::FORMS::Q_EDIT]{ANSI.RESET} {data}"

    if level == LoggingLevel.DEBUG and not DEBUG_NORM:
        return

    elif level == LoggingLevel.DEVELOPER and (not (qa_functions.App.DEV_MODE and DEBUG_DEV_FLAG) or not DEBUG_NORM):
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


def mc_label_gen(index: int) -> str:
    chars = 'abcdefghijklmnopqrstuvwxyz'.upper()
    c1 = chars[(index % len(chars)) - 1]
    c2 = math.floor((index - (index % len(chars))) / len(chars)) - (0 if c1 != 'z' else 1)
    return f"{c1}{c2}" if c2 > 0 else c1


if __name__ == "__main__":
    log(qa_functions.LoggingLevel.ERROR, f"Module 'qa_form_q_edit.py' must be used by a QuizzingApp dist script.")
    sys.exit(-1)
