@echo off
setlocal
title DXF to 3D Terrain Viewer - Setup and Run
color 0B
cd /d "%~dp0"

echo.
echo  ==============================================================
echo   DXF  -  3D Terrain Viewer   (setup + run)
echo  ==============================================================
echo.

REM ---------------------------------------------------------------
REM 1. Find a usable Python (3.11 or newer)
REM ---------------------------------------------------------------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY goto :nopython

echo  [1/3] Python found:
%PY% --version

REM ---------------------------------------------------------------
REM 2. Create the private environment (first run only)
REM ---------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  [2/3] Creating private environment in .venv  ^(first run only^)...
    %PY% -m venv .venv
    if errorlevel 1 goto :fail
)

REM ---------------------------------------------------------------
REM 3. Install packages (first run only)
REM ---------------------------------------------------------------
if not exist ".venv\deps_installed.flag" (
    echo.
    echo  [3/3] Installing required packages. This takes 2-5 minutes the first time.
    echo        Please keep this window open...
    echo.
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
    echo done> ".venv\deps_installed.flag"
) else (
    echo  [2/3] and [3/3] Environment already set up - skipping.
)

REM ---------------------------------------------------------------
REM 4. Start the app
REM ---------------------------------------------------------------
echo.
echo  ==============================================================
echo   Starting... your browser will open in a few seconds.
echo   Address: http://localhost:8501
echo   To stop the app: close this window or press Ctrl+C.
echo  ==============================================================
echo.

start "" /b cmd /c "timeout /t 6 /nobreak >nul & start "" http://localhost:8501"

".venv\Scripts\python.exe" -m streamlit run app.py --server.port=8501 --server.headless=true --browser.gatherUsageStats=false
pause
exit /b 0

:nopython
echo.
echo  [ERROR] Python 3.11 or newer was not found on this computer.
echo.
echo  What to do:
echo    1. Go to https://www.python.org/downloads/  and install Python 3.12
echo    2. On the first installer screen, TICK "Add python.exe to PATH"
echo    3. Close this window and double-click SETUP_AND_RUN.bat again
echo.
pause
exit /b 1

:fail
echo.
echo  [ERROR] Something went wrong during setup ^(see the messages above^).
echo  Check your internet connection and try again. If it keeps failing,
echo  delete the ".venv" folder and double-click SETUP_AND_RUN.bat again.
echo.
pause
exit /b 1
