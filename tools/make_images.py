"""Генерирует картинки проекта (логотип, заставку, заглушку обложки, иконки).

Запуск:  python tools/make_images.py
Готовые картинки уже лежат в папке images/, скрипт нужен только для их пересоздания.
"""
import os
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QGuiApplication, QImage,
                         QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "images")
ICONS = os.path.join(IMAGES, "icons")

ACCENT = QColor("#3f6fb5")
WARM = QColor("#e0893a")
DARK = QColor("#2b2d42")


def canvas(w, h):
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    return img, p


def draw_book(p, rect, color):
    """Закрытая книга: обложка + страницы."""
    x, y, w, h = rect
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#f4efe2"))
    p.drawRoundedRect(QRectF(x + w * 0.08, y + h * 0.04, w * 0.9, h * 0.94), 4, 4)
    p.setBrush(color)
    p.drawRoundedRect(QRectF(x, y, w * 0.9, h * 0.94), 5, 5)
    p.setBrush(color.darker(130))
    p.drawRect(QRectF(x, y, w * 0.12, h * 0.94))
    p.setPen(QPen(QColor(255, 255, 255, 180), max(1, w * 0.03)))
    p.drawLine(QPointF(x + w * 0.3, y + h * 0.25), QPointF(x + w * 0.75, y + h * 0.25))
    p.drawLine(QPointF(x + w * 0.3, y + h * 0.35), QPointF(x + w * 0.65, y + h * 0.35))


def logo():
    img, p = canvas(256, 256)
    grad = QLinearGradient(0, 0, 256, 256)
    grad.setColorAt(0, ACCENT.lighter(120))
    grad.setColorAt(1, ACCENT.darker(130))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(8, 8, 240, 240), 48, 48)
    # три книги на полке
    draw_book(p, (40, 70, 52, 130), WARM)
    draw_book(p, (98, 50, 56, 150), QColor("#f2c14e"))
    p.save()
    p.translate(170, 70)
    p.rotate(12)
    draw_book(p, (0, 0, 50, 128), QColor("#7bc67b"))
    p.restore()
    p.setBrush(QColor("#f4efe2"))
    p.drawRoundedRect(QRectF(30, 200, 196, 14), 5, 5)
    p.end()
    img.save(os.path.join(IMAGES, "logo.png"))
    return img


def no_cover():
    img, p = canvas(200, 300)
    grad = QLinearGradient(0, 0, 0, 300)
    grad.setColorAt(0, QColor("#d9dee7"))
    grad.setColorAt(1, QColor("#b8c1d1"))
    p.setPen(QPen(QColor("#8a94a6"), 2))
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(2, 2, 196, 296), 10, 10)
    draw_book(p, (65, 80, 70, 100), QColor("#8a94a6"))
    p.setPen(QColor("#4a5468"))
    p.setFont(QFont("DejaVu Sans", 13, QFont.Weight.Bold))
    p.drawText(QRectF(0, 200, 200, 60), Qt.AlignmentFlag.AlignCenter, "Нет обложки")
    p.end()
    img.save(os.path.join(IMAGES, "no_cover.png"))


def splash(logo_img):
    img, p = canvas(520, 300)
    grad = QLinearGradient(0, 0, 520, 300)
    grad.setColorAt(0, DARK)
    grad.setColorAt(1, ACCENT.darker(150))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(0, 0, 520, 300), 18, 18)
    p.drawImage(QRectF(30, 60, 170, 170), logo_img)
    p.setPen(Qt.GlobalColor.white)
    p.setFont(QFont("DejaVu Sans", 26, QFont.Weight.Bold))
    p.drawText(QRectF(215, 80, 290, 90), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, "Домашняя\nбиблиотека")
    p.setFont(QFont("DejaVu Sans", 12))
    p.setPen(QColor("#cfd6e6"))
    p.drawText(QRectF(215, 185, 290, 60), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
               "Учёт книг, авторов\nи прочитанных страниц")
    p.end()
    img.save(os.path.join(IMAGES, "splash.png"))


# ------------------------------------------------------------------ иконки
def icon(name, draw):
    img, p = canvas(48, 48)
    draw(p)
    p.end()
    img.save(os.path.join(ICONS, name + ".png"))


def circle(p, color):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawEllipse(QRectF(3, 3, 42, 42))


def white_pen(p, width=5):
    pen = QPen(Qt.GlobalColor.white, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)


def ic_add(p):
    circle(p, QColor("#3a9d5d"))
    white_pen(p)
    p.drawLine(24, 13, 24, 35)
    p.drawLine(13, 24, 35, 24)


def ic_edit(p):
    circle(p, ACCENT)
    white_pen(p, 4)
    p.drawLine(15, 33, 31, 17)
    p.setBrush(Qt.GlobalColor.white)
    p.drawPolygon(QPolygonF([QPointF(12, 36), QPointF(14, 29), QPointF(19, 34)]))


def ic_delete(p):
    circle(p, QColor("#cc4b4b"))
    white_pen(p)
    p.drawLine(16, 16, 32, 32)
    p.drawLine(32, 16, 16, 32)


