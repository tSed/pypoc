import sys
import os

from collections import namedtuple

from datetime import datetime, timezone
from random import choices

from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPainterPathStroker, QColor
from PyQt6.QtCore import Qt, QRect, QTimer, QPoint, QPointF, QSize


OutlineFormat = namedtuple('OutlineFormat', ('color', 'width'))

OSDFormat = namedtuple('OSDFormat', ('font', 'color', 'outline', 'alignment'))


class OSDWidget(QWidget):
    def __init__(self, text, osd_format, position, size, parent=None):
        super(OSDWidget, self).__init__(parent=parent)

        self._text = text
        self._format = osd_format
        self._pos = position
        self._size = size

    def paintEvent(self, e=None):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        if callable(self._text):
            text = self._text()
        else:
            text = self._text

        osd = QPainterPath()
        self.setGeometry(QRect(self._pos, self._size))
        osd.addText(QPointF(0, 0), self._format.font, text)
        osd.translate(0, self._format.font.pixelSize())

        qp.setRenderHint(QPainter.RenderHints.Antialiasing)

        qp.setPen(self._format.outline.color)
        qp.setBrush(self._format.outline.color)
        stroker = QPainterPathStroker()
        stroker.setWidth(self._format.outline.width)

        qp.drawPath(stroker.createStroke(osd))

        qp.setPen(self._format.color)
        qp.setBrush(self._format.color)
        qp.drawPath(osd)


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
        self.delays = choices(range(5, 15), k=1)
        print(self.delays)
        self.step = 0

        self.setGeometry(QRect(QPoint(0, 0), self.screen().size()))

        self.widgets = {}
        self.widgets['timer'] = TimerWidget(100, self.format_time, parent=self)
        self.widgets['timer'].setGeometry(500, 400, 200, 50)

        font =QFont()
        font.setPixelSize(30)
        self.widgets['osd'] = OSDWidget(self.format_time,
                                        OSDFormat(font,
                                                  Qt.GlobalColor.yellow,
                                                  OutlineFormat(QColor("#202020"), 5),
                                                  None),
                                        QPoint(self.width() - 220, 20),
                                        QSize(200, 40),
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
