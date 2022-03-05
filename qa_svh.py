import os, hashlib


FILE_IO_HANDLER_HASH = "3835557265073e103eea68a8fd31b1c2d982bdf5a9aeb01f607bd2f44827ff50156511928a31558e0c2dc3bb14a8e771805561ba910c3ac3ec95dc8ff522b5c1"
LOGGER_HASH = "86b60f91e904a3fd6fd92c64dcd388a63b17313621f18db0a6b3c73e00b3a9118ad5ec93a4fc86d19495370a1164b89f121f1fcf7e793cfa544e61fc45cca5eb"


def create_script_version_hash(file_path) -> str:
    assert os.path.isfile(file_path)

    with open(file_path, 'rb') as script:
        r = script.read()
        script.close()

    return hashlib.sha3_512(r).hexdigest()


def check_hash(script: str, expected_hash: str, script_type: str, self_id: str = "<Unknown>") -> None:
    global FILE_IO_HANDLER_HASH, LOGGER_HASH

    assert isinstance(script_type, str)
    assert isinstance(script, str)
    assert isinstance(expected_hash, str)
    assert isinstance(self_id, str)

    scripts = {
        'FileIOHandler': FILE_IO_HANDLER_HASH,
        'Logger':        LOGGER_HASH
    }

    assert script_type in ('import', 'self')
    assert script in scripts

    assert expected_hash == scripts[script], \
        f"[VERSION MISMATCH ERROR] Script: \"{script}\"; invalid script version hash provided." if script_type == 'self' else \
        f"[IMPORT ERROR] In {self_id}; Attempted-Import: {script}; outdated/invalid script version hash"

