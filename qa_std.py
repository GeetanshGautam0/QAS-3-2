from tkinter import messagebox
import wcag_contrast_ratio, re, tkinter as tk

from qa_enum import *
from typing import *
from qa_custom import *


def float_map(value: float, input_min: float, input_max: float, output_min: float, output_max: float, allow_overflow: bool = False) -> float:
    """
    **FLOAT_MAP**

    Takes in float 'value' between points 'input_min' and 'input_max' and scales it to fit into the output range (output_min >> output_max)

    :param value: Actual Value
    :param input_min: Input range (min)
    :param input_max: Input range (max)
    :param output_min: Output range (min)
    :param output_max: Output range (max)
    :param allow_overflow: If true: `value` can be outside of the input_min >> input_max range
    :return: mapped float
    """

    assert not allow_overflow and (input_min < value < input_max), "Value outside of given bounds"

    leftSpan = input_max - input_min
    rightSpan = output_max - output_min
    valueScaled = float(value - input_min) / float(leftSpan)
    return output_min + (valueScaled * rightSpan)


def check_hex_contrast(bg: HexColor, fg: HexColor, adjustment: int = 0) -> Tuple[bool, bool]:
    """
    **CHECK_HEX_CONTRAST**

    Checks to see whether there is sufficient contrast between `bg` and `fg` using the AA and AAA standards

    :param bg: Color 1 (Background)
    :param fg: Color 2 (Foreground)
    :param adjustment: Integer added to contrast ratio (def=0)
    :return: (Passes AA, Passes AAA)
    """

    err_str_1 = f"Invalid color `bg`; expected {type(HexColor)}"

    assert isinstance(bg, HexColor), err_str_1
    assert isinstance(fg, HexColor), err_str_1

    def map_rgb(color_rgb: Tuple[int, int, int]) -> Tuple:
        assert len(color_rgb) == 3, 'Invalid '
        o_tuple: List[float, float, float] = []

        for col in color_rgb:
            o_tuple.append(float_map(col, 0.00, 255.00, 0.00, 1.00))

        return *o_tuple,

    def hex_to_rgb(color: HexColor) -> tuple:
        return tuple(int("".join(i for i in re.findall(r"\w", color.color))[j:j + 2], 16) for j in (0, 2, 4))

    col1 = hex_to_rgb(bg)
    col2 = hex_to_rgb(fg)
    adjusted_contrast_ratio = wcag_contrast_ratio.rgb(map_rgb(col1), map_rgb(col2)) + adjustment

    AA_res = wcag_contrast_ratio.passes_AA(adjusted_contrast_ratio)
    AAA_res = wcag_contrast_ratio.passes_AAA(adjusted_contrast_ratio)

    return AA_res, AAA_res


def data_at_dict_path(path: str, dictionary: dict) -> Tuple[bool, any]:
    """
    **DATA_AT_DICT_PATH**

    Takes in dictionary 'dictionary' and finds data at path 'path'

    :param path: Path in dict (entries separated by '/' or '\\')
    :param dictionary: Data dictionary
    :return: Tuple (found?, data)
    """

    assert isinstance(path, str), "Invalid path input"
    assert isinstance(dictionary, dict), "Invalid dict input"

    path = path.replace('/', '\\')
    path_tokens = (*path.split('\\'), )

    found = True
    data = {**dictionary}

    for index, token in enumerate(path_tokens):
        if token == "root" and index == 0:
            continue

        found = token in data
        data = data[token] if found else None

        if index != len(path_tokens) - 1:
            if type(data) is not dict:
                found = False

        if not found:
            break

    return found, data


def show_bl_err(title, message) -> None:
    """
    **SHOW_BL_ERR**

    Shows error prompt; for use when no TK root is avail.

    :param title: Title of prompt
    :param message: Error message
    :return: None
    """

    assert isinstance(title, str)
    assert isinstance(message, str)

    bgf = tk.Tk()
    bgf.withdraw()
    bgf.title("%s - QAS" % title)

    messagebox.showerror(title, message)

    bgf.title("%s - QAS - Closed" % title)
    bgf.withdraw()

    return


def split_filename_direc(file_path: str) -> Tuple[str, str]:
    """
    **SPLIT_FILENAME_DIREC**

    Takes in file path `file_path`, splits the path into a file name the directory path

    :param file_path: Filename with path
    :return: Tuple [Path, Filename]
    """

    return File.split_file_path(file_path)


def dict_check_redundant_data_inter_dict(dic: dict, dic2: dict, root_name: str = '<root>') -> tuple:
    """
    Checks for redundant data between two dictionaries
    """

    assert isinstance(dic, dict)
    assert isinstance(dic2, dict)
    assert isinstance(root_name, str)

    def rec_add(d, d2, root='<root>') -> tuple:
        assert isinstance(d, dict)
        assert isinstance(d2, dict)
        assert isinstance(root, str)

        b = True
        oc = {}
        fnc = set()

        for k, v in d2.items():
            if isinstance(v, dict):
                if k in d:
                    b1, oc1, fnc1 = rec_add(d[k], d2[k], root='%s/%s' % (root, k))
                    b &= b1
                    oc = {**oc, **oc1}
                    fnc = {*fnc, *fnc1}

                continue

            if '%s/%s' % (root, v) not in d.values():
                oc['%s/%s' % (root, v)] = ('%s/%s' % (root, k), )

            else:
                b ^= b
                oc['%s/%s' % (root, v)] = (*oc['%s/%s' % (root, v)], '%s/%s' % (root, k))

        for v in oc:
            if len(oc[v]) > 1:
                fnc.add("'%s' is common between %s" % (v, oc[v]))

        return b, oc, fnc

    c, _, f = rec_add(dic, dic2)

    return not c, f


def dict_check_redundant_data(dic: dict, root_name: str = '<root>') -> tuple:
    """
    Checks for redundant data within a dictionary
    """

    assert isinstance(dic, dict)
    assert isinstance(root_name, str)

    def rec_add(d, root='<root>') -> tuple:
        assert isinstance(d, dict)
        assert isinstance(root, str)

        b = True
        oc = {}
        fnc = set()

        for k, v in d.items():
            if isinstance(v, dict):
                b1, oc1, fnc1 = rec_add(d[k], root='%s/%s' % (root, k))
                b &= b1
                oc = {**oc, **oc1}
                fnc = {*fnc, *fnc1}

                continue

            if '%s/%s' % (root, v) not in oc:
                oc['%s/%s' % (root, v)] = ('%s/%s' % (root, k), )

            else:
                b ^= b
                oc['%s/%s' % (root, v)] = (*oc['%s/%s' % (root, v)], '%s/%s' % (root, k))

        for v in oc:
            if len(oc[v]) > 1:
                fnc.add("'%s' is common between %s" % (v, oc[v]))

        return b, oc, fnc

    c, _, f = rec_add(dic, root_name)

    return not c, f


def copy_to_clipboard(text: str, shell: tk.Toplevel, clear_old: bool = True):
    """
    **COPY_TO_CLIPBOARD**

    Copies text to clipboard

    :param text: Text to copy
    :param shell: tk.Tk OR tk.Toplevel
    :param clear_old: Clear older data in clipboard (from the app)
    :return:
    """

    assert isinstance(text, str)
    assert isinstance(shell, tk.Toplevel) or isinstance(shell, tk.Tk)
    assert len(text) <= 100  # Max length = 100
    assert isinstance(clear_old, bool)

    if clear_old:
        shell.clipboard_clear()

    shell.clipboard_append(text)
    shell.update()
