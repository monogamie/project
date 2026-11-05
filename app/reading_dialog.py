"""Форма «Журнал чтения» для выбранной книги."""
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAbstractItemView, QDateEdit, QDial, QDialog,
                             QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                             QMessageBox, QProgressBar, QPushButton, QSpinBox,
                             QTableWidget, QTableWidgetItem, QVBoxLayout)

from .paths import icon
from .widgets import CoverLabel


class ReadingDialog(QDialog):
    def __init__(self, db, book_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.book_id = book_id
        book = db.book(book_id)
        self.total_pages = book["pages"] or 0
        self.setWindowTitle(f"Журнал чтения — {book['title']}")
        self.setWindowIcon(QIcon(icon("read")))
        self.resize(640, 460)

        cover = CoverLabel(100, 150)
        cover.set_cover(book["cover"])
        title = QLabel(f"<h3>{book['title']}</h3>{book['author']}<br>"
                       f"Всего страниц: {self.total_pages or 'не указано'}")
        title.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setFormat("%v из %m стр. (%p%)")
        info = QVBoxLayout()
        info.addWidget(title)
        info.addWidget(self.progress)
        info.addStretch()
        header = QHBoxLayout()
        header.addWidget(cover)
        header.addLayout(info, 1)

        # ----- добавление записи
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 2000)
        self.pages_spin.setValue(20)
        self.pages_spin.setSuffix(" стр.")
        self.dial = QDial()
        self.dial.setRange(1, 200)
        self.dial.setValue(20)
        self.dial.setNotchesVisible(True)
        self.dial.setFixedSize(70, 70)
        self.dial.valueChanged.connect(self.pages_spin.setValue)
        self.pages_spin.valueChanged.connect(
            lambda v: self.dial.setValue(min(v, self.dial.maximum())))
        add_btn = QPushButton(QIcon(icon("add")), "Добавить запись")
        add_btn.clicked.connect(self.add_record)

        add_box = QGroupBox("Новая запись")
        row = QHBoxLayout(add_box)
        row.addWidget(QLabel("Дата:"))
        row.addWidget(self.date_edit)
        row.addWidget(QLabel("Прочитано:"))
        row.addWidget(self.pages_spin)
        row.addWidget(self.dial)
        row.addWidget(add_btn)

        # ----- история
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Дата", "Страниц"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().hide()
        del_btn = QPushButton(QIcon(icon("delete")), "Удалить запись")
        del_btn.clicked.connect(self.delete_record)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        bottom = QHBoxLayout()
        bottom.addWidget(del_btn)
        bottom.addStretch()
        bottom.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(add_box)
        layout.addWidget(self.table)
        layout.addLayout(bottom)
        self.load()

    def load(self):
        rows = self.db.readings(book_id=self.book_id)
        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            date_item = QTableWidgetItem(QDate.fromString(rec["date"], Qt.ISODate)
                                         .toString("dd.MM.yyyy"))
            date_item.setData(Qt.UserRole, rec["id"])
            pages_item = QTableWidgetItem(str(rec["pages"]))
            pages_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 0, date_item)
            self.table.setItem(r, 1, pages_item)
        read = sum(rec["pages"] for rec in rows)
        maximum = max(self.total_pages, read, 1)
        self.progress.setRange(0, maximum)
        self.progress.setValue(read)
        return read

    def add_record(self):
        self.db.add_reading(self.book_id, self.date_edit.date().toString(Qt.ISODate),
                            self.pages_spin.value())
        read = self.load()
        book = self.db.book(self.book_id)
        if book["status"] == "Хочу прочитать":
            self.db.set_status(self.book_id, "Читаю")
        if self.total_pages and read >= self.total_pages and book["status"] != "Прочитано":
            answer = QMessageBox.question(
                self, "Книга прочитана?",
                "Вы прочитали все страницы. Отметить книгу как «Прочитано»?")
            if answer == QMessageBox.Yes:
                self.db.set_status(self.book_id, "Прочитано")

    def delete_record(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if QMessageBox.question(self, "Удаление", "Удалить выбранную запись?") == QMessageBox.Yes:
            self.db.delete_reading(self.table.item(row, 0).data(Qt.UserRole))
            self.load()
