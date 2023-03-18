import sys, qa_functions, os, PIL, subprocess, tkinter as tk, random, qa_files, json, hashlib
import traceback

from . import qa_prompts
from .qa_prompts import gsuid, configure_scrollbar_style, configure_entry_style
from qa_functions.qa_enum import ThemeUpdateCommands, ThemeUpdateVars, LoggingLevel
from qa_functions.qa_std import ANSI, AppLogColors
from qa_functions.qa_custom import HexColor
from qa_functions.qa_colors import Functions as ColorFunctions
from threading import Thread, Timer
from tkinter import ttk
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageTk
from io import BytesIO
from ctypes import windll
from typing import *
from tkinter import filedialog as tkfld
from . import qa_adv_forms as qa_forms


AUTO = 3
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
        wd_h = 550 if 550 <= self.screen_dim[1] else self.screen_dim[1]
        self.window_size = [wd_w, wd_h]
        self.screen_pos = [
            int(self.screen_dim[0] / 2 - self.window_size[0] / 2),
            int(self.screen_dim[1] / 2 - self.window_size[1] / 2)
        ]

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
        [self.LOGIN_PAGE, self.CONFIGURATION_PAGE, self.SUMMARY_PAGE] = range(3)
        for i in range(3): self.screen_data[i] = {}
        self.current_page = self.LOGIN_PAGE

        self.main_frame = tk.Frame(self.root)
        self.login_frame = tk.Frame(self.main_frame)
        self.config_frame = tk.Frame(self.main_frame)
        self.summary_frame = tk.Frame(self.main_frame)

        self.login_frame_gsuid = gsuid('QuizzingForm.PageMap<GSUID>')
        self.config_frame_gsuid = gsuid('QuizzingForm.PageMap<GSUID>')
        self.summary_frame_gsuid = gsuid('QuizzingForm.PageMap<GSUID>')

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
        self.first_name_field = ttk.Entry(self.ID_first_name_frame, textvariable=self.first_name, style='MyQuizzingApp.QFormLogin.TEntry')
        self.last_name_field = ttk.Entry(self.ID_last_name_frame, textvariable=self.last_name, style='MyQuizzingApp.QFormLogin.TEntry')
        self.ID_lbl = tk.Label(self.ID_cont, text='Unique ID Number')
        self.ID_field = ttk.Entry(self.ID_cont, textvariable=self.ID, style='MyQuizzingApp.QFormLogin.TEntry')

        self.database_frame = tk.LabelFrame(self.right_cont, text='Database Selection')
        self.select_database_btn = ttk.Button(self.database_frame, style='TButton')

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

        for _, timer in self.active_jobs.get('Jobs.SetErrorText.Timers', {}).items():
            cast(Timer, timer).cancel()

        sys.stdout.write("qf - _UI.close")
        self.ic.shell = self.ds
        self.ic.shell_ready = False

        self.root.after(0, self.root.quit)

    def proceed(self) -> None:
        if self.current_page == self.SUMMARY_PAGE:
            return

        self.setup_page(self.current_page + 1)

    def go_back(self) -> None:
        if self.current_page == self.LOGIN_PAGE:
            return

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
            assert _c1 == b'%qaQuiz', f'SET_DATABASE.ERR (strict) 4: _c1 failure'
            _dec1 = cast(bytes, _dec1)[:-7]

            # iii) Load file sections
            # AND iv) Check hashes
            # AND v) decrypt body
            _dec2_bytes, _dec2_str = cast(Tuple[bytes, str], qa_files.load_file(qa_functions.FileType.QA_QUIZ, _dec1))
            assert len(_dec2_str.strip()) > 0, 'SET_DATABASE.ERR (strict) 5: ~_dec2_str__LEN'

            # convert _dec2_str to dict
            _DB: Dict[str, Any] = json.loads(_dec2_str)  # type: ignore

            # vi) Check flag
            assert 'QZDB' in _DB['DB']['FLAGS'], 'SET_DATABASE.ERR (strict) 6: ~FLAG_QZDB'

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

                log(LoggingLevel.SUCCESS, 'SET_DATABASE: Authenticated')

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
                'verified': True
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
                style="Active.TButton"
            )

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
                log(LoggingLevel.WARNING, f'QuizzingForm.WARNINGS.SETUP_PAGE.CHECK_LOGIN_PAGE: (0x03)')

            elif not self.data['DATABASE']['verified']:
                N, e, _ = self._check_db(self.data['DATABASE']['data_recv']['read'])
                if N:
                    errs.append('Invalid / corrupt data found in selected database. Please try again.')
                    log(LoggingLevel.WARNING, f'QuizzingForm.WARNINGS.SETUP_PAGE.CHECK_LOGIN_PAGE: (0x04)')
                    for index, err in enumerate(e):
                        log(LoggingLevel.ERROR, f'\t{index}) {err}')

            else:
                log(LoggingLevel.INFO, 'QuizzingForm.INFO.SETUP_PAGE.CHECK_LOGIN_PAGE: db already verified')

            return len(errs) == 0, len(errs), errs

        def setup_config_frame() -> None:
            self.login_frame.pack_forget()
            self.summary_frame.pack_forget()
            self.config_frame.pack(fill=tk.BOTH, expand=True)
            self.title_info.config(text=f'Logged in as {" ".join([self.first_name.get(), self.last_name.get()]).title()} ({self.ID.get()})', anchor=tk.W, justify=tk.LEFT)

        def check_config_frame() -> Tuple[bool, int, List[str]]:
            return False, 1, ['Uh oh. It looks like you have just found something that is not programmed yet!']

        def setup_summary_frame() -> None:
            self.login_frame.pack_forget()
            self.config_frame.pack_forget()
            self.summary_frame.pack(fill=tk.BOTH, expand=True)
            self.title_info.config(text=f'Logged in as {" ".join([self.first_name.get(), self.last_name.get()]).title()} ({self.ID.get()})', anchor=tk.W, justify=tk.LEFT)

        def check_summary_frame() -> Tuple[bool, int, List[str]]:
            return False, 1, ['Uh oh. It looks like you have just found something that is not programmed yet!']

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

        self.next_frame.config(state=tk.NORMAL if not (self.current_page == self.SUMMARY_PAGE) else tk.DISABLED)
        self.prev_frame.config(state=tk.NORMAL if not (self.current_page == self.LOGIN_PAGE) else tk.DISABLED)

        self.update_ui()

        return True

    def run(self) -> None:
        global APP_TITLE

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

        self.inputs.extend([self.next_frame, self.prev_frame])
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
        timers = self.active_jobs.get(K, {})
        for _, timer in timers.items():
            timer.cancel()

        uid = gsuid('SET.Timers')
        timer = Timer(timeout_seconds, lambda: self._clear_error_text(uid))
        self.active_jobs[K] = {uid: timer}
        timer.start()

    def _clear_error_text(self, timer_uid: Optional[str] = None) -> None:
        if len(self.error_label.cget('text').strip()) <= 0: return

        self.data['GLOBAL'] = self.data.get('GLOBAL', {'Attr_'})
        self.data['GLOBAL']['Attr_'] = self.data['GLOBAL'].get('Attr_', {})
        self.data['GLOBAL']['Attr_']['Animating.PauseClose.Set'] = True

        # Fade out
        gradient = ColorFunctions.fade(self.theme_update_map[ThemeUpdateVars.ERROR].color, self.theme_update_map[ThemeUpdateVars.BG].color)  # type: ignore
        for stage in gradient:
            self.error_label.config(fg=stage)

            for i in range(int(3e5)): continue   # <.1s delay
            if not len(self.error_label.cget('text')): break

        self.error_label.config(text='', fg=self.theme_update_map[ThemeUpdateVars.ERROR].color)  # type: ignore

        self.data['GLOBAL']['Attr_']['Animating.PauseClose.Set'] = False

        # Timer handler
        if isinstance(timer_uid, str) and timer_uid in self.active_jobs.get('Jobs.SetErrorText.Timers', {}).keys():
            self.active_jobs['Jobs.SetErrorText.Timers'].pop(timer_uid)

    def update_ui(self, *_0: Optional[Any], **_1: Optional[Any]) -> None:
        self.load_theme()

        for timer_uid, timer in self.active_jobs.get('Jobs.SetErrorText.Timers', {}).items():
            try:
                timer.cancel()
            except Exception as E:
                log(LoggingLevel.WARNING, f'Failed to cancel Jobs.SetErrorText.Timer {timer_uid}: {E} {str(E)}')

        self._clear_error_text()

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

        configure_entry_style(self.ttk_style, self.theme, cast(Union[float, int], self.theme_update_map[ThemeUpdateVars.FONT_SIZE_MAIN]), pref='MyQuizzingApp.QFormLogin')

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
