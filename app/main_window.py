"""Главное окно приложения."""
import datetime
import os
import random

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QTextCharFormat
from PyQt6.QtWidgets import (QAbstractItemView, QButtonGroup,
                             QCalendarWidget, QCheckBox, QColorDialog, QComboBox,
                             QFileDialog, QFontDialog, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QListWidget,
                             QMainWindow, QMenu, QMessageBox, QProgressBar,
                             QPushButton, QRadioButton, QSplitter, QTableWidget,
                             QTableWidgetItem, QTabWidget, QTextBrowser,
                             QVBoxLayout, QWidget)

from .about_dialog import AboutDialog
from .author_dialog import AuthorsDialog, GenresDialog
from .book_dialog import BookDialog
from .database import STATUSES
from .paths import icon, resource_path
from .reading_dialog import ReadingDialog
from .stats_widget import StatsWidget
from .widgets import CoverLabel, StarRating

COLUMNS = ["", "Название", "Автор", "Жанр", "Год", "Страниц", "Прогресс", "Оценка", "Статус"]
STATUS_COLORS = {"Хочу прочитать": "#8a94a6", "Читаю": "#e0893a", "Прочитано": "#3a9d5d"}


class NumItem(QTableWidgetItem):
    """Ячейка таблицы, которая сортируется как число."""

    def __init__(self, value, text=None):
        super().__init__(str(value) if text is None else text)
        self.value = value
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(other, NumItem):
            return self.value < other.value
        return super().__lt__(other)


