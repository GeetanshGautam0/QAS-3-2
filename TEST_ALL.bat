@echo off

echo Running MyPy tests
mypy . > a.res
echo Running PyTest
pytest -vv > b.res

echo Consolidating
copy *.res exclude_TEST_RESULTS.log
del *.res

echo Done.
notepad.exe ".\exclude_TEST_RESULTS.log"
