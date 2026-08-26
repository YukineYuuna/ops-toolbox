@echo off
@echo off
setlocal
cd /d "%~dp0"

rem ---- find Python ----
set PY=
if exist "D:\python3.10.9\python.exe" set PY=D:\python3.10.9\python.exe
if defined PY goto :found
for /f "delims=" %%i in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do if not defined PY set PY=%%i
if defined PY goto :found
for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set PY=%%i
if not defined PY goto :no_python
:found

rem ---- find main script (the .py containing MaintenanceToolbox) ----
set APP=
for /f "delims=" %%f in ('findstr /m /c:"MaintenanceToolbox" *.py 2^>nul') do set APP=%%f
if not defined APP goto :no_app

"%PY%" "%APP%"
exit /b 0

:no_python
echo [ERROR] Python not found.
echo     Install Python 3.10+ from python.org (check "Add to PATH" during install).
pause
exit /b 1

:no_app
echo [ERROR] Main program file not found in this folder.
pause
exit /b 1
