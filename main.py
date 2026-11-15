"""Домашняя библиотека: учёт книг, авторов и прочитанных страниц.

Запуск: python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
