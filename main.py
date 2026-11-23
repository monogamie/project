"""Домашняя библиотека: учёт книг, авторов и прочитанных страниц.

Запуск: python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Стиль Fusion: программа одинаково выглядит в Windows 10 и 11
    app.setStyle("Fusion")
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
