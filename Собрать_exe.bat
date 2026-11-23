@echo off
rem Build LibraryApp.exe with PyInstaller (lesson QT 8).
rem Before the first build run once: pip install -r requirements.txt
cd /d "%~dp0"
python -m PyInstaller --onefile --noconsole --icon=images\app.ico --name=LibraryApp --add-data "ui;ui" --add-data "images;images" --add-data "data;data" --add-data "style.qss;." main.py
echo.
echo Done: dist\LibraryApp.exe
pause
