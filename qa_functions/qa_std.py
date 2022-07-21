import wcag_contrast_ratio, tkinter as tk, time, random, hashlib, re
from tkinter import messagebox
from shared_memory_dict import SharedMemoryDict
from .qa_custom import HexColor, File, ConverterFunctionArgs, UnexpectedEdgeCase
from .qa_enum import ErrorLevels
from .qa_err import raise_error
from .qa_info import App
from typing import *


HTTP_HEADERS_NO_CACHE = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache', 'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'}


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

    if not allow_overflow:
        assert (input_min <= value <= input_max), "Value outside of given bounds"

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

    err_str_1: Callable[[str], str] = lambda name: f"Invalid color `{name}`; expected {HexColor}"
    err_str_2: Callable[[str], str] = lambda name: f"Color `{name}` is not a valid hex color"

    assert isinstance(bg, HexColor), err_str_1('bg')
    assert bg.check(), err_str_2('bg')
    assert isinstance(fg, HexColor), err_str_1('fg')
    assert fg.check(), err_str_2('fg')

    def map_rgb(color_rgb: Tuple[int]) -> Tuple[float]:
        assert len(color_rgb) == 3, 'Invalid '
        o_tuple: Tuple[float] = cast(Tuple[float], (*[float_map(col, 0.00, 255.00, 0.00, 1.00) for col in color_rgb],))

        return o_tuple

    def hex_to_rgb(color: HexColor) -> Tuple[int]:
        return cast(Tuple[int], tuple(int("".join(i for i in re.findall(r"\w", color.color))[j:j + 2], 16) for j in (0, 2, 4)))

    col1: Tuple[int] = hex_to_rgb(bg)
    col2: Tuple[int] = hex_to_rgb(fg)
    adjusted_contrast_ratio = wcag_contrast_ratio.rgb(map_rgb(col1), map_rgb(col2)) + adjustment

    AA_res = wcag_contrast_ratio.passes_AA(adjusted_contrast_ratio)
    AAA_res = wcag_contrast_ratio.passes_AAA(adjusted_contrast_ratio)

    return AA_res, AAA_res


def data_at_dict_path(path: str, dictionary: Dict[Any, Any]) -> Tuple[bool, Any]:
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

    def tr(com: Callable[[Any, Any], Any], *args: Any) -> Tuple[bool, Any]:
        try:
            return True, com(*args)
        except Exception as E:
            return False, E

    for index, token in enumerate(path_tokens):
        if token == "root" and index == 0:
            continue

        found = token in data
        if not found:
            for t in (int, float, bool):
                f1, t1 = tr(t, token)
                if f1 and t1 in data:
                    found = True
                    token = t1
                    break

        data = data[token] if found else None

        if index != len(path_tokens) - 1:
            if type(data) is not dict:
                found = False

        if not found:
            break

    return found, data


