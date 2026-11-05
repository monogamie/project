#!/bin/sh
# Сборка единого исполняемого файла (Linux / macOS). Для Windows используйте build_exe.bat
pyinstaller --noconfirm --clean --onefile --windowed \
  --name LibraryApp \
  --add-data "images:images" \
  --add-data "data:data" \
  main.py
echo "Готово: dist/LibraryApp"
