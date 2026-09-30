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

if not exist "%PYEXE%" (
    echo  [ERROR] Bundled Python not found: "%PYEXE%"
    echo  Make sure the whole zip was extracted, not run from inside the zip.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

echo.
echo  ==============================================================
echo   DXF  -  3D Terrain Viewer
echo  ==============================================================
echo   Starting... your browser will open in a few seconds.
echo   Address: http://localhost:8501
echo   To stop, close this window or press Ctrl+C.
echo  ==============================================================
echo.

start "" /b cmd /c "timeout /t 5 /nobreak >nul & start "" http://localhost:8501"

"%PYEXE%" -m streamlit run "%APP_DIR%app.py" --global.developmentMode=false --server.headless=true --browser.gatherUsageStats=false --theme.base=dark --theme.primaryColor="#38bdf8" --theme.backgroundColor="#0f172a" --theme.secondaryBackgroundColor="#1e293b" --theme.textColor="#e2e8f0"

pause
