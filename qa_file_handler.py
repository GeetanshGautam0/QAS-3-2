from qa_custom import *
from qa_err import raise_error
import qa_info, os, random, hashlib, time, shutil, traceback, qa_std


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

        if not _bypass_checks:
            Save._path_check(file_obj)
        else:
            Save._path_check(file_obj, _mk_dir_only=True)  # Needs to be done every time.

        output_type = args.save_data_type
        assert output_type in (bytes, str), "Output data type can only be `str` or `bytes`"

        new_data = data_type_converter(data, output_type, ConverterFunctionArguments(
            args.list_val_sep, args.dict_key_val_sep, args.dict_line_sep
        ))

        if args.append:
            with open(file_obj.file_path, 'rb') as source_file:
                original_data = source_file.read().strip()
                source_file.close()

            original_data = data_type_converter(original_data, output_type, ConverterFunctionArguments(
                args.list_val_sep, args.dict_key_val_sep, args.dict_line_sep
            ))
            separator = data_type_converter(args.new_old_data_sep, output_type, ConverterFunctionArguments(
                args.list_val_sep, args.dict_key_val_sep, args.dict_line_sep
            ))

            original_data += separator

        else:
            original_data = "" if output_type is str else "".encode(qa_info.App.ENCODING)

        d2s = (original_data + new_data).replace('\r\n', '\n').strip()

        with open(file_obj.file_path, 'w' if output_type is str else 'wb') as output_file:
            output_file.write(d2s)
            output_file.close()


def data_type_converter(
        original: Union[str, bytes, list, tuple, set, dict, int, float],
        output_type: type,
        cfa: ConverterFunctionArguments
) -> \
        Union[str, bytes, list, tuple, set, dict, int, float]:

    # TODO: Add descriptions to UnexpectedEdgeCase exceptions

    if isinstance(original, output_type):
        if isinstance(original, bytes):
            # Check encoding
            exp = qa_info.App.ENCODING
            try:
                original.decode(exp)
                return original     # All good

            except:
                try:
                    _, s = qa_std.brute_force_decoding(original, (exp, ))
                    return s.encode(exp)

                except:
                    raise_error(
                        UnicodeEncodeError, ("Encoding for given bytes data not known", ), ErrorLevels.NON_FATAL
                    )

        else:
            return original

    accepted_input = (str, bytes, list, tuple, set, dict, int, float)
    assert type(original) in accepted_input, "Original data type not supported"

    original_type = type(original)

    def RE(e):
        raise_error(TypeError, (f"Failed to convert from {original_type} to {output_type} for given data: {str(e)}",), ErrorLevels.NON_FATAL)

    multi = (list, tuple, set, dict)
    single = (str, bytes, int, float)

    if original_type in single:
        if output_type in multi:
            assert original_type not in (float, int), "Unsupported conversion (Int/Float => List/Tuple/Set/Dict)"

            if output_type in (list, tuple, set):
                ns = data_type_converter(cfa.list_line_sep, original_type, cfa)
                no = data_type_converter(original, original_type, cfa)  # For bytes encoding

                o = no.split(ns)
                return output_type(o)

            elif output_type is dict:
                ns = data_type_converter(cfa.dict_line_sep, original_type, cfa)
                no = data_type_converter(original, original_type, cfa)  # For bytes encoding

                o = no.split(ns)
                o1 = {}

                for item in o:
                    k, v = \
                        item.split(cfa.dict_key_val_sep)[0], \
                        item.replace(item.split(cfa.dict_key_val_sep)[0], data_type_converter('', original_type, cfa), 1).lstrip()

                    o1[k] = v

                return o1

            else:
                raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

        elif output_type in single:  # DONE
            if output_type in (int, float) and original_type is str:  # DONE ?
                try:
                    return output_type(float(original))

                except Exception as E:
                    RE(E)

            elif output_type in (int, float) and original_type is bytes:  # DONE ?
                s = None

                try:
                    s = original.decode(qa_info.App.ENCODING)
                except:
                    try:
                        _, s = qa_std.brute_force_decoding(original, (qa_info.App.ENCODING, ))

                    except Exception as E:
                        RE(E)

                if s is not None:
                    try:
                        output_type(s)
                    except Exception as E:
                        RE(E)

            elif output_type is bytes and original_type is str:  # DONE
                return original.encode(qa_info.App.ENCODING)

            elif output_type is str and original_type is bytes:  # DONE
                try:
                    o = original.decode(qa_info.App.ENCODING)
                    return o
                except:
                    try:
                        _, s = qa_std.brute_force_decoding(original, (qa_info.App.ENCODING, ))
                        return s
                    except:
                        RE("Unknown encoding for given bytes data.")

            elif output_type in (str, bytes) and original_type in (int, float):
                o1 = str(original)
                return o1 if output_type is str else o1.encode(qa_info.App.ENCODING)

            elif output_type in (int, float) and original_type in (int, float):
                return output_type(original)

            else:
                raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

        else:
            raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

    elif original_type in multi:
        if output_type in multi:
            if original_type in (tuple, list, set):  # DONE
                if output_type is dict:  # DONE
                    o = {}

                    for item in original:
                        n_item = data_type_converter(item, str, cfa)  # (Recursive)
                        assert isinstance(n_item, str)

                        str_tokens = n_item.split(cfa.dict_key_val_sep)
                        k, v = str_tokens[0], n_item.replace(str_tokens[0], '', 1).lstrip()

                        o[k] = v

                    return o

                elif output_type in (tuple, list, set):  # DONE
                    return output_type([*original])

                else:
                    raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

            elif original_type is dict:  # DONE
                if output_type in (list, tuple, set):  # DONE ?
                    sep = cfa.dict_key_val_sep
                    n_sep = data_type_converter(sep, str, cfa)

                    if type(sep) not in (str, bytes):
                        sep = n_sep

                    o = []

                    for ok, ov in original.items():
                        k, v = \
                            data_type_converter(ok, str, cfa), \
                            data_type_converter(ov, str, cfa)

                        o.append(data_type_converter(f"{k}{n_sep}{v}", type(sep), cfa))

                    return output_type(o)  # Cast to appropriate type

                else:
                    raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

            else:
                raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

        elif output_type in single:
            if original_type in (list, tuple, set):
                if output_type in (float, int):
                    try:
                        return output_type(sum(original))
                    except:
                        acc = 0.0

                        for item in original:
                            acc += data_type_converter(item, float, cfa)

                        return output_type(acc)

                elif output_type in (str, bytes):
                    o1 = ""
                    for item in original:
                        i2 = data_type_converter(item, str, cfa)
                        o1 += f"{i2}{cfa.list_line_sep}"

                    if output_type is str:
                        return o1
                    elif output_type is bytes:
                        return o1.encode(qa_info.App.ENCODING)
                    else:
                        raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

                else:
                    raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

            elif original_type is dict:
                if output_type in (float, int):
                    return output_type(sum(list(original.values())))

                elif output_type in (str, bytes):
                    o1 = ""

                    for key, val in original.items():
                        k2, v2 = \
                            data_type_converter(key, str, cfa), \
                            data_type_converter(val, str, cfa)

                        o1 += f"{k2}{cfa.dict_key_val_sep}{v2}{cfa.dict_line_sep}"

                    if output_type is str:
                        return o1
                    elif output_type is bytes:
                        return o1.encode(qa_info.App.ENCODING)
                    else:
                        raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

                else:
                    raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

            else:
                raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

        else:
            raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

    else:
        raise_error(UnexpectedEdgeCase, (), ErrorLevels.NON_FATAL)

