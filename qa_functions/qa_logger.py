import qa_files, threading, time, sys, os
from .qa_svh import create_script_version_hash, check_hash, EXPECTED
from .qa_file_handler import Save
from .qa_info import App, Files, Extensions
from .qa_custom import LoggingPackage, File, SaveFunctionArgs
from typing import *


# Version Checking
LOGGER_SCRIPT_VERSION_HASH = create_script_version_hash(__file__, True)
print(f"{LOGGER_SCRIPT_VERSION_HASH=}")
try:
    check_hash('Logger', LOGGER_SCRIPT_VERSION_HASH, 'self')
except AssertionError:
    sys.stderr.write("[WARNING] Potential logger script hash mismatch\n")

EXPECTED_F_IO_H_SVH = EXPECTED['byLogger']['FILE_IO_HANDLER']
try:
    check_hash('FileIOHandler', EXPECTED_F_IO_H_SVH, 'import', 'Logger')
except AssertionError:
    sys.stderr.write("[WARNING] Potentially outdated FIO SVH expected by logger.")

# Global Variables
DEBUGGING_ENABLED = False


class _MultiThreadingLogger(threading.Thread):
    def __init__(self, package: LoggingPackage) -> None:
        threading.Thread.__init__(self)

        self.file = File(f"{App.appdata_dir}\\{Files.logs_folder}\\{package.file_name}.{qa_files.qa_files_ltbl.qa_log_extn}")
        self.data = package.data.strip()
        self.level = package.logging_level
        self.s_name = package.script_name

    def run(self) -> None:
        global DEBUGGING_ENABLED

        if self.data.strip() != '':
            string = f"[{self.level.name}] <{self.s_name} @ {time.ctime(time.time())}>: {self.data}\n"
        else:
            string = ""

        if DEBUGGING_ENABLED:
            sys.stdout.write(string)

        Save.secure(self.file, string, SaveFunctionArgs(True, False, b"", True, True))


def threaded_logger(logging_package: List[LoggingPackage]) -> None:
    """
    **THREADED_LOGGER**

    **WARNING: DO NOT INCLUDE LOGS FOR THE SAME FILE MORE THAN ONCE; ANY REDUNDANT FILES WILL BE SKIPPED**

    :param logging_package: List[LoggingPackage] --> Multiple logs can be handled at once
    :return: None
    """

    files = set()

    for package in logging_package:
        if package.file_name in files:
            sys.stdout.write(f"Skipped log for `{package.file_name}")
            continue

        lgr = _MultiThreadingLogger(package)
        lgr.start()
        files.add(package.file_name)

    return


def normal_logger(logging_package: List[LoggingPackage]) -> None:
    """
    **NORMAL_LOGGER**

    :param logging_package: List[LoggingPackage] --> Multiple logs can be handled at once
    :return: None
    """

    global DEBUGGING_ENABLED

    for package in logging_package:
        file = File(
            f"{App.appdata_dir}\\{Files.logs_folder}\\{package.file_name}.{Extensions.Logging.extn_str}"
        )

        if len(package.data.strip()) > 0:
            string = f"[{package.logging_level.name}] <{package.script_name} @ {time.ctime(time.time())}>: {package.data.strip()}\n"
        else:
            string = ""

        if DEBUGGING_ENABLED:
            sys.stdout.write(string)

        Save.secure(file, string, SaveFunctionArgs(True, False, b"", True, True))

    return


def clear_logs(ignore_list: Tuple[Any, ...] = ()) -> bool:
    """
    **CLEAR_LOGS**

    Clears logs folder

    :param ignore_list: Files to ignore
    :return: Bool: Successfully removed logs?
    """

    log_dir = f"{App.appdata_dir}\\{Files.logs_folder}"
    b = True

    for item in os.listdir(log_dir):
        global DEBUGGING_ENABLED

        path = f"{log_dir}\\{item}"

        if item not in ignore_list and path not in ignore_list and os.path.isfile(path):
            try:
                os.remove(path)

            except Exception as E:
                if DEBUGGING_ENABLED:
                    print(f"QA.Logger - Failed to remove file `{item}` - {E}")

                b &= False

    return b

