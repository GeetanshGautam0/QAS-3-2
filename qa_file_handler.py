from qa_custom import *
from qa_err import raise_error
import qa_info, os, random, hashlib, time, shutil, traceback


class Save:
    @staticmethod
    def secure(file_obj: File, data: any, args: SaveFunctionArguments) -> bool:
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

                raise_error(CannotSave, ("Failed to save data to requested file", ), ErrorLevels.NON_FATAL, traceback.format_exc())

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
                        CannotSave, ("Failed to save data to file AND failed to restore backup", ), ErrorLevels.NON_FATAL, traceback.format_exc()
                    )

        # 2(b) --> Step 3: Delete backup if requested
        if args.delete_backup:
            os.remove(backup_file)

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
    def normal(file_obj: File, data: any, args: SaveFunctionArguments, _bypass_checks: bool = False) -> None:
        """
        **SAVE.NORMAL**

        :param file_obj: File object
        :param data: Data (most types are accepted)
        :param args: Arguments (qa_custom.SaveFunctionArguments)
        :param _bypass_checks: Bypass `_path_check` (NOT RECOMMENDED)
        :return: None
        """

        pass


def data_type_converter(
        original: Union[str, bytes, list, tuple, set, dict, int, float],
        output_type: type,
        cfa: ConverterFunctionArguments
) -> \
        Union[str, bytes, list, tuple, set, dict, int, float]:

    accepted_input = (str, bytes, list, tuple, set, dict, int, float)
    assert type(original) in accepted_input, "Original data type not supported"

    original_type = type(original)

    multi = (list, tuple, set, dict)
    single = (str, bytes, int, float)

    if original_type in single:
        if output_type in multi:  # TODO
            pass

        elif output_type in single:  # DONE
            try:
                return output_type(original)

            except Exception as E:
                raise_error(TypeError, (f"Cannot convert from {original_type} to {output_type} for given data", ), ErrorLevels.NON_FATAL)

        else:
            assert False, "unreachable"

    elif original_type in multi:
        if output_type in multi:  # TODO
            pass

        elif output_type in single:  # TODO
            pass

        else:
            assert False, "unreachable"

    else:
        assert False, "unreachable"

