# Домашняя библиотека (PyQt6)

Настольное приложение для учёта домашней библиотеки: книги, авторы, жанры, журнал чтения, статистика.

## Запуск

```
pip install -r requirements.txt
python main.py
```

При первом запуске создаётся `library.db` и заполняется примерами из `data/books_sample.csv`.

## Сборка exe

Windows: запустите `build_exe.bat`. Готовый файл появится в `dist\LibraryApp.exe`.
Картинки и CSV упаковываются внутрь exe, база `library.db` и папка `covers` создаются рядом с ним.

## Документы

- `docs/ТЗ.md` — техническое задание
- `docs/Пояснительная_записка.md` — пояснительная записка
- `docs/Гайд_к_защите.md` — подробный разбор кода и инструкция для защиты
- `docs/Презентация.pptx` — презентация для защиты
- `ОПИСАНИЕ_ФАЙЛОВ.md` — зачем нужен каждый файл проекта

## Соответствие требованиям

| Требование | Где |
|---|---|
| requirements.txt | `requirements.txt` |
| Несколько форм | главное окно, книга, журнал чтения, авторы, автор, жанры, «О программе» |
| Изученные виджеты | кнопки, поля ввода, списки, таблицы, флажки, переключатели, ползунок, вкладки, прогресс-бар и др. |
| Дополнительные виджеты | QCalendarWidget, QDateEdit, QDial, QLCDNumber, QSplitter, QSplashScreen, свои виджеты на QPainter |
| Стандартные диалоги | QFileDialog, QMessageBox, QInputDialog, QFontDialog, QColorDialog |
| Картинки | `images/` (логотип, заставка, иконки), обложки книг |
| txt / csv | `data/quotes.txt`, `data/books_sample.csv`, импорт/экспорт CSV, отчёт TXT |
| Несколько таблиц в БД | genres, authors, books, readings, settings |
| Чтение / запись / изменение | `app/database.py` |
| exe | `build_exe.bat` (PyInstaller, `--onefile`) |
