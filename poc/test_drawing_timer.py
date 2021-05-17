""" PyQt6 sample program: Drawing timer.

"""

import sys
import os
import signal

from collections import namedtuple

from datetime import datetime, timezone
from random import sample

from PyQt6.QtWidgets import QWidget, QApplication, QStackedLayout, QMainWindow
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPainterPathStroker, QColor
from PyQt6.QtGui import QImageReader
from PyQt6.QtCore import Qt, QRect, QTimer, QPoint, QPointF, QSize

from Xlib.display import Display


OutlineFormat = namedtuple('OutlineFormat', ('color', 'width'))
""" Outline format class

"""

OSDFormat = namedtuple('OSDFormat', ('font', 'color', 'outline', 'alignment'))
"""OSD format class

"""


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

    def setWindowTitle(self, title):
        """ Set window title overload

        :param title: Title string to set

        """
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


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
        if self._format.alignment == Qt.AlignmentFlag.AlignAbsolute:
            translation = self._baseline_pos
        else:
            # No need for handling Qt.AlignmentFlag.AlignCenter since it is the combination
            # of Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter

            # Horizontal alignment
            if self._format.alignment & Qt.AlignmentFlag.AlignHCenter:
                offset_x = (self._size.width() - osd.width()) / 2
            elif self._format.alignment & Qt.AlignmentFlag.AlignLeft:
                offset_x = self._format.outline.width
            elif self._format.alignment & Qt.AlignmentFlag.AlignRight:
                offset_x = self._size.width() - osd.width() - self._format.outline.width
            else:
                offset_x = self._format.outline.width

            # Vertical alignement
            if self._baseline_pos.y() > osd.height():
                baseline_pos = osd.height()
            else:
                baseline_pos = self._baseline_pos.y()

            # OSD text alignment in this widget
            if self._format.alignment & Qt.AlignmentFlag.AlignVCenter:
                offset_y = (self._size.height() - osd.height()) / 2 + baseline_pos
            elif self._format.alignment & Qt.AlignmentFlag.AlignBaseline:
                offset_y = self._size.height() / 2
            elif self._format.alignment & Qt.AlignmentFlag.AlignTop:
                offset_y = baseline_pos + self._format.outline.width
            elif self._format.alignment & Qt.AlignmentFlag.AlignBottom:
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

        qpainter.setRenderHint(QPainter.RenderHint.Antialiasing)

        qpainter.setPen(self._format.outline.color)
        qpainter.setBrush(self._format.outline.color)
        stroker = QPainterPathStroker()
        stroker.setWidth(self._format.outline.width)

        qpainter.drawPath(stroker.createStroke(osd))

        qpainter.setPen(self._format.color)
        qpainter.setBrush(self._format.color)
        qpainter.drawPath(osd)

    # pylint: disable=invalid-name
    def setWindowTitle(self, title):
        """ Set window title overload

        :param title: Title string to set

        """
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


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

    # pylint: disable=invalid-name
    def setWindowTitle(self, title):
        """ Set window title overload

        :param title: Title string to set

        """
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


def choices_unique(population, k=1):
    """ Random choice of k elements for the given population.

    :param population: List of elements in which the samples will be picked up
    :param k:          The length of the output list

    """
    pop = []
    step = len(population)
    # pylint: disable=invalid-name
    for sample_length in range(0, k, step):
        pop.extend(sample(population, k - sample_length if k - sample_length < step else step))
    return pop


