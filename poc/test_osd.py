import sys
import os

from collections import namedtuple

from datetime import datetime, timezone
from random import choices

from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPainterPathStroker, QColor
from PyQt6.QtCore import Qt, QRect, QRectF, QTimer, QPoint, QPointF, QSize


OutlineFormat = namedtuple('OutlineFormat', ('color', 'width'))

OSDFormat = namedtuple('OSDFormat', ('font', 'color', 'outline', 'alignment'))


class OSDWidget(QWidget):
    def __init__(self, text, osd_format, position, size, fixed_postion=False, parent=None):
        super(OSDWidget, self).__init__(parent=parent)

        self._text = text
        self._format = osd_format
        self._pos = position
        self._size = size
        if fixed_postion:
            self._fixed_pos = None
        else:
            self._fixed_pos = fixed_postion

        font_size = self._format.font.pixelSize()
        if font_size < 0:
            font_size = (self._format.font.pointSize() * 4) / 3
        self._baseline_pos = QPointF(0, font_size)

    def paintEvent(self, e=None):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def compute_translation(self, osd):
        if self._format.alignment == Qt.Alignment.AlignAbsolute:
            translation = self._baseline_pos
        else:
            # No need for handling Qt.Alignment.AlignCenter since it is the combination
            # of Qt.Alignment.AlignVCenter | Qt.Alignment.AlignHCenter

            # Horizontal alignment
            if self._format.alignment & Qt.Alignment.AlignHCenter:
                dx = (self._size.width() - osd.width()) / 2
            elif self._format.alignment & Qt.Alignment.AlignLeft:
                dx = self._format.outline.width
            elif self._format.alignment & Qt.Alignment.AlignRight:
                dx = self._size.width() - osd.width() - self._format.outline.width
            else:
                dx = self._format.outline.width

            # Vertical alignement
            if self._baseline_pos.y() > osd.height():
                baseline_pos = osd.height()
            else:
                baseline_pos = self._baseline_pos.y()

            if self._format.alignment & Qt.Alignment.AlignVCenter:
                dy = (self._size.height() - osd.height()) / 2 + baseline_pos
            elif self._format.alignment & Qt.Alignment.AlignBaseline:
                dy = self._size.height() / 2
            elif self._format.alignment & Qt.Alignment.AlignTop:
                dy = baseline_pos + self._format.outline.width
            elif self._format.alignment & Qt.Alignment.AlignBottom:
                dy = (self._size.height()
                      - (osd.height() - baseline_pos)
                      - self._format.outline.width)
            else:
                dy = self._baseline_pos.y()

            translation = QPointF(dx, dy)

        return translation

    def draw(self, qp):
        if callable(self._text):
            text = self._text()
        else:
            text = self._text

        self.setGeometry(QRect(self._pos, self._size))

        osd = QPainterPath()
        osd.addText(QPointF(0, 0), self._format.font, text)

        if self._fixed_pos:
            translation = self._fixed_pos
        else:
            translation = self.compute_translation(osd.boundingRect())
            if self._fixed_pos is None:
                self._fixed_pos = translation

        osd.translate(translation)

        qp.setRenderHint(QPainter.RenderHints.Antialiasing)

        qp.setPen(self._format.outline.color)
        qp.setBrush(self._format.outline.color)
        stroker = QPainterPathStroker()
        stroker.setWidth(self._format.outline.width)

        qp.drawPath(stroker.createStroke(osd))

        qp.setPen(self._format.color)
        qp.setBrush(self._format.color)
        qp.drawPath(osd)

        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.setPen(QColor('#ff0000'))
        qp.drawRect(QRect(0, 0, self.width(), self.height()))

        qp.setPen(QColor('#00ff00'))
        qp.drawLine(QPointF(0, translation.y()),
                    QPointF(self.width(), translation.y()))

        osd_bounds = osd.boundingRect()
        qp.setPen(QColor('#00ffff'))
        qp.drawRect(QRectF(translation.x(),
                           translation.y() - osd_bounds.height(),
                           osd_bounds.width(),
                           osd_bounds.height()))


class TimerWidget(QWidget):
    def __init__(self, interval, format_func, parent=None):
        super(TimerWidget, self).__init__(parent=parent)

        self.interval = interval

        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.showTime)

    def start(self):
        self.timer.start(self.interval)

    def stop(self):
        self.timer.stop()
        self.showTime()

    def showTime(self):
        self.repaint()


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent=parent)
        self.init_UI(parent)

    def init_UI(self, parent=None):
        self.delays = choices(range(1, 5), k=1)
        print(self.delays)
        self.step = 0

        self.setGeometry(QRect(QPoint(0, 0), self.screen().size()))

        self.widgets = {}
        self.widgets['timer'] = TimerWidget(100, self.format_time, parent=self)
        self.widgets['timer'].setGeometry(500, 400, 200, 50)

        font =QFont()
        font.setPixelSize(30)
        #font.setPointSize(24)
        self.widgets['osd'] = OSDWidget(self.format_time,
                                        OSDFormat(font,
                                                  Qt.GlobalColor.yellow,
                                                  OutlineFormat(QColor("#202020"), 5),
                                                  0
                                                  #| Qt.Alignment.AlignAbsolute
                                                  #| Qt.Alignment.AlignCenter
                                                  #| Qt.Alignment.AlignHCenter
                                                  #| Qt.Alignment.AlignLeft
                                                  | Qt.Alignment.AlignRight
                                                  #| Qt.Alignment.AlignVCenter
                                                  #| Qt.Alignment.AlignBaseline
                                                  #| Qt.Alignment.AlignTop
                                                  | Qt.Alignment.AlignBottom
                                                 ),
                                        QPoint(self.width() - 220, 20),
                                        QSize(200, 80),
                                        True,
                                        self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start)

        layout = QVBoxLayout()
        layout.addWidget(self.widgets['timer'])
        self.setLayout(layout)

        self.start()

    def format_time(self):
        time = self.timer.remainingTime()
        time = datetime.fromtimestamp(time / 1000, tz=timezone.utc).time()
        text = time.strftime("%H:%M:%S.%f")[:-5]
        return text

    def start(self):
        if self.step >= len(self.delays):
            sys.exit()

        self.timer.start(self.delays[self.step] * 1000)
        if self.step % 2 == 0:
            self.widgets['timer'].start()
        else:
            self.widgets['timer'].stop()

        self.step += 1

    def paintEvent(self, e=None):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setBrush(Qt.GlobalColor.blue)
        qp.drawRect(self.geometry())


def main():
    app = QApplication([])
    w = QMainWindow()
    w.setWindowFlags(Qt.WindowFlags.WindowStaysOnTopHint |
                     Qt.WindowFlags.CustomizeWindowHint |
                     Qt.WindowFlags.MaximizeUsingFullscreenGeometryHint |
                     Qt.WindowFlags.FramelessWindowHint)
    w.setGeometry(QRect(QPoint(0, 0), w.screen().size()))
    w.setCentralWidget(Window(parent=w))
    w.showFullScreen()
    w.setWindowTitle(os.path.basename(__file__))
    app.exec()


if __name__ == '__main__':
    main()
