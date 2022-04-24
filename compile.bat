rem qa_update_apps.exe:
python.exe -m PyInstaller -w -D -i ".\.src\.icons\.app_ico\updater.ico" --clean --uac-admin ".\qa_installer_functions\qa_update_app.py"
del /S /F /Q .\.qa_update
Xcopy /S /Y dist\qa_update_app\* .\.qa_update

del /S /F /Q .\dist
del /S /F /Q .\build
del *.spec

pause
