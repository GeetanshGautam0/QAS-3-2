import pytest, os, sys, json, hashlib, subprocess, copy
from qa_functions.qa_std import data_type_converter, brute_force_decoding, data_at_dict_path, float_map, \
    flatten_list, ANSI
from qa_functions.qa_file_handler import _Crypt
from qa_functions.qa_custom import ConverterFunctionArgs, HexColor, UnexpectedEdgeCase
from qa_functions.qa_colors import Convert as ConvertColor, Functions as ColorFunctions
from qa_functions.qa_info import file_hash
from qa_functions.qa_svh import compile_svh_with_fn
from typing import Tuple, cast
from ctypes import windll


ROOT_RUN = "<PYTHON ? RUN_COMMAND>"


def test_cryptography() -> None:
    CryptTestString = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()-=_+`~ -> None"
    CryptTestKey = b"JdLNcw-2nAD_GrrDOgiSBcq6b21MinfQeRr-neeHLUw="
    assert data_type_converter(
        _Crypt.decrypt(
            _Crypt.encrypt(
                data_type_converter(CryptTestString, bytes, ConverterFunctionArgs()),
                CryptTestKey,
                ConverterFunctionArgs(),
                True
            ),
            CryptTestKey,
            ConverterFunctionArgs(),
            True
        ),
        str, ConverterFunctionArgs()
    ) == CryptTestString, "qa_file_handler._Crypt.encrypt"


def test_brute_force_decoding() -> None:
    assert brute_force_decoding('TestString'.encode('UTF-8'), (), ()) == ('UTF-8', 'TestString'), \
        "brute_force_decoding: UTF-8"

    assert brute_force_decoding('TestString'.encode('UTF-16'), (), ()) == ('UTF-16', 'TestString'), \
        "brute_force_decoding: UTF-16"


def test_convert_to_float() -> None:
    assert data_type_converter(b'1', float, ConverterFunctionArgs()) == 1.0, \
        "dtc - <bytes> -> <float>"

    assert data_type_converter('1', float, ConverterFunctionArgs()) == 1.0, \
        "dtc - <str> -> <float>"

    assert data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        float,
        ConverterFunctionArgs()
    ) == 148.18382323, "dtc - <list> -> <float>"

    assert data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        float,
        ConverterFunctionArgs()
    ) == 148.18382323, "dtc - <tuple> -> <float>"

    assert data_type_converter(
        {1, 2, 3, b"4", "5", 10.0, 123.18382323},
        float,
        ConverterFunctionArgs()
    ) == 148.18382323, "dtc - <set> -> <float>"

    assert data_type_converter(
        {1: 2, 3: 4, 5: 6},
        float,
        ConverterFunctionArgs()
    ) == 12.0, 'dtc - <dict> -> <float>'

    with pytest.raises(AssertionError):
        data_type_converter(
            False,
            float,
            ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        data_type_converter(
            True,
            float,
            ConverterFunctionArgs()
        )


def test_convert_to_int() -> None:
    assert data_type_converter(b'1', int, ConverterFunctionArgs()) == 1, \
        "dtc - <bytes> -> <int>"

    assert data_type_converter('1.2', int, ConverterFunctionArgs()) == 1, \
        "dtc - <str> -> <int>"

    assert data_type_converter('1.9', int, ConverterFunctionArgs()) == 1, \
        "dtc - <str> -> <int>"

    assert data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        int,
        ConverterFunctionArgs()
    ) == 148, "dtc - <list> -> <int>"

    assert data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        int,
        ConverterFunctionArgs()
    ) == 148, "dtc - <tuple> -> <int>"

    assert data_type_converter(
        {1, 2, 3, b"4", "5", 10.0, 123.18382323},
        int,
        ConverterFunctionArgs()
    ) == 148, "dtc - <set> -> <int>"

    assert data_type_converter(
        {1: 2, 3: 4, 5: 6},
        int,
        ConverterFunctionArgs()
    ) == 12, 'dtc - <dict> -> <int>'

    assert data_type_converter(
        False,
        int,
        ConverterFunctionArgs()
    ) == 0, "dtc - <bool[False]> -> <int>"

    assert data_type_converter(
        True,
        int,
        ConverterFunctionArgs()
    ) == 1, "dtc - <bool[True]> -> <int>"


def test_convert_to_str() -> None:
    assert data_type_converter(b'1', str, ConverterFunctionArgs()) == '1', \
        "dtc - <bytes> -> <str>"

    assert data_type_converter(1.2, str, ConverterFunctionArgs()) == '1.2', \
        "dtc - <int> -> <str>"

    assert data_type_converter(1, str, ConverterFunctionArgs()) == '1', \
        "dtc - <float> -> <str>"

    assert data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        str,
        ConverterFunctionArgs()
    ).strip() == "1\n2\n3\n4\n5\n10.0\n123.18382323", "dtc - <list> -> <str>"

    assert data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        str,
        ConverterFunctionArgs()
    ).strip() == "1\n2\n3\n4\n5\n10.0\n123.18382323", "dtc - <tuple> -> <str>"

    assert data_type_converter(
        {1: 2, 3: 4, 5: 6},
        str,
        ConverterFunctionArgs()
    ).strip() == '1 2\n3 4\n5 6', 'dtc - <dict> -> <str>'

    with pytest.raises(AssertionError):
        data_type_converter(
            False,
            str,
            ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        data_type_converter(
            True,
            str,
            ConverterFunctionArgs()
        )


def test_convert_to_bytes() -> None:
    assert data_type_converter('1', bytes, ConverterFunctionArgs()) == b'1', \
        "dtc - <str> -> <bytes>"

    assert data_type_converter(1.2, bytes, ConverterFunctionArgs()) == b'1.2', \
        "dtc - <int> -> <bytes>"

    assert data_type_converter(1, bytes, ConverterFunctionArgs()) == b'1', \
        "dtc - <float> -> <bytes>"

    assert data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        bytes,
        ConverterFunctionArgs()
    ).strip() == b"1\n2\n3\n4\n5\n10.0\n123.18382323", "dtc - <list> -> <bytes>"

    assert data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        bytes,
        ConverterFunctionArgs()
    ).strip() == b"1\n2\n3\n4\n5\n10.0\n123.18382323", "dtc - <tuple> -> <bytes>"

    assert data_type_converter(
        {1: 2, 3: 4, 5: 6},
        bytes,
        ConverterFunctionArgs()
    ).strip() == b'1 2\n3 4\n5 6', 'dtc - <dict> -> <bytes>'

    with pytest.raises(AssertionError):
        data_type_converter(
            False,
            bytes,
            ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        data_type_converter(
            True,
            bytes,
            ConverterFunctionArgs()
        )


def test_convert_to_list() -> None:
    assert data_type_converter('', list, ConverterFunctionArgs()) == [''], \
        "dtc - <str> -> <list> (empty1)"

    assert data_type_converter(' ', list, ConverterFunctionArgs()) == [' '], \
        "dtc - <str> -> <list> (empty1)"

    assert data_type_converter(b'1', list, ConverterFunctionArgs()) == [b'1'], \
        "dtc - <bytes> -> <list> (short)"

    assert data_type_converter(
        b"1\n2\n3\n4\n5\n10.0\n123.18382323",
        list,
        ConverterFunctionArgs()
    ) == [b"1", b"2", b"3", b"4", b"5", b"10.0", b"123.18382323"], "dtc - <bytes> -> <list> (long)"

    assert data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        list,
        ConverterFunctionArgs()
    ) == [1, 2, 3, b"4", "5", 10.0, 123.18382323], "dtc - <tuple> -> <list>"

    assert data_type_converter(
        {1: 2, 3: 4, 5: 6},
        list,
        ConverterFunctionArgs()
    ) == ['1 2', '3 4', '5 6'], 'dtc - <dict> -> <list>'

    with pytest.raises(AssertionError):
        data_type_converter(1.2, list, ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        data_type_converter(1, list, ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        data_type_converter(
            False,
            list,
            ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        data_type_converter(
            True,
            list,
            ConverterFunctionArgs()
        )


def test_convert_to_tuple() -> None:
    assert data_type_converter('', tuple, ConverterFunctionArgs()) == ('',), \
        "dtc - <str> -> <tuple> (empty1)"

    assert data_type_converter(' ', tuple, ConverterFunctionArgs()) == (' ',), \
        "dtc - <str> -> <tuple> (empty1)"

    assert data_type_converter(b'1', tuple, ConverterFunctionArgs()) == (b'1',), \
        "dtc - <bytes> -> <tuple> (short)"

    assert data_type_converter(
        b"1\n2\n3\n4\n5\n10.0\n123.18382323",
        tuple,
        ConverterFunctionArgs()
    ) == (b"1", b"2", b"3", b"4", b"5", b"10.0", b"123.18382323"), "dtc - <bytes> -> <tuple> (long)"

    assert data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        tuple,
        ConverterFunctionArgs()
    ) == (1, 2, 3, b"4", "5", 10.0, 123.18382323), "dtc - <list> -> <tuple>"

    assert data_type_converter(
        {1: 2, 3: 4, 5: 6},
        tuple,
        ConverterFunctionArgs()
    ) == ('1 2', '3 4', '5 6'), 'dtc - <dict> -> <tuple>'

    with pytest.raises(AssertionError):
        data_type_converter(1.2, tuple, ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        data_type_converter(1, tuple, ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        data_type_converter(
            False,
            tuple,
            ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        data_type_converter(
            True,
            tuple,
            ConverterFunctionArgs()
        )


def test_data_at_dict_path() -> None:
    assert data_at_dict_path(
        'a', {}
    ) == (False, None), \
        "data_at_dict_path - nf_test"

    assert data_at_dict_path(
        'a', {'a': []}
    ) == (True, []), \
        "data_at_dict_path - f_test"

    assert data_at_dict_path(
        '2\\1\\4\\a', {
            '2': {
                'a': False,
                '1': {
                    1: None,
                    2: None,
                    3: None,
                    4: {
                        'A': None,
                        'a': ['OK']
                    }
                }
            }
        }
    ) == (True, ['OK']), \
        "data_at_dict_path - nest_test"


def test_colors() -> None:
    assert ConvertColor.RGBToHex((255, 255, 255)) == '#ffffff'
    assert ConvertColor.HexToRGB('#000000') == (0, 0, 0)
    assert ColorFunctions.calculate_more_contrast(
        HexColor('#ffffff'), HexColor('#000000'), HexColor('#330a00')
    ).color.lower().strip() == "#ffffff"

    expected = ('#202020', '#202020', '#212121', '#222222', '#232323', '#242424', '#252525', '#262626', '#272727', '#282828', '#292929', '#2a2a2a',
                 '#2b2b2b', '#2c2c2c', '#2d2d2d', '#2e2e2e', '#2f2f2f', '#303030', '#313131', '#323232', '#333333', '#343434', '#353535', '#363636',
                 '#373737', '#383838', '#393939', '#3a3a3a', '#3b3b3b', '#3c3c3c', '#3d3d3d', '#3e3e3e', '#3f3f3f', '#404040', '#414141', '#424242',
                 '#434343', '#444444', '#454545', '#464646', '#474747', '#484848', '#494949', '#4a4a4a', '#4b4b4b', '#4c4c4c', '#4d4d4d', '#4e4e4e',
                 '#4f4f4f', '#505050', '#515151', '#525252', '#535353', '#545454', '#555555', '#565656', '#575757', '#585858', '#595959', '#5a5a5a',
                 '#5b5b5b', '#5c5c5c', '#5d5d5d', '#5e5e5e', '#5f5f5f', '#606060', '#616161', '#626262', '#636363', '#646464', '#656565', '#666666',
                 '#676767', '#686868', '#696969', '#6a6a6a', '#6b6b6b', '#6c6c6c', '#6d6d6d', '#6e6e6e', '#6f6f6f', '#707070', '#717171', '#727272',
                 '#737373', '#747474', '#757575', '#767676', '#777777', '#787878', '#797979', '#7a7a7a', '#7b7b7b', '#7c7c7c', '#7d7d7d', '#7e7e7e',
                 '#7f7f7f', '#808080', '#818181', '#828282', '#838383', '#848484', '#858585', '#868686', '#878787', '#888888', '#898989', '#8a8a8a',
                 '#8b8b8b', '#8c8c8c', '#8d8d8d', '#8e8e8e', '#8f8f8f', '#909090', '#919191', '#929292', '#939393', '#949494', '#959595', '#969696',
                 '#979797', '#989898', '#999999', '#9a9a9a', '#9b9b9b', '#9c9c9c', '#9d9d9d', '#9e9e9e', '#9f9f9f', '#a0a0a0', '#a1a1a1', '#a2a2a2',
                 '#a3a3a3', '#a4a4a4', '#a5a5a5', '#a6a6a6', '#a7a7a7', '#a8a8a8', '#a9a9a9', '#aaaaaa', '#ababab', '#acacac', '#adadad', '#aeaeae',
                 '#afafaf', '#b0b0b0', '#b1b1b1', '#b2b2b2', '#b3b3b3', '#b4b4b4', '#b5b5b5', '#b6b6b6', '#b7b7b7', '#b8b8b8', '#b9b9b9', '#bababa',
                 '#bbbbbb', '#bcbcbc', '#bdbdbd', '#bebebe', '#bfbfbf', '#c0c0c0', '#c1c1c1', '#c2c2c2', '#c3c3c3', '#c4c4c4', '#c5c5c5', '#c6c6c6',
                 '#c7c7c7', '#c8c8c8', '#c9c9c9', '#cacaca', '#cbcbcb', '#cccccc', '#cdcdcd', '#cecece', '#cfcfcf', '#d0d0d0', '#d1d1d1', '#d2d2d2',
                 '#d3d3d3', '#d4d4d4', '#d5d5d5', '#d6d6d6', '#d7d7d7', '#d8d8d8', '#d9d9d9', '#dadada', '#dbdbdb', '#dcdcdc', '#dddddd', '#dedede',
                 '#dfdfdf', '#e0e0e0', '#e1e1e1', '#e2e2e2', '#e3e3e3', '#e4e4e4', '#e5e5e5', '#e6e6e6', '#e7e7e7', '#e8e8e8', '#e9e9e9', '#eaeaea',
                 '#ebebeb', '#ececec', '#ededed', '#eeeeee', '#efefef', '#f0f0f0', '#f1f1f1', '#f2f2f2', '#f3f3f3', '#f4f4f4', '#f5f5f5', '#f6f6f6',
                 '#f7f7f7', '#f8f8f8', '#f9f9f9', '#fafafa', '#fbfbfb', '#fcfcfc', '#fdfdfd', '#fefefe', '#ffffff')

    assert cast(Tuple[str, ...], ColorFunctions.fade('#202020', '#ffffff')) == \
           cast(Tuple[str, ...], expected), "ColorFunctions.fade: unexpected output."


def test_float_map() -> None:
    assert float_map(1, 0, 10, 0, 5, False) == .5
    assert float_map(20, 0, 100, 0, 5, False) == 1
    assert float_map(-.1, 0, 5, 0, 1000, True) == -20
    with pytest.raises(AssertionError):
        float_map(-10, -1, 10, 0, 1, False)


def test_src_files() -> None:
    global ROOT_RUN

    excl = ('venv', 'unins000.dat', 'unins000.exe', '.qa_update', 'TODO', 'additional_themes', '.git', '.idea', '.mypy_cache', '.pytest_cache', '__pycache__', '', 'dist', 'build', 'installer')
    addons = ('ADDONS_THEME', )
    lsa = []

    with open('.config\\update_commands.json') as file:
        sd = json.loads(file.read().strip())
        for i in addons:
            if i in sd:
                sd.pop(i)

        lsd = [*{*flatten_list(
            [(*d.values(), ) for d in [*sd.values()]],
            lambda *args: ".\\{}".format(args[0].replace('/', '\\')),
        )}]
        file.close()

    for ls in copy.deepcopy(lsd):
        if ROOT_RUN in ls:
            lsd.pop(lsd.index(ls))

    def rc(root: str) -> None:
        ls = os.listdir(root)
        for f in ls:
            if f not in excl and "exclude_" not in f:
                if os.path.isdir(f"{root}\\{f}"):
                    rc(f"{root}\\{f}")
                elif os.path.isfile(f"{root}\\{f}"):
                    if f"{root}\\{f}" not in lsd:
                        sys.stderr.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_RED}[SRC] ERROR: File \"{root}\\{f}\" not included in UPDATE_COMMANDS{ANSI.RESET}\n")
                        lsa.append(f"{root}\\{f}")
                    else:
                        lsd.pop(lsd.index(f"{root}\\{f}"))

                else:
                    raise UnexpectedEdgeCase(f"Item type unknown for \"{root}\\{f}\".")

    rc('.')
    for a in lsd:
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_YELLOW}[SRC] WARNING: File \"{a}\" included in UPDATE_COMMANDS but doesn't actually exist.{ANSI.RESET}\n")

    assert len(lsa) == 0, f"The following files are not included in UPDATE_COMMANDS:\n\t* %s" % "\n\t* ".join(lsa)


def test_installer_iss() -> None:
    if not os.path.isfile("installer\\installer.iss"):
        return

    rt = "<test::uninstaller>"
    excl = ('venv', 'unins000.dat', 'unins000.exe', 'TODO', '.git', '.idea', '__pycache__', '.mypy_cache', '.pytest_cache', 'additional_themes', 'build', 'dist', 'installer')
    
    req = {*[i for i in os.listdir() if (i not in excl and "exclude_" not in i)]}
    extn_req = {*[i.split('.')[-1] for i in req if os.path.isfile(i)]}
    extn_del = []
    item_del = []
    
    with open("installer\\installer.iss", 'r') as iss_file:
        iss_data = iss_file.read()
        iss_file.close()

    fail = False

    if f"; {rt} start_here" in iss_data and f"; {rt} stop_here" in iss_data:
        if iss_data.count(f"; {rt} start_here") == iss_data.count(f"; {rt} stop_here") == 1:
            iss_data = iss_data.split(f"; {rt} start_here")[-1].split(f"; {rt} stop_here")[0]
            
            for line in iss_data.split('\n'):
                if len(line.strip()) == 0:
                    continue
                
                line = line.split("Name:")[-1].replace('{app}', '').strip().split('\"')[1].strip('\\')
                
                if '*.' in line:
                    extn_del.append(line.split('.')[-1])
                    if line.split('.')[-1] not in extn_req:
                        sys.stdout.write(f"{ANSI.FG_BRIGHT_YELLOW}{ANSI.BOLD}[WARNING] [INSTALLER] Extension \".{line.split('.')[-1]}\" in delete commands; not found in source directry.{ANSI.RESET}\n")
                        fail = True

                else:
                    item_del.append(line)
                    if line not in req:
                        sys.stdout.write(f"{ANSI.FG_BRIGHT_YELLOW}{ANSI.BOLD}[WARNING] [INSTALLER] Item \"{line}\" in delete commands; not found in source directry.{ANSI.RESET}\n")
                        fail = True
        else:
            assert False, "Invalid start and end points in iss_data."
    else:
        assert False, "Start and end points not found in iss_data."

    for name in req:
        extn = name.split('.')[-1]
        if extn not in extn_del and name not in item_del:
            sys.stdout.write(f"{ANSI.FG_BRIGHT_YELLOW}{ANSI.BOLD}[WARNING] [INSTALLER] Item \"{name}\" not covered by deletion commands.{ANSI.RESET}\n")
            fail = True

    assert not fail, "Potential failure in uninstaller (see warnings)."


def test_script_hash() -> None:
    subprocess.call('', shell=True)
    if os.name == 'nt':  # Only if we are running on Windows
        k = windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)

    svh, _ = compile_svh_with_fn()
    failures = []

    for f, h in svh.items():
        if file_hash.get(f) != h:
            m1: str = file_hash[f]['md5'] if file_hash.get(f) is not None else None
            s1: str = file_hash[f]['sha'] if m1 is not None else None
            failures.append(
                f"Invalid hash stored for file '{f}'; expected:\n\t* MD5: {ANSI.BOLD}{ANSI.FG_BRIGHT_MAGENTA}{h['md5']}{ANSI.RESET}\n\t* SHA3 (512): {ANSI.BOLD}{ANSI.FG_BRIGHT_CYAN}{h['sha']}{ANSI.RESET}\n\tGot:\n\t\t* MD5: {ANSI.BOLD}{ANSI.FG_BRIGHT_MAGENTA}{m1}{ANSI.RESET}\n\t\t* SHA3 (512): {ANSI.BOLD}{ANSI.FG_BRIGHT_CYAN}{s1}{ANSI.RESET}\n"
            )

    assert len(failures) == 0, "\n".join(failures).strip()

