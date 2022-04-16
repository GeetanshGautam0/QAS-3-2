try:
    from qa_functions import *
except:
    from ..qa_functions import *

try:
    from qa_files import *
except:
    from . import *

try:
    import qa_prompts
except:
    from .. import qa_prompts

import traceback, hashlib


_ft_map = {
    qa_enum.FileType.QA_FILE: [qa_file_extn, qa_file_enck],
    qa_enum.FileType.QA_ENC: [qa_enc_extn, qa_enc_enck],
    qa_enum.FileType.QA_EXPORT: [qa_export_extn, qa_export_enck],
    qa_enum.FileType.QA_QUIZ: [qa_quiz_extn, qa_quiz_enck]
}


def generate_file(file_type: qa_enum.FileType, raw_data: Union[bytes, str]) -> Union[type(None), tuple]:
    global _ft_map

    try:
        if file_type not in _ft_map:
            return data_type_converter(raw_data, bytes, ConverterFunctionArgs()).strip()

        EXTN, KEY = _ft_map[file_type]
        new_data = qa_file_handler._Crypt.encrypt(raw_data, KEY, ConverterFunctionArgs())
        d_hash = data_type_converter(hashlib.sha3_512(new_data).hexdigest(), bytes, ConverterFunctionArgs())

        return d_hash+new_data+d_hash, EXTN

    except Exception as E:
        E_hash = hashlib.md5(data_type_converter(str(E), bytes, ConverterFunctionArgs())).hexdigest()
        error_info = f"""Failed to generate required file data;
Exception Code: {E_hash}
Error String: {str(E)}

Technical Information: {traceback.format_exc()}"""

        qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(error_info, title="File Generation Error"), qoc=False)
        return None


def load_file(file_type: qa_enum.FileType, raw_data: bytes) -> Union[type(None), Tuple[bytes, str]]:
    global _ft_map

    try:
        assert isinstance(raw_data, bytes), 'Expected type \'bytes\' for raw_data input'
        assert file_type in _ft_map, 'Invalid FILE_TYPE enum provided'

        raw_data = raw_data.strip()

        assert len(raw_data) >= 256, 'Cannot compute hash; invalid data provided'

        _, KEY = _ft_map[file_type]
        h_hash = raw_data[:128:]
        f_hash = raw_data[-128::]

        assert h_hash == f_hash, "Hash mismatch between file header and footer; possibly corrupted data."

        enc_d = raw_data.strip(h_hash)
        uenc_d = qa_file_handler._Crypt.decrypt(enc_d, KEY, ConverterFunctionArgs())
        del enc_d, h_hash, f_hash, KEY, _, raw_data, file_type

        try:
            string = data_type_converter(uenc_d, str, ConverterFunctionArgs())
        except:
            string = ''

        return uenc_d, string

    except Exception as E:
        E_hash = hashlib.md5(data_type_converter(str(E), bytes, ConverterFunctionArgs())).hexdigest()
        error_info = f"""Failed to load (verify) file data;
Exception Code: {E_hash}
Error String: {str(E)}

Technical Information: {traceback.format_exc()}"""

        qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(error_info, title="Couldn't Load File"), qoc=False)
        return None

