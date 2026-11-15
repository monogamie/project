"""Форма добавления и изменения книги."""
from PyQt6 import uic
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from database import STATUSES
from paths import cover_pixmap, resource_path

# Первый пункт в списках авторов и жанров
NOT_SELECTED = "— не указан —"
# Формат, в котором даты хранятся в базе
DATE_FORMAT = "yyyy-MM-dd"


class BookForm(QWidget):
    """Окно книги. Если book_id не передан, добавляем новую книгу."""

    def __init__(self, parent_form, book_id=None):
        super().__init__()
        uic.loadUi(resource_path("ui/book_form.ui"), self)
        # Ссылка на главное окно: через неё попросим обновить таблицу
        self.parent_form = parent_form
        self.db = parent_form.db
        self.book_id = book_id
        # Путь к файлу обложки
        self.cover = ""

        self.statusBox.addItems(STATUSES)
        self.addedDate.setDate(QDate.currentDate())
        self.load_authors()
        self.load_genres()

        self.chooseCoverButton.clicked.connect(self.choose_cover)
        self.clearCoverButton.clicked.connect(self.clear_cover)
        self.addAuthorButton.clicked.connect(self.add_author)
        self.addGenreButton.clicked.connect(self.add_genre)
        self.saveButton.clicked.connect(self.save)
        self.cancelButton.clicked.connect(self.close)

        if self.book_id:
            self.setWindowTitle("Изменение книги")
            self.load_book()
        else:
            self.setWindowTitle("Новая книга")
        self.show_cover()

    def load_authors(self, selected=""):
        """Заполняет список авторов из базы данных."""
        self.authorBox.clear()
        self.authorBox.addItem(NOT_SELECTED)
        for author in self.db.get_authors():
            self.authorBox.addItem(author["name"])
        if selected:
            self.authorBox.setCurrentText(selected)

    def load_genres(self, selected=""):
        """Заполняет список жанров из базы данных."""
        self.genreBox.clear()
        self.genreBox.addItem(NOT_SELECTED)
        for genre in self.db.get_genres():
            self.genreBox.addItem(genre["title"])
        if selected:
            self.genreBox.setCurrentText(selected)

    def load_book(self):
        """При изменении книги раскладывает её данные по полям."""
        book = self.db.get_book(self.book_id)
        self.titleEdit.setText(book["title"])
        self.authorBox.setCurrentText(book["author"] or NOT_SELECTED)
        self.genreBox.setCurrentText(book["genre"] or NOT_SELECTED)
        self.yearSpin.setValue(book["year"] or 0)
        self.pagesSpin.setValue(book["pages"] or 0)
        self.ratingSpin.setValue(book["rating"] or 0)
        self.statusBox.setCurrentText(book["status"])
        self.favoriteCheck.setChecked(book["favorite"] == 1)
        self.notesEdit.setPlainText(book["notes"] or "")
        if book["added"]:
            self.addedDate.setDate(QDate.fromString(book["added"],
                                                    DATE_FORMAT))
        self.cover = book["cover"] or ""

    def show_cover(self):
        self.coverLabel.setPixmap(cover_pixmap(self.cover, 150, 225))

    def choose_cover(self):
        # Стандартный диалог выбора файла (урок QT 3)
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "",
            "Картинки (*.png *.jpg *.jpeg *.bmp);;Все файлы (*)")
        if path:
            self.cover = path
            self.show_cover()

    def clear_cover(self):
        self.cover = ""
        self.show_cover()

    def add_author(self):
        # Стандартный диалог ввода текста (урок QT 3)
        name, ok_pressed = QInputDialog.getText(self, "Новый автор",
                                                "ФИО автора:")
        if ok_pressed and name.strip():
            self.db.add_author(name)
            self.load_authors(name.strip())

    def add_genre(self):
        title, ok_pressed = QInputDialog.getText(self, "Новый жанр",
                                                 "Название жанра:")
        if ok_pressed and title.strip():
            self.db.add_genre(title)
            self.load_genres(title.strip())

    def save(self):
        title = self.titleEdit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название книги.")
            return

        # Вместо имени автора и названия жанра в книгу записываем их id
        author_id = None
        if self.authorBox.currentText() != NOT_SELECTED:
            author_id = self.db.find_author_id(self.authorBox.currentText())
        genre_id = None
        if self.genreBox.currentText() != NOT_SELECTED:
            genre_id = self.db.find_genre_id(self.genreBox.currentText())

        values = (title, author_id, genre_id, self.yearSpin.value(),
                  self.pagesSpin.value(), self.ratingSpin.value(),
                  self.statusBox.currentText(),
                  1 if self.favoriteCheck.isChecked() else 0,
                  self.cover, self.notesEdit.toPlainText().strip(),
                  self.addedDate.date().toString(DATE_FORMAT))

        if self.book_id:
            self.db.update_book(self.book_id, values)
        else:
            self.db.add_book(values)

        # Просим главное окно обновить данные и закрываем форму (урок QT 1)
        self.parent_form.refresh_all()
        self.close()
