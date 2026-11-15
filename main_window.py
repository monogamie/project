"""Главное окно программы «Домашняя библиотека»."""
import datetime
import random

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (QColorDialog, QFileDialog, QFontDialog,
                             QHeaderView, QMainWindow, QMessageBox,
                             QTableWidgetItem)

from book_form import BookForm
from chart_widget import ChartWidget
from database import SORT_ORDERS, LibraryDB
from directories_form import DirectoriesForm
from paths import cover_pixmap, resource_path
from reading_form import ReadingForm

# Подписи «все жанры» и «все статусы» в фильтрах
ALL_GENRES = "Все жанры"
ALL_STATUSES = "Все"
# Цель на год по умолчанию (в страницах)
DEFAULT_GOAL = 5000

ABOUT_TEXT = ("Домашняя библиотека, версия 1.0\n\n"
              "Учёт книг, авторов, жанров и прочитанных страниц.\n"
              "Python, PyQt6, SQLite.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загружаем дизайн окна, сделанный в Qt Designer (урок QT 2)
        uic.loadUi(resource_path("ui/main_window.ui"), self)

        self.db = LibraryDB()
        # При первом запуске заполняем базу примерами из CSV-файла
        if self.db.books_count() == 0:
            self.db.import_csv(resource_path("data/books.csv"), self.today())

        # Дочерние формы храним в атрибутах, иначе Python удалит их
        # сразу после открытия и окно мигнёт и пропадёт (урок QT 1)
        self.book_form = None
        self.reading_form = None
        self.directories_form = None

        self.logoLabel.setPixmap(QPixmap(resource_path("images/logo.png"))
                                 .scaled(128, 128))
        self.load_style()
        self.show_quote()

        # Диаграмму добавляем в пустую компоновку chartLayout из дизайна
        self.chart = ChartWidget()
        self.chartLayout.addWidget(self.chart)

        # Ширина столбцов таблицы по содержимому (урок QT 5)
        header = self.booksTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Столбцы «Название» и «Автор» делят между собой оставшееся место
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.sortBox.addItems(SORT_ORDERS.keys())
        self.goalSpin.setValue(int(self.db.get_setting("goal",
                                                       DEFAULT_GOAL)))
        self.apply_settings()
        self.connect_signals()
        self.refresh_all()

    # ===================================================== подготовка окна
    def today(self):
        """Сегодняшняя дата в формате базы: 2026-11-15."""
        return datetime.date.today().isoformat()

    def load_style(self):
        """Читает стили оформления из файла style.qss (урок QT 4)."""
        with open(resource_path("style.qss"), encoding="utf-8") as f:
            self.setStyleSheet(f.read())

    def show_quote(self):
        """Случайная цитата дня из текстового файла quotes.txt."""
        with open(resource_path("data/quotes.txt"), encoding="utf-8") as f:
            quotes = [line.strip() for line in f if line.strip()]
        if quotes:
            self.quoteBrowser.setHtml(f"<i>{random.choice(quotes)}</i>")

    def connect_signals(self):
        """Связываем сигналы кнопок, меню и полей с методами окна."""
        # Пункты меню (сами пункты созданы в Qt Designer)
        self.actionImport.triggered.connect(self.import_csv)
        self.actionExport.triggered.connect(self.export_csv)
        self.actionReport.triggered.connect(self.save_report)
        self.actionExit.triggered.connect(self.close)
        self.actionAdd.triggered.connect(self.add_book)
        self.actionEdit.triggered.connect(self.edit_book)
        self.actionDelete.triggered.connect(self.delete_book)
        self.actionReading.triggered.connect(self.open_reading)
        self.actionDirectories.triggered.connect(self.open_directories)
        self.actionFont.triggered.connect(self.choose_font)
        self.actionColor.triggered.connect(self.choose_color)
        self.actionAbout.triggered.connect(self.about)

        # Кнопки справа
        self.addButton.clicked.connect(self.add_book)
        self.editButton.clicked.connect(self.edit_book)
        self.deleteButton.clicked.connect(self.delete_book)
        self.readingButton.clicked.connect(self.open_reading)

        # Фильтры: при любом изменении заново читаем книги из базы
        self.searchEdit.textChanged.connect(self.refresh_books)
        self.genreBox.currentIndexChanged.connect(self.refresh_books)
        self.statusGroup.buttonClicked.connect(self.refresh_books)
        self.favoriteCheck.stateChanged.connect(self.refresh_books)
        self.sortBox.currentIndexChanged.connect(self.refresh_books)
        self.resetButton.clicked.connect(self.reset_filters)

        # Таблица: выбор строки и двойной щелчок
        self.booksTable.itemSelectionChanged.connect(self.show_book_info)
        self.booksTable.cellDoubleClicked.connect(self.edit_book)

        # Статистика
        self.goalSpin.valueChanged.connect(self.goal_changed)
        self.tabWidget.currentChanged.connect(self.refresh_stats)

    def apply_settings(self):
        """Восстанавливает шрифт и цвет таблицы, сохранённые в базе."""
        family = self.db.get_setting("font_family")
        if family:
            size = int(self.db.get_setting("font_size", "10"))
            self.booksTable.setFont(QFont(family, size))
        color = self.db.get_setting("table_color")
        if color:
            self.booksTable.setStyleSheet(f"background-color: {color};")

    # ================================================== обновление данных
    def refresh_all(self):
        """Перечитывает из базы всё: жанры, таблицу книг, статистику."""
        self.refresh_genres()
        self.refresh_books()
        self.refresh_stats()

    def refresh_genres(self):
        """Заполняет список жанров в фильтре, сохраняя выбранный жанр."""
        current = self.genreBox.currentText()
        self.genreBox.clear()
        self.genreBox.addItem(ALL_GENRES)
        for genre in self.db.get_genres():
            self.genreBox.addItem(genre["title"])
        self.genreBox.setCurrentText(current)

    def get_filters(self):
        """Собирает значения всех фильтров."""
        genre = self.genreBox.currentText()
        if genre == ALL_GENRES:
            genre = ""
        # Статус берём из текста выбранного переключателя (урок QT 2)
        status = self.statusGroup.checkedButton().text()
        if status == ALL_STATUSES:
            status = ""
        order = SORT_ORDERS.get(self.sortBox.currentText(), "books.title")
        return (self.searchEdit.text().strip(), genre, status,
                self.favoriteCheck.isChecked(), order)

    def refresh_books(self):
        """Заполняет таблицу книг с учётом фильтров."""
        books = self.db.get_books(*self.get_filters())
        self.booksTable.setRowCount(len(books))
        for i, book in enumerate(books):
            values = [book["id"],
                      "★" if book["favorite"] else "",
                      book["title"],
                      book["author"] or "",
                      book["genre"] or "",
                      book["year"] or "",
                      book["pages"],
                      f"{self.progress_percent(book)}%",
                      "★" * book["rating"],
                      book["status"]]
            for j, value in enumerate(values):
                self.booksTable.setItem(i, j, QTableWidgetItem(str(value)))
        self.statusbar.showMessage(f"Показано книг: {len(books)}")
        self.show_book_info()

    def progress_percent(self, book):
        """Сколько процентов книги прочитано."""
        if book["status"] == "Прочитано":
            return 100
        if not book["pages"]:
            return 0
        read = book["read_pages"] or 0
        return min(100, read * 100 // book["pages"])

    def refresh_stats(self):
        """Обновляет вкладку «Статистика»."""
        counts = self.db.count_by_status()
        self.lcdTotal.display(sum(counts.values()))
        self.lcdRead.display(counts["Прочитано"])
        self.lcdReading.display(counts["Читаю"])

        pages = self.db.pages_in_year(datetime.date.today().year)
        self.lcdPages.display(pages)
        goal = self.goalSpin.value()
        self.goalBar.setMaximum(goal)
        self.goalBar.setValue(min(pages, goal))

        self.chart.set_data(self.db.books_by_genre())

    def goal_changed(self, value):
        self.db.set_setting("goal", value)
        self.refresh_stats()

    def reset_filters(self):
        self.searchEdit.clear()
        self.genreBox.setCurrentIndex(0)
        self.radioAll.setChecked(True)
        self.favoriteCheck.setChecked(False)
        self.refresh_books()

    # ============================================== выбранная книга
    def selected_book_id(self):
        """id выбранной книги из нулевого столбца или None (урок QT 7)."""
        rows = list(set([i.row() for i in self.booksTable.selectedItems()]))
        if not rows:
            return None
        return int(self.booksTable.item(rows[0], 0).text())

    def need_book(self):
        """То же, но если книга не выбрана, сообщает об этом."""
        book_id = self.selected_book_id()
        if book_id is None:
            QMessageBox.information(self, "Нет выбора",
                                    "Сначала выберите книгу в таблице.")
        return book_id

    def show_book_info(self):
        """Показывает справа обложку, данные и заметки выбранной книги."""
        book_id = self.selected_book_id()
        if book_id is None:
            self.coverLabel.setPixmap(cover_pixmap("", 170, 250))
            self.infoLabel.setText("Выберите книгу в таблице")
            self.progressBar.setValue(0)
            self.notesBrowser.clear()
            return

        book = self.db.get_book(book_id)
        self.coverLabel.setPixmap(cover_pixmap(book["cover"], 170, 250))
        year = f", {book['year']}" if book["year"] else ""
        self.infoLabel.setText(f"<b>{book['title']}</b><br>"
                               f"{book['author'] or 'Автор не указан'}"
                               f"{year}<br>{book['status']}")
        self.progressBar.setValue(self.progress_percent(book))
        self.notesBrowser.setText(book["notes"] or "")

    # ================================================ работа с книгами
    def add_book(self):
        self.book_form = BookForm(self)
        self.book_form.show()

    def edit_book(self):
        book_id = self.need_book()
        if book_id:
            self.book_form = BookForm(self, book_id)
            self.book_form.show()

    def delete_book(self):
        book_id = self.need_book()
        if not book_id:
            return
        title = self.db.get_book(book_id)["title"]
        # Перед удалением спрашиваем подтверждение (урок QT 7)
        answer = QMessageBox.question(
            self, "Удаление книги",
            f"Удалить книгу «{title}» вместе с журналом чтения?",
            buttons=(QMessageBox.StandardButton.Yes
                     | QMessageBox.StandardButton.No))
        if answer == QMessageBox.StandardButton.Yes:
            self.db.delete_book(book_id)
            self.refresh_all()

    def open_reading(self):
        book_id = self.need_book()
        if book_id:
            self.reading_form = ReadingForm(self, book_id)
            self.reading_form.show()

    def open_directories(self):
        self.directories_form = DirectoriesForm(self)
        self.directories_form.show()

    # ======================================================== файлы
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт книг", "", "CSV-файлы (*.csv);;Все файлы (*)")
        if not path:
            return
        try:
            count = self.db.import_csv(path, self.today())
        except (OSError, UnicodeDecodeError) as error:
            QMessageBox.critical(self, "Ошибка импорта", str(error))
            return
        self.refresh_all()
        QMessageBox.information(self, "Импорт", f"Добавлено книг: {count}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт книг", "books.csv", "CSV-файлы (*.csv)")
        if not path:
            return
        # Сохраняем книги с учётом текущих фильтров
        count = self.db.export_csv(path,
                                   self.db.get_books(*self.get_filters()))
        QMessageBox.information(self, "Экспорт", f"Сохранено книг: {count}")

    def save_report(self):
        """Сохраняет отчёт о библиотеке в текстовый файл."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "report.txt", "Текстовые файлы (*.txt)")
        if not path:
            return
        counts = self.db.count_by_status()
        year = datetime.date.today().year
        lines = ["ОТЧЁТ «ДОМАШНЯЯ БИБЛИОТЕКА»",
                 f"Всего книг: {sum(counts.values())}"]
        for status, count in counts.items():
            lines.append(f"  {status}: {count}")
        lines.append(f"Прочитано страниц за {year} год: "
                     f"{self.db.pages_in_year(year)}")
        lines.append("")
        lines.append("Книги по жанрам:")
        for genre, count in self.db.books_by_genre():
            lines.append(f"  {genre}: {count}")
        lines.append("")
        lines.append("Список книг:")
        for number, book in enumerate(self.db.get_books(), 1):
            lines.append(f"{number}. {book['title']} — "
                         f"{book['author'] or 'автор не указан'} "
                         f"[{book['status']}]")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self.statusbar.showMessage("Отчёт сохранён")

    # =================================================== оформление
    def choose_font(self):
        # Стандартный диалог выбора шрифта (урок QT 3)
        font, ok_pressed = QFontDialog.getFont()
        if ok_pressed:
            self.booksTable.setFont(font)
            self.db.set_setting("font_family", font.family())
            self.db.set_setting("font_size", font.pointSize())

    def choose_color(self):
        # Стандартный диалог выбора цвета (урок QT 3)
        color = QColorDialog.getColor()
        if color.isValid():
            self.booksTable.setStyleSheet(
                f"background-color: {color.name()};")
            self.db.set_setting("table_color", color.name())

    def about(self):
        QMessageBox.information(self, "О программе", ABOUT_TEXT)

    # ============================================ клавиатура и закрытие
    def keyPressEvent(self, event):
        """Горячие клавиши (урок QT 8): Esc, Delete, F5."""
        if event.key() == Qt.Key.Key_Escape:
            # Esc очищает поиск
            self.searchEdit.clear()
        elif event.key() == Qt.Key.Key_Delete:
            # Delete удаляет выбранную книгу
            self.delete_book()
        elif event.key() == Qt.Key.Key_F5:
            # F5 обновляет всё
            self.refresh_all()

    def closeEvent(self, event):
        # При закрытии окна закрываем соединение с базой (урок QT 6)
        self.db.close()