def arrow(p, up):
    white_pen(p, 4)
    p.drawLine(24, 12, 24, 30)
    if up:
        p.drawPolyline(QPolygonF([QPointF(16, 20), QPointF(24, 12), QPointF(32, 20)]))
    else:
        p.drawPolyline(QPolygonF([QPointF(16, 22), QPointF(24, 30), QPointF(32, 22)]))
    p.drawLine(14, 36, 34, 36)


def ic_import(p):
    circle(p, QColor("#2f8f9d"))
    arrow(p, up=False)


def ic_export(p):
    circle(p, QColor("#8e5bb5"))
    arrow(p, up=True)


def ic_report(p):
    p.setPen(QPen(DARK, 2))
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(10, 5, 28, 38), 3, 3)
    p.setPen(QPen(ACCENT, 3))
    for y in (14, 21, 28, 35):
        p.drawLine(15, y, 33 if y != 35 else 26, y)


def ic_read(p):
    path = QPainterPath()
    path.moveTo(24, 14)
    path.cubicTo(18, 9, 9, 9, 4, 12)
    path.lineTo(4, 38)
    path.cubicTo(9, 35, 18, 35, 24, 40)
    path.cubicTo(30, 35, 39, 35, 44, 38)
    path.lineTo(44, 12)
    path.cubicTo(39, 9, 30, 9, 24, 14)
    p.setPen(QPen(DARK, 2))
    p.setBrush(QColor("#f4efe2"))
    p.drawPath(path)
    p.drawLine(24, 14, 24, 40)
    p.setPen(QPen(WARM, 2))
    for y in (19, 25, 31):
        p.drawLine(9, y, 20, y - 1)
        p.drawLine(28, y - 1, 39, y)


def ic_authors(p):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(ACCENT)
    p.drawEllipse(QRectF(16, 6, 16, 16))
    path = QPainterPath()
    path.addRoundedRect(QRectF(8, 25, 32, 20), 10, 10)
    p.drawPath(path)


def ic_genres(p):
    colors = [WARM, QColor("#f2c14e"), QColor("#7bc67b"), ACCENT]
    for i, c in enumerate(colors):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawRoundedRect(QRectF(6 + i * 9, 8 + (i % 2) * 4, 8, 34 - (i % 2) * 4), 2, 2)
    p.setBrush(DARK)
    p.drawRect(QRectF(4, 42, 40, 3))


def ic_stats(p):
    p.setPen(Qt.PenStyle.NoPen)
    for i, (h, c) in enumerate([(14, WARM), (26, QColor("#f2c14e")), (36, ACCENT)]):
        p.setBrush(c)
        p.drawRoundedRect(QRectF(8 + i * 12, 42 - h, 9, h), 2, 2)
    p.setBrush(DARK)
    p.drawRect(QRectF(5, 42, 38, 3))


def ic_about(p):
    circle(p, ACCENT)
    p.setPen(Qt.GlobalColor.white)
    p.setFont(QFont("DejaVu Serif", 24, QFont.Weight.Bold))
    p.drawText(QRectF(3, 3, 42, 42), Qt.AlignmentFlag.AlignCenter, "i")


def ic_exit(p):
    p.setPen(QPen(DARK, 3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolyline(QPolygonF([QPointF(26, 8), QPointF(10, 8), QPointF(10, 40), QPointF(26, 40)]))
    pen = QPen(QColor("#cc4b4b"), 4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(20, 24, 40, 24)
    p.drawPolyline(QPolygonF([QPointF(33, 17), QPointF(40, 24), QPointF(33, 31)]))


def ic_font(p):
    p.setPen(DARK)
    p.setFont(QFont("DejaVu Serif", 28, QFont.Weight.Bold))
    p.drawText(QRectF(0, 0, 48, 48), Qt.AlignmentFlag.AlignCenter, "Aa")


def ic_color(p):
    for i, c in enumerate([QColor("#cc4b4b"), QColor("#3a9d5d"), ACCENT]):
        c.setAlpha(200)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        x, y = [(8, 6), (20, 6), (14, 18)][i]
        p.drawEllipse(QRectF(x, y, 22, 22))


def ic_star(p):
    import math
    pts = []
    for i in range(10):
        r = 20 if i % 2 == 0 else 9
        a = math.pi / 2 + i * math.pi / 5
        pts.append(QPointF(24 + r * math.cos(a), 25 - r * math.sin(a)))
    p.setPen(QPen(WARM.darker(120), 2))
    p.setBrush(QColor("#f2c14e"))
    p.drawPolygon(QPolygonF(pts))


def ic_book(p):
    draw_book(p, (8, 4, 36, 42), ACCENT)


def main():
    os.makedirs(ICONS, exist_ok=True)
    app = QGuiApplication(sys.argv)
    lg = logo()
    no_cover()
    splash(lg)
    for name, func in [("add", ic_add), ("edit", ic_edit), ("delete", ic_delete),
                       ("import", ic_import), ("export", ic_export), ("report", ic_report),
                       ("read", ic_read), ("authors", ic_authors), ("genres", ic_genres),
                       ("stats", ic_stats), ("about", ic_about), ("exit", ic_exit),
                       ("font", ic_font), ("color", ic_color), ("star", ic_star),
                       ("book", ic_book)]:
        icon(name, func)
    # иконка для exe
    lg.scaled(256, 256).save(os.path.join(IMAGES, "app.ico"))
    print("Картинки сохранены в", IMAGES)
    del app


if __name__ == "__main__":
    main()
