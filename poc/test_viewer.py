""" PyQt6 sample program: Image viewer.

"""

import sys
import os

from random import choices

from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QImageReader, QPainter
from PyQt6.QtCore import Qt, QRect, QTimer, QPoint


class ViewerWidget(QWidget):
    """ Image viewer widget

    """
    def __init__(self, get_image, bg_color=Qt.GlobalColor.black, geometry=None, parent=None):
        super().__init__(geometry=geometry, parent=parent)

        if not geometry:
            size = parent.size() if parent else self.size()
            geometry = QRect(QPoint(0, 0), size)

        self.get_image = get_image
        self.bg_color = bg_color

        self.setGeometry(geometry)

    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
    def paintEvent(self, event=None):
        """ Paint event handler overload

        """
        self.setGeometry(self.parentWidget().frameGeometry())
        qpainter = QPainter()
        qpainter.begin(self)
        self.draw(qpainter)
        qpainter.end()

    def draw(self, qpainter):
        """ Draw the viewer widget

        :param qpainter: QPainter instance
        """
        qpainter.setPen(self.bg_color)
        qpainter.setBrush(self.bg_color)
        qpainter.drawRect(self.geometry())
        image = self.get_image(self.size())

        pos = QPoint((self.width() - image.width()) // 2, (self.height() - image.height()) // 2)
        qpainter.drawImage(QRect(pos, image.size()), image)


class Window(QWidget):
    """ Main window widget

    """

    IMAGE_FORMATS = ('bmp', 'gif', 'jpg', 'jpeg', 'png', 'pbm', 'pgm', 'ppm', 'xbm', 'xpm')
    """ Supported image formats

    """

    DELAY = 3000 # 3s
    COUNT = 10

    def __init__(self, image_dir, geometry=None, parent=None):
        super().__init__(geometry=geometry, parent=parent)
        self.image = None
        self.image_path = None
        self.init_ui(image_dir)

    def init_ui(self, image_dir):
        """ Initialize the UI

        :param image_dir: Path of the root image directory to be displayed

        """
        images = []
        for root, _, files in os.walk(image_dir):
            images.extend([os.path.join(root, fname) for fname in files
                           if fname.rsplit('.', 1)[-1].lower() in self.IMAGE_FORMATS])
        self.images = choices(images, k=self.COUNT)
        self.image = None
        self.image_path = None

        for path in self.images:
            print(path)

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
        """ Return the image object to be displayed in the give size window

        Original aspect of the image is kept, but image is scale to fill the most the window size.

        :param size: The window size

        :return: The QImage object
        """
        path = self.images[self.step]
        if self.image_path != path:
            self.image_path = path
            reader = QImageReader(path)
            reader.setScaledSize(reader.size().scaled(size, Qt.AspectRatioMode.KeepAspectRatio))
            self.image = reader.read()

        return self.image


    def start(self):
        """ Start the image timer

        """
        self.step += 1
        if self.step >= len(self.images):
            sys.exit()

        self.timer.start(self.DELAY)
        self.repaint()


def __main__():
    app = QApplication([])
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                          Qt.WindowType.CustomizeWindowHint |
                          Qt.WindowType.MaximizeUsingFullscreenGeometryHint |
                          Qt.WindowType.FramelessWindowHint)
    geometry = QRect(QPoint(0, 0), window.screen().size())
    window.setGeometry(geometry)
    window.setCentralWidget(Window(sys.argv[1], geometry=geometry, parent=window))
    window.showFullScreen()
    window.setWindowTitle(os.path.basename(__file__))
    app.exec()


if __name__ == '__main__':
    __main__()
