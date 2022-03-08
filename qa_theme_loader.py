import qa_file_handler as file_io, qa_std as std, qa_info as info, json, hashlib, sys, re
from qa_custom import *
from qa_enum import *


def _load_default() -> dict:
    default_file = File(info.Files.default_theme_file)
    default_theme_hash = File(info.Files.default_theme_hashes)

    ofa = OpenFunctionArgs()
    cfa = ConverterFunctionArgs()

    raw = file_io.Open.read_file(default_file, ofa, info.Encryption.default_key, cfa)
    hash_raw = file_io.Open.read_file(default_theme_hash, ofa, info.Encryption.default_key, cfa)

    json_data = json.loads(file_io.dtc(raw, str, cfa))
    hash_json = json.loads(file_io.dtc(hash_raw, str, cfa))

    assert json_data['file_info']['name'] in hash_json, "Invalid/corrupted default theme file (name not found)"

    file_hash = hashlib.sha3_512(file_io.dtc(raw, bytes, cfa)).hexdigest()
    expected_hash = hash_json[json_data['file_info']['name']]
    del hash_json

    if file_hash != expected_hash:
        sys.stderr.write(
            f"\n\n{'-'*100}\nDefault theme file mismatch; \n\t* Expected {expected_hash}\n\t* Got {file_hash}\n(Assertion invoked)\n{'-'*100}\n\n"
        )

        # raise AssertionError("Invalid/corrupted default theme file; hash mismatch.")

    assert _check_file(json_data), "Invalid/corrupted default theme file; checks failed."

    themes = {**json_data['file_info']['avail_themes']}
    themes.pop('num_themes')

    return _load_theme(json_data, themes, _skip_test=True)


def _load_theme(raw_theme_json: dict, theme_names: dict, _skip_test: bool = False) -> dict:

    o = {}

    for theme_name, theme in theme_names.items():
        assert theme in raw_theme_json, f"Data for '{theme_name}' theme not found."

        if not _skip_test:
            assert _check_theme(raw_theme_json[theme]), f"Theme '{theme_name}' - Invalid theme data found."

        t = raw_theme_json[theme]
        ot = Theme(
            raw_theme_json['file_info']['name'],
            raw_theme_json['file_info']['display_name'],
            t['display_name'],
            theme_name,
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
            t['border']['size'],
            HexColor(t['border']['colour']),
        )

        o = {**o, t['display_name']: ot}

    return o


def _check_file(json_data: dict) -> bool:  # TODO: Add tests here
    failures, warnings = [], []
    abort = False

    for i, k in [('name', str), ('display_name', str), ('avail_themes/num_themes', int)]:
        f, d = std.data_at_dict_path(f"file_info/{i}", json_data)

        if not f:
            failures.append(f"Data at key `file_info/{i}` not found; ABORTING")
            abort = True

        else:
            if not isinstance(d, k):
                failures.append(f"Data at key `file_info/{i}` has invalid data; ABORTING")
                abort = True

        del f, d

    if not abort:
        _, d1 = std.data_at_dict_path('file_info/avail_themes/num_themes', json_data)
        _, d0 = std.data_at_dict_path('file_info/avail_themes', json_data)

        if len(d0) != d1 + 1:
            failures.append('Invalid number of themes reported; ABORTING')
            abort = True

        else:
            if len(d0) == 1:
                failures.append('No themes in file; ABORTING')
                abort = True

        del _, d0, d1

    # Thorough checks
    if not abort:
        _, d0 = std.data_at_dict_path('file_info/avail_themes', json_data)
        d0 = {**d0}
        d0.pop('num_themes')

        for theme_name, theme in d0.items():
            if theme not in json_data:
                failures.append(f'Theme `{theme}` not found.')
                abort = True  # Will finish going through for loop before aborting

        if not abort:
            for theme_name in d0.values():
                _, f, w = _check_theme(theme_name, json_data[theme_name], True)
                failures.extend(f)
                warnings.extend(w)

    # Failure printer

    if len(failures) > 0:
        sys.stderr.write(f"{'-' *100}\n")
        for failure in failures:
            sys.stderr.write(f"[Theme File Checks] FAILURE: {failure}\n")

        if abort:
            sys.stderr.write("** Additional tests were ABORTED; unknown status for rest of file. **\n")

        sys.stderr.write(f"{'-' *100}\n\n")

    return len(failures) == 0


def _check_theme(theme_name: str, theme_data: dict, re_failures: bool = False) -> Union[bool, Tuple[bool, List, List]]:
    failures, warnings = [], []

    contrast_ratio_adjustment_tbl = {
        'warning': 2.25555
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
        e, d = std.data_at_dict_path(item_name, theme_data)
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
            if not(item_type is int and isinstance(d, float)):
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
                        AA, AAA = std.check_hex_contrast(HexColor(theme_data['background']), HexColor(d), 0 if item_name not in contrast_ratio_adjustment_tbl else contrast_ratio_adjustment_tbl.get(item_name))

                        if not AA:
                            acc[0] += 1
                            acc[1].append(f"`{theme_name}` - Error #{acc[0]}: Color value for `{item_name}` fails AA contrast check.")

                        if not AAA:
                            warnings.append(f"`{theme_name}` - Warning: Colour value for `{theme_name}` does not pass AAA contrast check (non-fatal.)")

                    else:
                        acc[0] += 1
                        acc[1].append(f"`{theme_name}` - Error #{acc[0]}: No background colour to compare to; contrast for color `{item_name}` unknown.")

    failures.extend(acc[1])

    if re_failures:
        return len(failures) == 0, failures, warnings

    else:
        return len(failures) == 0