class Window(QWidget):
    """ Main window widget

    """

    IMAGE_FORMATS = ('bmp', 'gif', 'jpg', 'jpeg', 'png', 'pbm', 'pgm', 'ppm', 'xbm', 'xpm')

    DELAY = 3   # 3s
    COUNT = 10

    def __init__(self, image_dir, parent=None):
        super().__init__(parent=parent)
        self.image = None
        self.image_path = None
        self.init_data(image_dir)
        self.init_ui()

    def init_data(self, image_dir):
        """ Initialize internal data

        :param image_dir: Path of the root image directory to be displayed

        """
        images = []
        for root, _, files in os.walk(image_dir):
            images.extend([os.path.join(root, fname) for fname in files
                           if fname.rsplit('.', 1)[-1].lower() in self.IMAGE_FORMATS])
        self.images = choices_unique(images, k=self.COUNT)
        self.image = None
        self.image_path = None

        self.delays = [self.DELAY * 1000 for _ in self.images]
        self.step = 0

    def get_image(self, size):
        """ Return the QImage object, scaled to the given size keeping the original
        image ratio.

        :param size: The widget size

        """
        path = self.images[self.step-1]
        if self.image_path != path:
            self.image_path = path
            reader = QImageReader(path)
            reader.setScaledSize(reader.size().scaled(size, Qt.AspectRatioMode.KeepAspectRatio))
            self.image = reader.read()

        return self.image

    def init_ui(self):
        """ Initialize the UI

        """
        geometry = QRect(QPoint(0,0), self.screen().size())

        self.setGeometry(geometry)

        self.widgets = {}
        timer_widget = TimerWidget(100, parent=self)
        timer_widget.setGeometry(500, 400, 200, 50)

        font = QFont('Lucida Console')
        font.setPixelSize(30)
        #font.setPointSize(24)
        font.setStyleHint(font.StyleHint.Monospace)
        osd_widget = OSDWidget(self.format_time,
                               OSDFormat(font,
                                         Qt.GlobalColor.yellow,
                                         OutlineFormat(QColor("#303030"), 5),
                                         0
                                         #| Qt.AlignmentFlag.AlignAbsolute
                                         #| Qt.AlignmentFlag.AlignCenter
                                         | Qt.AlignmentFlag.AlignHCenter
                                         #| Qt.AlignmentFlag.AlignLeft
                                         #| Qt.AlignmentFlag.AlignRight
                                         #| Qt.AlignmentFlag.AlignVCenter
                                         #| Qt.AlignmentFlag.AlignBaseline
                                         | Qt.AlignmentFlag.AlignTop
                                         #| Qt.AlignmentFlag.AlignBottom
                                        ),
                               QPoint(geometry.width() - 220, 20),
                               QSize(200, 80),
                               True,
                               self)

        view_widget = ViewerWidget(self.get_image, geometry=geometry, parent=self)

        self.widgets['osd'] = osd_widget
        self.widgets['timer'] = timer_widget
        self.widgets['view'] = view_widget

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start)

        layout = QStackedLayout()
        layout.setStackingMode(layout.StackingMode.StackAll)
        layout.addWidget(self.widgets['osd'])
        layout.addWidget(self.widgets['view'])
        layout.addWidget(self.widgets['timer'])
        self.setLayout(layout)

        for widget in self.widgets.values():
            widget.setFocusProxy(self)

        self.setFocus()

        self.start()

    def format_time(self):
        """ Return the time string from the given time.

        :param ts: Time to be formated

        """
        if self.timer.isActive():
            time = self.timer.remainingTime()
            time = datetime.fromtimestamp(time / 1000, tz=timezone.utc).time()
            text = time.strftime("%H:%M:%S.%f")[:-5]
        else:
            text = '--:--:--.-'
        return text

    def start(self):
        """ Start the image timer

        """
        if self.step >= len(self.delays):
            QApplication.instance().quit()
            return

        self.timer.start(self.delays[self.step])
        self.widgets['timer'].start()

        title = f"{self.step+1:{len(str(self.COUNT))}d}/{len(self.delays)}"
        title += f" - {os.path.basename(self.images[self.step])}"
        print(title)
        self.setWindowTitle(title)

        self.step += 1

    def pause_resume(self):
        """ Pause/resume the image timer

        """
        if self.timer.isActive():
            self.delays[self.step - 1] = self.timer.remainingTime()
            self.timer.stop()
        else:
            self.timer.start(self.delays[self.step - 1])

    # pylint: disable=invalid-name
    def setWindowTitle(self, title):
        """ Set window title overload

        :param title: Title string to set

        """
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)

    # pylint: disable=invalid-name
    def keyPressEvent(self, event):
        """ key press event handler overload

        :param event: Key event

        """
        key = Qt.Key(event.key())
        if key == Qt.Key.Key_Q:
            QApplication.instance().quit()
        elif key in (Qt.Key.Key_N, Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.start()
        elif key == Qt.Key.Key_Space:
            self.pause_resume()
        else:
            event.ignore()


class ScreenSaver:
    """ Screensaver class

    """
    def __init__(self, enable=False, timeout=600):
        self.display = Display()
        self.defaults = self.get_current_config()
        self.config = self.defaults.copy()

        if enable and not timeout:
            raise ValueError(f'Invalid timeout value: {timeout}')

        self.config['timeout'] = timeout if enable else 0

    @staticmethod
    def _fix_xlib_config(config):
        """ Fix Xlib screensaver config to match the set-format

        :param config: The config to fix

        """
        config.pop('sequence_number', None)
        if 'prefer_blanking' in config:
            config['prefer_blank'] = config.pop('prefer_blanking')

    def get_current_config(self):
        """ Read and return the current Xlib screensaver config

        """
        # pylint: disable=protected-access
        cfg = self.display.get_screen_saver()._data
        self._fix_xlib_config(cfg)
        return cfg

    def set_config(self, config):
        """ Set the given screensaver config into the Xlib screensaver.

        :param config: Xlib screensaver config

        """
        cfg = config.copy()
        self._fix_xlib_config(cfg)
        self.display.set_screen_saver(**cfg)
        # pylint: disable=protected-access
        assert self.display.get_screen_saver()._data['timeout'] == cfg['timeout']

    def apply(self):
        """ Apply the instance screensaver config
        """
        self.set_config(self.config)

    def restore(self):
        """ Restore the original screensaver config
        """
        self.set_config(self.defaults)


def __main__():
    app = QApplication([])

    screensaver = ScreenSaver(enable=False)
    screensaver.apply()

    signal.signal(signal.SIGTERM, lambda signum, frame: app.quit())
    signal.signal(signal.SIGINT, lambda signum, frame: app.quit())
    # Cannot register signal handler on SIGKILL
    #signal.signal(signal.SIGKILL, lambda signum, frame: app.quit())

    app.aboutToQuit.connect(screensaver.restore)

    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                          Qt.WindowType.CustomizeWindowHint |
                          Qt.WindowType.MaximizeUsingFullscreenGeometryHint |
                          Qt.WindowType.FramelessWindowHint)
    window.setGeometry(QRect(QPoint(0, 0), window.screen().size()))
    window.setCentralWidget(Window(sys.argv[1], parent=window))
    window.showFullScreen()

    return app.exec()


if __name__ == '__main__':
    sys.exit(__main__())
