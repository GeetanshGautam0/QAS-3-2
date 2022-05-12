import json, hashlib, sys, re, traceback, qa_files
from tkinter import ttk
from .qa_custom import *
from .qa_enum import *
from .qa_file_handler import *
from .qa_std import *
from .qa_info import *


def _reset_pref():
    direc = f"{App.appdata_dir}\\{Files.ad_theme_folder}"
    fp = f"{direc}\\{Files.ThemePrefFile}"

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


def _set_pref(file, theme, display_name):
    file = _save_prep_path(file)

    direc = f"{App.appdata_dir}\\{Files.ad_theme_folder}"
    fp = f"{direc}\\{Files.ThemePrefFile}"

    if not os.path.exists(fp): _reset_pref()
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


def _load_pref_data() -> list:
    direc = f"{App.appdata_dir}\\{Files.ad_theme_folder}"
    fp = f"{direc}\\{Files.ThemePrefFile}"
    odefault = Load._load_default()
    default = {}
    for kv in odefault.values():
        default = {**default, **kv}

    if not os.path.isdir(direc):
        os.makedirs(direc)

    if not os.path.isfile(fp):
        _reset_pref()

    raw = {}
    with open(fp, 'r') as pref_file:
        raw = json.loads(pref_file.read())
        pref_file.close()

    df, dd = \
        data_at_dict_path('t\\file', raw)[0] and data_at_dict_path('t\\theme', raw)[0] and data_at_dict_path('t\\display_name', raw)[0], \
        {'file': data_at_dict_path('t\\file', raw)[1], 'theme': data_at_dict_path('t\\theme', raw)[1], 'display_name': data_at_dict_path('t\\display_name', raw)[1]}

    if not df:
        _reset_pref()
        return _load_pref_data()

    dd['file'] = _load_path_prep(dd['file'])
    dd['theme'] = _load_path_prep(dd['theme'])

    ddp = {**dd}

    if dd['file'] == '<DEFAULT>': dd['file'] = Files.default_theme_file_code
    if dd['theme'] == '<DEFAULT>': dd['theme'] = list(default.values())[0].theme_code
    if dd['display_name'] == '<DEFAULT>': dd['display_name'] = f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}'

    for theme_and_data in Load.auto_load_all().values():
        theme = (*theme_and_data.values(),)[0]
        if theme.theme_file_path == dd['file'] and theme.theme_code == dd['theme'] and f'{theme.theme_file_display_name}: {theme.theme_display_name}' == dd['display_name']:
            if dd != ddp:
                _set_pref(dd['file'], dd['theme'], dd['display_name'])
                del ddp
                return [*dd.values()]

            return [*dd.values(), ]

    print('[INFO] [PREF_LOADER] No match; DEFAULTING')
    _set_pref(Files.default_theme_file_code, list(default.values())[0].theme_code, f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}')

    del dd

    return [Files.default_theme_file_code, list(default.values())[0].theme_code, f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}']


def _load_path_prep(opath: str):
    opath = opath.replace('/', '\\')
    opath = opath.replace('APP_DATA_DIR', App.appdata_dir)

    return opath


def _save_prep_path(opath: str):
    assert 'APP_DATA_DIR' not in opath

    opath = opath.replace('/', '\\')
    opath = opath.replace(App.appdata_dir.replace('/', '\\'), 'APP_DATA_DIR')

    return opath


