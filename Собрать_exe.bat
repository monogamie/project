@echo off
chcp 65001 >nul
REM Сборка программы в один файл LibraryApp.exe (урок QT 8)
REM Перед запуском один раз выполните: pip install -r requirements.txt

pyinstaller --onefile --noconsole --icon=images\app.ico --name=LibraryApp ^
  --add-data "ui;ui" ^
  --add-data "images;images" ^
  --add-data "data;data" ^
  --add-data "style.qss;." ^
  main.py

echo.
echo Готово! Программа лежит в папке dist: dist\LibraryApp.exe
pause
