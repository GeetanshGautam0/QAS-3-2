import json, hashlib, sys, traceback, qa_files, os
from tkinter import ttk
from tkinter import messagebox
from . import qa_custom
from . import qa_file_handler
from . import qa_std
from . import qa_enum
from . import qa_info
from typing import *


THEME_LOADER_ENABLE_DEV_DEBUGGING = False


def _reset_pref() -> None:
    direc = f"{qa_info.App.appdata_dir}\\{qa_info.Files.ad_theme_folder}"
    fp = f"{direc}\\{qa_info.Files.ThemePrefFile}"

    if not os.path.exists(direc):
        os.makedirs(direc)

    default_data = {
        't': {
            'file': "<DEFAULT>",
            'theme': "<DEFAULT>",
            'display_name': "<DEFAULT>"
        }
    }

    with open(fp, 'w') as pref_file:
        pref_file.write(json.dumps(default_data, indent=4))
        pref_file.close()


def set_pref(file: str, theme: str, display_name: str) -> None:
    file = _save_prep_path(file)

    direc = f"{qa_info.App.appdata_dir}\\{qa_info.Files.ad_theme_folder}"
    fp = f"{direc}\\{qa_info.Files.ThemePrefFile}"

    if not os.path.exists(fp):
        _reset_pref()
    bef = {}

    with open(fp, 'r') as pref_file:
        bef = json.loads(pref_file.read())
        pref_file.close()

    if 't' not in bef:
        bef['t'] = {}
    elif not isinstance(bef['t'], dict):
        bef['t'] = {}

    bef['t']['file'] = file
    bef['t']['theme'] = theme
    bef['t']['display_name'] = display_name

    with open(fp, 'w') as pref_file:
        pref_file.write(json.dumps(bef, indent=4))
        pref_file.close()


def load_pref_data() -> List[str]:
    direc = f"{qa_info.App.appdata_dir}\\{qa_info.Files.ad_theme_folder}"
    fp = f"{direc}\\{qa_info.Files.ThemePrefFile}"

    default: Dict[str, qa_custom.Theme] = {}
    for kv in Load.load_default_theme().values():
        default = {**default, **kv}

    if not os.path.isdir(direc):
        os.makedirs(direc)

    if not os.path.isfile(fp):
        _reset_pref()

    with open(fp, 'r') as pref_file:
        raw = json.loads(pref_file.read())
        pref_file.close()

    df, dd = \
        qa_std.data_at_dict_path('t\\file', raw)[0] and qa_std.data_at_dict_path('t\\theme', raw)[0] and qa_std.data_at_dict_path('t\\display_name', raw)[0], \
        {
            'file': cast(str, qa_std.data_at_dict_path('t\\file', raw)[1]),
            'theme': cast(str, qa_std.data_at_dict_path('t\\theme', raw)[1]),
            'display_name': cast(str, qa_std.data_at_dict_path('t\\display_name', raw)[1])
        }

    if not df:
        _reset_pref()
        return load_pref_data()

    dd['file'] = _load_path_prep(dd['file'])
    dd['theme'] = _load_path_prep(dd['theme'])

    ddp = {**dd}

    if dd['file'] == '<DEFAULT>':
        dd['file'] = qa_info.Files.default_theme_file_code
    if dd['theme'] == '<DEFAULT>':
        dd['theme'] = list(default.values())[0].theme_code
    if dd['display_name'] == '<DEFAULT>':
        dd['display_name'] = f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}'

    for theme_and_data in Load.auto_load_all().values():
        theme = (*theme_and_data.values(),)[0]
        if theme.theme_file_path == dd['file'] and theme.theme_code == dd['theme'] and f'{theme.theme_file_display_name}: {theme.theme_display_name}' == dd['display_name']:
            if dd != ddp:
                set_pref(dd['file'], dd['theme'], dd['display_name'])
                del ddp
                return [*dd.values()]

            return [*dd.values(), ]

    log(qa_enum.LoggingLevel.DEVELOPER, 'No match; DEFAULTING')
    set_pref(qa_info.Files.default_theme_file_code, list(default.values())[0].theme_code, f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}')

    del dd

    return [qa_info.Files.default_theme_file_code, list(default.values())[0].theme_code, f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}']


def _load_path_prep(original_path: str) -> str:
    original_path = original_path.replace('/', '\\')
    original_path = original_path.replace('APP_DATA_DIR', qa_info.App.appdata_dir)

    return original_path


