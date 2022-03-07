import os, hashlib


FILE_IO_HANDLER_HASH = "186fa69090cd2fef261c7517b5d489ca523d7ce7932c5128cbd10c11ad54cdf9fd468722a2d5c121ef50560150448f075fcbf6bbf37cfe5acdf5df6d39ccec32"
LOGGER_HASH = "cad49286d20290e3f7bdd9319b299ea076f152299164821be583b8bcb35fa33e9332382b51bd7e660df91ae920ced74ff226ba199e963058174ab65f00fb70cb"

EXPECTED = {
    'byLogger': {
        'FILE_IO_HANDLER': "186fa69090cd2fef261c7517b5d489ca523d7ce7932c5128cbd10c11ad54cdf9fd468722a2d5c121ef50560150448f075fcbf6bbf37cfe5acdf5df6d39ccec32"
    }
}


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