def show_bl_err(title: str, message: str) -> None:
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

    Takes in qa_files path `file_path`, splits the path into a qa_files name the directory path

    :param file_path: Filename with path
    :return: Tuple [Path, Filename]
    """

    return File.split_file_path(file_path)


def dict_check_redundant_data_inter_dict(dic: Dict[Any, Any], dic2: Dict[Any, Any], root_name: str = '<root>') -> Tuple[bool, Set[str]]:
    """
    Checks for redundant data between two dictionaries
    """

    assert isinstance(dic, dict)
    assert isinstance(dic2, dict)
    assert isinstance(root_name, str)

    def rec_add(d: Dict[Any, Any], d2: Dict[Any, Any], root: str = '<root>') -> Tuple[bool, Dict[str, Tuple[str, ...]], Set[str]]:
        assert isinstance(d, dict)
        assert isinstance(d2, dict)
        assert isinstance(root, str)

        b = True
        oc: Dict[str, Tuple[str, ...]] = {}
        fnc: Set[str] = set()

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


def dict_check_redundant_data(dic: Dict[Any, Any], root_name: str = '<root>') -> Tuple[bool, Set[str]]:
    """
    Checks for redundant data within a dictionary
    """

    assert isinstance(dic, dict)
    assert isinstance(root_name, str)

    def rec_add(d: Dict[Any, Any], root: str = '<root>') -> Tuple[bool, Dict[str, Tuple[str, ...]], Set[str]]:
        assert isinstance(d, dict)
        assert isinstance(root, str)

        b = True
        oc: Dict[str, Tuple[str, ...]] = {}
        fnc: Set[str] = set()

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


def copy_to_clipboard(text: str, shell: Union[tk.Tk, tk.Toplevel], clear_old: bool = True) -> None:
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
    assert len(text) <= 10000  # Max length = 10000
    assert isinstance(clear_old, bool)

    if clear_old:
        shell.clipboard_clear()

    shell.clipboard_append(text)
    shell.update()


def brute_force_decoding(data: bytes, excluded_encodings: Tuple[str, ...], extra_encodings_to_try: Tuple[str, ...] = ()) -> Tuple[str, str]:
    """

    **BRUTE_FORCE_DECODING**

    Will attempt to decode the given bytes data;
    Tries the following encodings:

    * UTF-7
    * UTF-8
    * UTF-16
    * UTF-32

    Will raise exception if no encodings work

    :param data: Read the name
    :param excluded_encodings: Read the name
    :param extra_encodings_to_try: Read the name
    :return: (encoding used, string) **
    """

    encodings = ('UTF-8', 'UTF-16', *extra_encodings_to_try)
    for encoding in encodings:
        if encoding in excluded_encodings:
            continue

        try:
            return encoding, data.decode(encoding)
        except:
            continue

    raise Exception("encoding not found")


def data_type_converter(
        original: Union[str, bytes, List[Any], Tuple[Any, ...], Set[Any], Dict[Any, Any], int, float],
        output_type: type,
        cfa: ConverterFunctionArgs
) -> Union[Any]:

    """
    **DATA_TYPE_CONVERTOR**

    Automatically converts from numerous different data types to other data types

    Supported data types:
    * str
    * bytes  ( CAST TO UTF-8 )
    * list
    * tuple
    * set
    * dict
    * int
    * float

    *Specific conversions are not allowed; (e.g.) [List/Tuple/Set] --> [Int/Float] is allowed, but not the other way around.


    :param original: Original data
    :param output_type: Data type to convert to
    :param cfa: ConverterFunctionArguments
    :return:
    """

    if isinstance(original, output_type):
        if isinstance(original, bytes):
            # Check encoding
            exp = App.ENCODING
            try:
                original.decode(exp)
                return original     # All good

            except:
                try:
                    _, s = brute_force_decoding(original, (exp, ))
                    return s.encode(exp)

                except:
                    raise_error(
                        UnicodeEncodeError, ["Encoding for given bytes data not known"], ErrorLevels.NON_FATAL
                    )

        else:
            return original

    accepted_input = (str, bytes, list, tuple, set, dict, int, float)
    assert type(original) in accepted_input, f"Original data type ({type(original)}) not supported"

    original_type = type(original)

    def RE(e: Any) -> None:
        raise_error(TypeError, [f"Failed to convert from {original_type} to {output_type} for given data: {str(e)}"], ErrorLevels.NON_FATAL)

    multi = (list, tuple, set, dict)
    single = (str, bytes, int, float)

    if original_type in single:
        if output_type in multi:
            assert original_type not in (float, int), "Unsupported conversion (Int/Float => List/Tuple/Set/Dict)"

            if output_type in (list, tuple, set):
                ns: Optional[str] = cast(Optional[str], data_type_converter(cfa.list_line_sep, original_type, cfa))
                no: str = cast(str, data_type_converter(original, original_type, cfa))  # For bytes encoding

                o = no.split(ns)

                del ns, no
                return output_type(o)

            elif output_type is dict:
                nsa: Optional[str] = cast(Optional[str], data_type_converter(cfa.dict_line_sep, original_type, cfa))
                noa: str = cast(str, data_type_converter(original, original_type, cfa))  # For bytes encoding

                oa = noa.split(nsa)
                oa1 = {}

                for item in oa:
                    k, v = \
                        item.split(cast(str, cfa.dict_key_val_sep))[0], \
                        item.replace(item.split(cast(str, cfa.dict_key_val_sep))[0], data_type_converter('', original_type, cfa), 1).lstrip()

                    oa1[k] = v

                return oa1

            else:
                raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

        elif output_type in single:  # DONE
            if output_type in (int, float) and original_type is str:  # DONE ?
                try:
                    return output_type(float(cast(str, original)))

                except Exception as E:
                    RE(E)

            elif output_type in (int, float) and original_type is bytes:  # DONE ?
                s = '0'

                try:
                    s = cast(bytes, original).decode(App.ENCODING)
                except:
                    try:
                        _, s = brute_force_decoding(cast(bytes, original), (App.ENCODING,))

                    except Exception as E:
                        RE(E)

                if s is not None:
                    try:
                        return output_type(s)
                    except Exception as E:
                        RE(E)

                return None

            elif output_type is bytes and isinstance(original, str):  # DONE
                return original.encode(App.ENCODING)

            elif output_type is str and original_type is bytes:  # DONE
                try:
                    return cast(bytes, original).decode(App.ENCODING)
                except Exception as E:
                    try:
                        _, s = brute_force_decoding(cast(bytes, original), (App.ENCODING,))
                        return s
                    except Exception as E:
                        RE("Unknown encoding for given bytes data.")

            elif output_type in (str, bytes) and original_type in (int, float):
                o1 = str(original)
                return o1 if output_type is str else o1.encode(App.ENCODING)

            elif output_type in (int, float) and original_type in (int, float):
                return output_type(original)

            else:
                raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

        else:
            raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

    elif original_type in multi:
        if output_type in multi:
            if isinstance(original, (list, tuple, set)):  # DONE
                if output_type is dict:  # DONE
                    of: Dict[str, str] = {}

                    for item_b in original:
                        n_item: str = cast(str, data_type_converter(item_b, str, cfa))  # (Recursive)
                        assert isinstance(n_item, str)

                        str_tokens: List[str] = n_item.split(cast(str, cfa.dict_key_val_sep))
                        k, v = str_tokens[0], n_item.replace(str_tokens[0], '', 1).lstrip()

                        of[k] = v

                    return of

                elif output_type is list:
                    return [*original]

                elif output_type is tuple:
                    return (*original, )

                elif output_type is set:
                    return {*original}

                else:
                    raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

            elif original_type is dict:  # DONE
                if output_type in (list, tuple, set):  # DONE ?
                    sep = cfa.dict_key_val_sep
                    n_sep = data_type_converter(sep, str, cfa)

                    if type(sep) not in (str, bytes):
                        sep = n_sep

                    o = []

                    for ok, ov in cast(Dict[Any, Any], original).items():
                        k, v = \
                            data_type_converter(ok, str, cfa), \
                            data_type_converter(ov, str, cfa)

                        o.append(data_type_converter(f"{k}{n_sep}{v}", type(sep), cfa))

                    return output_type(o)  # Cast to appropriate type

                else:
                    raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

            else:
                raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

        elif output_type in single:
            if original_type in (list, tuple, set):
                if output_type in (float, int):
                    try:
                        return output_type(sum(cast(Iterable[Union[int, float]], original)))
                    except:
                        acc = 0.0

                        for item in cast(Iterable[Any], original):
                            acc += cast(float, data_type_converter(item, float, cfa))

                        return output_type(acc)

                elif output_type in (str, bytes):
                    o1 = ""
                    for item_f in cast(Union[List[Any], Set[Any], Tuple[Any, ...]], original):
                        i2 = cast(str, data_type_converter(item_f, str, cfa))
                        o1 += f"{i2}{cast(str, data_type_converter(cfa.list_line_sep, str, cfa))}"

                    if output_type is str:
                        return o1
                    elif output_type is bytes:
                        return o1.encode(App.ENCODING)
                    else:
                        raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

                else:
                    raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

            if isinstance(original, dict):
                if output_type in (float, int):
                    return output_type(sum(list(cast(Dict[Any, Union[int, float]], original).values())))

                elif output_type in (str, bytes):
                    o1 = ""

                    for key, val in original.items():
                        k2, v2 = \
                            cast(str, data_type_converter(key, str, cfa)), \
                            cast(str, data_type_converter(val, str, cfa))

                        o1 += f"{k2}{cast(str, data_type_converter(cfa.dict_key_val_sep, str, cfa))}{v2}{cast(str, data_type_converter(cfa.dict_line_sep, str, cfa))}"

                    if output_type is str:
                        return o1
                    elif output_type is bytes:
                        return o1.encode(App.ENCODING)
                    else:
                        raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

                else:
                    raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

            else:
                raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

        else:
            raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

    else:
        raise_error(UnexpectedEdgeCase, [f'{original_type} -> {output_type}'], ErrorLevels.NON_FATAL)

    return None


def gen_short_uid(prefix: str = "qa") -> str:
    """
    Generates a LONG UID str, including the current time's hash (MD5)

    :param prefix: String to include at beginning of UID (ID purposes)
    :return: UID (str)
    """

    t = hashlib.md5(time.ctime(time.time()).encode()).hexdigest()
    r = (random.randint(11111, 99999) + random.random()) * 10 ** 3
    ra = int(random.random() * 10 ** 3)

    r *= ra if ra != 0 else 1
    return f"{prefix}::{t}_{r}_{str(random.random()).split('.')[-1]}"


class SMem:
    def __init__(self, size: int = 2048) -> None:
        assert isinstance(size, int)

        self.NullStr = '<!QApp::STD::SMEM(SharedMemory)::Code::NULL!>@$'

        self.size = size
        self.r1 = random.randint(10, 99)
        self.r2 = random.randint(10, 99)
        self.r3 = random.randint(10, 99)
        self.r4 = random.randint(10, 99)
        self.r5 = int(random.randint(10000, 99999))
        self.name = "%s%s%s%s" % (self.r4, self.r3, self.r1, self.r2)
        self.mem = SharedMemoryDict(name=self.name, size=self.size)

    def set(self, data: str, add: int = 0) -> None:
        assert isinstance(add, int)
        self.mem[str(self.r5 + add)] = data

    def get(self, add: int = 0) -> Union[None, str]:
        assert isinstance(add, int)
        return cast(Union[None, str], self.mem.get(str(self.r5 + add)))

    def get_name(self) -> str:
        return self.name

    def get_size(self) -> int:
        return self.size


def clamp(minimum: Union[int, float], actual: Union[int, float], maximum: Union[int, float]) -> Union[int, float]:
    return minimum if (actual < minimum) else (maximum if (actual > maximum) else actual)


class ANSI:
    FG_BLACK = "\x1b[30m"
    FG_RED = '\x1b[31m'
    FG_GREEN = '\x1b[32m'
    FG_YELLOW = '\x1b[33m'
    FG_BLUE = '\x1b[34m'
    FG_MAGENTA = '\x1b[35m'
    FG_CYAN = '\x1b[36m'
    FG_WHITE = '\x1b[37m'

    FG_BRIGHT_RED = '\x1b[31;1m'
    FG_BRIGHT_GREEN = '\x1b[32;1m'
    FG_BRIGHT_YELLOW = '\x1b[33;1m'
    FG_BRIGHT_BLUE = '\x1b[34;1m'
    FG_BRIGHT_MAGENTA = '\x1b[35;1m'
    FG_BRIGHT_CYAN = '\x1b[36;1m'
    FG_BRIGHT_WHITE = '\x1b[37;1m'

    BG_BLACK = "\x1b[40m"
    BG_RED = '\x1b[41m'
    BG_GREEN = '\x1b[42m'
    BG_YELLOW = '\x1b[43m'
    BG_BLUE = '\x1b[44m'
    BG_MAGENTA = '\x1b[45m'
    BG_CYAN = '\x1b[46m'
    BG_WHITE = '\x1b[47m'

    BG_BRIGHT_RED = '\x1b[41;1m'
    BG_BRIGHT_GREEN = '\x1b[42;1m'
    BG_BRIGHT_YELLOW = '\x1b[43;1m'
    BG_BRIGHT_BLUE = '\x1b[44;1m'
    BG_BRIGHT_MAGENTA = '\x1b[45;1m'
    BG_BRIGHT_CYAN = '\x1b[46;1m'
    BG_BRIGHT_WHITE = '\x1b[47;1m'

    BOLD = '\x1b[1m'
    UNDERLINE = '\x1b[4m'
    REVERSED = '\x1b[7m'
    RESET = '\x1b[0m'


class AppLogColors:
    THEMING_UTILITY = ANSI.FG_BRIGHT_YELLOW
    ADMIN_TOOLS = ANSI.FG_BRIGHT_RED
    QUIZZING_FORM = ANSI.FG_BRIGHT_CYAN
    RECOVERY_UTILITY = ANSI.FG_BRIGHT_GREEN
    QA_PROMPTS = ANSI.FG_BRIGHT_MAGENTA

    DEFAULT = ANSI.RESET
    EXTRA = f"{ANSI.UNDERLINE}{ANSI.BOLD}{ANSI.REVERSED}"


def flatten_list(ls: Union[List[Any], Tuple[Any, ...], Set[Any]], *additional_functions: Callable[[Any], Any]) -> List[Any]:
    """
    Flattens iterable objects; example: ([1, 2, 3], [4], {5, 6}) --> [1, 2, 3, 4, 5, 6]
    :param ls: Input (iterable)
    :param additional_functions: Additional functions to apply to each item (lambda statements; syntax: lambda *args; args[0] will be supplied with the item.)
    :return: flattened list
    """

    if len(additional_functions) == 0:
        return [
            item
            for sublist in ls
            for item in sublist
        ]

    else:
        fls = flatten_list(ls)
        new_fls = []
        for item in fls:
            i = None
            for function in additional_functions:
                i = function(item)

            new_fls.append(i)

        return new_fls
