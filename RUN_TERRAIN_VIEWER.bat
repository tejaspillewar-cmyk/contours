@echo off
setlocal
title DXF to 3D Terrain Viewer
color 0B

REM Uses ONLY the bundled Python. Nothing is installed; system Python is ignored.
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONNOUSERSITE=1"
set "APP_DIR=%~dp0"
set "PYEXE=%APP_DIR%python\python.exe"
set "PORT=8501"
set "URL=http://localhost:%PORT%"
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%PYEXE%" (
    echo  [ERROR] Bundled Python not found: "%PYEXE%"
    echo  Make sure the whole zip was extracted, not run from inside the zip.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

REM ---------------------------------------------------------------
REM Already running? Just open the existing tab. Starting a second
REM server would double the memory use and open a second browser.
REM ---------------------------------------------------------------
"%PS%" -NoProfile -Command "$c=New-Object Net.Sockets.TcpClient;try{$c.Connect('127.0.0.1',%PORT%);exit 0}catch{exit 1}finally{$c.Dispose()}" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  The viewer is already running on %URL%
    echo  Opening it in your browser - no second copy started.
    echo.
    start "" "%URL%"
    timeout /t 3 /nobreak >nul
    exit /b 0
)

echo.
echo  ==============================================================
echo   DXF  -  3D Terrain Viewer
echo  ==============================================================
echo   Starting... your browser opens as soon as the app is ready.
echo   Address: %URL%
echo   To stop, close this window or press Ctrl+C.
echo  ==============================================================
echo.

REM Open the browser once, the moment the server starts answering
REM (fixed wait times either opened too early or opened twice).
start "" /b "%PS%" -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 240;$i++){$c=New-Object Net.Sockets.TcpClient;try{$c.Connect('127.0.0.1',%PORT%);$c.Dispose();Start-Process '%URL%';break}catch{Start-Sleep -Milliseconds 500}}"

"%PYEXE%" -m streamlit run "%APP_DIR%app.py" --server.port=%PORT% --server.headless=true

pause
