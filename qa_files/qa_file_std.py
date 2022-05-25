import qa_functions, traceback, hashlib
from typing import *
from .qa_files_ltbl import *
from tkinter import messagebox


_ft_map = {
    qa_functions.qa_enum.FileType.QA_FILE: [qa_file_extn, qa_file_enck],
    qa_functions.qa_enum.FileType.QA_ENC: [qa_enc_extn, qa_enc_enck],
    qa_functions.qa_enum.FileType.QA_EXPORT: [qa_export_extn, qa_export_enck],
    qa_functions.qa_enum.FileType.QA_QUIZ: [qa_quiz_extn, qa_quiz_enck]
}


def generate_file(file_type: qa_functions.qa_enum.FileType, raw_data: Union[bytes, str]) -> Union[type(None), tuple]:
    global _ft_map

    try:
        if file_type not in _ft_map:
            return qa_functions.data_type_converter(raw_data, bytes, qa_functions.ConverterFunctionArgs()).strip()

        EXTN, KEY = _ft_map[file_type]
        new_data = qa_functions.qa_file_handler._Crypt.encrypt(raw_data, KEY, qa_functions.ConverterFunctionArgs())
        d_hash = qa_functions.data_type_converter(hashlib.sha3_512(new_data).hexdigest(), bytes, qa_functions.ConverterFunctionArgs())

        return d_hash+new_data+d_hash, EXTN

    except Exception as E:
        E_hash = hashlib.md5(qa_functions.data_type_converter(str(E), bytes, qa_functions.ConverterFunctionArgs())).hexdigest()
        error_info = f"""Failed to generate required file data;
Exception Code: {E_hash}
Error String: {str(E)}

Technical Information: {traceback.format_exc()}"""

        messagebox.showerror("File generation error", error_info)
        return None


def load_file(file_type: qa_functions.qa_enum.FileType, raw_data: bytes) -> Union[type(None), Tuple[bytes, str]]:
    global _ft_map

    try:
        assert isinstance(raw_data, bytes), 'Expected type \'bytes\' for raw_data input'
        if file_type not in _ft_map:
            return raw_data, qa_functions.data_type_converter(raw_data, str, qa_functions.ConverterFunctionArgs())

        raw_data = raw_data.strip()

        assert len(raw_data) >= 256, 'Cannot compute hash; invalid data provided'

        _, KEY = _ft_map[file_type]
        h_hash = raw_data[:128:]
        f_hash = raw_data[-128::]

        assert h_hash == f_hash, "Hash mismatch between file header and footer; possibly corrupted data."

        # enc_d = raw_data.strip(h_hash)    <didn't work in some cases?>
        enc_d = raw_data.replace(h_hash, b'', 1)
        enc_d = enc_d[::-1].replace(f_hash[::-1], b'', 1)[::-1]

        uenc_d = qa_functions.qa_file_handler._Crypt.decrypt(enc_d, KEY, qa_functions.ConverterFunctionArgs())
        del enc_d, h_hash, f_hash, KEY, _, raw_data, file_type

        try:
            string = qa_functions.data_type_converter(uenc_d, str, qa_functions.ConverterFunctionArgs())
        except:
            string = ''

        return uenc_d, string

    except Exception as E:
        E_hash = hashlib.md5(str(E).encode()).hexdigest()
        error_info = f"""Failed to load (verify) file data;
Exception Code: {E_hash}
Error String: {E.__class__.__name__}({E})

Technical Information: {traceback.format_exc()}"""

        messagebox.showerror("Couldn't load file", error_info)
        return None

