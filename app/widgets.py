"""Вспомогательные (дополнительные) виджеты."""
import os

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget

from .paths import COVERS_DIR, image


def cover_pixmap(cover, width=150, height=225):
    """Картинка обложки книги или заглушка «Нет обложки»."""
    path = ""
    if cover:
        path = cover if os.path.isabs(cover) else os.path.join(COVERS_DIR, cover)
    pix = QPixmap(path) if path and os.path.exists(path) else QPixmap()
    if pix.isNull():
        pix = QPixmap(image("no_cover.png"))
    return pix.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


class CoverLabel(QLabel):
    """QLabel, показывающий обложку книги."""

    def __init__(self, width=150, height=225, parent=None):
        super().__init__(parent)
        self.w, self.h = width, height
        self.setFixedSize(width + 4, height + 4)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_cover("")

    def set_cover(self, cover):
        self.setPixmap(cover_pixmap(cover, self.w, self.h))


class StarRating(QWidget):
    """Виджет «звёзды» для отображения оценки (рисуется через QPainter)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setMinimumSize(130, 26)

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont(self.font().family(), 16))
        for i in range(5):
            p.setPen(QColor("#f2a900") if i < self.value else QColor("#c8c8c8"))
            p.drawText(QRectF(i * 26, 0, 26, 26), Qt.AlignmentFlag.AlignCenter, "★")


class BarChart(QWidget):
    """Простая столбчатая диаграмма, нарисованная средствами QPainter."""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.items = []
        self.color = QColor("#3f6fb5")
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, items):
        """items — список пар (подпись, значение)."""
        self.items = list(items)
        self.update()

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), self.palette().base())
        p.setPen(self.palette().text().color())
        bold = QFont(self.font())
        bold.setBold(True)
        p.setFont(bold)
        p.drawText(QRectF(0, 4, w, 20), Qt.AlignmentFlag.AlignCenter, self.title)
        p.setFont(self.font())
        if not self.items or max(v for _, v in self.items) == 0:
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных")
            return
        top, bottom, left = 46, 40, 10
        area_h = h - top - bottom
        maximum = max(v for _, v in self.items)
        step = (w - 2 * left) / len(self.items)
        bar_w = step * 0.65
        small = QFont(self.font())
        small.setPointSize(max(7, small.pointSize() - 2))
        for i, (label, value) in enumerate(self.items):
            bar_h = area_h * value / maximum
            x = left + i * step + (step - bar_w) / 2
            y = top + area_h - bar_h
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.color.lighter(100 + (i % 3) * 15))
            p.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 3, 3)
            p.setPen(self.palette().text().color())
            p.setFont(small)
            p.drawText(QRectF(x - 10, y - 16, bar_w + 20, 16), Qt.AlignmentFlag.AlignCenter, str(value))
            text = p.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, int(step) - 2)
            p.drawText(QRectF(left + i * step, h - bottom + 4, step, bottom - 4),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
