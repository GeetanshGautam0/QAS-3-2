import os


def RunUpdater(cli="start --ReadFlags", path="qa_update\\"):
    os.system(f"{path}update.exe {cli}")

