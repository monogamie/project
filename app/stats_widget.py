"""Вкладка «Статистика»."""
import datetime

from PyQt5.QtWidgets import (QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLCDNumber, QProgressBar, QSpinBox,
                             QVBoxLayout, QWidget)

from .widgets import BarChart

MONTHS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
          "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]


class StatsWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.lcd_total = self._lcd()
        self.lcd_read = self._lcd()
        self.lcd_reading = self._lcd()
        self.lcd_pages = self._lcd(6)
        counters = QGroupBox("Счётчики")
        grid = QGridLayout(counters)
        for col, (title, lcd) in enumerate([("Всего книг", self.lcd_total),
                                            ("Прочитано", self.lcd_read),
                                            ("Читаю сейчас", self.lcd_reading),
                                            ("Страниц за год", self.lcd_pages)]):
            grid.addWidget(QLabel(title), 0, col)
            grid.addWidget(lcd, 1, col)

        year = datetime.date.today().year
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(year)
        self.year_spin.valueChanged.connect(self.refresh)
        self.goal_spin = QSpinBox()
        self.goal_spin.setRange(100, 100000)
        self.goal_spin.setSingleStep(500)
        self.goal_spin.setSuffix(" стр.")
        self.goal_spin.setValue(int(db.setting("goal_pages", 5000)))
        self.goal_spin.valueChanged.connect(self.goal_changed)
        self.goal_bar = QProgressBar()
        self.goal_bar.setFormat("%p%")
        goal = QGroupBox("Цель на год")
        form = QFormLayout(goal)
        form.addRow("Год:", self.year_spin)
        form.addRow("Цель:", self.goal_spin)
        form.addRow("Выполнено:", self.goal_bar)

        top = QHBoxLayout()
        top.addWidget(counters, 2)
        top.addWidget(goal, 1)

        self.genre_chart = BarChart("Книги по жанрам")
        self.month_chart = BarChart("Прочитано страниц по месяцам")
        charts = QHBoxLayout()
        charts.addWidget(self.genre_chart)
        charts.addWidget(self.month_chart)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(charts, 1)
        self.refresh()

    @staticmethod
    def _lcd(digits=4):
        lcd = QLCDNumber(digits)
        lcd.setSegmentStyle(QLCDNumber.Flat)
        lcd.setMinimumHeight(48)
        return lcd

    def goal_changed(self, value):
        self.db.set_setting("goal_pages", value)
        self.refresh()

    def set_color(self, color):
        self.genre_chart.set_color(color)
        self.month_chart.set_color(color)

    def refresh(self):
        by_status = self.db.count_by_status()
        year = self.year_spin.value()
        pages = self.db.pages_read_total(year)
        self.lcd_total.display(sum(by_status.values()))
        self.lcd_read.display(by_status["Прочитано"])
        self.lcd_reading.display(by_status["Читаю"])
        self.lcd_pages.display(pages)
        self.goal_bar.setRange(0, self.goal_spin.value())
        self.goal_bar.setValue(min(pages, self.goal_spin.value()))
        self.genre_chart.set_data(self.db.count_by_genre()[:8])
        self.month_chart.set_data(list(zip(MONTHS, self.db.pages_by_month(year))))
