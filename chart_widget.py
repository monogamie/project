"""Столбчатая диаграмма «Книги по жанрам» (рисование на форме, урок QT 3)."""
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

# Отступы диаграммы от краёв виджета (в пикселях)
MARGIN_LEFT = 20
MARGIN_TOP = 50
MARGIN_BOTTOM = 40
# Цвет столбиков
BAR_COLOR = QColor(63, 111, 181)


class ChartWidget(QWidget):
    """Виджет, который сам рисует диаграмму в методе paintEvent."""

    def __init__(self):
        super().__init__()
        # Данные для диаграммы: список пар (подпись, число)
        self.data = []
        self.setMinimumHeight(250)

    def set_data(self, data):
        """Запоминает новые данные и просит Qt перерисовать виджет."""
        self.data = data
        # update() ставит вызов paintEvent в очередь (урок QT 3)
        self.update()

    def paintEvent(self, event):
        # Метод вызывается автоматически при каждой перерисовке
        qp = QPainter()
        qp.begin(self)
        self.draw_chart(qp)
        qp.end()

    def draw_chart(self, qp):
        width = self.width()
        height = self.height()
        qp.drawText(MARGIN_LEFT, 25, "Книги по жанрам")

        if not self.data:
            qp.drawText(MARGIN_LEFT, MARGIN_TOP, "Нет данных")
            return

        # Самое большое значение: этот столбик будет во всю высоту
        max_value = max(count for title, count in self.data)
        # Место под каждый столбик
        step = (width - 2 * MARGIN_LEFT) // len(self.data)
        area_height = height - MARGIN_TOP - MARGIN_BOTTOM

        qp.setBrush(BAR_COLOR)
        for i, (title, count) in enumerate(self.data):
            # Высота столбика пропорциональна значению
            bar_height = area_height * count // max_value
            x = MARGIN_LEFT + i * step
            # Ось Y в Qt направлена вниз, поэтому верх столбика считаем так
            y = height - MARGIN_BOTTOM - bar_height
            qp.drawRect(x + 5, y, step - 10, bar_height)
            # Число над столбиком и подпись под ним
            qp.drawText(x + 5, y - 5, str(count))
            qp.drawText(x + 5, height - MARGIN_BOTTOM + 20, title[:12])
