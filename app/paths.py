"""Пути к ресурсам и пользовательским данным.

Работает и при обычном запуске (python main.py), и в собранном exe
(PyInstaller распаковывает ресурсы во временную папку sys._MEIPASS).
"""
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts):
    """Путь к файлу, который упакован вместе с программой (картинки, csv, txt)."""
    base = getattr(sys, "_MEIPASS", PROJECT_DIR)
    return os.path.join(base, *parts)


def user_dir():
    """Папка, в которой хранятся БД и обложки (рядом с exe или с main.py)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return PROJECT_DIR


DB_PATH = os.path.join(user_dir(), "library.db")
COVERS_DIR = os.path.join(user_dir(), "covers")


def icon(name):
    return resource_path("images", "icons", name + ".png")


def image(name):
    return resource_path("images", name)
