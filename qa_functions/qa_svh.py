import json
import os, hashlib
from typing import Dict, Tuple


with open('.\\.config\\esvh.json', 'r') as ESVH_FILE:
    ESVH_STR = ESVH_FILE.read()
    ESVH_FILE.close()

EXPECTED = json.loads(ESVH_STR)
del ESVH_STR


def create_script_version_hash(file_path: str, silent: bool = False) -> str:
    if silent and 'AppData\\Local\\Temp' in file_path.replace('/', '\\'):
        return ''

    assert os.path.isfile(file_path)
    fh_table = compile_svh()
    assert file_path in fh_table
    return fh_table[file_path]['sha']


def check_hash(script: str, expected_hash: str, script_type: str, self_id: str = "<Unknown>") -> None:
    assert isinstance(script_type, str), 'Parameter script_type must be of type "STRING"'
    assert isinstance(script, str), 'Parameter script must be of type "STRING"'
    assert isinstance(expected_hash, str), 'Parameter expected_hash must be of type "STRING"'
    assert isinstance(self_id, str), 'Parameter self_id must be of type "STRING"'

    scripts = {
        'FileIOHandler': '.\\qa_functions\\qa_file_handler.py',
        'Logger':        '.\\qa_functions\\qa_logger.py'
    }

    assert script_type in ('import', 'self'), 'Invalid `script_type` code provided.'

    fh_table = compile_svh()
    assert script in scripts or script in fh_table, 'Requested script not in SVH service table'

    assert expected_hash == (fh_table[scripts[script]]['sha'] if script in scripts else fh_table[script]), \
        f"[VERSION MISMATCH ERROR] Script: \"{script}\"; invalid script version hash provided." if script_type == 'self' else \
        f"[IMPORT ERROR] In {self_id}; Attempted-Import: {script}; outdated/invalid script version hash"


def compile_svh() -> Dict[str, Dict[str, str]]:
    output: Dict[str, Dict[str, str]] = {}
    excl = ('.vs', 'QAS_VENV', 'esvh.json', 'svh.json', 'TODO', '.git', '.idea', '__pycache__', '.mypy_cache', '.pytest_cache', 'additional_themes', 'build', 'dist', 'installer', '.qa_update')

    def rc(root: str) -> None:
        files = {*[i for i in os.listdir(root) if (i not in excl and "exclude_" not in i and os.path.isfile(f"{root}\\{i}"))]}
        dirs = {*[i for i in os.listdir(root) if (i not in excl and "exclude_" not in i and os.path.isdir(f"{root}\\{i}"))]}

        for file in files:
            if file.split('.')[-1].strip() not in ('json', 'svg', 'py', 'ini', 'bat', 'txt', 'toml', 'md', 'yml'):
                continue

            with open(f"{root}\\{file}", 'rb') as f:
                r = f.read()
                f.close()

            filename = file.split('\\')[-1].strip()

            s: str = brute_force_decoding(r, (), ())[1]
            r = s.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '').strip().encode('utf-8')

            md5 = hashlib.md5(r).hexdigest()
            sha = hashlib.sha3_512(r).hexdigest()

            output[f'{root}\\{filename}'] = {'md5': md5, 'sha': sha}

        for directory in dirs:
            rc(f'{root}\\{directory}')

    rc('.')

    return output


def compile_svh_with_fn() -> Tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    output: Dict[str, Dict[str, str]] = {}
    fn_output: Dict[str, str] = {}
    excl = ('QAS_VENV', '.vs', 'venv', 'esvh.json', 'svh.json', 'TODO', '.git', '.idea', '__pycache__', '.mypy_cache', '.pytest_cache', 'additional_themes', 'build', 'dist', 'installer', '.qa_update')

    def rc(root: str) -> None:
        files = {*[i for i in os.listdir(root) if (i not in excl and "exclude_" not in i and os.path.isfile(f"{root}\\{i}"))]}
        dirs = {*[i for i in os.listdir(root) if (i not in excl and "exclude_" not in i and os.path.isdir(f"{root}\\{i}"))]}

        for file in files:
            if file.split('.')[-1].strip() not in ('json', 'svg', 'py', 'ini', 'bat', 'txt', 'toml', 'md', 'yml'):
                continue

            with open(f"{root}\\{file}", 'rb') as f:
                r = f.read()
                f.close()

            filename = file.split('\\')[-1].strip()

            s: str = brute_force_decoding(r, (), ())[1]
            r = s.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '').strip().encode('utf-8')

            md5 = hashlib.md5(r).hexdigest()
            sha = hashlib.sha3_512(r).hexdigest()

            output[f'{root}\\{filename}'] = {'md5': md5, 'sha': sha}
            fn_output[f'{root}\\{filename}'] = r.decode('utf-8')

        for directory in dirs:
            rc(f'{root}\\{directory}')

    rc('.')

    return output, fn_output


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
