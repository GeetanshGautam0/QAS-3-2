import os


def RunUpdater(cli: str = "--ReadFlags", path: str = ".qa_update\\") -> None:
    os.system(f"{path}qa_update_app.exe update {cli}")


def UpdateSuite() -> None:
    RunUpdater('--UpdateAll')


def InstallThemeAddons() -> None:
    RunUpdater('addons -a ADDONS_THEME')