class Load:
    @staticmethod
    def auto_load_pref_theme() -> Theme:
        direc = f"{App.appdata_dir}\\{Files.ad_theme_folder}"
        fp = f"{direc}\\{Files.ThemePrefFile}"
        odefault = Load._load_default()
        default = {}
        for kv in odefault.values():
            default = {**default, **kv}

        if not os.path.isdir(direc):
            os.makedirs(direc)

        if not os.path.isfile(fp):
            print('[INFO] [THEME_LOADER] DEFAULTING')
            _reset_pref()

        raw = {}
        with open(fp, 'r') as pref_file:
            raw = json.loads(pref_file.read())
            pref_file.close()

        df, dd = \
            data_at_dict_path('t\\file', raw)[0] and data_at_dict_path('t\\theme', raw)[0] and data_at_dict_path('t\\display_name', raw)[0], \
            {'file': data_at_dict_path('t\\file', raw)[1], 'theme': data_at_dict_path('t\\theme', raw)[1], 'display_name': data_at_dict_path('t\\display_name', raw)[1]}

        if not df:
            _reset_pref()
            return Load.auto_load_pref_theme()

        dd['file'] = _load_path_prep(dd['file'])
        dd['theme'] = _load_path_prep(dd['theme'])

        ddp = {**dd}

        if dd['file'] == '<DEFAULT>': dd['file'] = Files.default_theme_file_code
        if dd['theme'] == '<DEFAULT>': dd['theme'] = list(default.values())[0].theme_code
        if dd['display_name'] == '<DEFAULT>': dd['display_name'] = f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}'

        for theme_and_data in Load.auto_load_all().values():
            theme = (*theme_and_data.values(), )[0]

            if theme.theme_file_path == dd['file'] and theme.theme_code == dd['theme'] and f'{theme.theme_file_display_name}: {theme.theme_display_name}' == dd['display_name']:
                if dd != ddp: _set_pref(dd['file'], dd['theme'], dd['display_name'])
                del dd
                return theme

        print('[INFO] [THEME_LOADER] No match; DEFAULTING')
        _set_pref(Files.default_theme_file_code, list(default.values())[0].theme_code, f'{list(default.values())[0].theme_file_display_name}: {list(default.keys())[0]}')

        del dd

        return (*default.values(), )[0]

    @staticmethod
    def auto_load_all(inc_def: bool = True) -> dict:
        output = {}
        extn = qa_files.qa_theme_extn

        direc = f"{App.appdata_dir}\\{Files.ad_theme_folder}"
        if not os.path.exists(direc):
            os.makedirs(direc)
            return output

        file_acc: int = 0
        themes = {}

        ERR = "[ERROR] [THEME_LOADER] "

        with os.scandir(direc) as fls:
            for file in fls:
                if file.name.endswith(extn):
                    fp = file.path

                    try:
                        with open(fp, 'r') as theme_file:
                            raw = json.loads(theme_file.read())
                            theme_file.close()

                    except Exception as E:
                        print(f"{ERR}Failed to load data from theme file (path at end): %s. File: %s" % (str(E), file.name))
                        continue

                    df, dd = data_at_dict_path('file_info/avail_themes', raw)
                    if not df:
                        print(f"{ERR}Failed to load data from theme file (path at end): File information unavailable %s" % file.name)
                        continue
                    if dd.get('num_themes') is None:
                        print(f"{ERR}Failed to load data from theme file (path at end): File information unavailable %s" % file.name)
                        continue

                    avail_themes = dd
                    avail_themes.pop('num_themes')

                    file_acc += 1
                    themes[len(themes)] = (avail_themes, raw, fp)

        for at, t, fp in themes.values():
            try:
                nd = Load._load_theme(fp, t, at, False)
            except Exception as E:
                fn = fp.replace('/', '\\').split('\\')[-1]
                stri = f"Failed to load theme from '{fn}': {str(E)}; \n{traceback.format_exc()}"
                sys.stderr.write(f"{stri}\n")
                messagebox.showerror('Automatic Theme Loading Manager', f'DELETED CORRUPTED THEME FILE\n{stri}')
                os.remove(fp)
                continue

            output = {**output, **nd}

        if inc_def:
            output = {**output, **Load._load_default()}

        print("[INFO] [THEME_LOADER] Found %d files from the AppData directory" % file_acc)

        return output

    @staticmethod
    def _load_default() -> dict:
        default_direc = Files.default_theme_dir
        default_theme_hash = File(Files.default_theme_hashes)

        ofa = OpenFunctionArgs()
        cfa = ConverterFunctionArgs()
        hashes = hash_raw = Open.read_file(default_theme_hash, ofa, Encryption.default_key, cfa)

        def load(path_to_file: os.PathLike):
            raw = Open.read_file(File(str(path_to_file)), ofa, Encryption.default_key, cfa)

            json_data = json.loads(dtc(raw, str, cfa))
            hash_json = json.loads(dtc(hash_raw, str, cfa))
            assert json_data['file_info']['name'] in hash_json, "Invalid/corrupted default theme qa_files (name not found)"

            file_hash = hashlib.sha3_512(dtc(raw, bytes, cfa)).hexdigest()
            expected_hash = hash_json[json_data['file_info']['name']]
            del hash_json

            if file_hash != expected_hash:
                sys.stderr.write(
                    f"\n\n{'-' * 100}\nDefault theme file mismatch; \n\t* Expected {expected_hash}\n\t* Got {file_hash}\n(Assertion invoked)\n{'-' * 100}\n\n"
                )

                raise AssertionError("Invalid/corrupted default theme file; hash mismatch.")

            assert Test.check_file(json_data), "Invalid/corrupted default theme file; checks failed."

            themes = {**json_data['file_info']['avail_themes']}
            themes.pop('num_themes')

            return Load._load_theme(default_direc, json_data, themes, _skip_test=True)

        output_acc = {}

        f1 = Files.default_theme_file.replace(default_direc, '', 1).strip("\\")
        output_acc = {**load(Files.default_theme_file)}

        with os.scandir(default_direc) as fls:
            for file in fls:
                if file.name not in (f1, default_theme_hash.file_name):
                    output_acc = {**output_acc, **load(file.path)}

        return output_acc

    @staticmethod
    def _load_theme(file_path, raw_theme_json: dict, theme_names: dict, _skip_test: bool = False) -> dict:
        o = {}

        for theme_name, theme in theme_names.items():
            assert theme in raw_theme_json, f"Data for '{theme_name}' theme not found."

            if not _skip_test:
                assert Test.check_theme(theme_name, raw_theme_json[theme], False), f"Theme '{theme_name}' - Invalid theme data found."

            t = raw_theme_json[theme]
            ot = Theme(
                raw_theme_json['file_info']['name'],
                raw_theme_json['file_info']['display_name'],
                t['display_name'],
                theme,
                file_path,
                HexColor(t['background']),
                HexColor(t['foreground']),
                HexColor(t['accent']),
                HexColor(t['error']),
                HexColor(t['warning']),
                HexColor(t['ok']),
                HexColor(t['gray']),
                t['font']['font_face'],
                t['font']['alt_font_face'],
                t['font']['size_small'],
                t['font']['size_main'],
                t['font']['size_subtitle'],
                t['font']['size_title'],
                t['font']['size_xl_title'],
                t['border']['size'],
                HexColor(t['border']['colour']),
            )

            o = {**o, theme: {t['display_name']: ot}}

        return o


