@echo off

taskkill /f /im qa_update_app.exe
del /S /F /Q .qa_update\*

python.exe -m PyInstaller --noconfirm -w -D -i ".\.src\.icons\.app_ico\updater.ico" --clean ".\qa_installer_functions\qa_update_app.py"
del /S /F /Q .\.qa_update
Xcopy /S /Y dist\qa_update_app\* .\.qa_update

del /S /F /Q .\dist
del /S /F /Q .\build

del /S /F /Q .\installer\.qa_update
Xcopy /S /Y .\.qa_update\* .\installer\.qa_update

del *.spec
