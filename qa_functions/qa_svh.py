import os, hashlib


FILE_IO_HANDLER_HASH = "97901231f6db542ff73d38378c113d6025b6d157b03d835edd12bb00f366bb0b1f053c218e4e43d5f371074823a9a1cd0ac6bde01e35181976d5a5a626e7ee59"
LOGGER_HASH = "b4b0d2aa9ed2e217924b4425650991fbaad6e56fdbe28efb25167e32e60ddb81fbe3d118bcd991fde14aa86df3c28c2b28212ad1cf87339b908033b77fb6e345"

EXPECTED = {
    'byLogger': {
        'FILE_IO_HANDLER': "97901231f6db542ff73d38378c113d6025b6d157b03d835edd12bb00f366bb0b1f053c218e4e43d5f371074823a9a1cd0ac6bde01e35181976d5a5a626e7ee59"
    }
}


def create_script_version_hash(file_path) -> str:
    print(file_path)
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

