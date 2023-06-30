import sys, qa_functions, os, PIL, math, subprocess, tkinter as tk, random, qa_files, json, hashlib, traceback, copy, re, datetime
from time import sleep
from . import qa_prompts
from .qa_prompts import gsuid, configure_scrollbar_style, configure_entry_style
from .qa_apps_admin_tools import CustomText
from qa_functions.qa_enum import ThemeUpdateCommands, ThemeUpdateVars, LoggingLevel
from qa_functions.qa_std import ANSI, AppLogColors
from qa_functions.qa_custom import HexColor
from qa_functions.qa_colors import Functions as ColorFunctions
from threading import Thread
from tkinter import ttk, filedialog
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from ctypes import windll
from typing import *
from tkinter import filedialog as tkfld
from . import qa_adv_forms as qa_forms
from .qa_adv_forms.qa_form_q_edit import Data0, Data1, DataEntry, DataType, mc_label_gen
from thefuzz import fuzz


script_name = "APP_QF"
APP_TITLE = "Quizzing Application | Quizzing Form"
LOGGER_AVAIL = False
LOGGER_FUNC = qa_functions.NormalLogger
LOGGING_FILE_NAME = ''
LOGGING_SCRIPT_NAME = script_name
DEBUG_NORM = False
DEBUG_DEV_FLAG = False


