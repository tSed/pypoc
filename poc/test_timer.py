""" PyQt6 sample program: Timer.

"""

import sys
import os

from datetime import datetime, timezone
from random import choices

from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QRect, QTimer, QPoint


class TimerWidget(QWidget):
    """ Timer widget

    """
    def __init__(self, interval, format_func, parent=None):
        super().__init__(parent=parent)

        size = parent.size() if parent else self.size()
        self.setGeometry(0, 0, size.width(), size.height())

        self.label = QLabel("", parent=self)
        self.label.setFont(QFont('Times', 15))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(0, 0, self.size().width(), self.size().height())

        self.format = format_func
        self.interval = interval

        self.master = None

        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.showTime)

    def start(self, master):
        """ Start the timer

        :param master: The master timer, which remaining time will be displayed

        """
        self.master = master
        self.timer.start(self.interval)

    def stop(self):
        """ Stop the timer

        """
        self.master = None
        self.timer.stop()
        self.showTime()

    # pylint: disable=invalid-name
    def showTime(self):
        """ Show time event handler overload

        """
        self.draw()

    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
    def paintEvent(self, event=None):
        """ Paint event handler overload

        :param event: The event

        """
        self.draw()

    def draw(self):
        """ Display the timer

        """
        if self.master:
            ts = self.master.remainingTime()
            text = self.format(ts)
        else:
            text = "..."
        self.label.setText(text)


class Window(QWidget):
    """ Main window widget

    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()

    @staticmethod
    def format_time(timestamp):
        """ Return the time string from the given time.

        :param ts: Time to be formated

        """
        date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        text = date.time().strftime("%H:%M:%S.%f")[:-5]
        return text

    def init_ui(self):
        """ Initialize the UI

        :param image_dir: Path of the root image directory to be displayed

        """
        self.delays = choices(range(5, 30), k=5)
        print(self.delays)
        self.step = 0

        self.setGeometry(QRect(QPoint(0, 0), self.screen().size()))

        self.widgets = {}
        self.widgets['timer'] = TimerWidget(100, self.format_time, parent=self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start)

        layout = QVBoxLayout()
        layout.addWidget(self.widgets['timer'])
        self.setLayout(layout)

        self.start()

    def start(self):
        """ Start the image timer

        """
        if self.step >= len(self.delays):
            sys.exit()

        self.timer.start(self.delays[self.step] * 1000)
        if self.step % 2 == 0:
            self.widgets['timer'].start(self.timer)
        else:
            self.widgets['timer'].stop()

        self.step += 1


def __main__():
    app = QApplication([])
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                          Qt.WindowType.CustomizeWindowHint |
                          Qt.WindowType.MaximizeUsingFullscreenGeometryHint |
                          Qt.WindowType.FramelessWindowHint)
    window.setGeometry(QRect(QPoint(0, 0), window.screen().size()))
    window.setCentralWidget(Window(parent=window))
    window.showFullScreen()
    window.setWindowTitle(os.path.basename(__file__))
    app.exec()


if __name__ == '__main__':
    __main__()
