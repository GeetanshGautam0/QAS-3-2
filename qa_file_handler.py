"""
Quizzing Application 3
Module Name: File IO Handler (Version 1)

Geetansh Gautam
February 28, 2022

Official Website: geetanshgautam.wixsite.com/home
Source Code: geetanshgautam0.github.io/QAS3-2
"""


from qa_custom import *
from qa_err import raise_error
import qa_info, os, random, hashlib, time, shutil, traceback, qa_std, qa_svh as svh
from cryptography.fernet import Fernet, InvalidToken


FILE_IO_HANDLER_SCRIPT_VERSION_HASH = svh.create_script_version_hash(os.path.abspath('qa_file_handler.py'))
print(f"{FILE_IO_HANDLER_SCRIPT_VERSION_HASH=}")
svh.check_hash('FileIOHandler', FILE_IO_HANDLER_SCRIPT_VERSION_HASH, 'self')


class Open:
    @staticmethod
    def load_file(file_obj: File, ofa: OpenFunctionArgs) -> Union[str, bytes]:
        assert os.path.isfile(file_obj.file_path), "File does not exist."
        assert ofa.d_type in (str, bytes), "Invalid data type requested."

        with open(file_obj.file_path, 'r' if ofa.d_type is str else 'rb') as f:
            o = f.readlines() if ofa.lines_mode else f.read()
            f.close()

        return o

    @staticmethod
    def read_file(file_obj: File, ofa: OpenFunctionArgs, enc_key: bytes, cfa: ConverterFunctionArgs = ConverterFunctionArgs()) -> Union[str, bytes]:
        assert isinstance(enc_key, bytes)
        assert len(enc_key) == 44

        og_d_type = ofa.d_type
        ofa.d_type = bytes
        raw = Open.load_file(file_obj, ofa)

        cfa = cfa

        no = _Crypt.decrypt(raw, enc_key, cfa, True)
        return dtc(no, og_d_type, cfa) if no is not False else dtc(raw, og_d_type, cfa)


class Save:
    @staticmethod
    def secure(file_obj: File, data: any, args: SaveFunctionArgs) -> bool:
        """
        **SAVE.SECURE**

        Creates backup and attempts to save data to files; if saving fails, the backup is restored

        :param file_obj: `File` object
        :param data: Data to save (most data types supported)
        :param args: Arguments package for secure save
        :return: Saved successfully? (bool)
        """

        # Step 1: Create backup (BYTES)
        # Step 2: Attempt to save (call SAVE.NORMAL)
        #       (a) If fails, toggle `failed` flag and restore backup
        #           [i] Check restoration
        #       (b) If pass, continue normally
        # Step 3: Delete backup if requested

        # Checks to conduct before saving
        Save._path_check(file_obj)

        saved_successfully = False

        # Step 1: Create backup [CONDITIONAL]
        backup_file_name = \
            hashlib.sha3_512(
                f"{time.ctime(time.time())}{random.random()}".encode(qa_info.App.ENCODING)
            ).hexdigest() + \
            f".{qa_info.Extensions.BackupFile.extn_str}"

        backup_file = f"{qa_info.Files.backup_folder}\\{backup_file_name}"
        backed_up = os.path.exists(file_obj.file_path)

        if backed_up:
            Save._path_check(File(backup_file), _mk_dir_only=True)

            try:
                shutil.copy(file_obj.file_path, backup_file)

                if args.run_hash_check:
                    with open(backup_file, 'rb') as bf, open(file_obj.file_path, 'rb') as of:
                        bd, od = bf.read(), of.read()
                        bf.close()
                        of.close()

                    del bf, of

                    hash1, hash2 = hashlib.sha3_512(bd).hexdigest(), hashlib.sha3_512(od).hexdigest()
                    assert hash1 == hash2, "Backup creation failed: invalid data stored in backup file"

                    del hash1, hash2, bd, od

            except Exception:
                raise_error(CannotCreateBackup, (file_obj.file_path, traceback.format_exc()), ErrorLevels.NON_FATAL)
                return False

        # Step 2: Save
        try:
            Save.normal(
                file_obj,
                data,
                args,
                _bypass_checks=True
            )

            saved_successfully = True

        except Exception:
            # Step 2(a) Failed; restore backup (*)
            if not backed_up:
                if os.path.exists(file_obj.file_path):
                    os.remove(file_obj.file_path)

                raise_error(CannotSave, ("Failed to save data to requested file",), ErrorLevels.NON_FATAL, traceback.format_exc())

            else:
                # Restore backup
                MAX_ATTEMPTS, attempts = 1000, 0
                f1 = False
                try:

                    while attempts <= MAX_ATTEMPTS:
                        assert os.path.isfile(backup_file), "Lost backup file"

                        os.remove(file_obj.file_path)
                        Save._path_check(file_obj, _mk_dir_only=True)

                        shutil.copy(backup_file, file_obj.file_path)

                        with open(backup_file, 'rb') as bf, open(file_obj.file_path, 'rb') as of:
                            bd, od = bf.read(), of.read()
                            bf.close()
                            of.close()

                        hash1, hash2 = hashlib.sha3_512(bd), hashlib.sha3_512(od)
                        f1 = hash1 == hash2

                        del hash1, hash2, bd, od, bf, of

                        if f1:
                            break

                        attempts += 1

                    assert f1, "Could not restore backup - unknown reason"

                except:
                    raise_error(
                        CannotSave, ("Failed to save data to file AND failed to restore backup",), ErrorLevels.NON_FATAL, traceback.format_exc()
                    )

        # 2(b) --> Step 3: Delete backup if requested
        try:
            if args.delete_backup:
                os.remove(backup_file)
        except FileNotFoundError:
            pass

        # Return success status
        return saved_successfully

    @staticmethod
    def _path_check(file_obj: File, _mk_dir_only: bool = False) -> None:
        # Any checks that need to happen BEFORE saving data

        if not _mk_dir_only:
            # Check whether we are allowed to modify the file
            pass

        while not os.path.exists(file_obj.path):
            os.makedirs(file_obj.path)

        return None

    @staticmethod
    def normal(file_obj: File, data: any, args: SaveFunctionArgs, _bypass_checks: bool = False) -> None:
        """
        **SAVE.NORMAL**

        :param file_obj: File object
        :param data: Data (most types are accepted)
        :param args: Arguments (qa_custom.SaveFunctionArguments)
        :param _bypass_checks: Bypass `_path_check` (NOT RECOMMENDED)
        :return: None
        """

        Save._path_check(file_obj, _mk_dir_only=_bypass_checks)  # Needs to be done every time.

        output_type = args.save_data_type
        if args.encrypt:
            args.save_data_type = bytes
            output_type = bytes

        args.append &= os.path.isfile(file_obj.file_path)

        assert output_type in (bytes, str), "Output data type can only be `str` or `bytes`"

        cfa = ConverterFunctionArgs(
            args.list_val_sep,
            args.dict_key_val_sep,
            args.dict_line_sep
        )

        new_data = dtc(data, output_type, cfa)

        if args.append:
            with open(file_obj.file_path, 'rb') as source_file:
                original_data = source_file.read().strip()
                source_file.close()

            original_data = dtc(original_data, output_type, cfa)
            separator = dtc(args.new_old_data_sep, output_type, cfa)

        else:
            original_data = "" if output_type is str else "".encode(qa_info.App.ENCODING)
            separator = "" if output_type is str else "".encode(qa_info.App.ENCODING)

        if args.encrypt:
            if len(original_data.strip()) > 0:
                new_data = _Crypt.save_sr_append_data(original_data, new_data, separator, args.encryption_key, cfa)

            d2s = _Crypt.encrypt(new_data, args.encryption_key, cfa)

        else:
            d2s = (original_data + separator + new_data).replace(
                dtc('\r\n', output_type, cfa),
                dtc('\n', output_type, cfa)
            ).strip()

        with open(file_obj.file_path, 'w' if output_type is str else 'wb') as output_file:
            output_file.write(d2s)
            output_file.close()


