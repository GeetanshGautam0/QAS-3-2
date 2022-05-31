import os


def RunUpdater(cli="--ReadFlags", path=".qa_update\\"):
    os.system(f"{path}qa_update_app.exe update {cli}")


def UpdateSuite():
    RunUpdater('--UpdateAll')


def InstallThemeAddons():
    RunUpdater('addons -a ADDONS_THEME')
