import qa_file_handler as file_io, qa_std as std, qa_info as info, json, hashlib, sys
from qa_custom import *
from qa_enum import *


def _load_default() -> tuple:
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

        raise AssertionError("Invalid/corrupted default theme file; hash mismatch.")

    assert _check_file(json_data), "Invalid/corrupted default theme file; checks failed."

    themes = {**json_data['file_info']['avail_themes']}
    themes.pop('num_themes')

    return _load_theme(json_data, themes)


def _load_theme(raw_theme_json: dict, theme_names: dict) -> tuple:

    o = ()

    for theme_name, theme in theme_names.items():
        assert theme in raw_theme_json, f"Data for '{theme_name}' theme not found."
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
            t['font']['font_face'],
            t['font']['alt_font_face'],
            t['font']['size_small'],
            t['font']['size_main'],
            t['font']['size_subtitle'],
            t['font']['size_title'],
            t['border']['size'],
            HexColor(t['border']['colour']),
        )

        o = (*o, ot)

    return o


def _check_file(json_data: dict) -> bool:  # TODO: Add tests here
    return True


def _check_theme(json_data: dict) -> bool:  # TODO: Add tests here
    return True
