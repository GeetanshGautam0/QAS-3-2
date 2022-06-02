import qa_functions, pytest, os, sys, json
from typing import *


def test_cryptography():
    CryptTestString = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()-=_+`~"
    CryptTestKey = b"JdLNcw-2nAD_GrrDOgiSBcq6b21MinfQeRr-neeHLUw="
    assert qa_functions.data_type_converter(
        qa_functions.qa_file_handler._Crypt.decrypt(
            qa_functions.qa_file_handler._Crypt.encrypt(
                qa_functions.data_type_converter(CryptTestString, bytes, qa_functions.ConverterFunctionArgs()),
                CryptTestKey,
                qa_functions.ConverterFunctionArgs(),
                True
            ),
            CryptTestKey,
            qa_functions.ConverterFunctionArgs(),
            True
        ),
        str, qa_functions.ConverterFunctionArgs()
    ) == CryptTestString, "qa_functions.qa_file_handler._Crypt.encrypt"


def test_brute_force_decoding():
    assert qa_functions.brute_force_decoding('TestString'.encode('UTF-8'), (), ()) == ('UTF-8', 'TestString'), \
        "qa_functions.brute_force_decoding: UTF-8"

    assert qa_functions.brute_force_decoding('TestString'.encode('UTF-16'), (), ()) == ('UTF-16', 'TestString'), \
        "qa_functions.brute_force_decoding: UTF-16"


def test_convert_to_float():
    assert qa_functions.data_type_converter(b'1', float, qa_functions.ConverterFunctionArgs()) == 1.0, \
        "qa_functions.dtc - <bytes> -> <float>"

    assert qa_functions.data_type_converter('1', float, qa_functions.ConverterFunctionArgs()) == 1.0, \
        "qa_functions.dtc - <str> -> <float>"

    assert qa_functions.data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        float,
        qa_functions.ConverterFunctionArgs()
    ) == 148.18382323, "qa_functions.dtc - <list> -> <float>"

    assert qa_functions.data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        float,
        qa_functions.ConverterFunctionArgs()
    ) == 148.18382323, "qa_functions.dtc - <tuple> -> <float>"

    assert qa_functions.data_type_converter(
        {1, 2, 3, b"4", "5", 10.0, 123.18382323},
        float,
        qa_functions.ConverterFunctionArgs()
    ) == 148.18382323, "qa_functions.dtc - <set> -> <float>"

    assert qa_functions.data_type_converter(
        {1: 2, 3: 4, 5: 6},
        float,
        qa_functions.ConverterFunctionArgs()
    ) == 12.0, 'qa_functions.dtc - <dict> -> <float>'

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            False,
            float,
            qa_functions.ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            True,
            float,
            qa_functions.ConverterFunctionArgs()
        )


def test_convert_to_int():
    assert qa_functions.data_type_converter(b'1', int, qa_functions.ConverterFunctionArgs()) == 1, \
        "qa_functions.dtc - <bytes> -> <int>"

    assert qa_functions.data_type_converter('1.2', int, qa_functions.ConverterFunctionArgs()) == 1, \
        "qa_functions.dtc - <str> -> <int>"

    assert qa_functions.data_type_converter('1.9', int, qa_functions.ConverterFunctionArgs()) == 1, \
        "qa_functions.dtc - <str> -> <int>"

    assert qa_functions.data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        int,
        qa_functions.ConverterFunctionArgs()
    ) == 148, "qa_functions.dtc - <list> -> <int>"

    assert qa_functions.data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        int,
        qa_functions.ConverterFunctionArgs()
    ) == 148, "qa_functions.dtc - <tuple> -> <int>"

    assert qa_functions.data_type_converter(
        {1, 2, 3, b"4", "5", 10.0, 123.18382323},
        int,
        qa_functions.ConverterFunctionArgs()
    ) == 148, "qa_functions.dtc - <set> -> <int>"

    assert qa_functions.data_type_converter(
        {1: 2, 3: 4, 5: 6},
        int,
        qa_functions.ConverterFunctionArgs()
    ) == 12, 'qa_functions.dtc - <dict> -> <int>'

    assert qa_functions.data_type_converter(
        False,
        int,
        qa_functions.ConverterFunctionArgs()
    ) == 0, "qa_functions.dtc - <bool[False]> -> <int>"

    assert qa_functions.data_type_converter(
        True,
        int,
        qa_functions.ConverterFunctionArgs()
    ) == 1, "qa_functions.dtc - <bool[True]> -> <int>"


def test_convert_to_str():
    assert qa_functions.data_type_converter(b'1', str, qa_functions.ConverterFunctionArgs()) == '1', \
        "qa_functions.dtc - <bytes> -> <str>"

    assert qa_functions.data_type_converter(1.2, str, qa_functions.ConverterFunctionArgs()) == '1.2', \
        "qa_functions.dtc - <int> -> <str>"

    assert qa_functions.data_type_converter(1, str, qa_functions.ConverterFunctionArgs()) == '1', \
        "qa_functions.dtc - <float> -> <str>"

    assert qa_functions.data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        str,
        qa_functions.ConverterFunctionArgs()
    ).strip() == "1\n2\n3\n4\n5\n10.0\n123.18382323", "qa_functions.dtc - <list> -> <str>"

    assert qa_functions.data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        str,
        qa_functions.ConverterFunctionArgs()
    ).strip() == "1\n2\n3\n4\n5\n10.0\n123.18382323", "qa_functions.dtc - <tuple> -> <str>"

    assert qa_functions.data_type_converter(
        {1: 2, 3: 4, 5: 6},
        str,
        qa_functions.ConverterFunctionArgs()
    ).strip() == '1 2\n3 4\n5 6', 'qa_functions.dtc - <dict> -> <str>'

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            False,
            str,
            qa_functions.ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            True,
            str,
            qa_functions.ConverterFunctionArgs()
        )


def test_convert_to_bytes():
    assert qa_functions.data_type_converter('1', bytes, qa_functions.ConverterFunctionArgs()) == b'1', \
        "qa_functions.dtc - <str> -> <bytes>"

    assert qa_functions.data_type_converter(1.2, bytes, qa_functions.ConverterFunctionArgs()) == b'1.2', \
        "qa_functions.dtc - <int> -> <bytes>"

    assert qa_functions.data_type_converter(1, bytes, qa_functions.ConverterFunctionArgs()) == b'1', \
        "qa_functions.dtc - <float> -> <bytes>"

    assert qa_functions.data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        bytes,
        qa_functions.ConverterFunctionArgs()
    ).strip() == b"1\n2\n3\n4\n5\n10.0\n123.18382323", "qa_functions.dtc - <list> -> <bytes>"

    assert qa_functions.data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        bytes,
        qa_functions.ConverterFunctionArgs()
    ).strip() == b"1\n2\n3\n4\n5\n10.0\n123.18382323", "qa_functions.dtc - <tuple> -> <bytes>"

    assert qa_functions.data_type_converter(
        {1: 2, 3: 4, 5: 6},
        bytes,
        qa_functions.ConverterFunctionArgs()
    ).strip() == b'1 2\n3 4\n5 6', 'qa_functions.dtc - <dict> -> <bytes>'

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            False,
            bytes,
            qa_functions.ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            True,
            bytes,
            qa_functions.ConverterFunctionArgs()
        )


def test_convert_to_list():
    assert qa_functions.data_type_converter('', list, qa_functions.ConverterFunctionArgs()) == [''], \
        "qa_functions.dtc - <str> -> <list> (empty1)"

    assert qa_functions.data_type_converter(' ', list, qa_functions.ConverterFunctionArgs()) == [' '], \
        "qa_functions.dtc - <str> -> <list> (empty1)"

    assert qa_functions.data_type_converter(b'1', list, qa_functions.ConverterFunctionArgs()) == [b'1'], \
        "qa_functions.dtc - <bytes> -> <list> (short)"

    assert qa_functions.data_type_converter(
        b"1\n2\n3\n4\n5\n10.0\n123.18382323",
        list,
        qa_functions.ConverterFunctionArgs()
    ) == [b"1", b"2", b"3", b"4", b"5", b"10.0", b"123.18382323"], "qa_functions.dtc - <bytes> -> <list> (long)"

    assert qa_functions.data_type_converter(
        (1, 2, 3, b"4", "5", 10.0, 123.18382323),
        list,
        qa_functions.ConverterFunctionArgs()
    ) == [1, 2, 3, b"4", "5", 10.0, 123.18382323], "qa_functions.dtc - <tuple> -> <list>"

    assert qa_functions.data_type_converter(
        {1: 2, 3: 4, 5: 6},
        list,
        qa_functions.ConverterFunctionArgs()
    ) == ['1 2', '3 4', '5 6'], 'qa_functions.dtc - <dict> -> <list>'

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(1.2, list, qa_functions.ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(1, list, qa_functions.ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            False,
            list,
            qa_functions.ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            True,
            list,
            qa_functions.ConverterFunctionArgs()
        )


def test_convert_to_tuple():
    assert qa_functions.data_type_converter('', tuple, qa_functions.ConverterFunctionArgs()) == ('',), \
        "qa_functions.dtc - <str> -> <tuple> (empty1)"

    assert qa_functions.data_type_converter(' ', tuple, qa_functions.ConverterFunctionArgs()) == (' ',), \
        "qa_functions.dtc - <str> -> <tuple> (empty1)"

    assert qa_functions.data_type_converter(b'1', tuple, qa_functions.ConverterFunctionArgs()) == (b'1',), \
        "qa_functions.dtc - <bytes> -> <tuple> (short)"

    assert qa_functions.data_type_converter(
        b"1\n2\n3\n4\n5\n10.0\n123.18382323",
        tuple,
        qa_functions.ConverterFunctionArgs()
    ) == (b"1", b"2", b"3", b"4", b"5", b"10.0", b"123.18382323"), "qa_functions.dtc - <bytes> -> <tuple> (long)"

    assert qa_functions.data_type_converter(
        [1, 2, 3, b"4", "5", 10.0, 123.18382323],
        tuple,
        qa_functions.ConverterFunctionArgs()
    ) == (1, 2, 3, b"4", "5", 10.0, 123.18382323), "qa_functions.dtc - <list> -> <tuple>"

    assert qa_functions.data_type_converter(
        {1: 2, 3: 4, 5: 6},
        tuple,
        qa_functions.ConverterFunctionArgs()
    ) == ('1 2', '3 4', '5 6'), 'qa_functions.dtc - <dict> -> <tuple>'

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(1.2, tuple, qa_functions.ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(1, tuple, qa_functions.ConverterFunctionArgs())

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            False,
            tuple,
            qa_functions.ConverterFunctionArgs()
        )

    with pytest.raises(AssertionError):
        qa_functions.data_type_converter(
            True,
            tuple,
            qa_functions.ConverterFunctionArgs()
        )


def test_data_at_dict_path():
    assert qa_functions.data_at_dict_path(
        'a', {}
    ) == (False, None), \
        "qa_functions.data_at_dict_path - nf_test"

    assert qa_functions.data_at_dict_path(
        'a', {'a': []}
    ) == (True, []), \
        "qa_functions.data_at_dict_path - f_test"

    assert qa_functions.data_at_dict_path(
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
        "qa_functions.data_at_dict_path - nest_test"


def test_colors():
    assert qa_functions.ConvertColor.RGBToHex((255, 255, 255)) == '#ffffff'
    assert qa_functions.ConvertColor.HexToRGB('#000000') == (0, 0, 0)
    assert qa_functions.ColorFunctions.calculate_more_contrast(
        qa_functions.HexColor('#ffffff'), qa_functions.HexColor('#000000'), qa_functions.HexColor('#330a00')
    ).color.lower().strip() == "#ffffff"
    assert qa_functions.ColorFunctions.fade('#202020', '#ffffff') == \
           ('#202020', '#202020', '#212121', '#222222', '#232323', '#242424', '#252525', '#262626', '#272727', '#282828', '#292929', '#2a2a2a',
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
            '#f7f7f7', '#f8f8f8', '#f9f9f9', '#fafafa', '#fbfbfb', '#fcfcfc', '#fdfdfd', '#fefefe', '#ffffff'), "qa_functions.ColorFunctions.fade: unexpected output."


def test_float_map():
    assert qa_functions.float_map(1, 0, 10, 0, 5, False) == .5
    assert qa_functions.float_map(20, 0, 100, 0, 5, False) == 1
    assert qa_functions.float_map(-.1, 0, 5, 0, 1000, True) == -20
    with pytest.raises(AssertionError):
        qa_functions.float_map(-10, -1, 10, 0, 1, False)



def test_src_files():
    excl = ('.qa_update', 'TODO', 'additional_themes', '.git', '.idea', '.mypy_cache', '.pytest_cache', '__pycache__', '', 'dist', 'build', 'installer')
    addons = ('ADDONS_THEME', )
    lsa = []

    with open('.config\\update_commands.json') as file:
        sd = json.loads(file.read().strip())
        for i in addons:
            if i in sd:
                sd.pop(i)

        lsd = [*{*qa_functions.flatten_list(
            [(*d.values(), ) for d in [*sd.values()]],
            lambda *args: ".\\{}".format(args[0].replace('/', '\\')),
        )}]
        file.close()

    def rc(root):        
        ls = os.listdir(root)
        for f in ls:
            if f not in excl and "exclude_" not in f:
                if os.path.isdir(f"{root}\\{f}"):
                    rc(f"{root}\\{f}")
                elif os.path.isfile(f"{root}\\{f}"):
                    if f"{root}\\{f}" not in lsd:
                        sys.stderr.write(f"{qa_functions.ANSI.BOLD}{qa_functions.ANSI.FG_BRIGHT_RED}[SRC] ERROR: File \"{root}\\{f}\" not included in UPDATE_COMMANDS{qa_functions.ANSI.RESET}\n")
                        lsa.append(f"{root}\\{f}")
                    else:
                        lsd.pop(lsd.index(f"{root}\\{f}"))

                else:
                    raise qa_functions.UnexpectedEdgeCase(f"Item type unknown for \"{root}\\{f}\".")

    rc('.')
    for a in lsd:
        sys.stdout.write(f"{qa_functions.ANSI.BOLD}{qa_functions.ANSI.FG_BRIGHT_YELLOW}[SRC] WARNING: File \"{a}\" included in UPDATE_COMMANDS but doesn't actually exist.{qa_functions.ANSI.RESET}\n")
    assert len(lsa) == 0, f"The following files are not included in UPDATE_COMMANDS:\n\t* %s" % "\n\t* ".join(lsd)


def test_installer_iss():
    rt = "<test::uninstaller>"
    excl = ('TODO', '.git', '.idea', '__pycache__', '.mypy_cache', '.pytest_cache', 'additional_themes', 'build', 'dist', 'installer')
    
    req = {*[i for i in os.listdir() if (i not in excl and "exclude_" not in i)]}
    extn_req = {*[i.split('.')[-1] for i in req if os.path.isfile(i)]}
    extn_del = []
    item_del = []
    
    with open("installer\\installer.iss", 'r') as iss_file:
        iss_data = iss_file.read()
        iss_file.close()

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
                        sys.stdout.write(f"{qa_functions.ANSI.FG_BRIGHT_YELLOW}{qa_functions.ANSI.BOLD}[WARNING] [INSTALLER] Extension \".{line.split('.')[-1]}\" in delete commands; not found in source directry.{qa_functions.ANSI.RESET}\n")
                    
                else:
                    item_del.append(line)
                    if line not in req:
                        sys.stdout.write(f"{qa_functions.ANSI.FG_BRIGHT_YELLOW}{qa_functions.ANSI.BOLD}[WARNING] [INSTALLER] Item \"{line}\" in delete commands; not found in source directry.{qa_functions.ANSI.RESET}\n")
        else:
            assert False, "Invalid start and end points in iss_data."
    else:
        assert False, "Start and end points not found in iss_data."
    
    for name in req:
        extn = name.split('.')[-1]
        if extn not in extn_del and name not in item_del:
            sys.stdout.write(f"{qa_functions.ANSI.FG_BRIGHT_YELLOW}{qa_functions.ANSI.BOLD}[WARNING] [INSTALLER] Item \"{name}\" not covered by deletion commands.{qa_functions.ANSI.RESET}\n")            
    