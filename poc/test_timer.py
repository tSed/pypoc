import sys
import os

from datetime import datetime, timezone
from random import choices

from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QRect, QTimer, QPoint


class TimerWidget(QWidget):
    def __init__(self, interval, format_func, parent=None):
        super(TimerWidget, self).__init__(parent=parent)

        size = parent.size() if parent else self.size()
        self.setGeometry(0, 0, size.width(), size.height())

        self.label = QLabel("", parent=self)
        self.label.setFont(QFont('Times', 15))
        self.label.setAlignment(Qt.Alignment.AlignCenter)
        self.label.setGeometry(0, 0, self.size().width(), self.size().height())

        self.format = format_func
        self.interval = interval

        self.master = None

        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.showTime)

    def start(self, master):
        self.master = master
        self.timer.start(self.interval)

    def stop(self):
        self.master = None
        self.timer.stop()
        self.showTime()

    def showTime(self):
        self.draw()

    def paintEvent(self, e=None):
        self.draw()

    def draw(self):
        if self.master:
            ts = self.master.remainingTime()
            text = self.format(ts)
        else:
            text = "..."
        self.label.setText(text)


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent=parent)
        self.init_UI(parent)

    @staticmethod
    def format_time(ts):
        text = datetime.fromtimestamp(ts/1000, tz=timezone.utc).time().strftime("%H:%M:%S.%f")[:-5]
        return text

    def init_UI(self, parent=None):
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
        if self.step >= len(self.delays):
            sys.exit()

        self.timer.start(self.delays[self.step] * 1000)
        if self.step % 2 == 0:
            self.widgets['timer'].start(self.timer)
        else:
            self.widgets['timer'].stop()

        self.step += 1


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
