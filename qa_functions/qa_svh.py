import os, hashlib
from typing import Dict


EXPECTED = {
    'byLogger': {
        'FILE_IO_HANDLER': "969af6200ed5a3bdfd9ef6e7d7ce79e1b0b55a4027f6e8d8ac3aacc4a5d609e7ce1e1a523ed9b6aa5e14c651bf6a8dbf958a13fc400b7017875de081557e103f"
    }
}


def create_script_version_hash(file_path: str, silent: bool = False) -> str:
    if silent and 'AppData\\Local\\Temp' in file_path.replace('/', '\\'):
        return ''

    assert os.path.isfile(file_path)

    with open(file_path, 'rb') as script:
        r = script.read()
        script.close()

    return hashlib.sha3_512(r).hexdigest()


def check_hash(script: str, expected_hash: str, script_type: str, self_id: str = "<Unknown>") -> None:
    assert isinstance(script_type, str)
    assert isinstance(script, str)
    assert isinstance(expected_hash, str)
    assert isinstance(self_id, str)

    scripts = {
        'FileIOHandler': '.\\qa_functions\\qa_file_handler.py',
        'Logger':        '.\\qa_functions\\qa_logger.py'
    }

    assert script_type in ('import', 'self')
    assert script in scripts

    fh_table = compile_svh()

    assert expected_hash == fh_table[scripts[script]]['sha'], \
        f"[VERSION MISMATCH ERROR] Script: \"{script}\"; invalid script version hash provided." if script_type == 'self' else \
        f"[IMPORT ERROR] In {self_id}; Attempted-Import: {script}; outdated/invalid script version hash"


def compile_svh() -> Dict[str, Dict[str, str]]:
    output: Dict[str, Dict[str, str]] = {}
    excl = ('svh.json', 'TODO', '.git', '.idea', '__pycache__', '.mypy_cache', '.pytest_cache', 'additional_themes', 'build', 'dist', 'installer', '.qa_update')

    def rc(root: str) -> None:
        files = {*[i for i in os.listdir(root) if (i not in excl and "exclude_" not in i and os.path.isfile(f"{root}\\{i}"))]}
        dirs = {*[i for i in os.listdir(root) if (i not in excl and "exclude_" not in i and os.path.isdir(f"{root}\\{i}"))]}

        for file in files:
            if file.split('.')[-1].strip() not in ('json', 'svg', 'py', 'int', 'bat', 'txt', 'toml', 'md', 'yml'):
                continue

            with open(f"{root}\\{file}", 'rb') as f:
                r = f.read()
                f.close()

            filename = file.split('\\')[-1].strip()

            md5 = hashlib.md5(r).hexdigest()
            sha = hashlib.sha3_512(r).hexdigest()

            output[f'{root}\\{filename}'] = {'md5': md5, 'sha': sha}

        for directory in dirs:
            rc(f'{root}\\{directory}')

    rc('.')

    return output