def load_quotes():
    """Цитаты о книгах из текстового файла data/quotes.txt."""
    try:
        with open(resource_path("data", "quotes.txt"), encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except OSError:
        return []


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.accent = QColor(db.setting("accent", "#3f6fb5"))
        self.setWindowTitle("Домашняя библиотека")
        self.setWindowIcon(QIcon(resource_path("images", "logo.png")))
        self.resize(1360, 760)

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_central()
        self.statusBar()
        self.apply_accent()
        self.refresh_all()

    # ============================================================ интерфейс
    def _action(self, text, icon_name, slot, shortcut=None):
        act = QAction(QIcon(icon(icon_name)), text, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        return act

    def _create_actions(self):
        self.act_add = self._action("Добавить книгу", "add", self.add_book, "Ctrl+N")
        self.act_edit = self._action("Изменить", "edit", self.edit_book, "Ctrl+E")
        self.act_delete = self._action("Удалить", "delete", self.delete_book, "Delete")
        self.act_read = self._action("Журнал чтения", "read", self.open_readings, "Ctrl+R")
        self.act_fav = self._action("Любимая / не любимая", "star", self.toggle_favorite, "Ctrl+F")
        self.act_import = self._action("Импорт из CSV…", "import", self.import_csv, "Ctrl+I")
        self.act_export = self._action("Экспорт в CSV…", "export", self.export_csv, "Ctrl+S")
        self.act_report = self._action("Сохранить отчёт (TXT)…", "report", self.save_report)
        self.act_exit = self._action("Выход", "exit", self.close, "Ctrl+Q")
        self.act_authors = self._action("Авторы…", "authors", self.open_authors)
        self.act_genres = self._action("Жанры…", "genres", self.open_genres)
        self.act_font = self._action("Шрифт таблицы…", "font", self.choose_font)
        self.act_color = self._action("Цвет оформления…", "color", self.choose_color)
        self.act_about = self._action("О программе", "about", self.about, "F1")

    def _create_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&Файл")
        file_menu.addActions([self.act_import, self.act_export, self.act_report])
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)
        book_menu = menu.addMenu("&Книги")
        book_menu.addActions([self.act_add, self.act_edit, self.act_delete])
        book_menu.addSeparator()
        book_menu.addActions([self.act_read, self.act_fav])
        ref_menu = menu.addMenu("&Справочники")
        ref_menu.addActions([self.act_authors, self.act_genres])
        view_menu = menu.addMenu("&Вид")
        view_menu.addActions([self.act_font, self.act_color])
        help_menu = menu.addMenu("&Справка")
        help_menu.addAction(self.act_about)

    def _create_toolbar(self):
        tb = self.addToolBar("Основная панель")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tb.addActions([self.act_add, self.act_edit, self.act_delete, self.act_read])
        tb.addSeparator()
        tb.addActions([self.act_authors, self.act_genres])
        tb.addSeparator()
        tb.addActions([self.act_import, self.act_export, self.act_report])

    def _create_filters(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Название или автор…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.refresh_books)

        self.genre_filter = QComboBox()
        self.genre_filter.currentIndexChanged.connect(self.refresh_books)

        status_box = QGroupBox("Статус")
        status_layout = QVBoxLayout(status_box)
        self.status_group = QButtonGroup(self)
        for i, text in enumerate(["Все"] + STATUSES):
            rb = QRadioButton(text)
            rb.setChecked(i == 0)
            self.status_group.addButton(rb, i)
            status_layout.addWidget(rb)
        self.status_group.buttonClicked.connect(self.refresh_books)

        self.fav_check = QCheckBox("Только любимые")
        self.fav_check.stateChanged.connect(self.refresh_books)

        reset = QPushButton("Сбросить фильтры")
        reset.clicked.connect(self.reset_filters)

        quotes = load_quotes()
        self.quote_label = QLabel(random.choice(quotes) if quotes else "")
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet("color: #555; font-style: italic;")
        quote_box = QGroupBox("Цитата дня")
        QVBoxLayout(quote_box).addWidget(self.quote_label)

        layout.addWidget(QLabel("Поиск:"))
        layout.addWidget(self.search_edit)
        layout.addWidget(QLabel("Жанр:"))
        layout.addWidget(self.genre_filter)
        layout.addWidget(status_box)
        layout.addWidget(self.fav_check)
        layout.addWidget(reset)
        layout.addStretch()
        layout.addWidget(quote_box)
        return panel

    def _create_preview(self):
        panel = QWidget()
        panel.setMinimumWidth(230)
        layout = QVBoxLayout(panel)
        self.preview_cover = CoverLabel(170, 255)
        self.preview_title = QLabel()
        self.preview_title.setWordWrap(True)
        self.preview_stars = StarRating()
        self.preview_progress = QProgressBar()
        self.preview_progress.setFormat("Прочитано %p%")
        self.preview_notes = QTextBrowser()
        read_btn = QPushButton(QIcon(icon("read")), "Журнал чтения")
        read_btn.clicked.connect(self.open_readings)
        layout.addWidget(self.preview_cover, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.preview_title)
        layout.addWidget(self.preview_stars)
        layout.addWidget(self.preview_progress)
        layout.addWidget(QLabel("Заметки:"))
        layout.addWidget(self.preview_notes, 1)
        layout.addWidget(read_btn)
        return panel

    def _create_calendar_tab(self):
        tab = QWidget()
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMaximumDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self.refresh_day)
        self.day_label = QLabel()
        self.day_list = QListWidget()
        right = QVBoxLayout()
        right.addWidget(self.day_label)
        right.addWidget(self.day_list)
        layout = QHBoxLayout(tab)
        layout.addWidget(self.calendar, 2)
        layout.addLayout(right, 1)
        return tab

    def _create_central(self):
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().hide()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 165)
        self.table.itemSelectionChanged.connect(self.update_preview)
        self.table.itemDoubleClicked.connect(lambda _: self.edit_book())
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        font = self.db.setting("table_font")
        if font:
            f = self.table.font()
            f.fromString(font)
            self.table.setFont(f)

        self.stats = StatsWidget(self.db)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.table, QIcon(icon("book")), "Книги")
        self.tabs.addTab(self.stats, QIcon(icon("stats")), "Статистика")
        self.tabs.addTab(self._create_calendar_tab(), QIcon(icon("read")), "Календарь чтения")
        self.tabs.currentChanged.connect(self.refresh_extra)

        splitter = QSplitter()
        splitter.addWidget(self._create_filters())
        splitter.addWidget(self.tabs)
        splitter.addWidget(self._create_preview())
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([210, 920, 230])
        self.setCentralWidget(splitter)

    # ============================================================ обновление
    def refresh_all(self):
        self.refresh_genre_filter()
        self.refresh_books()
        self.refresh_extra()

    def refresh_extra(self, *_):
        self.stats.refresh()
        self.refresh_calendar()

    def refresh_genre_filter(self):
        current = self.genre_filter.currentData()
        self.genre_filter.blockSignals(True)
        self.genre_filter.clear()
        self.genre_filter.addItem("Все жанры", None)
        for g in self.db.genres():
            self.genre_filter.addItem(f"{g['name']} ({g['cnt']})", g["id"])
        index = self.genre_filter.findData(current)
        self.genre_filter.setCurrentIndex(max(index, 0))
        self.genre_filter.blockSignals(False)

    def current_filters(self):
        status_id = self.status_group.checkedId()
        return {
            "text": self.search_edit.text().strip(),
            "genre_id": self.genre_filter.currentData(),
            "status": STATUSES[status_id - 1] if status_id > 0 else None,
            "favorites": self.fav_check.isChecked(),
        }

    def refresh_books(self, *_):
        selected = self.selected_id()
        books = self.db.books(**self.current_filters())
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(books))
        for row, b in enumerate(books):
            percent = 0
            if b["pages"]:
                percent = min(100, round(b["read_pages"] * 100 / b["pages"]))
            if b["status"] == "Прочитано":
                percent = 100
            fav = NumItem(b["favorite"], "★" if b["favorite"] else "")
            fav.setForeground(QColor("#f2a900"))
            title = QTableWidgetItem(b["title"])
            title.setData(Qt.ItemDataRole.UserRole, b["id"])
            status = QTableWidgetItem(b["status"])
            status.setForeground(QColor(STATUS_COLORS.get(b["status"], "#000")))
            items = [fav, title, QTableWidgetItem(b["author"]), QTableWidgetItem(b["genre"]),
                     NumItem(b["year"], str(b["year"] or "")),
                     NumItem(b["pages"]), NumItem(percent, f"{percent}%"),
                     NumItem(b["rating"], "★" * b["rating"]), status]
            for col, item in enumerate(items):
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.select_id(selected)
        self.statusBar().showMessage(f"Показано книг: {len(books)}")
        self.update_preview()

    def refresh_calendar(self):
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        fmt = QTextCharFormat()
        fmt.setBackground(self.accent.lighter(170))
        fmt.setFontWeight(QFont.Weight.Bold)
        for d in self.db.reading_dates():
            self.calendar.setDateTextFormat(QDate.fromString(d, Qt.DateFormat.ISODate), fmt)
        self.refresh_day()

    def refresh_day(self):
        date = self.calendar.selectedDate()
        rows = self.db.readings(date=date.toString(Qt.DateFormat.ISODate))
        self.day_list.clear()
        for r in rows:
            self.day_list.addItem(f"{r['title']} — {r['pages']} стр.")
        total = sum(r["pages"] for r in rows)
        self.day_label.setText(f"<b>{date.toString('dd.MM.yyyy')}</b>: прочитано {total} стр.")

    def selected_id(self):
        row = self.table.currentRow()
        if row < 0 or not self.table.selectedItems():
            return None
        return self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)

    def select_id(self, book_id):
        if book_id is None:
            return
        for row in range(self.table.rowCount()):
            if self.table.item(row, 1).data(Qt.ItemDataRole.UserRole) == book_id:
                self.table.selectRow(row)
                return

    def update_preview(self):
        book_id = self.selected_id()
        b = self.db.book(book_id) if book_id else None
        if not b:
            self.preview_cover.set_cover("")
            self.preview_title.setText("<i>Выберите книгу в таблице</i>")
            self.preview_stars.set_value(0)
            self.preview_progress.setValue(0)
            self.preview_notes.clear()
            return
        self.preview_cover.set_cover(b["cover"])
        year = f", {b['year']}" if b["year"] else ""
        self.preview_title.setText(
            f"<h3>{b['title']}</h3>{b['author'] or 'Автор не указан'}{year}<br>"
            f"<span style='color:{STATUS_COLORS[b['status']]}'>{b['status']}</span>")
        self.preview_stars.set_value(b["rating"])
        self.preview_progress.setRange(0, max(b["pages"], 1))
        value = b["pages"] if b["status"] == "Прочитано" else min(b["read_pages"], b["pages"])
        self.preview_progress.setValue(value)
        self.preview_notes.setPlainText(b["notes"] or "")

    # ============================================================== действия
    def need_book(self):
        book_id = self.selected_id()
        if book_id is None:
            QMessageBox.information(self, "Нет выбора", "Сначала выберите книгу в таблице.")
        return book_id

    def add_book(self):
        dlg = BookDialog(self.db, parent=self)
        if dlg.exec():
            self.refresh_all()
            self.select_id(dlg.book_id)

    def edit_book(self):
        book_id = self.need_book()
        if book_id and BookDialog(self.db, book_id, self).exec():
            self.refresh_all()

    def delete_book(self):
        book_id = self.need_book()
        if not book_id:
            return
        title = self.db.book(book_id)["title"]
        answer = QMessageBox.question(
            self, "Удаление книги",
            f"Удалить книгу «{title}» вместе с журналом чтения?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.db.delete_book(book_id)
            self.refresh_all()

    def open_readings(self):
        book_id = self.need_book()
        if book_id:
            ReadingDialog(self.db, book_id, self).exec()
            self.refresh_all()

    def toggle_favorite(self):
        book_id = self.need_book()
        if book_id:
            self.db.set_favorite(book_id, not self.db.book(book_id)["favorite"])
            self.refresh_books()

    def set_status(self, status):
        book_id = self.need_book()
        if book_id:
            self.db.set_status(book_id, status)
            self.refresh_all()

    def context_menu(self, pos):
        if self.table.itemAt(pos) is None:
            return
        menu = QMenu(self)
        menu.addActions([self.act_edit, self.act_read, self.act_fav])
        status_menu = menu.addMenu("Статус")
        for s in STATUSES:
            status_menu.addAction(s, lambda s=s: self.set_status(s))
        menu.addSeparator()
        menu.addAction(self.act_delete)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def open_authors(self):
        AuthorsDialog(self.db, self).exec()
        self.refresh_all()

    def open_genres(self):
        GenresDialog(self.db, self).exec()
        self.refresh_all()

    def reset_filters(self):
        self.search_edit.clear()
        self.genre_filter.setCurrentIndex(0)
        self.status_group.button(0).setChecked(True)
        self.fav_check.setChecked(False)
        self.refresh_books()

    # ----------------------------------------------------------- файлы
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт книг", "", "CSV-файлы (*.csv);;Все файлы (*)")
        if not path:
            return
        try:
            count = self.db.import_csv(path)
        except (OSError, UnicodeDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))
            return
        self.refresh_all()
        QMessageBox.information(self, "Импорт", f"Добавлено книг: {count}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт книг", "books.csv", "CSV-файлы (*.csv)")
        if not path:
            return
        try:
            count = self.db.export_csv(path, self.db.books(**self.current_filters()))
        except OSError as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))
            return
        QMessageBox.information(self, "Экспорт", f"Сохранено книг: {count}\n{path}")

    def save_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "report.txt", "Текстовые файлы (*.txt)")
        if not path:
            return
        year = datetime.date.today().year
        by_status = self.db.count_by_status()
        lines = [
            "ОТЧЁТ «ДОМАШНЯЯ БИБЛИОТЕКА»",
            f"Дата: {datetime.date.today():%d.%m.%Y}",
            "",
            f"Всего книг: {sum(by_status.values())}",
        ]
        lines += [f"  {s}: {n}" for s, n in by_status.items()]
        lines += ["", f"Прочитано страниц за {year} год: {self.db.pages_read_total(year)}",
                  "", "Книги по жанрам:"]
        lines += [f"  {g}: {n}" for g, n in self.db.count_by_genre()]
        lines += ["", "Список книг:"]
        for i, b in enumerate(self.db.books(), 1):
            lines.append(f"{i:3}. {b['title']} — {b['author'] or 'автор не указан'} "
                         f"[{b['status']}] {'★' * b['rating']}")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except OSError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        self.statusBar().showMessage(f"Отчёт сохранён: {os.path.basename(path)}", 5000)

    # ----------------------------------------------------------- вид
    def choose_font(self):
        font, ok = QFontDialog.getFont(self.table.font(), self, "Шрифт таблицы")
        if ok:
            self.table.setFont(font)
            self.db.set_setting("table_font", font.toString())

    def choose_color(self):
        color = QColorDialog.getColor(self.accent, self, "Цвет оформления")
        if color.isValid():
            self.accent = color
            self.db.set_setting("accent", color.name())
            self.apply_accent()
            self.refresh_calendar()

    def apply_accent(self):
        c = self.accent.name()
        self.setStyleSheet(
            f"QHeaderView::section {{ background: {c}; color: white; padding: 4px;"
            f" border: none; font-weight: bold; }}"
            f"QProgressBar::chunk {{ background: {c}; }}"
            f"QTableWidget {{ selection-background-color: {self.accent.darker(110).name()}; }}")
        self.stats.set_color(self.accent)

    def about(self):
        AboutDialog(self).exec()

    def closeEvent(self, event):
        answer = QMessageBox.question(self, "Выход", "Закрыть программу?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if answer == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
