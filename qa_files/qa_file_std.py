import traceback, hashlib
from typing import *
from .qa_files_ltbl import *
from tkinter import messagebox
from qa_functions.qa_std import data_type_converter
from qa_functions.qa_custom import ConverterFunctionArgs
from qa_functions.qa_enum import FileType
from qa_functions.qa_file_handler import _Crypt


_ft_map: Dict[FileType, Tuple[str, bytes]] = {
    FileType.QA_FILE: (qa_file_extn, qa_file_enck),
    FileType.QA_ENC: (qa_enc_extn, qa_enc_enck),
    FileType.QA_EXPORT: (qa_export_extn, qa_export_enck),
    FileType.QA_QUIZ: (qa_quiz_extn, qa_quiz_enck),
}


def generate_file(file_type: FileType, raw_data: Union[bytes, str]) -> Union[
    None,
    Tuple[bytes, str],
    bytes
]:
    global _ft_map

    try:
        if file_type not in _ft_map:
            return cast(bytes, data_type_converter(raw_data, bytes, ConverterFunctionArgs()).strip())

        EXTN, KEY = _ft_map[file_type]
        new_data = cast(bytes, _Crypt.encrypt(raw_data, KEY, ConverterFunctionArgs()))
        d_hash = data_type_converter(hashlib.sha3_512(new_data).hexdigest(), bytes, ConverterFunctionArgs())

        return d_hash+new_data+d_hash, EXTN

    except Exception as E:
        E_hash = hashlib.md5(cast(bytes, data_type_converter(str(E), bytes, ConverterFunctionArgs()))).hexdigest()
        error_info = f"""Failed to generate required file data;
Exception Code: {E_hash}
Error String: {str(E)}

Technical Information: {traceback.format_exc()}"""

        messagebox.showerror("File generation error", error_info)
        return None


def load_file_sections(file_type: FileType, raw_data: bytes) -> Union[List[bytes], Tuple[bytes, bytes]]:
    global _ft_map
    
    if not isinstance(raw_data, bytes): 
        return b'', b''

    if file_type not in _ft_map:
        return b'', raw_data

    raw_data = raw_data.strip()
    assert len(raw_data) >= 256, len(raw_data)

    h_hash, f_hash = raw_data[:128], raw_data[-128::]
    assert h_hash == f_hash
    enc_d = raw_data.replace(h_hash, b'', 1)
    enc_d = enc_d[::-1].replace(f_hash[::-1], b'', 1)[::-1]

    return h_hash, enc_d


def load_file(file_type: FileType, raw_data: bytes) -> Union[None, Tuple[bytes, str]]:
    global _ft_map

    try:
        assert isinstance(raw_data, bytes), 'Expected type \'bytes\' for raw_data input'
        if file_type not in _ft_map:
            return raw_data, data_type_converter(raw_data, str, ConverterFunctionArgs())

        raw_data = raw_data.strip()

        assert len(raw_data) >= 256, 'Cannot compute hash; invalid data provided'

        _, KEY = _ft_map[file_type]
        h_hash = raw_data[:128:]
        f_hash = raw_data[-128::]

        assert h_hash == f_hash, "Hash mismatch between file header and footer; possibly corrupted data."

        # enc_d = raw_data.strip(h_hash)    <didn't work in some cases?>
        enc_d = raw_data.replace(h_hash, b'', 1)
        enc_d = enc_d[::-1].replace(f_hash[::-1], b'', 1)[::-1]

        unencrypted_data = cast(bytes, _Crypt.decrypt(enc_d, KEY, ConverterFunctionArgs()))
        del enc_d, h_hash, f_hash, KEY, _, raw_data, file_type

        try:
            string = cast(str, data_type_converter(unencrypted_data, str, ConverterFunctionArgs()))
        except Exception:
            string = ''

        return unencrypted_data, string

    except Exception as E:
        E_hash = hashlib.md5(str(E).encode()).hexdigest()
        error_info = f"""Failed to load (verify) file data;
Exception Code: {E_hash}
Error String: {E.__class__.__name__}({E})

Technical Information: {traceback.format_exc()}"""

        messagebox.showerror("Couldn't load file", error_info)
        return None

