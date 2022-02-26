from qa_std import *
from qa_file_handler import Save

import threading, time, sys


DEBUGGING_ENABLED = False

LEVELS = {
    LoggingLevel.INFO: "INFO",
    LoggingLevel.WARNING: "WARNING",
    LoggingLevel.ERROR: "ERROR",
    LoggingLevel.DEBUG: "DEBUG",
}


class _MultiThreadingLogger(threading.Thread):
    def __init__(self, package: LoggingPackage):
        threading.Thread.__init__(self)

        self.file_path = package.file_path
        self.data = package.data.strip()
        self.level = package.logging_level

    def run(self):
        global LEVELS, DEBUGGING_ENABLED

        if DEBUGGING_ENABLED:
            sys.stdout.write(
                f"[{LEVELS[self.level]}] {time.ctime(time.time())} {self.data}\n"
            )

        Save.secure_save(
            self.file_path,
            f"[{LEVELS[self.level]}] {time.ctime(time.time())} {self.data}\n"
        )


def threaded_logger(logging_package: List[LoggingPackage]) -> None:
    """
    **THREADED_LOGGER**

    **WARNING: DO NOT INCLUDE LOGS FOR THE SAME FILE MORE THAN ONCE; ANY REDUNDANT FILES WILL BE SKIPPED**

    :param logging_package: List[LoggingPackage] --> Multiple logs can be handled at once
    :return: None
    """

    files = set()

    for package in logging_package:
        if package.file_path in files:
            sys.stdout.write(f"Skipped log for `{package.file_path}")
            continue

        lgr = _MultiThreadingLogger(package)
        lgr.start()
        files.add(package.file_path)

    return


def normal_logger(logging_package: List[LoggingPackage]) -> None:
    """
    **NORMAL_LOGGER**

    :param logging_package: List[LoggingPackage] --> Multiple logs can be handled at once
    :return: None
    """

    global LEVELS, DEBUGGING_ENABLED

    for package in logging_package:
        if DEBUGGING_ENABLED:
            sys.stdout.write(
                f"[{LEVELS[package.logging_level]}] {time.ctime(time.time())} {package.data.strip()}\n"
            )

        Save.secure_save(
            package.file_path,
            f"[{LEVELS[package.logging_level]}] {time.ctime(time.time())} {package.data.strip()}\n"
        )

    return
