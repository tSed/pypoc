import sys
import os

from datetime import datetime, timezone
from random import choices

from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QFont, QImage, QImageReader, QPainter
from PyQt6.QtCore import Qt, QRect, QTimer, QPoint


class ViewerWidget(QWidget):
    def __init__(self, get_image, bg_color=Qt.GlobalColor.black, geometry=None, parent=None):
        super(ViewerWidget, self).__init__(geometry=geometry, parent=parent)

        if not geometry:
            size = parent.size() if parent else self.size()
            geometry = QRect(QPoint(0, 0), size)

        self.get_image = get_image
        self.bg_color = bg_color

        self.setGeometry(geometry)

    def paintEvent(self, e=None):
        self.setGeometry(self.parentWidget().frameGeometry())
        qp = QPainter();
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setPen(self.bg_color)
        qp.setBrush(self.bg_color)
        qp.drawRect(self.geometry())
        image = self.get_image(self.size())

        pos = QPoint((self.width() - image.width()) // 2, (self.height() - image.height()) // 2)
        qp.drawImage(QRect(pos, image.size()), image)


class Window(QWidget):

    IMAGE_FORMATS = ('bmp', 'gif', 'jpg', 'jpeg', 'png', 'pbm', 'pgm', 'ppm', 'xbm', 'xpm')

    DELAY = 3000 # 3s
    COUNT = 10

    def __init__(self, image_dir, geometry=None, parent=None):
        super(Window, self).__init__(geometry=geometry, parent=parent)
        self.init_UI(image_dir, parent)

    def init_UI(self, image_dir, parent=None):

        images = []
        for r, _, fs in os.walk(image_dir):
            images.extend([os.path.join(r, f) for f in fs
                           if f.rsplit('.', 1)[-1].lower() in self.IMAGE_FORMATS])
        self.images = choices(images, k=self.COUNT)
        self.image = None
        self.image_path = None

        for p in self.images:
            print(p)

        geometry = self.frameGeometry()
        self.setGeometry(geometry)

        self.widgets = {}
        self.widgets['view'] = ViewerWidget(self.get_image, geometry=geometry, parent=self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start)

        layout = QVBoxLayout()
        layout.addWidget(self.widgets['view'])
        self.setLayout(layout)

        self.step = -1
        self.start()

    def get_image(self, size):
        path = self.images[self.step]
        if self.image_path != path:
            self.image_path = path
            reader = QImageReader(path)
            reader.setScaledSize(reader.size().scaled(size, Qt.AspectRatioMode.KeepAspectRatio))
            self.image = reader.read()

        return self.image


    def start(self):
        self.step += 1
        if self.step >= len(self.images):
            sys.exit()

        self.timer.start(self.DELAY)
        self.repaint()


def main():
    app = QApplication([])
    w = QMainWindow()
    w.setWindowFlags(Qt.WindowFlags.WindowStaysOnTopHint |
                     Qt.WindowFlags.CustomizeWindowHint |
                     Qt.WindowFlags.MaximizeUsingFullscreenGeometryHint |
                     Qt.WindowFlags.FramelessWindowHint)
    geometry = QRect(QPoint(0, 0), w.screen().size())
    w.setGeometry(geometry)
    w.setCentralWidget(Window(sys.argv[1], geometry=geometry, parent=w))
    w.showFullScreen()
    w.setWindowTitle(os.path.basename(__file__))
    app.exec()


if __name__ == '__main__':
    main()
