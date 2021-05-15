""" PyQt6 sample program: OSD.

"""

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
    """ OSD (on-screen-display) widget

    """
    # pylint: disable=too-many-arguments
    def __init__(self, text, osd_format, position, size, fixed_postion=False, parent=None):
        super().__init__(parent=parent)

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

    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
    def paintEvent(self, event=None):
        """ Paint event handler overload

        """
        qpainter = QPainter()
        qpainter.begin(self)
        self.draw(qpainter)
        qpainter.end()

    # pylint: disable=too-many-branches
    def compute_translation(self, osd):
        """ Compute the translation vector of the widget

        :param osd: Bounding rectangle of the OSD text

        :return: The translation vector as a QPointF
        """
        if self._format.alignment == Qt.Alignment.AlignAbsolute:
            translation = self._baseline_pos
        else:
            # No need for handling Qt.Alignment.AlignCenter since it is the combination
            # of Qt.Alignment.AlignVCenter | Qt.Alignment.AlignHCenter

            # Horizontal alignment
            if self._format.alignment & Qt.Alignment.AlignHCenter:
                offset_x = (self._size.width() - osd.width()) / 2
            elif self._format.alignment & Qt.Alignment.AlignLeft:
                offset_x = self._format.outline.width
            elif self._format.alignment & Qt.Alignment.AlignRight:
                offset_x = self._size.width() - osd.width() - self._format.outline.width
            else:
                offset_x = self._format.outline.width

            # Vertical alignement
            if self._baseline_pos.y() > osd.height():
                baseline_pos = osd.height()
            else:
                baseline_pos = self._baseline_pos.y()

            # OSD text alignment in this widget
            if self._format.alignment & Qt.Alignment.AlignVCenter:
                offset_y = (self._size.height() - osd.height()) / 2 + baseline_pos
            elif self._format.alignment & Qt.Alignment.AlignBaseline:
                offset_y = self._size.height() / 2
            elif self._format.alignment & Qt.Alignment.AlignTop:
                offset_y = baseline_pos + self._format.outline.width
            elif self._format.alignment & Qt.Alignment.AlignBottom:
                offset_y = (self._size.height()
                      - (osd.height() - baseline_pos)
                      - self._format.outline.width)
            else:
                offset_y = self._baseline_pos.y()

            translation = QPointF(offset_x, offset_y)

        return translation

    def draw(self, qpainter):
        """ Draw the viewer widget

        :param qpainter: QPainter instance
        """
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

        qpainter.setRenderHint(QPainter.RenderHints.Antialiasing)

        qpainter.setPen(self._format.outline.color)
        qpainter.setBrush(self._format.outline.color)
        stroker = QPainterPathStroker()
        stroker.setWidth(self._format.outline.width)

        qpainter.drawPath(stroker.createStroke(osd))

        qpainter.setPen(self._format.color)
        qpainter.setBrush(self._format.color)
        qpainter.drawPath(osd)

        qpainter.setBrush(Qt.BrushStyle.NoBrush)
        qpainter.setPen(QColor('#ff0000'))
        qpainter.drawRect(QRect(0, 0, self.width(), self.height()))

        qpainter.setPen(QColor('#00ff00'))
        qpainter.drawLine(QPointF(0, translation.y()),
                    QPointF(self.width(), translation.y()))

        osd_bounds = osd.boundingRect()
        qpainter.setPen(QColor('#00ffff'))
        qpainter.drawRect(QRectF(translation.x(),
                           translation.y() - osd_bounds.height(),
                           osd_bounds.width(),
                           osd_bounds.height()))


class TimerWidget(QWidget):
    """ Timer widget

    """
    def __init__(self, interval, parent=None):
        super().__init__(parent=parent)

        self.interval = interval

        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.showTime)

    def start(self):
        """ Start the image timer

        """
        self.timer.start(self.interval)

    def stop(self):
        """ Stop the timer

        """
        self.timer.stop()
        self.showTime()

    # pylint: disable=invalid-name
    def showTime(self):
        """ Show time event handler overload

        """
        self.repaint()


class Window(QWidget):
    """ Main window widget

    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()

    def init_ui(self):
        """ Initialize the UI

        :param image_dir: Path of the root image directory to be displayed

        """
        self.delays = choices(range(1, 5), k=1)
        print(self.delays)
        self.step = 0

        self.setGeometry(QRect(QPoint(0, 0), self.screen().size()))

        self.widgets = {}
        self.widgets['timer'] = TimerWidget(100, parent=self)
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
        """ Return the time string from the given time.

        :param ts: Time to be formated

        """
        time = self.timer.remainingTime()
        time = datetime.fromtimestamp(time / 1000, tz=timezone.utc).time()
        text = time.strftime("%H:%M:%S.%f")[:-5]
        return text

    def start(self):
        """ Start the image timer

        """
        if self.step >= len(self.delays):
            sys.exit()

        self.timer.start(self.delays[self.step] * 1000)
        if self.step % 2 == 0:
            self.widgets['timer'].start()
        else:
            self.widgets['timer'].stop()

        self.step += 1

    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
    def paintEvent(self, event=None):
        """ Paint event handler overload

        :param event: The event

        """
        qpainter = QPainter()
        qpainter.begin(self)
        self.draw(qpainter)
        qpainter.end()

    def draw(self, qpainter):
        """ Display the timer

        :param qpainter: QPainter instance
        """
        qpainter.setBrush(Qt.GlobalColor.blue)
        qpainter.drawRect(self.geometry())


def __main__():
    app = QApplication([])
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowFlags.WindowStaysOnTopHint |
                          Qt.WindowFlags.CustomizeWindowHint |
                          Qt.WindowFlags.MaximizeUsingFullscreenGeometryHint |
                          Qt.WindowFlags.FramelessWindowHint)
    window.setGeometry(QRect(QPoint(0, 0), window.screen().size()))
    window.setCentralWidget(Window(parent=window))
    window.showFullScreen()
    window.setWindowTitle(os.path.basename(__file__))
    app.exec()


if __name__ == '__main__':
    __main__()