def _save_prep_path(original_path: str) -> str:
    assert 'APP_DATA_DIR' not in original_path

    original_path = original_path.replace('/', '\\')
    original_path = original_path.replace(qa_info.App.appdata_dir.replace('/', '\\'), 'APP_DATA_DIR')

    return original_path


class Load:
    @staticmethod
    def auto_load_pref_theme() -> qa_custom.Theme:
        direc = f"{qa_info.App.appdata_dir}\\{qa_info.Files.ad_theme_folder}"
        fp = f"{direc}\\{qa_info.Files.ThemePrefFile}"

        default: Dict[str, qa_custom.Theme] = {}
        for kv in Load.load_default_theme().values():
            default = {**default, **kv}

        if not os.path.isdir(direc):
            os.makedirs(direc)

        if not os.path.isfile(fp):
            log(qa_enum.LoggingLevel.DEVELOPER, 'DEFAULTING')
            _reset_pref()

        raw = {}
        with open(fp, 'r') as pref_file:
            raw = json.loads(pref_file.read())
            pref_file.close()

        df, dd = \
            qa_std.data_at_dict_path('t\\file', raw)[0] and qa_std.data_at_dict_path('t\\theme', raw)[0] and qa_std.data_at_dict_path('t\\display_name', raw)[0], \
            {
                'file': cast(str, qa_std.data_at_dict_path('t\\file', raw)[1]),
                'theme': cast(str, qa_std.data_at_dict_path('t\\theme', raw)[1]),
                'display_name': cast(str, qa_std.data_at_dict_path('t\\display_name', raw)[1])
            }

        if not df:
            _reset_pref()
            return Load.auto_load_pref_theme()

        dd['file'] = _load_path_prep(dd['file'])
        dd['theme'] = _load_path_prep(dd['theme'])

        ddp = {**dd}

        if dd['file'] == '<DEFAULT>':
            dd['file'] = qa_info.Files.default_theme_file_code
        if dd['theme'] == '<DEFAULT>':
            dd['theme'] = list(default.values())[0].theme_code
        if dd['display_name'] == '<DEFAULT>':
            dd['display_name'] = f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}'

        for theme_and_data in Load.auto_load_all().values():
            theme = (*theme_and_data.values(), )[0]

            if theme.theme_file_path == dd['file'] and theme.theme_code == dd['theme'] and f'{theme.theme_file_display_name}: {theme.theme_display_name}' == dd['display_name']:
                if dd != ddp: set_pref(dd['file'], dd['theme'], dd['display_name'])
                del dd
                return theme

        log(qa_enum.LoggingLevel.ERROR, 'No match; DEFAULTING')
        set_pref(qa_info.Files.default_theme_file_code, list(default.values())[0].theme_code, f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}')

        del dd

        return (*default.values(), )[0]

    @staticmethod
    def auto_load_all(inc_def: bool = True) -> Dict[str, Dict[str, qa_custom.Theme]]:
        output: Dict[str, Dict[str, qa_custom.Theme]] = {}
        extn = qa_files.qa_files_ltbl.qa_theme_extn

        direc = f"{qa_info.App.appdata_dir}\\{qa_info.Files.ad_theme_folder}"
        if not os.path.exists(direc):
            os.makedirs(direc)
            return output

        file_acc: int = 0
        themes: Dict[int, Tuple[Any, ...]] = {0: ('', )}

        with os.scandir(direc) as fls:
            for file in fls:
                if file.name.endswith(extn):
                    fp: str = file.path

                    try:
                        with open(fp, 'r') as theme_file:
                            raw = json.loads(theme_file.read())
                            theme_file.close()

                    except Exception as E:
                        log(qa_enum.LoggingLevel.ERROR, "Failed to load data from theme file (path at end): %s. File: %s" % (str(E), file.name))
                        continue

                    df, dd = qa_std.data_at_dict_path('file_info/avail_themes', raw)
                    if not df:
                        log(qa_enum.LoggingLevel.ERROR, "Failed to load data from theme file (path at end): File information unavailable %s" % file.name)
                        continue
                    if dd.get('num_themes') is None:
                        log(qa_enum.LoggingLevel.ERROR, "Failed to load data from theme file (path at end): File information unavailable %s" % file.name)
                        continue

                    avail_themes = dd
                    avail_themes.pop('num_themes')

                    file_acc += 1
                    themes[len(themes)] = (avail_themes, raw, fp)

        themes.pop(0)
        for at, t, fp in themes.values():
            try:
                nd = Load._load_theme(fp, t, at, False)
            except Exception as E:
                fn = fp.replace('/', '\\').split('\\')[-1]
                string = f"Failed to load theme from '{fn}': {str(E)}; \n{traceback.format_exc()}"
                log(qa_enum.LoggingLevel.ERROR, f"{string}")
                messagebox.showerror('Automatic Theme Loading Manager', f'DELETED CORRUPTED THEME FILE\n{string}')
                os.remove(fp)
                continue

            output = {**output, **nd}

        if inc_def:
            output = {**output, **Load.load_default_theme()}

        log(qa_enum.LoggingLevel.DEVELOPER, "Found %d files from the AppData directory." % file_acc)

        return output

    @staticmethod
    def load_default_theme() -> Dict[str, Dict[str, qa_custom.Theme]]:
        default_direc = qa_info.Files.default_theme_dir
        default_theme_hash = qa_custom.File(qa_info.Files.default_theme_hashes)

        ofa = qa_custom.OpenFunctionArgs()
        cfa = qa_custom.ConverterFunctionArgs()
        hash_raw = cast(bytes, qa_file_handler.Open.read_file(default_theme_hash, ofa, qa_info.Encryption.default_key, cfa))

        def load(path_to_file: str) -> Dict[str, Dict[str, qa_custom.Theme]]:
            raw = qa_file_handler.Open.read_file(qa_custom.File(str(path_to_file)), ofa, qa_info.Encryption.default_key, cfa)

            json_data = json.loads(qa_file_handler.dtc(raw, str, cfa))
            hash_json = json.loads(qa_file_handler.dtc(hash_raw, str, cfa))
            assert json_data['file_info']['name'] in hash_json, "Invalid/corrupted default theme qa_files (name not found)"

            file_hash = hashlib.sha3_512(qa_file_handler.dtc(raw, bytes, cfa)).hexdigest()
            expected_hash = hash_json[json_data['file_info']['name']]
            del hash_json

            if file_hash != expected_hash:
                log(
                    qa_enum.LoggingLevel.ERROR,
                    f"\n\n{'-' * 100}\nDefault theme file mismatch; \n\t* Expected {expected_hash}\n\t* Got {file_hash}\n(Assertion invoked)\n{'-' * 100}\n\n"
                )

                raise AssertionError("Invalid/corrupted default theme file; hash mismatch.")

            assert Test.check_file(json_data), "Invalid/corrupted default theme file; checks failed."

            themes = {**json_data['file_info']['avail_themes']}
            themes.pop('num_themes')

            return Load._load_theme(default_direc, json_data, themes, _skip_test=True)

        f1 = qa_info.Files.default_theme_file.replace(default_direc, '', 1).strip("\\")
        output_acc = {**load(qa_info.Files.default_theme_file)}

        with os.scandir(default_direc) as fls:
            for file in fls:
                if file.name not in (f1, default_theme_hash.file_name):
                    output_acc = {**output_acc, **load(file.path)}

        return output_acc

    @staticmethod
    def _load_theme(file_path: str, raw_theme_json: Dict[str, Any], theme_names: Dict[Any, Any], _skip_test: bool = False) -> Dict[str, Dict[str, qa_custom.Theme]]:
        o: Dict[str, Dict[str, qa_custom.Theme]] = {}

        for theme_name, theme in theme_names.items():
            assert theme in raw_theme_json, f"Data for '{theme_name}' theme not found."

            if not _skip_test:
                assert Test.check_theme(theme_name, raw_theme_json[theme], False), f"Theme '{theme_name}' - Invalid theme data found."

            t = raw_theme_json[theme]
            ot = qa_custom.Theme(
                raw_theme_json['file_info']['name'],
                raw_theme_json['file_info']['display_name'],
                t['display_name'],
                theme,
                file_path,
                qa_custom.HexColor(t['background']),
                qa_custom.HexColor(t['foreground']),
                qa_custom.HexColor(t['accent']),
                qa_custom.HexColor(t['error']),
                qa_custom.HexColor(t['warning']),
                qa_custom.HexColor(t['ok']),
                qa_custom.HexColor(t['gray']),
                t['font']['font_face'],
                t['font']['alt_font_face'],
                t['font']['size_small'],
                t['font']['size_main'],
                t['font']['size_subtitle'],
                t['font']['size_title'],
                t['font']['size_xl_title'],
                t['border']['size'],
                qa_custom.HexColor(t['border']['colour']),
            )

            o = {**o, theme: {t['display_name']: ot}}

        return o