class Test:
    @staticmethod
    def check_file(json_data: dict, re_results: bool = False) -> bool:  # TODO: Add tests here
        failures, warnings = [], []
        abort = False

        for i, k in [('name', str), ('display_name', str), ('avail_themes/num_themes', int)]:
            f, d = data_at_dict_path(f"file_info/{i}", json_data)

            if not f:
                failures.append(f"Data at key `file_info/{i}` not found; ABORTING")
                abort = True

            else:
                if not isinstance(d, k):
                    failures.append(f"Data at key `file_info/{i}` has invalid data; ABORTING")
                    abort = True

            del f, d

        if not abort:
            _, d1 = data_at_dict_path('file_info/avail_themes/num_themes', json_data)
            _, d0 = data_at_dict_path('file_info/avail_themes', json_data)

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
            _, d0 = data_at_dict_path('file_info/avail_themes', json_data)
            d0 = {**d0}
            d0.pop('num_themes')

            for theme_name, theme in d0.items():
                if theme not in json_data:
                    failures.append(f'Theme `{theme}` not found.')
                    abort = True  # Will finish going through for loop before aborting

            if not abort:
                for theme_name in d0.values():
                    _, f, w = Test.check_theme(theme_name, json_data[theme_name], True)
                    failures.extend(f)
                    warnings.extend(w)

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
    def check_theme(theme_name: str, theme_data: dict, re_failures: bool = False) -> Union[bool, Tuple[bool, List, List]]:
        failures, warnings = [], []

        contrast_ratio_adjustment_tbl = {
            'warning': 2.25555,
            'accent': 2.0899
        }

        checks = (
            ('display_name', str),
            ('background', HexColor),
            ('foreground', HexColor),
            ('accent', HexColor),
            ('error', HexColor),
            ('warning', HexColor),
            ('ok', HexColor),
            ('gray', HexColor),
            ('font/font_face', str),
            ('font/alt_font_face', str),
            ('font/size_small', int),
            ('font/size_main', int),
            ('font/size_subtitle', int),
            ('font/size_title', int),
            ('border/size', int),
            ('border/colour', HexColor)
        )

        acc = [0, []]
        for item_name, item_type in checks:
            e, d = data_at_dict_path(item_name, theme_data)
            f1 = acc[0]
            bg_okay = True

            acc[0] += abs(int(e) - 1)

            if not e:
                acc[1].append(f"`{theme_name}` - Error #{acc[0]}: Data for `{item_name}` not found")

            if item_type is HexColor:
                if not isinstance(d, str):
                    acc[0] += 1
                    acc[1].append(f"`{theme_name}` - Error #{acc[0]}: Data for `{item_name}` has invalid/corrupted data (data type not supported.)")

                else:
                    if not HexColor(d).check():
                        acc[0] += 1
                        acc[1].append(f"`{theme_name}` - Error #{acc[0]}: Data for `{item_name}` has invalid/corrupted data (HexColor Check.)")

                        if item_name == "background":
                            bg_okay = True

            elif not isinstance(d, item_type):
                if not (item_type is int and isinstance(d, float)):
                    acc[0] += 1
                    acc[1].append(f"`{theme_name}` - Error #{acc[0]}: Data for `{item_name}` has invalid/corrupted data (data type not supported.)")

            f1 = acc[0] == f1
            if f1 and "border" not in item_name:
                if item_type is int:
                    if d <= 0:
                        acc[0] += 1
                        acc[1].append(f"{theme_name}` - Error #{acc[0]}: Value for `{item_name}` must have a value of at least 1.")

                    if d < 6:
                        warnings.append(f"{theme_name}` - Warning: Value for `{item_name}` must has a value of {d}; if value relates to font, the size may be too small.")

                if item_type is str:
                    if len(d) <= 0:
                        acc[0] += 1;
                        acc[1].append(f'`{theme_name}` - Error #{acc[0]}: Empty string provided for `{item_name}`')

                if item_type is HexColor:
                    if item_name != "background":
                        if bg_okay:
                            AA, AAA = check_hex_contrast(HexColor(theme_data['background']), HexColor(d), 0 if item_name not in contrast_ratio_adjustment_tbl else contrast_ratio_adjustment_tbl.get(item_name))

                            if not AA:
                                acc[0] += 1
                                acc[1].append(f"`{theme_name}` - Error #{acc[0]}: Color value for `{item_name}` fails AA contrast check.")

                            if not AAA:
                                warnings.append(f"`{theme_name}` - Warning: Colour value for `{item_name}` does not pass AAA contrast check (non-fatal.)")

                        else:
                            acc[0] += 1
                            acc[1].append(f"`{theme_name}` - Error #{acc[0]}: No background colour to compare to; contrast for color `{item_name}` unknown.")

        failures.extend(acc[1])

        if re_failures:
            return len(failures) == 0, failures, warnings

        else:
            if len(failures) > 0:
                sys.stderr.write(
                    '\n' + f"-"*100 + "\nCheck theme failures:\n\t*" + "\n\t*".join(failure for failure in failures) + f"\n{'-'*100}\n\n"
                )

            return len(failures) == 0


