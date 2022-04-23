import os, urllib3


def RunUpdater(cli="--ReadFlags", path=".qa_update\\"):
    os.system(f"{path}qa_update_app.exe start {cli}")


def UpdateSuite():
    pass