class Test:
    @staticmethod
    def check_file(json_data: Dict[str, Any], re_results: bool = False) -> Union[bool, Tuple[bool, List[str], List[str]]]:
        failures: List[str] = []
        warnings: List[str] = []
        abort = False

        for i, k in [('name', str), ('display_name', str), ('avail_themes/num_themes', int)]:
            f, d = qa_std.data_at_dict_path(f"file_info/{i}", json_data)

            if not f:
                failures.append(f"Data at key `file_info/{i}` not found; ABORTING")
                abort = True

            else:
                if not isinstance(d, k):
                    failures.append(f"Data at key `file_info/{i}` has invalid data; ABORTING")
                    abort = True

            del f, d

        if not abort:
            _, d1 = qa_std.data_at_dict_path('file_info/avail_themes/num_themes', json_data)
            _, d0 = qa_std.data_at_dict_path('file_info/avail_themes', json_data)

            if len(d0) != d1 + 1:
                failures.append('Invalid number of themes reported; ABORTING')
                abort = True

            else:
                if len(d0) == 1:
                    failures.append('No themes in qa_files; ABORTING')
                    abort = True

            del _, d0, d1

        # Thorough checks
        if not abort:
            _, d0 = qa_std.data_at_dict_path('file_info/avail_themes', json_data)
            d0 = {**d0}
            d0.pop('num_themes')

            for theme_name, theme in d0.items():
                if theme not in json_data:
                    failures.append(f'Theme `{theme}` not found.')
                    abort = True  # Will finish going through for loop before aborting

            if not abort:
                for theme_name in d0.values():
                    fa = Test.check_theme(theme_name, json_data[theme_name], True)
                    failures.extend(cast(Tuple[bool, List[str], List[str]], fa)[1])
                    warnings.extend(cast(Tuple[bool, List[str], List[str]], fa)[2])

                    del fa

        # Failure printer

        if len(failures) > 0:
            sys.stderr.write(f"{'-' * 100}\n")
            for failure in failures:
                sys.stderr.write(f"[Theme File Checks] FAILURE: {failure}\n")

            if abort:
                sys.stderr.write("** Additional tests were ABORTED; unknown status for rest of qa_files. **\n")

            sys.stderr.write(f"{'-' * 100}\n\n")

        return len(failures) == 0 if not re_results else (len(failures) == 0, failures, warnings)

    @staticmethod
    def check_theme(theme_name: str, theme_data: Dict[Any, Any], re_failures: bool = False) -> Union[bool, Tuple[bool, List[str], List[str]]]:
        failures: List[str] = []
        warnings: List[str] = []

        contrast_ratio_adjustment_tbl = {
            'warning': 2.25555,
            'accent': 2.0899
        }

        checks = (
            ('display_name', str),
            ('background', qa_custom.HexColor),
            ('foreground', qa_custom.HexColor),
            ('accent', qa_custom.HexColor),
            ('error', qa_custom.HexColor),
            ('warning', qa_custom.HexColor),
            ('ok', qa_custom.HexColor),
            ('gray', qa_custom.HexColor),
            ('font/font_face', str),
            ('font/alt_font_face', str),
            ('font/size_small', int),
            ('font/size_main', int),
            ('font/size_subtitle', int),
            ('font/size_title', int),
            ('border/size', int),
            ('border/colour', qa_custom.HexColor)
        )

        n_acc: int = 0
        acc: List[str] = []
        for item_name, item_type in checks:
            e, d = qa_std.data_at_dict_path(item_name, theme_data)
            f1 = n_acc
            bg_okay = True

            n_acc += abs(int(e) - 1)

            if not e:
                acc.append(f"`{theme_name}` - Error #{n_acc}: Data for `{item_name}` not found")

            if item_type is qa_custom.HexColor:
                if not isinstance(d, str):
                    n_acc += 1
                    acc.append(f"`{theme_name}` - Error #{n_acc}: Data for `{item_name}` has invalid/corrupted data (data type not supported.)")

                else:
                    if not qa_custom.HexColor(d).check():
                        n_acc += 1
                        acc.append(f"`{theme_name}` - Error #{n_acc}: Data for `{item_name}` has invalid/corrupted data (HexColor Check.)")

                        if item_name == "background":
                            bg_okay = True

            elif not isinstance(d, item_type):
                if not (item_type is int and isinstance(d, float)):
                    n_acc += 1
                    acc.append(f"`{theme_name}` - Error #{n_acc}: Data for `{item_name}` has invalid/corrupted data (data type not supported.)")

            f1 = n_acc == f1
            if f1 and "border" not in item_name:
                if item_type is int:
                    if d <= 0:
                        n_acc += 1
                        acc.append(f"{theme_name}` - Error #{n_acc}: Value for `{item_name}` must have a value of at least 1.")

                    if d < 6:
                        warnings.append(f"{theme_name}` - Warning: Value for `{item_name}` must has a value of {d}; if value relates to font, the size may be too small.")

                if item_type is str:
                    if len(d) <= 0:
                        n_acc += 1
                        acc.append(f'`{theme_name}` - Error #{n_acc}: Empty string provided for `{item_name}`')

                if item_type is qa_custom.HexColor:
                    if item_name != "background":
                        if bg_okay:
                            AA, AAA = qa_std.check_hex_contrast(qa_custom.HexColor(theme_data['background']), qa_custom.HexColor(d), cast(int, (1 if item_name not in contrast_ratio_adjustment_tbl else contrast_ratio_adjustment_tbl.get(item_name))))

                            if not AA:
                                n_acc += 1
                                acc.append(f"`{theme_name}` - Error #{n_acc}: Color value for `{item_name}` fails AA contrast check.")

                            if not AAA:
                                warnings.append(f"`{theme_name}` - Warning: Colour value for `{item_name}` does not pass AAA contrast check (non-fatal.)")

                        else:
                            n_acc += 1
                            acc.append(f"`{theme_name}` - Error #{n_acc}: No background colour to compare to; contrast for color `{item_name}` unknown.")

        failures.extend(acc)

        if re_failures:
            return len(failures) == 0, failures, warnings

        else:
            if len(failures) > 0:
                log(
                    qa_enum.LoggingLevel.WARNING,
                    '\n' + f"-"*100 + "\nCheck theme failures:\n\t*" + "\n\t*".join(failure for failure in failures) + f"\n{'-'*100}\n"
                )

            return len(failures) == 0


