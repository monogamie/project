"""Форма журнала чтения: в какой день сколько страниц прочитано."""
from PyQt6 import uic
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem, QWidget

from paths import resource_path

# Формат даты в базе и формат даты на экране
DATE_FORMAT = "yyyy-MM-dd"
SHOW_FORMAT = "dd.MM.yyyy"


class ReadingForm(QWidget):
    """Журнал чтения одной книги."""

    def __init__(self, parent_form, book_id):
        super().__init__()
        uic.loadUi(resource_path("ui/reading_form.ui"), self)
        self.parent_form = parent_form
        self.db = parent_form.db
        self.book_id = book_id

        book = self.db.get_book(book_id)
        self.total_pages = book["pages"] or 0
        self.setWindowTitle(f"Журнал чтения: {book['title']}")
        self.titleLabel.setText(f"<b>{book['title']}</b><br>"
                                f"Всего страниц: {self.total_pages}")

        # Нельзя выбрать дату из будущего
        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit.setMaximumDate(QDate.currentDate())

        self.addButton.clicked.connect(self.add_record)
        self.deleteButton.clicked.connect(self.delete_records)
        self.closeButton.clicked.connect(self.close)
        self.load_history()

    def load_history(self):
        """Заполняет таблицу записями журнала и возвращает сумму страниц."""
        rows = self.db.get_readings(self.book_id)
        self.historyTable.setRowCount(len(rows))
        read = 0
        for i, row in enumerate(rows):
            date = QDate.fromString(row["date"], DATE_FORMAT)
            self.historyTable.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.historyTable.setItem(
                i, 1, QTableWidgetItem(date.toString(SHOW_FORMAT)))
            self.historyTable.setItem(
                i, 2, QTableWidgetItem(str(row["pages"])))
            read += row["pages"]

        # Шкала прогресса: прочитано из общего числа страниц
        self.progressBar.setMaximum(max(self.total_pages, read, 1))
        self.progressBar.setValue(read)
        return read

    def add_record(self):
        date = self.dateEdit.date().toString(DATE_FORMAT)
        self.db.add_reading(self.book_id, date, self.pagesSpin.value())
        read = self.load_history()

        # Если книгу ещё не начинали, теперь она в статусе «Читаю»
        book = self.db.get_book(self.book_id)
        if book["status"] == "Хочу прочитать":
            self.db.set_status(self.book_id, "Читаю")

        # Если прочитаны все страницы, предлагаем отметить книгу
        if (self.total_pages and read >= self.total_pages
                and book["status"] != "Прочитано"):
            answer = QMessageBox.question(
                self, "Книга прочитана?",
                "Прочитаны все страницы. Отметить книгу как «Прочитано»?",
                buttons=(QMessageBox.StandardButton.Yes
                         | QMessageBox.StandardButton.No))
            if answer == QMessageBox.StandardButton.Yes:
                self.db.set_status(self.book_id, "Прочитано")

        self.parent_form.refresh_all()

    def delete_records(self):
        # Номера выделенных строк без повторов (урок QT 7)
        rows = list(set([i.row() for i in self.historyTable.selectedItems()]))
        if not rows:
            return
        # id записей берём из нулевого столбца
        ids = [self.historyTable.item(i, 0).text() for i in rows]
        answer = QMessageBox.question(
            self, "Удаление", "Удалить выделенные записи журнала?",
            buttons=(QMessageBox.StandardButton.Yes
                     | QMessageBox.StandardButton.No))
        if answer == QMessageBox.StandardButton.Yes:
            self.db.delete_readings(ids)
            self.load_history()
            self.parent_form.refresh_all()
