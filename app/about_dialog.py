"""Форма «О программе»."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .paths import icon, image

VERSION = "1.0"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setWindowIcon(QIcon(icon("about")))
        logo = QLabel()
        logo.setPixmap(QPixmap(image("logo.png")).scaled(
            128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        text = QLabel(
            f"<h2>Домашняя библиотека</h2>"
            f"<p>Версия {VERSION}</p>"
            "<p>Программа для учёта домашней библиотеки: книги, авторы, жанры, "
            "журнал чтения и статистика.</p>"
            "<p>Проект выполнен на Python + PyQt5, данные хранятся в SQLite.</p>")
        text.setWordWrap(True)
        text.setMinimumWidth(300)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        top = QHBoxLayout()
        top.addWidget(logo, 0, Qt.AlignTop)
        top.addWidget(text, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(ok, 0, Qt.AlignRight)