class _UI(Thread):
    def __init__(self, root: Union[tk.Toplevel, tk.Tk], ic: Any, ds: Any, **kwargs: Optional[Any]) -> None:
        super().__init__()
        Thread.__init__(self)

        self.root, self.ic, self.ds, self.kwargs = root, ic, ds, kwargs
        self.root.withdraw()

        self.screen_dim = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        wd_w = 1000 if 1000 <= self.screen_dim[0] else self.screen_dim[0]
        wd_h = 600 if 600 <= self.screen_dim[1] else self.screen_dim[1]
        self.window_size = [wd_w, wd_h]
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
        ]
        self.original_pos = f'{self.window_size[0]}x{self.window_size[1]}+{self.screen_pos[0]}+{self.screen_pos[1]}'

        self.theme: qa_functions.qa_custom.Theme = qa_functions.LoadTheme.auto_load_pref_theme()
        self.theme_update_map: Dict[ThemeUpdateVars, Union[int, float, HexColor, str]] = {}  # type: ignore
        self.active_jobs = {}  # type: ignore

        self.padX = 20
        self.padY = 10

        self.gi_cl = True
        self._job: Union[None, str] = None

        self.inputs: List[Union[tk.Button, ttk.Button, ttk.Entry, tk.Entry, tk.Text]] = []

        self.load_theme()
        self.update_requests: Dict[str, List[Any]] = {}  # type: ignore
        self.late_update_requests: Dict[tk.Widget, List[Any]] = {}  # type: ignore
        self.data: Dict[Any, Any] = {'GLOBAL': {}}  # type: ignore

        self.img_path = qa_functions.Files.QF_png
        self.img_size = (75, 75)
        self.svgs: Dict[str, Any] = {
            'arrow_left': {'accent': '', 'normal': ''},
            'arrow_right': {'accent': '', 'normal': ''},
            'settings_cog': {'accent': '', 'normal': ''},
            'question': {'accent': '', 'normal': ''},
            'checkmark': {'accent': '', 'normal': ''},
            'export': {'accent': '', 'normal': ''},
            'arrow_left_large': {'accent': '', 'normal': ''},
            'arrow_right_large': {'accent': '', 'normal': ''},
            'settings_cog_large': {'accent': '', 'normal': ''},
            'question_large': {'accent': '', 'normal': ''},
            'checkmark_large': {'accent': '', 'normal': ''},
            'export_large': {'accent': '', 'normal': ''},

            'qf': ''
        }
        self.checkmark_src = "./.src/.icons/.progress/checkmark.svg"
        self.cog_src = './.src/.icons/.misc/settings.svg'
        self.arrow_left_src = './.src/.icons/.misc/left_arrow.svg'
        self.question_src = './.src/.icons/.misc/question.svg'
        self.arrow_right_src = './.src/.icons/.misc/right_arrow.svg'
        self.export_src = './.src/.icons/.misc/export.svg'
        self.svg_tmp = f"{qa_functions.App.appdata_dir}\\.tmp\\.icon_setup".replace('/', '\\')
        self.load_png()

        self.ttk_theme = cast(str, self.kwargs['ttk_theme'])
        self.ttk_style = ttk.Style()
        self.ttk_style.theme_use(self.ttk_theme)
        self.ttk_style = configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'QF')
        self.ttk_style = qa_functions.TTKTheme.configure_button_style(self.ttk_style, self.theme, self.theme.accent.color)
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size, 'My')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

        self.title_box = tk.Frame(self.root)
        self.title_img = tk.Label(self.title_box)
        self.title_txt = tk.Label(self.title_box)
        self.title_info = tk.Label(self.title_box)

        self.screen_data: Dict[int, Dict[Any, Any]] = {}
        [self.LOGIN_PAGE, self.CONFIGURATION_PAGE, self.SUMMARY_PAGE, self._page_code_aft] = range(4)
        for i in range(3): self.screen_data[i] = {}
        self.current_page = self.LOGIN_PAGE

        self.main_frame = tk.Frame(self.root)
        self.login_frame = tk.Frame(self.main_frame)
        self.config_frame = tk.Frame(self.main_frame)
        self.summary_frame = tk.Frame(self.main_frame)

        self.login_frame_gsuid = gsuid('QuizzingForm.PageMap<GSUID>')
        self.config_frame_gsuid = gsuid('QuizzingForm.PageMap<GSUID>')
        self.summary_frame_gsuid = gsuid('QuizzingForm.PageMap<GSUID>')
        self.quiz_frame_gsuid = gsuid('QuizzingForm.PageMap.QUIZ<GSUID>')
        self.complete_frame_gsuid = gsuid('QuizingForm.PageMap.DONE<GSUID>')

        self.nav_btn_frame = tk.Frame(self.root)
        self.next_frame = ttk.Button(self.nav_btn_frame, text='Next Step \u2b9e', style='MyQuizzingApp.QFormRoot.TButton', command=self.proceed)
        self.prev_frame = ttk.Button(self.nav_btn_frame, text='\u2b9c Previous Step', style='MyQuizzingApp.QFormRoot.TButton', command=self.go_back)

        self.error_label = tk.Label(self.main_frame)

        # Login
        self.first_name, self.last_name, self.ID, self.psw = \
            tk.StringVar(self.root), tk.StringVar(self.root), tk.StringVar(self.root), tk.StringVar(self.root)

        self.left_cont = tk.Frame(self.login_frame)
        self.right_cont = tk.Frame(self.login_frame)

        self.login_page_title = tk.Label(self.left_cont)

        self.ID_cont = tk.LabelFrame(self.right_cont, text='About You')
        self.ID_name_frame = tk.Frame(self.ID_cont)
        self.ID_first_name_frame = tk.Frame(self.ID_name_frame)
        self.ID_last_name_frame = tk.Frame(self.ID_name_frame)
        self.first_name_lbl = tk.Label(self.ID_first_name_frame, text='First Name')
        self.last_name_lbl = tk.Label(self.ID_last_name_frame, text='Last Name')
        self.first_name_field = ttk.Entry(self.ID_first_name_frame, textvariable=self.first_name, style='My.TEntry')
        self.last_name_field = ttk.Entry(self.ID_last_name_frame, textvariable=self.last_name, style='TEntry')
        self.ID_lbl = tk.Label(self.ID_cont, text='Unique ID Number')
        self.ID_field = ttk.Entry(self.ID_cont, textvariable=self.ID)

        self.database_frame = tk.LabelFrame(self.right_cont, text='Database Selection')
        self.select_database_btn = ttk.Button(self.database_frame, style='TButton')

        # Configuration page
        self.config_acc_status = tk.Label(self.config_frame)
        self.config_qd_frame = tk.LabelFrame(self.config_frame, text="Quiz Distribution Configuration")
        self.config_qd_lbl = tk.Label(self.config_qd_frame)
        self.config_qd_poa_P = ttk.Button(self.config_qd_frame)

        self.config_qd_ssd = tk.StringVar(self.root)
        self.config_qd_ssd_lbl = tk.Label(self.config_qd_frame)
        self.config_qd_ssd_field = ttk.Entry(self.config_qd_frame, textvariable=self.config_qd_ssd, style='MyQuizzingApp.TEntry')

        self.config_rqo_lbl = tk.Label(self.config_qd_frame)
        self.config_rqo_enb = ttk.Button(self.config_qd_frame)

        self.config_pc_frame = tk.LabelFrame(self.config_frame, text="Penalty Configuration")
        self.config_pc_lbl = tk.Label(self.config_pc_frame)
        self.config_pc_enb = ttk.Button(self.config_pc_frame)

        self.config_pc_a2d = tk.StringVar(self.root)
        self.config_pc_a2d_lbl = tk.Label(self.config_pc_frame)
        self.config_pc_a2d_field = ttk.Entry(self.config_pc_frame, textvariable=self.config_pc_a2d, style='MyQuizzingApp.TEntry')

        self.summ_ttl = tk.Label(self.summary_frame)
        self.summ_txt = CustomText(self.summary_frame)

        self.quiz_frame = tk.Frame(self.main_frame)
        self.complete_frame = tk.Frame(self.main_frame)
        
        self.complete_stage_1 = tk.Frame(self.complete_frame)  # Checking answers
        self.complete_stage_2 = tk.Frame(self.complete_frame)  # Done (allow to exit)
        
        self.quiz_activity_lbl = tk.Label(self.quiz_frame)
        self.quiz_activity_box = CustomText(self.quiz_frame)
        
        self.quiz_host_frame = tk.Frame(self.quiz_frame)
        self.quiz_host_canvas = tk.Canvas(self.quiz_host_frame)
        self.quiz_host_vsb = ttk.Scrollbar(self.quiz_host_frame, style='MyQF.TScrollbar')
        self.quiz_host_xsb = ttk.Scrollbar(self.quiz_host_frame, style='MyHorizQF.TScrollbar', orient=tk.HORIZONTAL)
        self.quiz_H_frame = tk.Frame(self.quiz_host_canvas)
        
        self.quiz_curnt_time_lbl = tk.Label(self.quiz_host_frame)
        self.quiz_time_taken_lbl = tk.Label(self.quiz_host_frame)
        
        self.quiz_submit_btn = ttk.Button(self.quiz_host_frame)
        self.quiz_err_lbl = tk.Label(self.quiz_host_frame) 
        self.quiz_WAIT_lbl = tk.Label(self.quiz_frame)
        
        self.start()
        self.root.deiconify()
        self.root.focus_get()
        self.root.mainloop()

    def close(self) -> None:
        # if self.data.get('GLOBAL', {}).get('Attr_', {}).get('Animating.PauseClose.Set', False):
            # log(LoggingLevel.WARNING, 'QuizzingForm.CLOSE: Flag Animating.PauseClose.Set is active; re-executing close fn after 0.1s')
            # Timer(0.1, self.close).start()
            # return

        if len(self.error_label.cget('text')):
            log(LoggingLevel.WARNING, 'QuizzingForm.WARNINGS.Task_f1')
            self.error_label.config(text='')  # clearing the text will automatically clear the animation and cancel any invoked animation calls.

        for _, task in self.active_jobs.get('Jobs.SetErrorText.Timers', {}).items():
            self.root.after_cancel(task)

        sys.stdout.write("qf - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.after(0, self.root.quit)

    def _abort_quiz(self, _: bool = True) -> None:
        s_f, s_d = qa_functions.data_at_dict_path('<QUIZ>/is_started', self.data)
        
        if not (s_f and s_d):
            return 
    
        self.root.overrideredirect(False)
        self.root.wm_attributes('-topmost', 0)
        self.root.geometry(self.original_pos)

        log(LoggingLevel.WARNING, 'QuizAborted')

        self.close()
        
        return
    
    def _get_attempt_number(self) -> int:
        s_f, s_d = qa_functions.data_at_dict_path('<QUIZ>/is_started', self.data)
        
        if not (s_f and s_d):
            return -1
        
        i, f = 0, 0
        
        while i < 10000:
            s = self._gen_user_id() + f"({i})"
            m = 'QZ.ActAb'
            
            if qa_functions.VerifyNVFlag(m, s):
                f += 1
            
            i += 1
        
        log(LoggingLevel.INFO, f'{ANSI.BG_MAGENTA}{ANSI.FG_WHITE}{ANSI.BOLD}User {s[:-1* (len(str(i)) + 2):]} has had {f} attempts (excluding current attempt).{ANSI.RESET}')
        
        return f
    
    def _gen_user_id(self, ex: str = "") -> str:
        return \
            hex(int(hashlib.md5(f'{self.last_name.get()}.{self.first_name.get()}.{self.ID.get()}{self.data["DATABASE"]["data_recv"]["name"]}{ex}'.encode()).hexdigest(), 16))[2:]
    
    def _start_quiz(self) -> None:
        if self.current_page != self.SUMMARY_PAGE:
            raise Exception (f'QA.PageSequencing Error <{self.current_page}> -> <_aft>. Error ECC Code: _start_quiz+0x02')
        
        self.root.geometry("{}x{}+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', 1)
        self.root.protocol("WM_DELETE_WINDOW", self._abort_quiz)
        self.data['<QUIZ>'] = {'is_started': True}
        
        self.current_page = self._page_code_aft
        self.summary_frame.pack_forget()
        self.nav_btn_frame.pack_forget()
        
        self.quiz_frame.pack(fill=tk.BOTH, expand=True)
        self.update_requests[self.quiz_frame_gsuid + '.bg'] = [self.quiz_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        
        self.late_update_requests[self.quiz_activity_box] = [
            [
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args: cast(CustomText, args[0]).auto_size(),
                    self.quiz_activity_box
                ]
            ],
            [
                ThemeUpdateCommands.CUSTOM,
                [
                    lambda *args, **kwargs: cast(CustomText, args[5]).config(
                        bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                        relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0]
                    ),
                    ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                    ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN,
                    self.quiz_activity_box
                ]
            ]
        ]
        
        self.quiz_activity_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
        self.quiz_activity_box.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=(0, self.padY))
        
        self.label_formatter(self.quiz_activity_lbl, fg=ThemeUpdateVars.GRAY)
        self.quiz_activity_lbl.config(text="Setup Activity Monitor", justify=tk.LEFT, anchor=tk.W)
        
        self.quiz_activity_box.config(state=tk.NORMAL)
        self.quiz_activity_box.delete('1.0', 'end')
        self.quiz_activity_box.config(state=tk.DISABLED)
        
        self.update_ui()
        
        self._prepare_quiz()
        self._prompt_quiz()
        
        self.root.bind('<FocusOut>', self._on_focus_lost)
        self.root.bind('<FocusIn>', self._on_focus_gained)
    
    def _on_focus_lost(self, event: tk.Event) -> None:  # type: ignore
        if event.widget == self.root and not self.data.get('__attr_quiz_complete', False):
            self.data['__quiz']['__log'] = {
                **self.data['__quiz'].get('__log', {}),
                datetime.datetime.now().strftime("%H:%M:%S"): 'Quizzing form lost focus, likely due to user input.'
            }
    
    def _on_focus_gained(self, event: Any) -> None:
        if event.widget == self.root and not self.data.get('__attr_quiz_complete', False):
            self.data['__quiz']['__log'] = {
                **self.data['__quiz'].get('__log', {}),
                datetime.datetime.now().strftime("%H:%M:%S"): 'Quizzing form regained focus.'
            }    
        
    def _prompt_quiz(self) -> None:
        assert qa_functions.data_at_dict_path('__quiz/__prep', self.data)[1], 'QA.QzSeq.Prompt.!Prep <0xF0>'

        i = 0   
        while i < 10000:
            s = self._gen_user_id() + f"({i})"
            m = 'QZ.ActAb'
            
            if not qa_functions.VerifyNVFlag(m, s):
                qa_functions.CreateNVFlag(m, s)
                break
            
            i += 1
            
        if self._get_attempt_number() != self.data['__quiz']['__attempt']:
            assert i < 9999, f'Too many attempts for {self._gen_user_id()}. Please contact your quiz administrator for further instructions.'
                
            qa_functions.DeleteNVFlag(m, s)
            assert False, 'Could not process attempt number. Please try again.'
            
        log(LoggingLevel.SUCCESS, f'QA.QzSeq.Prompt: Successfully configured attempt number ({self._get_attempt_number()}); id: {self._gen_user_id()}')
        
        # Setup quiz frame        
        self.quiz_submit_btn.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
        self.quiz_err_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0), side=tk.BOTTOM)
        
        self.quiz_curnt_time_lbl.pack(fill=tk.X, expand=False, padx=self.padX)
        self.quiz_time_taken_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY//8, self.padY))
        
        self.quiz_curnt_time_lbl.config(justify=tk.LEFT, anchor=tk.W)
        self.quiz_time_taken_lbl.config(justify=tk.LEFT, anchor=tk.W)
        
        self.quiz_submit_btn.config(text="Submit Answers", command=self._submit_quiz, style='My.Accent2LG.TButton')
        
        # Add update requests        
        self.update_requests[gsuid()] = [self.quiz_host_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.label_formatter(self.quiz_curnt_time_lbl, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL)
        self.label_formatter(self.quiz_time_taken_lbl, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL)
        self.label_formatter(self.quiz_err_lbl, fg=ThemeUpdateVars.ERROR)
        
        self.data['qz_tick'] = True
        
        # Add the damn quiz form
        self._setup_form()
        
        # Final things
        self.quiz_activity_box.pack_forget()
        self.quiz_activity_lbl.pack_forget()
        self.quiz_host_frame.pack(fill=tk.BOTH, expand=True)
        self.update_ui()
        
        self.data['qz_tm_started'] = datetime.datetime.now()
        self._qz_tick()
    
    def onFrameConfig(self, *_: Optional[Any]) -> None:
        self.quiz_host_canvas.configure(scrollregion=self.quiz_host_canvas.bbox("all"))
    
    def _on_mousewheel(self, event: Any) -> None:
        """
        Straight out of stackoverflow
        Article: https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        Change: added "int" around the first arg
        """
        
        self.quiz_host_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _setup_form(self) -> None:        
        assert qa_functions.data_at_dict_path('__quiz/__questionBase', self.data)[1]
        
        if '_setup_qz_host' not in self.data:
            self.quiz_host_xsb.pack(fill=tk.X, expand=False, pady=self.padY, padx=self.padX, side=tk.BOTTOM)
            self.quiz_host_vsb.pack(fill=tk.Y, expand=False, pady=self.padY, padx=self.padX, side=tk.RIGHT)
            self.quiz_host_canvas.pack(fill=tk.BOTH, expand=True, padx=self.padX, side=tk.LEFT)
            
            self.quiz_host_vsb.configure(command=self.quiz_host_canvas.yview)
            self.quiz_host_xsb.configure(command=self.quiz_host_canvas.xview)
            
            self.quiz_host_canvas.configure(yscrollcommand=self.quiz_host_vsb.set, xscrollcommand=self.quiz_host_xsb.set)

            self.quiz_host_canvas.create_window(
                0, 0,
                window=self.quiz_H_frame,
                anchor="nw",
                tags="self.quiz_H_frame"
            )

            self.quiz_H_frame.update()
            self.quiz_H_frame.bind("<Configure>", self.onFrameConfig)
            self.quiz_host_canvas.bind("<MouseWheel>", self._on_mousewheel)
            
            self.late_update_requests[self.quiz_host_canvas] = [
                *self.late_update_requests.get(self.quiz_host_canvas, []),
                [
                    ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *x: self.quiz_host_canvas.configure(width=x[0], bg=x[1], borderwidth=0, highlightthickness=0, highlightbackground=x[1]),
                        ('<EXECUTE>', lambda *_: self.quiz_host_frame.winfo_width()), ThemeUpdateVars.BG
                    ]
                ],
                [
                    ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *x: self.quiz_H_frame.configure(width=x[0], bg=x[1]),
                        ('<EXECUTE>', lambda *_: self.root.winfo_width()), ThemeUpdateVars.BG
                    ]
                ]
            ]
        
            self.data['_setup_qz_host'] = 1
        
        for i, question in self.data['__quiz']['__questionBase'].items():
            # 0: mode   
            #
            # 1: question
            #
            # 2: answer         
            #
            # d: data           xxxxx
            #                   AutoMark (0; 1), AutoMark:FuzzyMatch(1; 1), AutoMark:FuzzyMatch:Threshold(2; 2), exD1(4, 1)
            #                   exD1: if MC     -> MC<exD1>     -> mc0 or mc1 
            #                                        <dictates whether option order is randomized or not>
            
            # The above is valid as of BUILD alpha_2306178.1411410104 and should only be used as a referrence.
            # To avoid errors, use qa_form_q_edit.DATA0, ...DATA1
            
            # Extract question info
            Q = question['1']
            D0 = question['d']
            D1 = question['0']
            exD1 = D0[(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))-len(D0)]  # type: ignore
            D0 = D0[:(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]  # type: ignore
            A = question['2']
            
            tp: str = D1[Data1.QuestionType.index:Data1.QuestionType.index + Data1.QuestionType.size]
            
            if (tp not in ('mc', 'nm', 'tf')) or (len(exD1) != 1):
                self.data['__quiz']['__errors'] = {
                    **self.data['__quiz'].get('__errors', {}),
                    datetime.datetime.now().strftime("%H:%M:%S"): 'Errors.QuestionPrompt.QuestionTypeError (likely due to corrupted data)'
                }
                continue
            
            if tp == 'mc':
                tp += exD1
                
            self._qz_aq(Q, tp, int(i), A)            
            
        return
    
    def _qz_aq(self, question: str, question_type: str, index: int, A: Any) -> None:
        
        Q = question
        q_uid = gsuid(f'qz<{index}>.question')
        tp = question_type
        
        self.data['__quiz']['__qMap'] = {
            **self.data['__quiz'].get('__qMap', {}),
            str(index): [q_uid, tp, Q]
        }
        
        q_cont = tk.LabelFrame(self.quiz_H_frame, text=f'Question {index + 1}')
        q_lbl = tk.Label(q_cont, text=Q.strip(), justify=tk.LEFT, anchor=tk.W)
        q_elem = []
        
        q_lbl.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY, side=tk.TOP)
        
        def _mc(L: str, O: str) -> None:
            q_B = ttk.Button(q_cont, text=f"[ {L} ] {O.strip()}", style='My.TButton', command=lambda: self._qz_q_mc_clk(q_uid, L))
            q_elem.append(q_B)
            
            q_B.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY // 4)
            
            self.data['__quiz']['__Ans'] = {
                **self.data['__quiz'].get("__Ans", {}),
                q_uid: {
                    **self.data['__quiz'].get('__Ans', {}).get(q_uid, {
                        '__sel': None
                    }),
                    L: [O, q_B]
                }
            }
            
        if tp == 'nm':
            # Written Response
            q_E = CustomText(q_cont)
            self.data['__quiz']['__Ans'] = {
                **self.data['__quiz'].get('__Ans', {}),
                q_uid: [index, tp, q_E]
            }

            q_elem.append(q_E)  # type: ignore
            
            q_E.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)
            
            self.late_update_requests[q_E] = [
                [
                    ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *args, **kwargs: cast(CustomText, args[5]).config(
                            bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                            relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0]
                        ),
                        ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                        ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN,
                        q_E
                    ]
                ]
            ]
            
        elif tp == 'tf':
            # True/False
            q_T = ttk.Button(q_cont, text="TRUE", command=lambda: self._qz_q_tf_clk(q_uid, True), style='My.TButton') 
            q_F = ttk.Button(q_cont, text="FALSE", command=lambda: self._qz_q_tf_clk(q_uid, False), style='My.TButton')
             
            self.data['__quiz']['__Ans'] = {
                **self.data['__quiz'].get('__Ans', {}),
                q_uid: [index, tp, q_T, q_F, None]
            }
            
            q_elem.extend([q_T, q_F])

            q_T.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
            q_F.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY, side=tk.LEFT)
            
        elif tp == 'mc0':  # option order not randomized
            assert isinstance(A, dict)
            C = A['C'].split('/')
            N = A['N']
            
            Ap = copy.deepcopy(A)
            Ap.pop('C')
            Ap.pop('N')
            
            assert len(Ap) == N
            
            for i, option in enumerate(Ap.values()):
                _mc(mc_label_gen(i + 1), option)
            
        elif tp == 'mc1':  # option order randomized
            assert isinstance(A, dict)
            C = A['C'].split('/')
            N = A['N']
            
            Ap = copy.deepcopy(A)
            Ap.pop('C')
            Ap.pop('N')
            
            assert len(Ap) == N
            
            # Shuffling
            Al = [*set(Ap.keys())]
            As = {Ap[k] for k in Al}
            
            for i, option in enumerate(As):
                _mc(mc_label_gen(i + 1), option)
        
        else:
            raise qa_functions.UnexpectedEdgeCase ('_qz_aq k1')
        
        self.data['__quiz'] = {
            **self.data.get('__quiz', {}),
            '_q_cont_mp': {
                **self.data['__quiz'].get('_q_cont_mp', {}),
                q_uid: [q_cont, q_lbl, *q_elem]
            }
        }
        
        self.update_requests[gsuid('qz-form-lbl')] = [
            q_lbl,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: q_lbl.config(wraplength=args[0]-args[1]*8),
                ('<EXECUTE>', lambda *_: self.root.winfo_width()), ('<LOOKUP>', 'padX')
            ]
        ]
        
        self.update_requests[gsuid('qz-form-cont')] = [
            q_lbl,
            ThemeUpdateCommands.CUSTOM,
            [
                lambda *args: q_cont.config(width=args[0] - args[1]*4, highlightbackground=args[2], highlightcolor=args[2]),
                ('<EXECUTE>', lambda *_: self.root.winfo_width()), ('<LOOKUP>', 'padX'), ThemeUpdateVars.GRAY
            ]
        ]
        
        self.label_formatter(q_cont, fg=ThemeUpdateVars.GRAY, size=ThemeUpdateVars.FONT_SIZE_SMALL)
        self.label_formatter(q_lbl)
        
        q_cont.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY // 2)
    
    def _qz_q_tf_clk(self, question_uid: str, selection: bool) -> None:        
        self.data['__quiz']['__Ans'][question_uid][-1] = selection
        log(LoggingLevel.DEBUG, f'{question_uid} T/F -> {selection}')
        
        if selection:
            cast(ttk.Button, self.data['__quiz']['__Ans'][question_uid][2]).configure(style='My.Active.TButton')
            cast(ttk.Button, self.data['__quiz']['__Ans'][question_uid][3]).configure(style='My.TButton')
            
        else:
            cast(ttk.Button, self.data['__quiz']['__Ans'][question_uid][3]).configure(style='My.Active.TButton')
            cast(ttk.Button, self.data['__quiz']['__Ans'][question_uid][2]).configure(style='My.TButton')
    
    def _qz_q_mc_clk(self, question_uid: str, label: str) -> None: 
        log(LoggingLevel.DEBUG, f'{question_uid} M/C -> {label}')
               
        self.data['__quiz']['__Ans'][question_uid]['__sel'] = label
        
        for L, V in self.data['__quiz']['__Ans'][question_uid].items():
            if L == '__sel': continue
            
            (_, B) = V
            
            if L == label:
                B.configure(style="My.Active.TButton")
            else:
                B.configure(style='My.TButton')
                
        return
    
    def _submit_quiz(self) -> None:
        self.quiz_submit_btn.config(state=tk.DISABLED)
        self.quiz_WAIT_lbl.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
        self.quiz_WAIT_lbl.config(text="Please wait as your SCORE file is being generated", wraplength=self.root.winfo_width() - self.padX * 4)
        self.label_formatter(self.quiz_WAIT_lbl, fg=ThemeUpdateVars.ACCENT, size=ThemeUpdateVars.FONT_SIZE_LARGE, uid='SETUID_quiz_WAIT_lbl')
        
        self.data['qz_tick'] = False
        self.data['__quiz']['__score'] = {
            'correct': 0,
            'incorrect': 0,
            'questions': self.data['__quiz']['__questionBase'],
            'configuration': self.data['CONFIG_INF:<DB>']['CONFIGURATION'],
            'd': []
        }
        
        assert qa_functions.data_at_dict_path('__quiz/__questionBase', self.data)[1]
        self.quiz_host_frame.pack_forget()
        self.update_ui()  # Also resets all colors to their default (essentially clears errors)
        
        def _show_error_q(quid: str) -> None:
            q_cont, q_lbl = self.data['__quiz']['_q_cont_mp'][quid][:2]
            q_cont.config(
                highlightbackground=self.theme_update_map[ThemeUpdateVars.ERROR].color,  # type: ignore
                highlightcolor=self.theme_update_map[ThemeUpdateVars.ERROR].color,  # type: ignore
                fg=self.theme_update_map[ThemeUpdateVars.ERROR].color  # type: ignore
            )
            q_lbl.config(fg=self.theme_update_map[ThemeUpdateVars.ERROR].color)  # type: ignore
            
            q_cont.update()
            q_lbl.update()
        
        def _ret(err_txt: str = "Failed to submit answers; 'Time Elapsed' timer continues...") -> None:
            
            self.data['__quiz']['__log'] = {
                **self.data['__quiz'].get('__log', {}),
                datetime.datetime.now().strftime('%H:%M:%S'): 'User attempted to submit quiz but the submission was rejected by the system.'
            }
            
            self.quiz_host_canvas.yview_moveto(0)
            self.quiz_host_canvas.xview_moveto(0)
            
            self.data['qz_tick'] = True
            self.quiz_WAIT_lbl.pack_forget()
            self.quiz_host_frame.pack(fill=tk.BOTH, expand=True)
            self.quiz_err_lbl.config(wraplength=self.root.winfo_width() - 4 * self.padX)
            self.quiz_submit_btn.config(state=tk.NORMAL)
            self._qz_set_error_text(err_txt.strip(), 10)
            self._qz_tick()
        
        tp_map = {
            DataType.boolean:   lambda string: bool(int(string)),
            DataType.integer:   lambda string: int(string),
            DataType.string:    lambda string: string
        }
        
        for i, question in self.data['__quiz']['__questionBase'].items():
            
            D1 = question['0']
            Q = question['1']
            A = question['2']
            D0 = question['d']
            
            exD1 = D0[(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))-len(D0)]  # type: ignore
            D0 = D0[:(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]  # type: ignore
            
            tp: str = D1[Data1.QuestionType.index:Data1.QuestionType.index + Data1.QuestionType.size]
            
            if (tp not in ('mc', 'nm', 'tf')) or (len(exD1) != 1):
                continue
            
            if tp == 'mc':
                tp += exD1
                
            AutoMark = tp_map[Data0.AutoMark.type](D0[Data0.AutoMark.index : Data0.AutoMark.index + Data0.AutoMark.size])
            AutoMark_UseApproxMatch = AutoMark & tp_map[Data0.Fuzzy.type](D0[Data0.Fuzzy.index : Data0.Fuzzy.index + Data0.Fuzzy.size])
            AutoMark_ApproxMatch_PM = tp_map[Data0.FuzzyThrs.type](D0[Data0.FuzzyThrs.index:Data0.FuzzyThrs.index + Data0.FuzzyThrs.size])
            
            (QUID, TPp, Qp) = self.data['__quiz']['__qMap'][i]
            
            if (TPp != tp) or (Qp != Q):
                _ret('An error occured when checking your answers. Error Code: qz.Seq.Sbm.Chk: TTp vs tp, Qp vs Q <0xA0>.')
                
                qa_prompts.MessagePrompts.show_error(
                    qa_prompts.InfoPacket('An error occured while checking your answers. Please contact your administartor. Error Code: 0xA0', 'EXIT', 'Quizzing Form | Response Verifier'),
                    tk.Toplevel(self.root),
                    True
                )
                
                self._abort_quiz()
                return

            _AnsConfig = self.data['__quiz']['__Ans'][QUID]
            
            if isinstance(_AnsConfig, dict): 
                # MC
                selection = _AnsConfig['__sel']
                
                if selection is None:
                    _show_error_q(QUID)                    
                    _ret(f"Please answer all quesions before submitting the quiz.")
                    return
            
                correct_answers = [A[j] for j in A['C'].split('/')]
                selected_answer = _AnsConfig[selection][0]
                
                if selected_answer in correct_answers:
                    self.data['__quiz']['__score']['correct'] += 1 
                    self.data['__quiz']['__score']['d'].append(qa_files.SCR_QUESTION(
                        int(i), QUID, Q, selected_answer, 
                        100, qa_files.SCR_VERDICT.CORRECT, 
                        AutoMark, AutoMark_UseApproxMatch, AutoMark_ApproxMatch_PM
                    ))

                else:
                    self.data['__quiz']['__score']['incorrect'] += 1
                    self.data['__quiz']['__score']['d'].append(qa_files.SCR_QUESTION(
                        int(i), QUID, Q, selected_answer, 
                        0, qa_files.SCR_VERDICT.INCORRECT, 
                        AutoMark, AutoMark_UseApproxMatch, AutoMark_ApproxMatch_PM
                    ))
            
            elif isinstance(_AnsConfig, (list, tuple)):
                if len(_AnsConfig) == 3:
                    # WR
                    box: CustomText = _AnsConfig[-1]
                    response = box.get('1.0', 'end').strip()
                    box.delete('1.0', 'end')
                    box.insert('end', response)
                    
                    if not len(response):
                        _show_error_q(QUID)
                        _ret("Please answer all questions before submitting the quiz.")
                        return                   
                    
                    match = fuzz.ratio(response, A)
                    
                    #                                        [ID    Q  given answer     [%match, correct?], [conf_AM, conf_AM_Ap, conf_AM_PM]]
                    if not AutoMark:
                        self.data['__quiz']['__score']['d'].append(qa_files.SCR_QUESTION(
                            int(i), QUID, Q, response, 
                            match, qa_files.SCR_VERDICT.UNDETERMINED, 
                            AutoMark, AutoMark_UseApproxMatch, AutoMark_ApproxMatch_PM
                        ))
                    
                    else:
                        if not AutoMark_UseApproxMatch:
                            # Needs exact match
                            c = (match == 1)
                        
                        else:
                            c = (match >= AutoMark_ApproxMatch_PM)
                        
                        self.data['__quiz']['__score']['correct' if c else 'incorrect'] += 1
                        self.data['__quiz']['__score']['d'].append(qa_files.SCR_QUESTION(
                            int(i), QUID, Q, response, 
                            match, qa_files.SCR_VERDICT.CORRECT if c else qa_files.SCR_VERDICT.INCORRECT, 
                            AutoMark, AutoMark_UseApproxMatch, AutoMark_ApproxMatch_PM
                        ))
                    
                elif len(_AnsConfig) == 5:
                    # TF
                    state = _AnsConfig[-1]
                    
                    if state not in (True, False):
                        _show_error_q(QUID)
                        _ret("Please answer all questions before submitting the quiz.")
                        return

                    correct_answer = bool(int(A))
                    
                    if correct_answer == state:
                        self.data['__quiz']['__score']['correct'] += 1 
                        self.data['__quiz']['__score']['d'].append(qa_files.SCR_QUESTION(
                            int(i), QUID, Q, state, 
                            100, qa_files.SCR_VERDICT.CORRECT, 
                            AutoMark, AutoMark_UseApproxMatch, AutoMark_ApproxMatch_PM
                        ))

                    else:
                        self.data['__quiz']['__score']['incorrect'] += 1
                        self.data['__quiz']['__score']['d'].append(qa_files.SCR_QUESTION(
                            int(i), QUID, Q, state, 
                            0, qa_files.SCR_VERDICT.INCORRECT, 
                            AutoMark, AutoMark_UseApproxMatch, AutoMark_ApproxMatch_PM
                        ))
                    
                else:
                    _ret(); return
            
            else:
                _ret(); return
        
        # Successfully answered all questions.
        # log(LoggingLevel.SUCCESS, json.dumps(self.data['__quiz']['__score'], indent=4))
        self.quiz_WAIT_lbl.config(text='Your score file is ready! Please select a location to export the file to.')
        
        self.data['__attr_quiz_complete'] = True
        self.export_score()
        
    def export_score(self) -> None:
        assert self.data.get('__attr_quiz_complete'), 'export_score called before quiz is complete E: 0xB1.'
        
        self.root.wm_attributes('-topmost', 0)
        self.root.geometry(self.original_pos)
        
        errors = self.data['__quiz'].get('__errors', {})
        logs = self.data['__quiz'].get('__log', {})
        score_c = self.data['__quiz']['__score']['correct']
        score_i = self.data['__quiz']['__score']['incorrect']
        score_q = self.data['__quiz']['__score']['questions']
        score_C = self.data['__quiz']['__score']['configuration']
        score_d = self.data['__quiz']['__score']['d']
        
        for time, error in errors.items():
            log(LoggingLevel.ERROR, f'LOG created during quiz: {time}: {error}')    
            
        for time, log_str in logs.items():
            log(LoggingLevel.INFO, f'LOG created during quiz: {time}: {log_str}')    
        
        output_data = qa_files.SCR_GEN_LATEST(
            self.first_name.get(), self.last_name.get(), self.ID.get(),
            self._gen_user_id(), self.data['__quiz']['__user_session_code'],
            datetime.datetime.now().strftime('%a, %B %d, %Y - %H:%M:%S'), 
            qa_functions.qa_info.App.version, qa_functions.qa_info.App.build_id,
            self.data['qz_tm_started'].strftime('%a, %B %d, %Y - %H:%M:%S'), 
            self.quiz_time_taken_lbl.cget('text'), self._get_attempt_number(),
            errors, logs, qa_files.SCR_RES(score_c, score_i, score_q, score_C, score_d)
        )[-1]
        
        # log(LoggingLevel.SUCCESS, output_data)
        
        data_to_write, extension = qa_files.generate_file(qa_functions.FileType.QA_SCORE, output_data)  # type: ignore
        output_file = filedialog.asksaveasfilename(filetypes=((f'.{extension}', f'.{extension}'),), defaultextension=f'.{extension}')
        
        while (not isinstance(output_file, str)) or (output_file in ('None', '')):
            self.set_error_text('You MUST select an output location and filename', 5)
            output_file = filedialog.asksaveasfilename(filetypes=((f'.{extension}', f'.{extension}'),), defaultextension=f'.{extension}')

        assert isinstance(output_file, str), 'no idea how this assertion would fail Error code: 0x¯\_( ͡° ͜ʖ ͡°)_/¯'

        if output_file.split('.')[-1] != extension:
            output_file += f'.{extension}'
            
        assert qa_functions.SaveFile.secure(
            qa_functions.File(output_file), data_to_write, qa_functions.SaveFunctionArgs(False, save_data_type=bytes)
        ), 'Failed to save SCORE (SCR) file. Please contact your administrator. Error: 0xBF'
        
        log(LoggingLevel.SUCCESS, f'Successfully created .qaScore file')
        qa_prompts.MessagePrompts.show_info(
            qa_prompts.InfoPacket('Successfully saved your score; share the file with your administrator.', 'EXIT', 'You\'re Done Here!')
        )
        
        log(LoggingLevel.WARNING, 'Shutting down application after nominal operations.')
        self.close()
        
        
    def _qz_tick(self) -> None:
        if not self.data.get('qz_tick', False):
            return
        
        n = datetime.datetime.now()
        d = int(cast(datetime.timedelta, (n - self.data['qz_tm_started'])).total_seconds())
        
        self.quiz_curnt_time_lbl.config(text=f"Current Time: {n.strftime('%H:%M:%S')}")
        self.quiz_time_taken_lbl.config(text='Time Elapsed: %02d:%02d:%02d' % ((d // 3600), (d // 60) % 60 , (d % 60)))
    
        self.active_jobs['qztck'] = self.root.after(1000, self._qz_tick)
        
    def _prepare_quiz(self) -> None:
        self.quiz_activity_box.auto_size()
        self.quiz_activity_box.setup_color_tags(self.theme_update_map)
        
        def _ins(text: str, frmt: str = "") -> None:
            self.quiz_activity_box.config(state=tk.NORMAL)
            self.quiz_activity_box.insert('end', text, frmt)
            self.quiz_activity_box.config(state=tk.DISABLED)

            self.quiz_activity_box.update()
            self.root.update()
            
        _ins('Computing your session ID.', '<accent>')
        
        self.data['__quiz'] = {}
        self.data['__quiz']['__user_session_code'] = self._gen_user_id(datetime.datetime.now().strftime("%H%M%S%d%m%Y"))
        self.data['__quiz']['__attempt'] = self._get_attempt_number() + 1
       
        _ins(f'\nYour session ID: ')
        _ins(self.data['__quiz']['__user_session_code'], '<warning>')
        _ins(f'\n   --> Note that this code is provided to the administrator to identify this session.', '<italics>')
                
        _ins('\n\nComputing attempt number.', '<accent>')
        _ins(f'\nFor this user ({self.last_name.get()}, {self.first_name.get()} :: {self.ID.get()}), this is attempt {self.data["__quiz"]["__attempt"]}')
       
        self.title_info.config(
            text=(self.title_info.cget('text') + f' Session ID: {self.data["__quiz"]["__user_session_code"]}. Attempt {self.data["__quiz"]["__attempt"]}')
        )
        
        _ins('\n\nLoading questions from database.', '<accent>')
        _q = self.data['CONFIG_INF:<DB>']['QUESTIONS']
        
        if not len(_q):
            _ins(f'\n[FATAL] Did not find any questions in database.', '<error>')
            _ins(f'\n      --> The quiz has been ABORTED. Please contact your administrator.', '<error>')
            _ins(f'\n      --> This attempt is not counted towards your reported "# of attempts" statistic.')
            
            self._abort_quiz(False)
            
            return
        
        _ins(f'\nFound {len(_q)} questions in database "{self.data["DATABASE"]["data_recv"]["name"]}".', '<okay>')
        _ins('\n\nArranging questions ...\n\n')
        
        q = self._arr_q(_q, _ins)
        _ins(f'\nSuccessfully arranged questions.\n\n', '<okay>')
        sleep(1)
        
        self.data['__quiz']['__questionBase'] = copy.deepcopy(q)        
        self.data['__quiz']['__prep'] = True
        
        _ins(f'\nPreparing quiz form... Get Ready!', '<warning>')
        
    def _arr_q(self, q: Dict[Any, Any], _ins: Any) -> Dict[Any, Any]:        
        ssb = self.data['CONFIG_INF:<DB>']['CONFIGURATION']['poa']
        ssd = self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd']
        rqo = self.data['CONFIG_INF:<DB>']['CONFIGURATION']['rqo']
        
        assert ssb in ('p', 'a'), 'QA.PrepSeq._arr_q: E0x1 <SSB>'
        assert isinstance(rqo, bool), 'Qa.PreSeq._arr_q: E0x2 <RQO>'
        assert isinstance(ssd, int), 'Qa.PreSeq._arr_q: E0x3 <SSD>'
        
        subsampling: bool = (ssb == 'p') 
        
        _ins("  * Checking administrator policy for question distribution: ")
        _ins(f"\n       - Subsampling: ")
        _ins('Enabled' if subsampling else 'Disabled', '<accent>')
        _ins(f'\n       - Randomize Question Order: ')
        _ins('Enabled' if rqo else 'Disabled', '<accent>')
        
        qPb: Dict[Any, Any] = {}
        
        if rqo:
            qPa: List[str] = cast(List[str], [*q.keys()])
            
            for I in range(len(q)):
                r = random.randint(0, len(qPa) - 1)
                qPb[str(I)] = q[qPa[r]]
                qPa.pop(r)
            
        else:
            qPb = copy.deepcopy(q)
        
        if subsampling:
            ind0 = random.randint(0, len(q) // ssd)
            indf = ind0 + math.ceil(len(q) / ssd)
            
            qPa = [*qPb.keys()]
            qPc = {str(i): qPb[k] for i, k in enumerate(qPa[ind0:indf])}

            return qPc
        
        else:
            return qPb
    
    def proceed(self) -> None:
        if self.current_page == self.SUMMARY_PAGE:
            raise Exception ("Unprogrammed behavior")
        
        self.setup_page(self.current_page + 1)

    def go_back(self) -> None:
        if self.current_page == self.LOGIN_PAGE:
            raise Exception ("Unprogrammed behavior")

        self.setup_page(self.current_page - 1)

    @staticmethod
    def _check_db(db: Dict[str, Any]) -> Tuple[int, List[str], Dict[str, Any]]:
        assert isinstance(db, dict)
        name_f, name_d = qa_functions.data_at_dict_path('DB/name', db)
        assert name_f

        errors: List[str] = []

        log(LoggingLevel.INFO, 'QuizzingForm._CHECK_DB: Checking database integrity')

        if not isinstance(name_d, str):
            errors.append('QuizzingForm._CHECK_DB.ERR: 0x1a - DB_NAME: T')
        elif len(name_d.strip()) <= 0:
            errors.append('QuizzingForm._CHECK_DB.ERR: 0x1b - DB_NAME: L')

        _, psw_d = qa_functions.data_at_dict_path('DB/psw', db)
        b = isinstance(psw_d, list)
        if b:
            b &= len(psw_d) == 2
            if b:
                b &= isinstance(psw_d[0], bool)
                b &= isinstance(psw_d[1], str)

                if b:
                    b &= not (len(psw_d[1]) != 128 and psw_d[0])  # NAND logic

                    # NAND:
                    # <!128> and <!enb>: True
                    # <128> and <!enb>: False
                    # <!128> and <enb>: False
                    # <128> and <enb>: True

        if not b:
            errors.append('QuizzingForm._CHECK_DB.ERR: 0x2a DB_PSW.')

        del psw_d

        _, q_psw_d = qa_functions.data_at_dict_path('DB/q_psw', db)
        b = isinstance(q_psw_d, list)
        if b:
            b &= len(q_psw_d) == 2
            if b:
                b &= isinstance(q_psw_d[0], bool)
                b &= isinstance(q_psw_d[1], str)

                if b:
                    b &= not (len(q_psw_d[1]) != 128 and q_psw_d[0])  # NAND logic gate

                    # NAND:
                    # <!128> and <!enb>: True
                    # <128> and <!enb>: False
                    # <!128> and <enb>: False
                    # <128> and <enb>: True

        if not b:
            errors.append('QuizzingForm._CHECK_DB.ERR: 0x2b QZ_PSW.')

        # Configuration checks
        cr = 'CONFIGURATION'
        cd = db.get(cr)

        if not cd:
            errors.append("QuizzingForm._CHECK_DB.ERR: 0x3a ~CONFIG.")

        elif isinstance(cd, dict):
            f: List[Any] = []

            for k, (tp, default, opts) in (
                    ('acc', (bool, False, [])),
                    ('poa', (str, 'p', ['p', 'a'])),
                    ('rqo', (bool, False, [])),
                    ('ssd', (int, 2, [])),
                    ('dpi', (bool, False, [])),
                    ('a2d', (int, 1, [])),
            ):
                assert isinstance(k, str)
                assert isinstance(opts, (list, tuple, set))

                if not isinstance(cd.get(k), tp):
                    f.append(f'"{k}": TP')
                    continue

                if len(cast(Sized, opts)) > 0:
                    if cd.get(k) not in opts:
                        f.append(f'"{k}": OPT')
                        continue

                log(LoggingLevel.SUCCESS, f'QuizzingForm._CHECK_DB.CONFIG: Value for "{k}" is okay (tp, opt).')

            for failure in f:
                errors.append(f'QuizzingForm._CHECK_DB.ERR: 0xA0 - {failure}')

            db[cr] = cd

        else:
            raise qa_functions.UnexpectedEdgeCase('QuizzingForm._CHECK_DB.ERR: 0xF1 :: ?CONFIG (cd) :: !dict, !NoneType')

        qr = 'QUESTIONS'
        qd = db.get(qr)
        cQAcc = 0

        if qd is None:
            errors.append("QuizzingForm._CHECK_DB.ERR: 0x4a ~QUESTIONS.")

        elif isinstance(qd, dict):
            if not qd:
                errors.append('QuizzingForm._CHECK_DB.ERR: 0x4b - NO QUESTIONS.')

            for i, (k, v) in enumerate(list(qd.items())):
                try:
                    assert isinstance(k, str), f'QuizzingForm._CHECK_DB.ERR: 0x50 qTe::tpT1'
                    try:
                        int(k)
                    except Exception as e1:
                        raise AssertionError('QuizzingForm._CHECK_DB.ERR: 0x51 qTe::tpT2')

                    assert isinstance(v, dict), 'QuizzingForm._CHECK_DB.ERR: 0x52 aTe::tpT1'
                    assert len(v.values()) == 4, 'QuizzingForm._CHECK_DB.ERR: 0x53 aTe::vv2'
                    assert min([vk in v for vk in ('0', '1', '2', 'd')]), f'QuizzingForm._CHECK_DB.ERR: 0x54 aTe::vk3'

                    t, q, a, d = v['0'], v['1'], v['2'], v['d']
                    assert t in ('nm', 'tf', 'mc0', 'mc1'), f'QuizzingForm._CHECK_DB.ERR: 0x55 aTe::aTp4'
                    assert isinstance(q, str), 'QuizzingForm._CHECK_DB.ERR: 0x56 qTe::TpF'
                    assert isinstance(d, str), 'QuizzingForm._CHECK_DB.ERR: 0x57 dTe::Tp1'
                    assert isinstance(a, str if t[:2] != 'mc' else dict), 'QuizzingForm._CHECK_DB.ERR: 0x58 aTe::TpF'

                    dSize = sum([d0.size for d0 in qa_forms.question_editor_form.Data0.entries]) + \
                            sum([d1.size for d1 in qa_forms.question_editor_form.Data1.exEntries])

                    assert len(d) == dSize, f'QuizzingForm._CHECK_DB.ERR: 0x59 dTe::Ln2'
                    if t[:2] == 'mc':
                        assert t[2] == d[sum([d0.size for d0 in qa_forms.question_editor_form.Data0.entries])], \
                            'QuizzingForm._CHECK_DB.ERR: 0x5A dTe+tTe::m1'
                        assert len(cast(Dict[str, Union[int, str]], a)) >= 4, \
                            'QuizzingForm._CHECK_DB.ERR: 0x5B aTe::mc1'

                except Exception as E:
                    cQAcc += 1
                    errors.append(f'{str(E)} <{i}>')

        else:
            raise qa_functions.UnexpectedEdgeCase('QuizzingForm._CHECK_DB.ERR: 0xF2 :: ~QUESTIONS :: !dict, !NoneType')

        if not cQAcc:
            log(LoggingLevel.SUCCESS, f'QuizzingForm._CHECK_DB.QUESTIONS: Successfully loaded questions (no errors found)')

        else:
            errors.append('QuizzingForm._CHECK_DB.ERR: 0x5F: 0+cQAcc')

        return len(errors), errors, db

    def set_database(self) -> None:
        try:
            self.disable_all_inputs()
            self.select_database_btn.config(text='Select a Database', style='TButton', image="", compound=tk.CENTER)
            self.data['DATABASE'] = {'file_path': "", 'data_recv': {'name': "", '_raw': b"", '_flags': [], '_security_info': {}, 'read': {}}, 'verified': False}

            assert self.current_page == self.LOGIN_PAGE, 'SET_DATABASE.ERR (strict) 1: ~LoginPage'
            res = tkfld.askopenfilename(defaultextension=qa_files.qa_quiz_extn, filetypes=(('Quiz Database', qa_files.qa_quiz_extn), ))

            if not len(res.strip()):
                self.set_error_text('No file selected.', 3)
                return

            assert os.path.isfile(res), 'SET_DATABASE.ERR (strict) 2: ~is_file'

            file = qa_functions.File(res)
            self.data['DATABASE']['file_path'] = file.file_path

            # Load contents
            with open(file.file_path, 'rb') as _database_file_handle:
                _raw = _database_file_handle.read()
                _database_file_handle.close()

            # Steps to read:
            # i) Decrypt _raw
            # ii) Check and remove extension verifier
            # iii) Load file sections (header, footer, body)
            # iv) Check hashes
            # v) Decrypt body
            # vi) Check flags
            #
            # After reading:
            # vii) Check for q_psw hash & enable flag (+ weak verification)
            # viii) Prompt and check for password (if needed)

            # i) Decrypting _raw
            _dec1 = qa_functions.qa_file_handler._Crypt.decrypt(_raw, qa_files.qa_quiz_enck, qa_functions.ConverterFunctionArgs())

            # ii) Check and remove extension verifier (last 5 characters)
            assert len(_dec1) >= 5, 'SET_DATABASE.ERR (strict) 3: _dec1__LEN~>=5'  # type: ignore
            _c1 = cast(bytes, _dec1)[-7:]
            assert _c1 == qa_files.C_QZ_TRAILING_ID.encode(), f'SET_DATABASE.ERR (strict) 4: _c1 failure'
            _dec1 = cast(bytes, _dec1)[:-7]

            # iii) Load file sections
            # AND iv) Check hashes
            # AND v) decrypt body
            _, _dec2_str = cast(Tuple[bytes, str], qa_files.load_file(qa_functions.FileType.QA_QUIZ, _dec1))
            assert len(_dec2_str.strip()) > 0, 'SET_DATABASE.ERR (strict) 5: ~_dec2_str__LEN'

            # convert _dec2_str to QZDB
            # _DB: Dict[str, Any] = json.loads(_dec2_str)  # type: ignore
            _QZDB = qa_files.QZDB_ReadData(_dec2_str)

            # vi) Check flag
            assert 'QZDB' in _QZDB.meta_FLAGS, 'SET_DATABASE.ERR (strict) 6: ~FLAG_QZDB'

            # NEW STEP: Convert QZDB to dict
            _DB: Dict[str, Any] = {
                'DB':
                    {
                        'name': _QZDB.meta_NAME,
                        'psw': _QZDB.meta_PSWA,
                        'q_psw': _QZDB.meta_PSWQ,
                        'FLAGS': _QZDB.meta_FLAGS
                    },
                'CONFIGURATION': _QZDB.content_CONFIG,
                'QUESTIONS': cast(Dict[str, Any], _QZDB.content_QUESTIONS)
            }
            
            # check database integrity
            N_errors, errors, _DB = self._check_db(_DB)

            if N_errors:
                log(LoggingLevel.ERROR, f'SET_DATABASE.ERR (strict) 7: _DB.errs. {N_errors=}:')
                for index, error in enumerate(errors):
                    log(LoggingLevel.ERROR, f'\t{index}) {error} <7-strict>')

                assert False, f'SET_DATABASE.ERR (strict) 7: _DB.errs.'

            del N_errors, errors
            log(LoggingLevel.SUCCESS, 'SET_DATABASE: No errors found')

            # vii) q_psw
            E_PSWQ, H_PSWQ = cast(Tuple[bool, str], _DB['DB']['q_psw'])

            if E_PSWQ:
                # need to check password.
                s_mem = qa_functions.SMem()
                qa_prompts.InputPrompts.SEntryPrompt(s_mem, f'Enter database password for \'{_DB["DB"]["name"]}\'', '')

                r = s_mem.get()
                if r is None:
                    del s_mem
                    qa_prompts.MessagePrompts.show_error(
                        qa_prompts.InfoPacket('Couldn\'t open database: Invalid password', title='Quizzing Form | Security')
                    )
                    assert False, 'SET_DATABASE.ERR (strict) 8a: Q_PSW'

                if r.strip() == '':
                    del s_mem
                    qa_prompts.MessagePrompts.show_error(
                        qa_prompts.InfoPacket('Couldn\'t open database: Invalid password', title='Quizzing Form | Security')
                    )
                    assert False, 'SET_DATABASE.ERR (strict) 8b: Q_PSW'

                if hashlib.sha3_512(r.encode()).hexdigest() != H_PSWQ:
                    del s_mem
                    qa_prompts.MessagePrompts.show_error(
                        qa_prompts.InfoPacket('Couldn\'t open database: Invalid password', title='Quizzing Form | Security')
                    )

                    assert False, 'SET_DATABASE.ERR (strict) 8c: Q_PSW'

                log(LoggingLevel.SUCCESS, 'Authenticated')

            else:
                log(LoggingLevel.INFO, 'SET_DATABASE: Flag E_PSWQ not set')

            self.data['DATABASE'] = {
                'file_path': file.file_path,
                'data_recv': {
                    'name': cast(str, _DB['DB']['name']),
                    '_raw': _raw,
                    '_flags': cast(List[str], _DB['DB']['FLAGS']).copy(),
                    '_security_info': {
                        'E_PSW0': cast(bool, _DB['DB']['psw'][0]),
                        'H_PSW0': cast(str, _DB['DB']['psw'][1]),
                        'E_PSWQ': cast(bool, _DB['DB']['q_psw'][0]),
                        'H_PSWQ': cast(str, _DB['DB']['q_psw'][1]),
                    },
                    'read': _DB,
                },
                'verified': True,
                '__raw_QZDB_struct': _QZDB
            }

        except Exception as E:
            log(LoggingLevel.ERROR, f'{E}\n{traceback.format_exc()}')
            self.data['DATABASE'] = {'file_path': None, 'data_recv': {'name': "", '_raw': b"", '_flags': [], '_security_info': {}, 'read': {}}, 'verified': False}
            self.set_error_text('Invalid/Corrupt data found in database. Please try again.', 3)

        else:
            self.select_database_btn.config(
                text=f'Selected "{_DB["DB"]["name"]}"',
                image=self.svgs['checkmark']['accent'],
                compound=tk.LEFT,
                style="My.Active.TButton"
            )

        finally:
            self.enable_all_inputs()

    def setup_page(self, page_index: int) -> bool:

        if not isinstance(page_index, int):
            log(LoggingLevel.ERROR, f'QuizzingForm.SetupPage: page_index is not an integer ({type(page_index)}')

        if not (self.LOGIN_PAGE <= page_index <= self.SUMMARY_PAGE):
            log(LoggingLevel.ERROR, f'QuizzingForm.SetupPage: page_index out of range ({page_index})')
            return False

        self.disable_all_inputs()

        # if self.data.get('GLOBAL', {}).get('Attr_', {}).get('Animating.PauseClose.Set', False):
        if len(self.error_label.cget('text')):
            log(LoggingLevel.WARNING, 'QuizzingForm.WARNINGS.Task_f1')
            self.error_label.config(text='')  # clearing the text will automatically clear the animation and cancel any invoked animation calls.

        def setup_login_frame() -> None:
            self.config_frame.pack_forget()
            self.summary_frame.pack_forget()
            self.login_frame.pack(fill=tk.BOTH, expand=True)
            self.title_info.config(text='')

            if 'DATABASE' in self.data:
                self.data['DATABASE']['verified'] = False  # any time the page is changed back to the login page, the database must be re-verified

            if not self.data.get('flag_SetupLoginElements', False):
                log(LoggingLevel.INFO, 'Setting up QF.LOGIN page')

                self.left_cont.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
                self.right_cont.pack(fill=tk.BOTH, side=tk.RIGHT, expand=True)

                self.login_page_title.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=self.padY)
                self.login_page_title.config(text='Getting Started')

                self.ID_cont.pack(fill=tk.BOTH, expand=True)
                self.database_frame.pack(fill=tk.BOTH, expand=False)

                self.ID_name_frame.pack(fill=tk.BOTH, expand=False)
                self.ID_first_name_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)
                self.ID_last_name_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

                self.first_name_lbl.config(anchor=tk.W, justify=tk.LEFT)
                self.last_name_lbl.config(anchor=tk.W, justify=tk.LEFT)

                self.first_name_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))
                self.last_name_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

                self.first_name_field.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))
                self.last_name_field.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))

                self.ID_lbl.config(justify=tk.LEFT, anchor=tk.W)
                self.ID_lbl.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0))

                self.ID_field.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))

                self.select_database_btn.pack(fill=tk.X, expand=True, padx=self.padX, pady=self.padY)
                self.select_database_btn.config(text='Select a Database', command=self.set_database)

                self.first_name.set('')
                self.last_name.set('')
                self.ID.set('')

                self.data['DATABASE'] = {
                    'file_path': None,
                    'data_recv': {
                        'name': "",
                        '_raw': b"",
                        '_flags': [],
                        '_security_info': {},
                        'read': {},
                    },
                    'verified': False
                }

                self.data['flag_SetupLoginElements'] = True

            if not self.data.get('flag_SetupLoginUpdateRequests', False):
                self.update_requests[gsuid()] = [self.login_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

                self.update_requests[gsuid()] = [self.left_cont, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.right_cont, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

                self.update_requests[gsuid()] = [self.login_page_title, ThemeUpdateCommands.FG, [ThemeUpdateVars.ACCENT]]
                self.update_requests[gsuid()] = [self.login_page_title, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.login_page_title, ThemeUpdateCommands.FONT, [ThemeUpdateVars.TITLE_FONT_FACE, ThemeUpdateVars.FONT_SIZE_TITLE]]

                self.update_requests[gsuid() + '&cus+LBLF'] = [
                    None, ThemeUpdateCommands.CUSTOM, [
                        lambda *args: self.ID_cont.config(
                            bg=args[0], fg=args[1], bd=args[2], borderwidth=args[2], highlightthickness=args[2], highlightcolor=args[3],
                            highlightbackground=args[3], font=(args[4], args[5])
                        ),
                        ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, 0, ThemeUpdateVars.BG, ThemeUpdateVars.TITLE_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
                    ]
                ]

                self.update_requests[gsuid() + '&cus+LBLF'] = [
                    None, ThemeUpdateCommands.CUSTOM, [
                        lambda *args: self.database_frame.config(
                            bg=args[0], fg=args[1], bd=args[2], borderwidth=args[2], highlightthickness=args[2], highlightcolor=args[3],
                            highlightbackground=args[3], font=(args[4], args[5])
                        ),
                        ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, 0, ThemeUpdateVars.BG, ThemeUpdateVars.TITLE_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
                    ]
                ]

                self.update_requests[gsuid()] = [self.ID_name_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.ID_first_name_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.ID_last_name_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

                self.update_requests[gsuid() + '&cus+LBL'] = [
                    None, ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *args: self.first_name_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                        ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
                    ]
                ]

                self.update_requests[gsuid() + '&cus+LBL'] = [
                    None, ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *args: self.last_name_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                        ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
                    ]
                ]

                self.update_requests[gsuid() + '&cus+LBL'] = [
                    None, ThemeUpdateCommands.CUSTOM,
                    [
                        lambda *args: self.ID_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3])),
                        ThemeUpdateVars.BG, ThemeUpdateVars.ACCENT, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL
                    ]
                ]

                self.data['flag_SetupLoginUpdateRequests'] = True

        def check_login_frame() -> Tuple[bool, int, List[str]]:
            errs: List[str] = []
            self.first_name.set(self.first_name.get().strip().title())
            self.last_name.set(self.last_name.get().strip().title())
            self.ID.set(self.ID.get().strip())

            if not (bool(len(self.first_name.get())) & bool(len(self.last_name.get()))):
                errs.append('Please enter your first and last names.')
                log(LoggingLevel.WARNING, f'QuizzingForm.WARNINGS.SETUP_PAGE.CHECK_LOGIN_PAGE: (0x01) {len(self.first_name.get())} & {len(self.last_name.get())} => {bool(len(self.first_name.get())) & bool(len(self.last_name.get()))}')

            if not len(self.ID.get()) >= 6:
                errs.append('Please enter an alphanumeric ID, consisting of at least 6 characters.')
                log(LoggingLevel.WARNING, f'QuizzingForm.WARNINGS.SETUP_PAGE.CHECK_LOGIN_PAGE: (0x02) {len(self.ID.get())}')

            if self.data.get('DATABASE', {}).get('file_path') is None or \
                (not os.path.isfile(self.data.get('DATABASE', {}).get('file_path', ''))) or \
                len(self.data.get('DATABASE', {}).get('data_recv', {}).get('name').strip()) == 0 or \
                len(self.data.get('DATABASE', {}).get('data_recv', {}).get('_raw').strip()) == 0 or \
                len(self.data.get('DATABASE', {}).get('data_recv', {}).get('_flags')) == 0 or \
                len(self.data.get('DATABASE', {}).get('data_recv', {}).get('_security_info')) == 0 or \
                len(self.data.get('DATABASE', {}).get('data_recv', {}).get('read')) == 0:
                errs.append('Please select a Quizzing Application | Quizzing Form database.')
                log(LoggingLevel.WARNING, f'QuizzingForm.WARNINGS.SETUP_PAGE.CHECK_LOGIN_PAGE: (0x03) n<DB>')

            elif not self.data['DATABASE']['verified']:
                N, e, _ = self._check_db(self.data['DATABASE']['data_recv']['read'])
                if N:
                    errs.append('Invalid / corrupt data found in selected database. Please try again.')
                    log(LoggingLevel.WARNING, f'QuizzingForm.WARNINGS.SETUP_PAGE.CHECK_LOGIN_PAGE: (0x04) [V]n<DB>')
                    for index, err in enumerate(e):
                        log(LoggingLevel.ERROR, f'\t{index}) {err}')

                elif self.current_page != page_index:
                    self.data['DATABASE']['verified'] = True

            else:
                log(LoggingLevel.INFO, 'QuizzingForm.INFO.SETUP_PAGE.CHECK_LOGIN_PAGE: db already verified')

            return len(errs) == 0, len(errs), errs

        def setup_config_frame() -> None:
            assert self.data['DATABASE']['verified'], 'QuizzingForm.ERR.SETUP_PAGE.CONFIG_FRAME: (strict) 0: <DB>nVerified'

            self.login_frame.pack_forget()
            self.summary_frame.pack_forget()
            self.config_frame.pack(fill=tk.BOTH, expand=True)
            self.title_info.config(text=f'Logged in as {" ".join([self.first_name.get(), self.last_name.get()]).title()} ({self.ID.get()})', anchor=tk.W, justify=tk.LEFT)

            # Though the elements only need to be placed once, their states must be reset when entering the page, iff the database is changed
            if not self.data.get('flag_SetupConfigElements', False):
                # Logical configuration
                self.inputs.extend([self.config_qd_ssd_field, self.config_qd_poa_P, self.config_rqo_enb, self.config_pc_a2d_field, self.config_pc_enb])
                self.config_qd_ssd.trace('w', self._config_ssd_mod)
                self.config_pc_a2d.trace('w', self._config_a2d_mod)

                # Interface configuration
                self.config_acc_status.pack(fill=tk.X, expand=False, padx=self.padX, side=tk.TOP)
                self.config_qd_frame.pack(fill=tk.BOTH, expand=True, padx=(self.padX, 0), pady=(self.padY, 0), side=tk.LEFT)
                self.config_pc_frame.pack(fill=tk.BOTH, expand=True, padx=self.padX, pady=(self.padY, 0), side=tk.RIGHT)

                self.config_acc_status.config(anchor=tk.W, justify=tk.LEFT)

                self.config_qd_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=(self.padY, 0))
                self.config_qd_poa_P.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))
                self.config_qd_ssd_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=(self.padY, 0))
                self.config_qd_ssd_field.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))

                self.config_qd_lbl.config(text='Select whether to be prompted with a subset or all of the questions.', anchor=tk.W, justify=tk.LEFT)
                self.config_qd_ssd_lbl.config(text='Select by what factor should the questions be divided by (only applicable if the above is set to "Subset" mode).', anchor=tk.W, justify=tk.LEFT)

                self.config_rqo_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=(self.padY, 0))
                self.config_rqo_enb.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY / 4, self.padY))
                self.config_rqo_lbl.config(text="Select whether to randomize question order or not.", anchor=tk.W, justify=tk.LEFT)

                self.config_pc_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=self.padY)
                self.config_pc_enb.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY / 4, self.padY))

                self.config_pc_lbl.config(text='Select whether to penalize erroneous responses.', anchor=tk.W, justify=tk.LEFT)

                self.config_pc_a2d_lbl.pack(fill=tk.BOTH, expand=False, padx=self.padX, pady=(self.padY, 0))
                self.config_pc_a2d_field.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY/4, self.padY))

                self.config_pc_a2d_lbl.config(text="Select how many points to deduct when an erroneous answers are provided.", anchor=tk.W, justify=tk.LEFT)

            if not self.data.get('flag_SetupConfigUpdateRequests', False):
                self.update_requests[gsuid()] = [self.config_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

                self.update_requests[gsuid()] = [self.config_qd_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.config_qd_frame, ThemeUpdateCommands.FG, [ThemeUpdateVars.ACCENT]]
                self.update_requests[gsuid()] = [self.config_qd_frame, ThemeUpdateCommands.FONT, [ThemeUpdateVars.TITLE_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL]]

                self.update_requests[gsuid()] = [self.config_pc_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.config_pc_frame, ThemeUpdateCommands.FG, [ThemeUpdateVars.ACCENT]]
                self.update_requests[gsuid()] = [self.config_pc_frame, ThemeUpdateCommands.FONT, [ThemeUpdateVars.TITLE_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL]]

                self.update_requests[gsuid()] = [self.config_acc_status, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
                self.update_requests[gsuid()] = [self.config_acc_status, ThemeUpdateCommands.FONT, [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN]]

                self.update_requests[gsuid()] = [self.config_qd_lbl, ThemeUpdateCommands.CUSTOM, [
                    lambda *args: self.config_qd_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=int(args[4]//2-4*args[5])),
                    ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL, ('<LOOKUP>', 'root_width'),
                    ('<LOOKUP>', 'padX')
                ]]

                self.update_requests[gsuid()] = [self.config_qd_ssd_lbl, ThemeUpdateCommands.CUSTOM, [
                    lambda *args: self.config_qd_ssd_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=int(args[4] // 2 - 4 * args[5])),
                    ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL, ('<LOOKUP>', 'root_width'),
                    ('<LOOKUP>', 'padX')
                ]]

                self.update_requests[gsuid()] = [self.config_pc_a2d_lbl, ThemeUpdateCommands.CUSTOM, [
                    lambda *args: self.config_pc_a2d_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=int(args[4] // 2 - 4 * args[5])),
                    ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL, ('<LOOKUP>', 'root_width'),
                    ('<LOOKUP>', 'padX')
                ]]

                self.update_requests[gsuid()] = [self.config_rqo_lbl, ThemeUpdateCommands.CUSTOM, [
                    lambda *args: self.config_rqo_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=int(args[4] // 2 - 4 * args[5])),
                    ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL, ('<LOOKUP>', 'root_width'),
                    ('<LOOKUP>', 'padX')
                ]]

                self.update_requests[gsuid()] = [self.config_pc_lbl, ThemeUpdateCommands.CUSTOM, [
                    lambda *args: self.config_pc_lbl.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=int(args[4] - 4 * args[5])),
                    ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL, ('<LOOKUP>', 'root_width'),
                    ('<LOOKUP>', 'padX')
                ]]

            if str(qa_functions.FlattenedDict(self.data.get('CONFIG_INF:<DB> _copy', {}), strict_flattening=True)) != \
                    str(qa_functions.FlattenedDict(self.data['DATABASE']['data_recv']['read'], strict_flattening=True)):

                log(LoggingLevel.WARNING, 'QuizzingForm.WARNINGS.SETUP_PAGE.SETUP_CONFIG_PAGE: (0x1) - rst due to db ch')

                self.update_requests['CONFIG.ACC.STATUS.FG'] = [
                    self.config_acc_status, ThemeUpdateCommands.FG,
                    [ThemeUpdateVars.OKAY if self.data['DATABASE']['data_recv']['read']['CONFIGURATION']['acc'] else ThemeUpdateVars.ERROR]
                ]

                self.data['CONFIG_INF:<DB> _copy'] = copy.deepcopy(self.data['DATABASE']['data_recv']['read'])
                self.data['CONFIG_INF:<DB>'] = copy.deepcopy(self.data['DATABASE']['data_recv']['read'])

            # Configure all inputs
            self.config_acc_status.config(text= "The administrator allows for custom quiz configuration." if self.data['CONFIG_INF:<DB>']['CONFIGURATION']['acc'] else \
                                                  "The administrator does not allow for custom quiz configuration.")
            _DB = self.data['CONFIG_INF:<DB>']
            _ST = {True: tk.NORMAL, False: tk.DISABLED}[_DB['CONFIGURATION']['acc']]
            self.config_qd_poa_P.config(text='Subset' if _DB['CONFIGURATION']['poa'] == 'p' else 'All', command=self._config_qd_poa_switch, state=_ST)

            if _DB['CONFIGURATION']['poa'] == 'p':
                self.config_qd_ssd.set(str(_DB['CONFIGURATION']['ssd']))
                self.config_qd_ssd_field.configure(state=_ST)
            else:
                self.config_qd_ssd.set('Set the above to "Subset" to modify.')
                self.config_qd_ssd_field.configure(state=tk.DISABLED)

            self.config_rqo_enb.config(text='Randomized' if _DB['CONFIGURATION']['rqo'] else 'Not Randomized', command=self._config_qd_rqo_switch, state=_ST)

            self.config_pc_enb.config(text='Enabled' if _DB['CONFIGURATION']['dpi'] else 'Disabled', state=_ST, command=self._config_pc_switch)
            if _DB['CONFIGURATION']['dpi']:
                self.config_pc_a2d.set(str(_DB['CONFIGURATION']['a2d']))
                self.config_pc_a2d_field.configure(state=_ST)
            else:
                self.config_pc_a2d.set('Set the above to "Enabled" to modify.')
                self.config_pc_a2d_field.configure(state=tk.DISABLED)

        def check_config_frame() -> Tuple[bool, int, List[str]]:
            errs = []

            nce, ce, _= self._check_db(self.data['CONFIG_INF:<DB>'])
            if nce:
                errs.extend(['Configuration error.', *ce])

            return len(errs) == 0, len(errs), errs

        def setup_summary_frame() -> None:
            self.login_frame.pack_forget()
            self.config_frame.pack_forget()
            self.summary_frame.pack(fill=tk.BOTH, expand=True)
            self.title_info.config(text=f'Logged in as {" ".join([self.first_name.get(), self.last_name.get()]).title()} ({self.ID.get()})', anchor=tk.W, justify=tk.LEFT)

            if not self.data.get('flag_SetupSummaryElements', False):
                self.summ_ttl.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
                self.summ_ttl.config(text='Summary', anchor=tk.W, justify=tk.LEFT)

                self.summ_txt.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY)
                self.summ_txt.delete('1.0', tk.END)

                self.data['flag_SetupSummaryElements'] = True

            if not self.data.get('flag_SetupSummaryUpdateRequests', False):
                TUC, TUV = ThemeUpdateCommands, ThemeUpdateVars

                self.update_requests[gsuid()] = [self.summ_ttl, TUC.BG, [TUV.BG]]
                self.update_requests[gsuid()] = [self.summ_ttl, TUC.FG, [TUV.ACCENT]]
                self.update_requests[gsuid()] = [self.summ_ttl, TUC.FONT, [TUV.TITLE_FONT_FACE, TUV.FONT_SIZE_TITLE]]

                self.update_requests[gsuid()] = [self.summary_frame, TUC.BG, [TUV.BG]]

                self.late_update_requests[self.summ_txt] = [
                    [
                        TUC.CUSTOM,
                        [
                            lambda *args: cast(CustomText, args[0]).auto_size(),
                            self.summ_txt
                        ]
                    ],
                    [
                        TUC.CUSTOM,
                        [
                            lambda *args, **kwargs: cast(CustomText, args[5]).config(
                                bg=args[0], fg=args[1], insertbackground=args[2], font=(args[3], args[4]),
                                relief=tk.GROOVE, selectbackground=args[2], selectforeground=args[0]
                            ),
                            ThemeUpdateVars.BG, ThemeUpdateVars.FG, ThemeUpdateVars.ACCENT,
                            ThemeUpdateVars.ALT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_MAIN,
                            self.summ_txt
                        ]
                    ]
                ]

            self.summ_txt.config(state=tk.NORMAL)

            _conf = self.data['CONFIG_INF:<DB>']['CONFIGURATION']

            self.summ_txt.delete('1.0', 'end')

            self.summ_txt.auto_size()
            self.summ_txt.setup_color_tags(self.theme_update_map)
            self.summ_txt.insert('end', 'Your Information:\n', '<accent>')
            self.summ_txt.insert('end', '\t\u2022 Name: ')
            self.summ_txt.insert('end', f'{self.last_name.get()}, {self.first_name.get()}\n', '<accent>')
            self.summ_txt.insert('end', f'\t\u2022 ID: ')
            self.summ_txt.insert('end', f'{self.ID.get()}\n\n', '<accent>')

            self.summ_txt.insert('end', f'Configuration:\n', '<accent>')
            self.summ_txt.insert('end', '\t\u2022 Question subsampling: ')
            self.summ_txt.insert('end', 'Prompt with %s\n' % ('all questions.' if _conf['poa'] == 'a' else f'1/{_conf["ssd"]} of the questions.'), '<accent>')

            self.summ_txt.insert('end', '\t\u2022 Question ordering: ')
            self.summ_txt.insert('end', '%sandomize question order.\n' % ('R' if _conf['rqo'] else 'Do not r'), '<accent>')

            self.summ_txt.insert('end', '\t\u2022 Erroneous response entry: ')
            self.summ_txt.insert('end', 'Penalties disabled.' if not _conf['dpi'] else f"Deduct {_conf['a2d']} points per incorrect response.\n", '<accent>')

            self.summ_txt.insert('end', '\nNote that this configuration will be reported to the quiz administrator along with your score.', '<gray_fg>')
            self.summ_txt.config(state=tk.DISABLED)

        def check_summary_frame() -> Tuple[bool, int, List[str]]:
            return True, 0, []

        page_map = {
            self.LOGIN_PAGE: {
                'IKey': self.login_frame_gsuid,
                'ParentFrame': self.login_frame,
                'Fn1': setup_login_frame,
                'Fn0': check_login_frame,
            },
            self.CONFIGURATION_PAGE: {
                'IKey': self.login_frame_gsuid,
                'ParentFrame': self.config_frame,
                'Fn1': setup_config_frame,
                'Fn0': check_config_frame,
            },
            self.SUMMARY_PAGE: {
                'IKey': self.login_frame_gsuid,
                'ParentFrame': self.summary_frame,
                'Fn1': setup_summary_frame,
                'Fn0': check_summary_frame,
            }
        }

        log(LoggingLevel.INFO, f'Current frame: {page_index} - {page_map[page_index]["IKey"]}. Running checks')

        Fn0, Fn1 = page_map[self.current_page]['Fn0'], page_map[page_index]['Fn1']

        if self.current_page >= page_index:
            passed, n_errors, error = True, 0, []  # type: ignore

        else:
            passed, n_errors, errors = Fn0()  # type: ignore

        if not passed:
            log(LoggingLevel.ERROR, f'Failed to fulfill page change request; N Errors: {n_errors}; {errors}')
            self.enable_all_inputs()
            self.set_error_text(errors[0], 5)
            return False

        log(LoggingLevel.INFO, f'Request made to change page to {page_index} (ID): {page_map[page_index]["IKey"]} (GSUID)')

        Fn1()  # type: ignore
        self.current_page = page_index
        self.enable_all_inputs()

        # self.next_frame.config(state=tk.NORMAL if not (self.current_page == self.SUMMARY_PAGE) else tk.DISABLED)
        self.prev_frame.config(state=tk.NORMAL if not (self.current_page == self.LOGIN_PAGE) else tk.DISABLED)

        if self.current_page == self.SUMMARY_PAGE:
            self.next_frame.config(command=self._start_quiz, text="Start Quiz")
        else:
            self.next_frame.config(command=self.proceed, text="Next Step \u2b9e")
        
        self.update_ui()

        return True

    def _config_a2d_mod(self, *_: Any) -> None:
        if self.current_page != self.CONFIGURATION_PAGE:
            return

        if not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['dpi']:
            return

        try:
            d_set = self.config_pc_a2d.get().strip()
            p = True

            if d_set in ('', None):
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = 1
                return

            if not d_set.isnumeric():
                fx = re.findall(r'[0-9]{1,2}', self.config_pc_a2d.get().strip())
                self.config_pc_a2d.set(fx[0] if fx else '1')
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = fx[0] if fx else 1
                p = False

            if p and not 1 <= len(d_set) <= 2:
                if len(d_set) == 0:
                    self.config_pc_a2d.set('1')
                    self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = 1

                else:
                    fx = re.findall(r'[0-9]{1,2}', d_set)
                    self.config_pc_a2d.set(fx[0] if fx else '1')
                    self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = fx[0] if fx else 1

                p = False

            assert p, 'Penalty must be an integer between 1 and 10'

            f = float(d_set)
            if not (1 <= f <= 10):
                self.config_pc_a2d.set('1' if f < 1 else '10')
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = '1' if f < 1 else '10'
                assert False, 'Penalty must be between 1 and 10'

            if f != int(f):
                self.config_pc_a2d.set(str(int(f)))
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = int(f)
                assert False, 'Penalty cannot contain a decimal'

            self.data['CONFIG_INF:<DB>']['CONFIGURATION']['a2d'] = int(f)

        except Exception as E:
            self.set_error_text(str(E), 3)
            return

    def _config_ssd_mod(self, *_: Any) -> None:
        if self.current_page != self.CONFIGURATION_PAGE:
            return

        if self.data['CONFIG_INF:<DB>']['CONFIGURATION']['poa'] != 'p':
            return

        try:
            d_set = self.config_qd_ssd.get().strip()
            p = True

            if d_set in ('', None):
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = 1
                # self.config_qd_ssd.set('1')
                return

            if not d_set.isnumeric():
                fx = re.findall(r'[0-9]{1,2}', self.config_qd_ssd.get().strip())
                self.config_qd_ssd.set(fx[0] if fx else '1')
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = fx[0] if fx else 1
                p = False

            if p and not 1 <= len(d_set) <= 2:
                if len(d_set) == 0:
                    self.config_qd_ssd.set('1')
                    self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = 1

                else:
                    fx = re.findall(r'[0-9]{1,2}', d_set)
                    self.config_qd_ssd.set(fx[0] if fx else '1')
                    self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = fx[0] if fx else 1

                p = False

            assert p, 'Subsample divisor must be an integer between 1 and 10'

            f = float(d_set)
            if not (1 <= f <= 10):
                self.config_qd_ssd.set('1' if f < 1 else '10')
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = '1' if f < 1 else '10'
                assert False, 'Subsample divisor must be between 1 and 10'

            if f != int(f):
                self.config_qd_ssd.set(str(int(f)))
                self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = int(f)
                assert False, 'Subsample divisor cannot contain a decimal'

            self.data['CONFIG_INF:<DB>']['CONFIGURATION']['ssd'] = int(f)

        except Exception as E:
            self.set_error_text(str(E), 3)
            return

    def _config_pc_switch(self) -> None:
        assert isinstance(self.data.get('CONFIG_INF:<DB>'), dict)

        self.data['CONFIG_INF:<DB>']['CONFIGURATION']['dpi'] = not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['dpi']
        log(LoggingLevel.WARNING, f'QuizzingForm._CONFIG_QD_POA_SWITCH: Switched "DPI" state to "{self.data["CONFIG_INF:<DB>"]["CONFIGURATION"]["dpi"]}"')
        self.setup_page(self.CONFIGURATION_PAGE)

    def _config_qd_poa_switch(self) -> None:
        assert isinstance(self.data.get('CONFIG_INF:<DB>'), dict)

        self.data['CONFIG_INF:<DB>']['CONFIGURATION']['poa'] = 'p' if self.data['CONFIG_INF:<DB>']['CONFIGURATION']['poa'] == 'a' else 'a'
        log(LoggingLevel.WARNING, f'QuizzingForm._CONFIG_QD_POA_SWITCH: Switched "POA" mode to "{self.data["CONFIG_INF:<DB>"]["CONFIGURATION"]["poa"]}"')
        self.setup_page(self.CONFIGURATION_PAGE)

    def _config_qd_rqo_switch(self) -> None:
        assert isinstance(self.data.get('CONFIG_INF:<DB>'), dict)

        self.data['CONFIG_INF:<DB>']['CONFIGURATION']['rqo'] = not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['rqo']
        log(LoggingLevel.WARNING, f'QuizzingForm._CONFIG_QD_POA_SWITCH: Switched "RQO" state to "{self.data["CONFIG_INF:<DB>"]["CONFIGURATION"]["rqo"]}"')
        self.setup_page(self.CONFIGURATION_PAGE)

    def run(self) -> None:
        global APP_TITLE

        self.root.resizable(False, False)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.iconbitmap(qa_functions.Files.QF_ico)
        self.root.title(APP_TITLE)
        self.root.geometry('%s+%s' % ('x'.join(str(d) for d in self.window_size), '+'.join(str(d) for d in self.screen_pos)))

        self.update_requests['QFRoot'] = [self.root, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleBox'] = [self.title_box, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleBG'] = [self.title_txt, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleFG'] = [self.title_txt, ThemeUpdateCommands.FG, [ThemeUpdateVars.ACCENT]]
        self.update_requests['QFTitleFont'] = [self.title_txt, ThemeUpdateCommands.FONT, [ThemeUpdateVars.TITLE_FONT_FACE, ThemeUpdateVars.FONT_SIZE_XL_TITLE]]
        self.update_requests['QFTitleImgBG'] = [self.title_img, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleInfoBG'] = [self.title_info, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests['QFTitleInfoFG'] = [self.title_info, ThemeUpdateCommands.FG, [ThemeUpdateVars.GRAY]]
        self.update_requests['QFTitleInfoFont'] = [self.title_info, ThemeUpdateCommands.FONT, [ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL]]

        self.title_info.pack(fill=tk.X, expand=False, padx=self.padX, pady=self.padY, side=tk.BOTTOM)
        self.title_box.pack(fill=tk.X, expand=False, pady=self.padY, side=tk.TOP)
        self.title_img.config(justify=tk.CENTER, anchor=tk.E, width=self.img_size[0], height=self.img_size[1])
        self.title_img.config(image=cast(str, self.svgs['qf']))
        self.title_img.pack(fill=tk.X, expand=False, padx=(self.padX, self.padX / 8), pady=self.padY, side=tk.LEFT)
        self.title_txt.config(text='Quizzing Form', anchor=tk.W, justify=tk.LEFT)
        self.title_txt.pack(fill=tk.X, expand=False, padx=(self.padX / 8, self.padX), pady=self.padY, side=tk.LEFT)

        self.main_frame.pack(fill=tk.BOTH, expand=True, pady=self.padY)
        self.nav_btn_frame.pack(fill=tk.X, expand=False, side=tk.BOTTOM)

        self.error_label.pack(fill=tk.X, expand=False, padx=self.padX, pady=(self.padY, 0), side=tk.BOTTOM)

        self.next_frame.pack(fill=tk.X, expand=True, side=tk.RIGHT)
        self.prev_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

        self.inputs.extend([self.next_frame, self.prev_frame, self.first_name_field, self.last_name_field, self.select_database_btn, self.ID_field])
        self.update_requests[gsuid()] = [self.main_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gsuid()] = [self.nav_btn_frame, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]
        self.update_requests[gsuid()] = [self.error_label, ThemeUpdateCommands.CUSTOM, [
            lambda *args: self.error_label.config(bg=args[0], fg=args[1], font=(args[2], args[3]), wraplength=(args[4] - args[5])),
            ThemeUpdateVars.BG, ThemeUpdateVars.ERROR, ThemeUpdateVars.DEFAULT_FONT_FACE, ThemeUpdateVars.FONT_SIZE_SMALL,
            ('<LOOKUP>', 'root_width'), ('<LOOKUP>', 'padX')
        ]]
        self.update_requests[gsuid()] = [self.right_cont, ThemeUpdateCommands.BG, [ThemeUpdateVars.BG]]

        self.update_ui()

        # Start the app
        assert self.setup_page(self.LOGIN_PAGE), 'failed to setup LOGIN page'

    def set_error_text(self, text: str, timeout_seconds: float) -> None:
        assert 1 <= timeout_seconds <= 60, 'Timeout delay must be between 1 and 60 seconds (incl.)'

        text = f'\u26a0 {text.strip()}'
        self.error_label.config(text=text)

        # Start timeout
        K = 'Jobs.SetErrorText.Timers'
        _tasks = self.active_jobs.get(K, {})
        for n, _task in _tasks.items():
            if 'timers' not in n.lower(): continue
            self.root.after_cancel(_task)

        uid = gsuid('SET.Timers')
        _task = self.root.after(int(timeout_seconds*1000), lambda: self._clear_error_text(uid))
        self.active_jobs[K] = {uid: _task}

    def _clear_error_text(self, timer_uid: Optional[str] = None) -> None:
        # Timer handler
        if isinstance(timer_uid, str) and timer_uid in self.active_jobs.get('Jobs.SetErrorText.Timers', {}).keys():
            try: self.root.after_cancel(self.active_jobs['Jobs.SetErrorText.Timers'][timer_uid])
            except Exception as _: pass
            self.active_jobs['Jobs.SetErrorText.Timers'].pop(timer_uid)
        if len(self.error_label.cget('text').strip()) <= 0: return

        self.data['GLOBAL'] = self.data.get('GLOBAL', {'Attr_'})
        self.data['GLOBAL']['Attr_'] = self.data['GLOBAL'].get('Attr_', {})
        self.data['GLOBAL']['Attr_']['Animating.PauseClose.Set'] = True

        # Fade out
        gradient = ColorFunctions.fade(self.theme_update_map[ThemeUpdateVars.ERROR].color, self.theme_update_map[ThemeUpdateVars.BG].color)  # type: ignore
        for stage in gradient:
            self.error_label.config(fg=stage)
            self.error_label.update()

            for _ in range(int(3e5)): continue  # type: ignore
            if not len(self.error_label.cget('text')): break

        self.error_label.config(text='', fg=self.theme.error.color)  # type: ignore

        self.data['GLOBAL']['Attr_']['Animating.PauseClose.Set'] = False

    def _qz_set_error_text(self, text: str, timeout_seconds: float) -> None:
        assert 1 <= timeout_seconds <= 60, 'Timeout delay must be between 1 and 60 seconds (incl.)'

        text = f'\u26a0 {text.strip()}'
        self.quiz_err_lbl.config(text=text)

        # Start timeout
        K = 'Jobs.QZSetErrorText.Timers'
        _tasks = self.active_jobs.get(K, {})
        
        for n, _task in _tasks.items():
            if 'timers' not in n.lower(): continue
            self.root.after_cancel(_task)

        uid = gsuid('SET.Timers')
        _task = self.root.after(int(timeout_seconds*1000), lambda: self._qz_clear_error_text(uid))
        self.active_jobs[K] = {uid: _task}

    def _qz_clear_error_text(self, timer_uid: Optional[str] = None) -> None:
        # Timer handler
        if isinstance(timer_uid, str) and timer_uid in self.active_jobs.get('Jobs.QZSetErrorText.Timers', {}).keys():
            try: self.root.after_cancel(self.active_jobs['Jobs.QZSetErrorText.Timers'][timer_uid])
            except Exception as _: pass
            self.active_jobs['Jobs.QZSetErrorText.Timers'].pop(timer_uid)
            
        if len(self.quiz_err_lbl.cget('text').strip()) <= 0: return

        self.data['GLOBAL'] = self.data.get('GLOBAL', {'Attr_'})
        self.data['GLOBAL']['Attr_'] = self.data['GLOBAL'].get('Attr_', {})
        self.data['GLOBAL']['Attr_']['Animating.PauseClose.Set'] = True

        # Fade out
        gradient = ColorFunctions.fade(self.theme_update_map[ThemeUpdateVars.ERROR].color, self.theme_update_map[ThemeUpdateVars.BG].color)  # type: ignore
        for stage in gradient:
            self.quiz_err_lbl.config(fg=stage)
            self.quiz_err_lbl.update()

            for _ in range(int(3e5)): continue  # type: ignore
            if not len(self.quiz_err_lbl.cget('text')): break

        self.quiz_err_lbl.config(text='', fg=self.theme.error.color)  # type: ignore

        self.data['GLOBAL']['Attr_']['Animating.PauseClose.Set'] = False
    
    def _ent_size_update(self) -> None:
        for _i in self.inputs:
            if isinstance(_i, ttk.Entry):
                _i.configure(font=(self.theme.font_face, self.theme.font_main_size), style='My.TEntry')

    def update_ui(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.load_theme()

        for task_uid, task in self.active_jobs.get('Jobs.SetErrorText.Timers', {}).items():
            try:
                self.root.after_cancel(task)
            except Exception as E:
                log(LoggingLevel.WARNING, f'Failed to cancel Jobs.SetErrorText.Timer {task_uid}: {E} {str(E)}')

        self._clear_error_text()

        self.root.after(0, self._ent_size_update)

        self.window_size = [self.root.winfo_width(), self.root.winfo_height()]
        self.screen_pos = [self.root.winfo_x(), self.root.winfo_y()]

        def tr(com: Any, *a: Any, **k: Any) -> Tuple[bool, str]:
            try:
                return True, com(*a, **k)
            except Exception as E:
                return False, f"{E.__class__.__name__}({E})"

        def log_error(com: str, el: tk.Widget, reason: str, ind: int) -> None:
            log(LoggingLevel.ERROR, f'[UPDATE_UI] Failed to apply command \'{com}\' to {el}: {reason} ({ind}) <{elID}>')

        def log_norm(com: str, el: tk.Widget) -> None:
            log(LoggingLevel.DEVELOPER, f'[UPDATE_UI] Applied command \'{com}\' to {el} successfully <{elID}>')

        for elID, (_e, _c, _a) in self.update_requests.items():
            command = cast(ThemeUpdateCommands, _c)
            element = cast(tk.Button, _e)
            args = cast(List[Any], _a)

            lCommand = [False, '', -1]
            cleaned_args = []

            if 'logText' in elID:
                print('UPDATE_UI', 'LOG_TEXT', args)

            for index, arg in enumerate(args):
                cleaned_arg = arg if arg not in ThemeUpdateVars.__members__.values() else self.theme_update_map[arg]

                if isinstance(arg, tuple):
                    if len(arg) >= 2:
                        if arg[0] == '<EXECUTE>':
                            if 'logText' in elID:
                                print('UPDATE_UI LOG_TEXT exec :: ', end='')

                            ps, res = (tr(arg[1]) if len(args) == 2 else tr(arg[1], arg[2::]))
                            if ps:
                                cleaned_arg = res
                                if 'logText' in elID:
                                    print('SUCCESS', f'"{cleaned_arg}"')
                            else:
                                if 'logText' in elID:
                                    print('ERROR')
                                log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

                        elif arg[0] == '<LOOKUP>':
                            if 'logText' in elID:
                                print('UPDATE_UI LOG_TEXT look :: ', end='')

                            rs_b: int = cast(int, {
                                'padX': self.padX,
                                'padY': self.padY,
                                'root_width': self.root.winfo_width(),
                                'root_height': self.root.winfo_height(),
                                'uid': elID,
                                'UI': self,
                                'SELF': element
                            }.get(cast(str, arg[1])))

                            if rs_b is not None:
                                cleaned_arg = rs_b
                                if 'logText' in elID:
                                    print('SUCCESS', f'"{cleaned_arg}"')
                            else:
                                if 'logText' in elID:
                                    print('ERROR')
                                log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

                cleaned_args.append(cleaned_arg)

                if isinstance(cleaned_args[index], qa_functions.HexColor):
                    cleaned_args[index] = cleaned_args[index].color

            if 'logArgs' in elID:
                print('UPDATE_UI LOG_ARGS', cleaned_args)

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
            'MyLG.TButton',
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
            'MyLG.TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        cb_fg = qa_functions.qa_colors.Functions.calculate_more_contrast(qa_functions.HexColor("#000000"), qa_functions.HexColor("#ffffff"), self.theme.background).color

        self.ttk_style.configure(
            'My.Contrast.TButton',
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
            'My.Contrast.TButton',
            background=[('active', cb_fg), ('disabled', self.theme.background.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.gray.color), ('readonly', self.theme.background.color)]
        )

        del cb_fg

        self.ttk_style = qa_functions.TTKTheme.configure_scrollbar_style(self.ttk_style, self.theme, self.theme.accent.color, 'Admin')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_main_size)
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_large_size, 'MyLarge')
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, self.theme.font_small_size, 'MySmall')

        self.ttk_style.configure(
            'My.Active.TButton',
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
            'My.Active.TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.accent.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'My.Accent2.TButton',
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
            'My.Accent2.TButton',
            background=[('active', self.theme.warning.color), ('disabled', self.theme.warning.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'My.Accent2LG.TButton',
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
            'My.Accent2LG.TButton',
            background=[('active', self.theme.warning.color), ('disabled', self.theme.warning.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'My.ActiveLG.TButton',
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
            'My.ActiveLG.TButton',
            background=[('active', self.theme.accent.color), ('disabled', self.theme.accent.color), ('readonly', self.theme.gray.color)],
            foreground=[('active', self.theme.background.color), ('disabled', self.theme.background.color), ('readonly', self.theme.background.color)]
        )

        self.ttk_style.configure(
            'My.TSeparator',
            background=self.theme.gray.color
        )

        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, pref='MyQuizzingApp')  # type: ignore
        self.ttk_style = qa_functions.TTKTheme.configure_entry_style(self.ttk_style, self.theme, pref='MyQuizzingApp')  # type: ignore

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
                                    log(LoggingLevel.ERROR, f'Failed to run `exec_replace` routine in late_update: {res}:: {element}')

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
                                    log(LoggingLevel.ERROR, f'Failed to run `lookup_replace` routine in late_update: KeyError({arg[1]}):: {element}')

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
                lambda *args: log(LoggingLevel.WARNING, f'{args[0]} : (from ButtonFormatter) !Btn'),
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
                    lambda *args: log(LoggingLevel.WARNING, f'{args[0]} : (from LabelFormatter) !Lbl, !LblF'),
                    ('<LOOKUP>', 'uid')
                ]
            )
        ]

    def load_theme(self) -> None:
        self.theme = qa_functions.qa_theme_loader.Load.auto_load_pref_theme()
        assert self.theme.check(), 'Loaded theme does not comply with all basic restrictions (err. 0x01)'

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
            ThemeUpdateVars.TITLE_FONT_FACE: self.theme.title_font_face,
        }

    def load_png(self) -> None:
        i = Image.open(self.img_path)
        i = i.resize(self.img_size, Image.ANTIALIAS)
        self.svgs['qf'] = ImageTk.PhotoImage(i)

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
                log(LoggingLevel.ERROR, f'admt::load_png - Failed to load requested svg ({src}): {E}')

    def disable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        for btn in self.inputs:
            if btn not in exclude:
                btn.config(state=tk.DISABLED)

    def enable_all_inputs(self, *exclude: Tuple[Union[tk.Button, ttk.Button], ...]) -> None:
        if self.current_page == self.LOGIN_PAGE:
            exclude = (*exclude, self.prev_frame)  # type: ignore

        # elif self.current_page == self.SUMMARY_PAGE:
        #     exclude = (*exclude, self.next_frame)  # type: ignore

        if self.current_page == self.CONFIGURATION_PAGE:
            if (self.data['CONFIG_INF:<DB>']['CONFIGURATION']['poa'] == 'a') or not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['acc']:
                exclude = (*exclude, self.config_qd_ssd_field)  # type: ignore

            if not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['dpi'] or not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['acc']:
                exclude = (*exclude, self.config_pc_a2d_field)  # type: ignore

            if not self.data['CONFIG_INF:<DB>']['CONFIGURATION']['acc']:
                exclude = (*exclude, self.config_rqo_enb, self.config_pc_enb, self.config_qd_poa_P)  # type: ignore

        for btn in self.inputs:
            if btn not in exclude:
                btn.config(state=tk.NORMAL)

        self.update_ui()


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

    data = f"{AppLogColors.QUIZZING_FORM}{AppLogColors.EXTRA}[QUIZZING_FORM]{ANSI.RESET} {data}"

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


def RunApp(instance_class: object, default_shell: Union[tk.Tk, tk.Toplevel], **kwargs: Any) -> tk.Toplevel:
    transfer_log_info(qa_prompts)

    qa_functions.qa_theme_loader.THEME_LOADER_ENABLE_DEV_DEBUGGING = DEBUG_DEV_FLAG

    subprocess.call('', shell=True)
    if os.name == 'nt':  # Only if we are running on Windows
        k = windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)

    log(LoggingLevel.ERROR, '[USER CHECK] Error message logging available')
    log(LoggingLevel.SUCCESS, '[USER CHECK] Success message logging available')
    log(LoggingLevel.INFO, '[USER CHECK] Info message logging available')
    log(LoggingLevel.WARNING, '[USER CHECK] Warning message logging available')
    log(LoggingLevel.DEBUG, '[USER CHECK] Debug message logging available')
    log(LoggingLevel.DEVELOPER, '[USER CHECK] Developer console logging available')

    ui_root = tk.Toplevel()
    _UI(ui_root, ic=instance_class, ds=default_shell, **kwargs)

    return ui_root


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


def transfer_log_info(script: Any) -> None:
    global LOGGER_AVAIL, LOGGER_FUNC, LOGGING_FILE_NAME, DEBUG_NORM, DEBUG_DEV_FLAG

    script.LOGGER_AVAIL = LOGGER_AVAIL  # type: ignore
    script.LOGGER_FUNC = LOGGER_FUNC   # type: ignore
    script.LOGGING_FILE_NAME = LOGGING_FILE_NAME    # type: ignore
    script.DEBUG_NORM = DEBUG_NORM  # type: ignore
    script.DEBUG_DEV_FLAG = DEBUG_DEV_FLAG  # type: ignore