class TTK:
    @staticmethod
    def configure_scrollbar_style(style: ttk.Style, theme: qa_custom.Theme, accent_color: str, name_suffix: str = '') -> ttk.Style:
        style.layout(f'My{name_suffix}.TScrollbar',
                     [
                         (
                             f'My{name_suffix}.TScrollbar.trough', {
                                 'children':
                                     [
                                         ('Vertical.Scrollbar.uparrow', {'side': 'top', 'sticky': ''}),
                                         ('Vertical.Scrollbar.downarrow', {'side': 'bottom', 'sticky': ''}),
                                         ('Vertical.Scrollbar.thumb',
                                          {'unit': '1', 'children': [
                                                ('Vertical.Scrollbar.grip',
                                                 {'sticky': ''}
                                                 )
                                            ], 'sticky': 'nswe'
                                           }
                                          )
                                     ],
                                 'sticky': 'ns'})
                     ])

        style.configure(f'My{name_suffix}.TScrollbar', troughcolor=theme.background.color)

        style.configure(
            f'My{name_suffix}.TScrollbar',
            background=theme.background.color,
            arrowcolor=accent_color
        )
        style.map(
            f'My{name_suffix}.TScrollbar',
            background=[
                ("active", accent_color), ('disabled', theme.background.color)
            ],
            foreground=[
                ("active", accent_color), ('disabled', theme.background.color)
            ],
            arrowcolor=[
                ('disabled', theme.background.color)
            ]
        )

        style.layout(
            f'MyHoriz{name_suffix}.TScrollbar',
            [
                (f'MyHoriz{name_suffix}.TScrollbar.trough', {
                    'children': [
                             ('Horizontal.Scrollbar.leftarrow', {'side': 'left', 'sticky': ''}),
                             ('Horizontal.Scrollbar.rightarrow', {'side': 'right', 'sticky': ''}),
                             ('Horizontal.Scrollbar.thumb', {'unit': '1', 'children': [
                                 ('Horizontal.Scrollbar.grip', {'sticky': ''})
                                ], 'sticky': 'nswe'}
                              )], 'sticky': 'ew'})
                      ])

        style.configure(f'MyHoriz{name_suffix}.TScrollbar', troughcolor=theme.background.color)

        style.configure(
            f'MyHoriz{name_suffix}.TScrollbar',
            background=theme.background.color,
            arrowcolor=accent_color
        )
        style.map(
            f'MyHoriz{name_suffix}.TScrollbar',
            background=[
                ("active", accent_color), ('disabled', theme.background.color)
            ],
            foreground=[
                ("active", accent_color), ('disabled', theme.background.color)
            ],
            arrowcolor=[
                ('disabled', theme.background.color)
            ]
        )

        return style

    @staticmethod
    def configure_button_style(style: ttk.Style, theme: qa_custom.Theme, accent: Union[None, str] = None) -> ttk.Style:
        if accent is None:
            accent = theme.accent.color

        assert isinstance(accent, str)

        style.configure(
            'TButton',
            background=theme.background.color,
            foreground=accent,
            font=(theme.font_face, theme.font_main_size),
            focuscolor=accent,
            bordercolor=0
        )

        style.map(
            'TButton',
            background=[('active', accent), ('disabled', theme.background.color), ('readonly', theme.gray.color)],
            foreground=[('active', theme.background.color), ('disabled', theme.gray.color), ('readonly', theme.background.color)]
        )

        return style

    @staticmethod
    def configure_entry_style(style: ttk.Style, theme: qa_custom.Theme, font_size: Union[float, int] = -1, pref: str = 'My') -> ttk.Style:
        style.configure(
            f'{pref}.TEntry',
            background=theme.background.color,
            foreground=theme.accent.color,
            font=(theme.font_face, font_size if font_size != -1 else theme.font_main_size),
            bordercolor=theme.accent.color,
            fieldbackground=theme.background.color,
            selectbackground=theme.accent.color,
            selectforeground=theme.background.color,
            insertcolor=theme.accent.color
        )

        style.map(
            f'{pref}.TEntry',
            background=[('disabled', theme.background.color), ('readonly', theme.gray.color)],
            foreground=[('disabled', theme.gray.color), ('readonly', theme.background.color)],
            fieldbackground=[('disabled', theme.background.color), ('readonly', theme.gray.color)]
        )

        return style


