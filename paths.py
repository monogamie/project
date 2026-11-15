"""Пути к файлам программы и загрузка картинок обложек."""
import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


def resource_path(relative_path):
    """Возвращает путь к файлу программы.

    Приём из урока QT 8: собранный exe распаковывает свои файлы
    (окна .ui, картинки, csv) во временную папку sys._MEIPASS,
    а при обычном запуске они лежат в папке проекта.
    """
    if hasattr(sys, '_MEIPASS'):
        # Программа запущена из exe: файлы лежат во временной папке
        base_path = sys._MEIPASS
    else:
        # Обычный запуск: файлы лежат в текущей папке
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def cover_pixmap(path, width, height):
    """Картинка обложки нужного размера.

    Если обложка не выбрана или файл не найден,
    возвращается картинка-заглушка «Нет обложки».
    """
    pixmap = QPixmap(path) if path else QPixmap()
    # QPixmap не выдаёт ошибку, если файла нет, а просто остаётся пустым
    if pixmap.isNull():
        pixmap = QPixmap(resource_path("images/no_cover.png"))
    # Уменьшаем картинку, сохраняя пропорции (урок QT 3)
    return pixmap.scaled(width, height,
                         Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
