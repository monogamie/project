@echo off
chcp 65001 >nul
REM Сборка единого исполняемого файла LibraryApp.exe (Windows)
REM Перед запуском:  pip install -r requirements.txt

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name LibraryApp ^
  --icon images\app.ico ^
  --add-data "images;images" ^
  --add-data "data;data" ^
  main.py

echo.
echo Готово! Файл: dist\LibraryApp.exe
pause
