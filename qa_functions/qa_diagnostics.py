import ctypes, sys, os

try:
    from qa_functions import *
except:
    from . import qa_theme_loader

try:
    from qa_installer_functions import update
except:
    from ..qa_installer_functions import update


class Diagnostics:
    pass


class Fix:
    @staticmethod
    def default_theme_error():
        CreateNVFlag('L_UPDATE', 'DEFAULT_THEME')
        run_updater()


def run_updater():
    update.RunUpdater()

