@echo off

taskkill /f /im qa_update_app.exe
del qa_update_app.exe

@REM qa_update_apps.exe:
@REM python.exe -m PyInstaller -w -D -i ".\.src\.icons\.app_ico\updater.ico" --clean --uac-admin ".\qa_installer_functions\qa_update_app.py"
python.exe -m PyInstaller -w -D -i ".\.src\.icons\.app_ico\updater.ico" --clean ".\qa_installer_functions\qa_update_app.py"
del /S /F /Q .\.qa_update
Xcopy /S /Y dist\qa_update_app\* .\.qa_update

del /S /F /Q .\dist
del /S /F /Q .\build

del /S /F /Q .\installer\.qa_update
Xcopy /S /Y .\.qa_update\* .\installer\.qa_update


@REM python.exe -m PyInstaller -w -F -i ".\.src\.icons\.app_ico\updater.ico" --uac-admin --clean ".\qa_installer_functions\qa_update_app.py"
@REM python.exe -m PyInstaller -w -F -i ".\.src\.icons\.app_ico\updater.ico" --clean ".\qa_installer_functions\qa_update_app.py"
@REM move .\dist\*.exe .

del *.spec
