"""Домашняя библиотека — точка входа.

Запуск:  python main.py
"""
import sys

from PyQt6.QtCore import QLibraryInfo, QLocale, Qt, QTimer, QTranslator
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen

from app.database import Database
from app.main_window import MainWindow
from app.paths import DB_PATH, image, resource_path


def excepthook(exc_type, exc, tb):
    """Показывает непойманную ошибку в окне, чтобы exe не закрывался молча."""
    import traceback
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    print(text, file=sys.stderr)
    QMessageBox.critical(None, "Ошибка", text[-1500:])


def main():
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # русский язык для стандартных диалогов и календаря
    QLocale.setDefault(QLocale(QLocale.Language.Russian, QLocale.Country.Russia))
    translator = QTranslator(app)
    if translator.load("qtbase_ru", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    app.setWindowIcon(QIcon(image("logo.png")))

    splash = QSplashScreen(QPixmap(image("splash.png")))
    splash.show()
    splash.showMessage("Загрузка базы данных…", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, Qt.GlobalColor.white)
    app.processEvents()

    try:
        db = Database(DB_PATH)
        if db.is_empty():
            # первый запуск — заполняем библиотеку примерами из CSV
            db.import_csv(resource_path("data", "books_sample.csv"))
    except Exception as e:  # noqa: BLE001
        splash.close()
        QMessageBox.critical(None, "Ошибка", f"Не удалось открыть базу данных:\n{e}")
        return 1

    window = MainWindow(db)
    QTimer.singleShot(1200, lambda: (window.show(), splash.finish(window)))
    code = app.exec()
    db.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
