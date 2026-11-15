"""Форма справочников: авторы и жанры на двух вкладках."""
import sqlite3

from PyQt6 import uic
from PyQt6.QtWidgets import QInputDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtWidgets import QWidget

from paths import resource_path

# Номер столбца с названием в таблицах справочников
NAME_COLUMN = 2


class DirectoriesForm(QWidget):
    """Справочники. Правка прямо в таблице, как в уроке QT 7:
    изменения собираются в словарь, а по кнопке сохраняются в базу."""

    def __init__(self, parent_form):
        super().__init__()
        uic.loadUi(resource_path("ui/directories_form.ui"), self)
        self.parent_form = parent_form
        self.db = parent_form.db
        # Изменённые названия: id записи -> новое название
        self.modified_authors = {}
        self.modified_genres = {}

        self.authorsTable.itemChanged.connect(self.author_changed)
        self.genresTable.itemChanged.connect(self.genre_changed)
        self.addAuthorButton.clicked.connect(self.add_author)
        self.addGenreButton.clicked.connect(self.add_genre)
        self.saveAuthorsButton.clicked.connect(self.save_authors)
        self.saveGenresButton.clicked.connect(self.save_genres)
        self.deleteAuthorButton.clicked.connect(self.delete_authors)
        self.deleteGenreButton.clicked.connect(self.delete_genres)
        self.closeButton.clicked.connect(self.close)
        self.load_tables()

    def fill_table(self, table, rows, name_field):
        """Заполняет таблицу справочника строками из базы."""
        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            table.setItem(i, 1, QTableWidgetItem(str(row["books"])))
            table.setItem(i, NAME_COLUMN, QTableWidgetItem(row[name_field]))

    def load_tables(self):
        self.fill_table(self.authorsTable, self.db.get_authors(), "name")
        self.fill_table(self.genresTable, self.db.get_genres(), "title")
        # При заполнении таблиц тоже срабатывает itemChanged,
        # поэтому после загрузки очищаем словари изменений
        self.modified_authors = {}
        self.modified_genres = {}

    def author_changed(self, item):
        # Запоминаем только изменения в столбце с именем
        if item.column() == NAME_COLUMN:
            author_id = self.authorsTable.item(item.row(), 0).text()
            self.modified_authors[author_id] = item.text().strip()

    def genre_changed(self, item):
        if item.column() == NAME_COLUMN:
            genre_id = self.genresTable.item(item.row(), 0).text()
            self.modified_genres[genre_id] = item.text().strip()

    def add_author(self):
        name, ok_pressed = QInputDialog.getText(self, "Новый автор",
                                                "ФИО автора:")
        if ok_pressed and name.strip():
            self.db.add_author(name)
            self.after_change()

    def add_genre(self):
        title, ok_pressed = QInputDialog.getText(self, "Новый жанр",
                                                 "Название жанра:")
        if ok_pressed and title.strip():
            self.db.add_genre(title)
            self.after_change()

    def save_authors(self):
        for author_id, name in self.modified_authors.items():
            if not name:
                continue
            try:
                self.db.rename_author(author_id, name)
            except sqlite3.IntegrityError:
                # Имя автора в таблице уникальное (UNIQUE)
                QMessageBox.warning(self, "Ошибка",
                                    f"Автор «{name}» уже есть.")
        self.after_change()

    def save_genres(self):
        for genre_id, title in self.modified_genres.items():
            if not title:
                continue
            try:
                self.db.rename_genre(genre_id, title)
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка",
                                    f"Жанр «{title}» уже есть.")
        self.after_change()

    def selected_ids(self, table):
        """id выделенных строк таблицы (из нулевого столбца)."""
        rows = list(set([i.row() for i in table.selectedItems()]))
        return [table.item(i, 0).text() for i in rows]

    def confirm(self, text):
        answer = QMessageBox.question(
            self, "Удаление", text,
            buttons=(QMessageBox.StandardButton.Yes
                     | QMessageBox.StandardButton.No))
        return answer == QMessageBox.StandardButton.Yes

    def delete_authors(self):
        ids = self.selected_ids(self.authorsTable)
        if ids and self.confirm("Удалить выделенных авторов? "
                                "У их книг автор станет «не указан»."):
            for author_id in ids:
                self.db.delete_author(author_id)
            self.after_change()

    def delete_genres(self):
        ids = self.selected_ids(self.genresTable)
        if ids and self.confirm("Удалить выделенные жанры? "
                                "У их книг жанр станет «не указан»."):
            for genre_id in ids:
                self.db.delete_genre(genre_id)
            self.after_change()

    def after_change(self):
        """После любого изменения обновляем справочник и главное окно."""
        self.load_tables()
        self.parent_form.refresh_all()