class _Crypt:
    @staticmethod
    def _make_fernet(key: bytes):  # Run any desired checks
        assert isinstance(key, bytes)
        assert len(key) == 44

        return Fernet(key)

    @staticmethod
    def encrypt(data: any, key: bytes, cfa: ConverterFunctionArgs = ConverterFunctionArgs(), silent=False):
        fer = _Crypt._make_fernet(key)
        b_data: bytes = dtc(data, bytes, cfa)

        try:
            return fer.encrypt(b_data)
        except Exception as E:
            if not silent:
                raise_error(EncryptionError, (f"Failed to encrypt data; {str(E)}", ), ErrorLevels.NON_FATAL, traceback.format_exc())
            return False

    @staticmethod
    def decrypt(data: any, key: bytes, cfa: ConverterFunctionArgs = ConverterFunctionArgs(), silent=False):
        fer = _Crypt._make_fernet(key)
        b_data: bytes = dtc(data, bytes, cfa)

        try:
            return fer.decrypt(b_data)
        except InvalidToken:
            if not silent:
                raise_error(EncryptionError, ("Failed to decrypt data; InvalidToken exception", ), ErrorLevels.NON_FATAL)
            return False

    @staticmethod
    def save_sr_append_data(old_data: any, new_data: any, sep: any, key: bytes, cfa: ConverterFunctionArgs = ConverterFunctionArgs()) -> bytes:
        od = dtc(old_data, bytes, cfa)
        nd = dtc(new_data, bytes, cfa)
        sd = dtc(sep,      bytes, cfa)

        nod: bytes = b""
        nnd: bytes = b""
        nsd: bytes = b""

        try:
            nod = _Crypt.decrypt(od, key, cfa, True)
        except Exception as E:
            raise_error(E.__class__, (str(E), ), ErrorLevels.NON_FATAL, traceback.format_exc())

        try:
            nnd = _Crypt.decrypt(nd, key, cfa, True)
        except Exception as E:
            raise_error(E.__class__, (str(E), ), ErrorLevels.NON_FATAL)

        try:
            nsd = _Crypt.decrypt(sd, key, cfa, True)
        except Exception as E:
            raise_error(E.__class__, (str(E), ), ErrorLevels.NON_FATAL)

        nod = nod if nod is not False else od
        nnd = nnd if nnd is not False else nd
        nsd = nsd if nsd is not False else sd

        return nod + nsd + nnd


def dtc(od, tp, cfa):
    return qa_std.data_type_converter(od, tp, cfa)
