"""Формы справочников: авторы и жанры."""
import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox,
                             QFormLayout, QHBoxLayout, QHeaderView, QInputDialog,
                             QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                             QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
                             QVBoxLayout)

from .paths import icon


class AuthorEditDialog(QDialog):
    """Маленькая форма ввода данных одного автора."""

    def __init__(self, name="", country="", year=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Автор")
        self.setWindowIcon(QIcon(icon("authors")))
        self.name_edit = QLineEdit(name)
        self.country_edit = QLineEdit(country)
        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 2100)
        self.year_spin.setSpecialValueText("—")
        self.year_spin.setValue(year or 0)
        form = QFormLayout(self)
        form.addRow("ФИО*:", self.name_edit)
        form.addRow("Страна:", self.country_edit)
        form.addRow("Год рождения:", self.year_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _check(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите имя автора.")
            return
        self.accept()

    def values(self):
        return (self.name_edit.text().strip(), self.country_edit.text().strip(),
                self.year_spin.value())


class AuthorsDialog(QDialog):
    """Справочник авторов: таблица с редактированием прямо в ячейках."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.loading = False
        self.setWindowTitle("Справочник авторов")
        self.setWindowIcon(QIcon(icon("authors")))
        self.resize(620, 420)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Страна", "Год рождения", "Книг"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self.item_changed)

        add_btn = QPushButton(QIcon(icon("add")), "Добавить")
        add_btn.clicked.connect(self.add)
        del_btn = QPushButton(QIcon(icon("delete")), "Удалить")
        del_btn.clicked.connect(self.delete)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.addWidget(add_btn)
        buttons.addWidget(del_btn)
        buttons.addStretch()
        buttons.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(buttons)
        self.load()

    def load(self):
        self.loading = True
        rows = self.db.authors()
        self.table.setRowCount(len(rows))
        for r, a in enumerate(rows):
            values = [a["name"], a["country"] or "", str(a["birth_year"] or ""), str(a["cnt"])]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, a["id"])
                if c == 3:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)
        self.loading = False

    def item_changed(self, item):
        """Изменение данных в БД при редактировании ячейки."""
        if self.loading:
            return
        row = item.row()
        author_id = item.data(Qt.ItemDataRole.UserRole)
        name = self.table.item(row, 0).text().strip()
        country = self.table.item(row, 1).text().strip()
        year_text = self.table.item(row, 2).text().strip()
        if not name or (year_text and not year_text.isdigit()):
            QMessageBox.warning(self, "Ошибка",
                                "Имя не может быть пустым, а год должен быть числом.")
            self.load()
            return
        try:
            self.db.update_author(author_id, name, country, int(year_text or 0))
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Автор с таким именем уже существует.")
            self.load()

    def add(self):
        dlg = AuthorEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self.db.add_author(*dlg.values())
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка", "Такой автор уже есть.")
            self.load()

    def delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        count = self.table.item(row, 3).text()
        answer = QMessageBox.question(
            self, "Удаление автора",
            f"Удалить автора «{name}»?\nУ {count} книг(и) автор станет «не указан».")
        if answer == QMessageBox.StandardButton.Yes:
            self.db.delete_author(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
            self.load()


class GenresDialog(QDialog):
    """Справочник жанров на основе QListWidget и QInputDialog."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Справочник жанров")
        self.setWindowIcon(QIcon(icon("genres")))
        self.resize(380, 400)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(lambda _: self.rename())

        add_btn = QPushButton(QIcon(icon("add")), "Добавить")
        add_btn.clicked.connect(self.add)
        ren_btn = QPushButton(QIcon(icon("edit")), "Переименовать")
        ren_btn.clicked.connect(self.rename)
        del_btn = QPushButton(QIcon(icon("delete")), "Удалить")
        del_btn.clicked.connect(self.delete)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)

        side = QVBoxLayout()
        for b in (add_btn, ren_btn, del_btn):
            side.addWidget(b)
        side.addStretch()
        side.addWidget(close_btn)

        layout = QHBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(side)
        self.load()

    def load(self):
        self.list.clear()
        for g in self.db.genres():
            item = QListWidgetItem(QIcon(icon("genres")), f"{g['name']}  ({g['cnt']})")
            item.setData(Qt.ItemDataRole.UserRole, g["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, g["name"])
            self.list.addItem(item)

    def add(self):
        name, ok = QInputDialog.getText(self, "Новый жанр", "Название:")
        if ok and name.strip():
            try:
                self.db.add_genre(name.strip())
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка", "Такой жанр уже есть.")
            self.load()

    def rename(self):
        item = self.list.currentItem()
        if not item:
            return
        name, ok = QInputDialog.getText(self, "Переименовать жанр", "Новое название:",
                                        text=item.data(Qt.ItemDataRole.UserRole + 1))
        if ok and name.strip():
            try:
                self.db.rename_genre(item.data(Qt.ItemDataRole.UserRole), name.strip())
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка", "Такой жанр уже есть.")
            self.load()

    def delete(self):
        item = self.list.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Удаление",
                                f"Удалить жанр «{item.data(Qt.ItemDataRole.UserRole + 1)}»?") == QMessageBox.StandardButton.Yes:
            self.db.delete_genre(item.data(Qt.ItemDataRole.UserRole))
            self.load()