def log(level: qa_enum.LoggingLevel, data: str) -> None:
    global THEME_LOADER_ENABLE_DEV_DEBUGGING
    assert isinstance(data, str)

    if level == qa_enum.LoggingLevel.DEVELOPER and not THEME_LOADER_ENABLE_DEV_DEBUGGING:
        return

    if level == qa_enum.LoggingLevel.ERROR:
        data = f'{qa_std.ANSI.FG_BRIGHT_RED}{qa_std.ANSI.BOLD}[{level.name.upper()}] {data}{qa_std.ANSI.RESET}\n'
    elif level == qa_enum.LoggingLevel.SUCCESS:
        data = f'{qa_std.ANSI.FG_BRIGHT_GREEN}{qa_std.ANSI.BOLD}[{level.name.upper()}] {data}{qa_std.ANSI.RESET}\n'
    elif level == qa_enum.LoggingLevel.WARNING:
        data = f'{qa_std.ANSI.FG_BRIGHT_YELLOW}[{level.name.upper()}] {data}{qa_std.ANSI.RESET}\n'
    elif level == qa_enum.LoggingLevel.DEVELOPER:
        data = f'{qa_std.ANSI.FG_BRIGHT_BLUE}{qa_std.ANSI.BOLD}[{level.name.upper()}]{qa_std.ANSI.RESET} {data}\n'
    elif level == qa_enum.LoggingLevel.DEBUG:
        data = f'{qa_std.ANSI.FG_BRIGHT_MAGENTA}[{level.name.upper()}]{qa_std.ANSI.RESET} {data}\n'
    else:
        data = f'[{level.name.upper()}] {data}\n'

    data = f"{qa_std.AppLogColors.QA_PROMPTS}{qa_std.AppLogColors.EXTRA}[THEME_LOADER]{qa_std.ANSI.RESET} {data}"

    if level == qa_enum.LoggingLevel.ERROR:
        sys.stderr.write(data)
    else:
        sys.stdout.write(data)
