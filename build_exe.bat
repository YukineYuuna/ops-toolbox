@echo off
@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Windows Toolbox v3 - Build Script
echo ============================================
echo.

rem ---- 1. find Python ----
set PY=
if exist "D:\python3.10.9\python.exe" set PY=D:\python3.10.9\python.exe
if defined PY goto :py_found
for /f "delims=" %%i in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do if not defined PY set PY=%%i
if defined PY goto :py_found
for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set PY=%%i
if not defined PY goto :no_python
:py_found
echo [1/4] Python: %PY%
"%PY%" --version
echo.

rem ---- 2. check PyInstaller ----
echo [2/4] Checking PyInstaller...
"%PY%" -m PyInstaller --version >nul 2>&1
if not errorlevel 1 goto :installer_ok
echo     Not installed. Installing via pip (needs network)...
"%PY%" -m pip install pyinstaller
if errorlevel 1 goto :pip_fail
:installer_ok
echo     PyInstaller OK
echo.

rem ---- 3. build ----
echo [3/4] Building, please wait (about 1-3 min)...
set SPEC=Windows运维工具箱_v3.spec
if not exist "%SPEC%" goto :no_spec
"%PY%" -m PyInstaller --clean --noconfirm "%SPEC%"
if errorlevel 1 goto :build_fail
echo.

rem ---- 4. done ----
echo [4/4] Build finished! Output files:
dir /b "dist\*.exe" 2>nul
if exist "dist\*.exe" explorer dist
echo.
pause
exit /b 0

:no_python
echo [ERROR] Python not found.
echo     Install Python 3.10+ from python.org (check "Add to PATH"),
echo     or edit this file and set PY= to your python.exe path.
goto :fail

:pip_fail
echo [ERROR] Failed to install PyInstaller. Check your network.
goto :fail

:no_spec
echo [ERROR] No .spec file found in this folder.
goto :fail

:build_fail
echo [ERROR] Build failed. See the messages above.
goto :fail

:fail
echo.
pause
exit /b 1
