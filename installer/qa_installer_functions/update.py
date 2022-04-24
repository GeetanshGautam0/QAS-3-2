import os
from tkinter import messagebox
from . import qa_update_app


def RunUpdater(cli="--ReadFlags", path=".qa_update\\"):
    os.system(f"{path}qa_update_app.exe start {cli}")


def UpdateSuite():
    qa_update_app.nv_clear_all_app_flags(qa_update_app._NV_ROOT)
    qa_update_app.nv_create_flag(qa_update_app._NV_ROOT, 'UPDATE_MANIFEST')
    qa_update_app.nv_create_flag(qa_update_app._NV_ROOT, 'UPDATE_COMMANDS')
    qa_update_app.nv_create_flag(qa_update_app._NV_ROOT, 'MAIN_CONFIG')

    if os.path.isdir('.qa_update'): path = '.qa_update'
    elif os.path.isdir('..\\.qa_update'): path = '..\\.qa_update'
    else:
        messagebox.showerror('Quizzing App | Updater', 'Failed to locate updater executable.')
        return

    RunUpdater()

    qa_update_app.nv_clear_all_app_flags(qa_update_app._NV_ROOT)
    qa_update_app.nv_create_flag(qa_update_app._NV_ROOT, 'DEFAULT_THEME')

    RunUpdater()