class TTK:
    @staticmethod
    def configure_scrollbar_style(style: ttk.Style, theme: Theme, accent_color):
        style.layout("My.TScrollbar",
                     [('My.Scrollbar.trough', {'children':
                         [
                             ('Vertical.Scrollbar.uparrow', {'side': 'top', 'sticky': ''}),
                             ('Vertical.Scrollbar.downarrow', {'side': 'bottom', 'sticky': ''}),
                             ('Vertical.Scrollbar.thumb', {'unit': '1', 'children':
                                 [('Vertical.Scrollbar.grip', {'sticky': ''})], 'sticky': 'nswe'})],
                         'sticky': 'ns'})
                      ])
        # style.configure("My.TScrollbar", *style.configure("TScrollbar"))
        style.configure("My.TScrollbar", troughcolor=theme.background.color)

        style.configure(
            'My.TScrollbar',
            background=theme.background.color,
            arrowcolor=accent_color
        )
        style.map(
            "My.TScrollbar",
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

        style.layout("MyHoriz.TScrollbar",
                     [('MyHoriz.Scrollbar.trough', {'children':
                         [
                             ('Horizontal.Scrollbar.leftarrow', {'side': 'left', 'sticky': ''}),
                             ('Horizontal.Scrollbar.rightarrow', {'side': 'right', 'sticky': ''}),
                             ('Horizontal.Scrollbar.thumb', {'unit': '1', 'children':
                                 [('Horizontal.Scrollbar.grip', {'sticky': ''})], 'sticky': 'nswe'})],
                         'sticky': 'ew'})
                      ])
        # style.configure("My.TScrollbar", *style.configure("TScrollbar"))
        style.configure("MyHoriz.TScrollbar", troughcolor=theme.background.color)

        style.configure(
            'MyHoriz.TScrollbar',
            background=theme.background.color,
            arrowcolor=accent_color
        )
        style.map(
            "MyHoriz.TScrollbar",
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
    def configure_button_style(style: ttk.Style, theme: Theme, accent=None):
        if accent is None:
            accent = theme.accent.color

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
    def configure_entry_style(style: ttk.Style, theme: Theme):
        style.configure(
            'TEntry',
            background=theme.background.color,
            foreground=theme.accent.color,
            font=(theme.font_face, theme.font_main_size),
            bordercolor=theme.accent.color,
            fieldbackground=theme.background.color,
            selectbackground=theme.accent.color,
            selectforeground=theme.background.color,
            insertcolor=theme.accent.color
        )

        style.map(
            'TEntry',
            background=[('disabled', theme.background.color), ('readonly', theme.gray.color)],
            foreground=[('disabled', theme.gray.color), ('readonly', theme.background.color)],
            fieldbackground=[('disabled', theme.background.color), ('readonly', theme.gray.color)]
        )

        return style
