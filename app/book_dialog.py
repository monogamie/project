"""Форма добавления / редактирования книги."""
import os
import shutil
import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFileDialog, QFormLayout, QHBoxLayout, QInputDialog,
                             QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                             QPushButton, QSlider, QSpinBox, QToolButton,
                             QVBoxLayout)

from .author_dialog import AuthorEditDialog
from .database import STATUSES
from .paths import COVERS_DIR, icon
from .widgets import CoverLabel


class BookDialog(QDialog):
    def __init__(self, db, book_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.book_id = book_id
        self.cover = ""
        self.setWindowTitle("Редактирование книги" if book_id else "Новая книга")
        self.setWindowIcon(QIcon(icon("book")))
        self.setMinimumWidth(620)
        self._build_ui()
        self._load_authors()
        self._load_genres()
        if book_id:
            self._load_book()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Название книги")

        self.author_combo = QComboBox()
        add_author = QToolButton()
        add_author.setIcon(QIcon(icon("add")))
        add_author.setToolTip("Добавить автора")
        add_author.clicked.connect(self.add_author)
        author_row = QHBoxLayout()
        author_row.addWidget(self.author_combo, 1)
        author_row.addWidget(add_author)

        self.genre_combo = QComboBox()
        add_genre = QToolButton()
        add_genre.setIcon(QIcon(icon("add")))
        add_genre.setToolTip("Добавить жанр")
        add_genre.clicked.connect(self.add_genre)
        genre_row = QHBoxLayout()
        genre_row.addWidget(self.genre_combo, 1)
        genre_row.addWidget(add_genre)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 2100)
        self.year_spin.setSpecialValueText("—")
        self.year_spin.setValue(2000)

        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(0, 10000)
        self.pages_spin.setSuffix(" стр.")

        self.rating_slider = QSlider(Qt.Orientation.Horizontal)
        self.rating_slider.setRange(0, 5)
        self.rating_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rating_slider.setTickInterval(1)
        self.rating_label = QLabel()
        self.rating_slider.valueChanged.connect(self._rating_changed)
        rating_row = QHBoxLayout()
        rating_row.addWidget(self.rating_slider, 1)
        rating_row.addWidget(self.rating_label)
        self._rating_changed(0)

        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUSES)

        self.favorite_check = QCheckBox("Любимая книга")

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Заметки, цитаты, впечатления…")

        form = QFormLayout()
        form.addRow("Название*:", self.title_edit)
        form.addRow("Автор:", author_row)
        form.addRow("Жанр:", genre_row)
        form.addRow("Год издания:", self.year_spin)
        form.addRow("Страниц:", self.pages_spin)
        form.addRow("Оценка:", rating_row)
        form.addRow("Статус:", self.status_combo)
        form.addRow("", self.favorite_check)
        form.addRow("Заметки:", self.notes_edit)

        self.cover_label = CoverLabel(150, 225)
        choose = QPushButton("Выбрать обложку…")
        choose.clicked.connect(self.choose_cover)
        clear = QPushButton("Убрать обложку")
        clear.clicked.connect(lambda: self._set_cover(""))
        cover_box = QVBoxLayout()
        cover_box.addWidget(self.cover_label)
        cover_box.addWidget(choose)
        cover_box.addWidget(clear)
        cover_box.addStretch()

        top = QHBoxLayout()
        top.addLayout(cover_box)
        top.addLayout(form, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(buttons)

    def _rating_changed(self, value):
        self.rating_label.setText("★" * value + "☆" * (5 - value))

    def _set_cover(self, cover):
        self.cover = cover
        self.cover_label.set_cover(cover)

    # -------------------------------------------------------------- данные
    def _load_authors(self, select_id=None):
        self.author_combo.clear()
        self.author_combo.addItem("— не указан —", None)
        for a in self.db.authors():
            self.author_combo.addItem(a["name"], a["id"])
        if select_id:
            self.author_combo.setCurrentIndex(self.author_combo.findData(select_id))

    def _load_genres(self, select_id=None):
        self.genre_combo.clear()
        self.genre_combo.addItem("— не указан —", None)
        for g in self.db.genres():
            self.genre_combo.addItem(g["name"], g["id"])
        if select_id:
            self.genre_combo.setCurrentIndex(self.genre_combo.findData(select_id))

    def _load_book(self):
        b = self.db.book(self.book_id)
        self.title_edit.setText(b["title"])
        self.author_combo.setCurrentIndex(max(0, self.author_combo.findData(b["author_id"])))
        self.genre_combo.setCurrentIndex(max(0, self.genre_combo.findData(b["genre_id"])))
        self.year_spin.setValue(b["year"] or 0)
        self.pages_spin.setValue(b["pages"] or 0)
        self.rating_slider.setValue(b["rating"] or 0)
        self.status_combo.setCurrentText(b["status"])
        self.favorite_check.setChecked(bool(b["favorite"]))
        self.notes_edit.setPlainText(b["notes"] or "")
        self._set_cover(b["cover"] or "")

    # ------------------------------------------------------------- действия
    def add_author(self):
        dlg = AuthorEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, country, year = dlg.values()
            try:
                new_id = self.db.add_author(name, country, year)
            except Exception:
                QMessageBox.warning(self, "Ошибка", "Такой автор уже есть.")
                new_id = self.db.author_id(name, create=False)
            self._load_authors(new_id)

    def add_genre(self):
        name, ok = QInputDialog.getText(self, "Новый жанр", "Название жанра:")
        name = name.strip()
        if ok and name:
            self._load_genres(self.db.genre_id(name))

    def choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "",
            "Картинки (*.png *.jpg *.jpeg *.bmp *.gif);;Все файлы (*)")
        if not path:
            return
        os.makedirs(COVERS_DIR, exist_ok=True)
        name = uuid.uuid4().hex[:12] + os.path.splitext(path)[1].lower()
        try:
            shutil.copy(path, os.path.join(COVERS_DIR, name))
        except OSError as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать файл:\n{e}")
            return
        self._set_cover(name)

    def data(self):
        return {
            "title": self.title_edit.text().strip(),
            "author_id": self.author_combo.currentData(),
            "genre_id": self.genre_combo.currentData(),
            "year": self.year_spin.value(),
            "pages": self.pages_spin.value(),
            "rating": self.rating_slider.value(),
            "status": self.status_combo.currentText(),
            "favorite": int(self.favorite_check.isChecked()),
            "cover": self.cover,
            "notes": self.notes_edit.toPlainText().strip(),
        }

    def save(self):
        data = self.data()
        if not data["title"]:
            QMessageBox.warning(self, "Ошибка", "Введите название книги.")
            self.title_edit.setFocus()
            return
        if self.book_id:
            self.db.update_book(self.book_id, data)
        else:
            self.book_id = self.db.add_book(data)
        self.accept()
