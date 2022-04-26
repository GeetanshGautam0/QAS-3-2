import os
from tkinter import messagebox
from . import qa_update_app


def RunUpdater(cli="--ReadFlags", path=".qa_update\\"):
    os.system(f"{path}qa_update_app.exe update {cli}")


def UpdateSuite():
    RunUpdater('--UpdateAll')


def InstallThemeAddons():
    RunUpdater('addons -a ADDONS_THEME')
