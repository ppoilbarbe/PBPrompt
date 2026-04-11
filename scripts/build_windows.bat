@echo off
REM Build a standalone Windows executable with PyInstaller.
REM Prerequisites: pip install pyinstaller pyqt5
REM Usage: scripts\build_windows.bat

setlocal
set APP_NAME=pbprompt
set ROOT=%~dp0..
set DIST=%ROOT%\dist

echo Building %APP_NAME% for Windows...

cd /d "%ROOT%"

REM Ensure translations compiled (requires gettext tools on PATH)
REM make all

pyinstaller ^
    --onefile ^
    --windowed ^
    --name %APP_NAME% ^
    --icon "%ROOT%\resources\icons\app_color.svg" ^
    --add-data "%ROOT%\locales;locales" ^
    --add-data "%ROOT%\resources;resources" ^
    --paths "%ROOT%\src" ^
    "%ROOT%\src\pbprompt\__main__.py"

echo Executable: %DIST%\%APP_NAME%.exe
echo Done.
endlocal
