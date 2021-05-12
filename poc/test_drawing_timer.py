import sys
import os

from collections import namedtuple

from datetime import datetime, timezone
from random import sample

from PyQt6.QtWidgets import QWidget, QApplication, QStackedLayout, QMainWindow
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPainterPathStroker, QColor
from PyQt6.QtGui import QImageReader, QImage
from PyQt6.QtCore import Qt, QRect, QRectF, QTimer, QPoint, QPointF, QSize

from Xlib.display import Display
import signal

OutlineFormat = namedtuple('OutlineFormat', ('color', 'width'))

OSDFormat = namedtuple('OSDFormat', ('font', 'color', 'outline', 'alignment'))


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

    def setWindowTitle(self, title):
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


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

        #qp.setBrush(Qt.BrushStyle.NoBrush)
        #qp.setPen(QColor('#ff0000'))
        #qp.drawRect(QRect(0, 0, self.width(), self.height()))

        #qp.setPen(QColor('#00ff00'))
        #qp.drawLine(QPointF(0, translation.y()),
        #            QPointF(self.width(), translation.y()))

        #osd_bounds = osd.boundingRect()
        #qp.setPen(QColor('#00ffff'))
        #qp.drawRect(QRectF(translation.x(),
        #                   translation.y() - osd_bounds.height(),
        #                   osd_bounds.width(),
        #                   osd_bounds.height()))

    def setWindowTitle(self, title):
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


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

    def setWindowTitle(self, title):
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


def choices_unique(population, *args, k=1, **kwargs):
    pop = []
    step = len(population)
    for n in range(0, k, step):
        pop.extend(sample(population, k - n if k - n < step else step))
    return pop


class Window(QWidget):

    IMAGE_FORMATS = ('bmp', 'gif', 'jpg', 'jpeg', 'png', 'pbm', 'pgm', 'ppm', 'xbm', 'xpm')

    DELAY = 3   # 3s
    COUNT = 10

    def __init__(self, image_dir, parent=None):
        super(Window, self).__init__(parent=parent)
        self.init_data(image_dir)
        self.init_ui(parent)

    def init_data(self, image_dir):
        images = []
        for r, _, fs in os.walk(image_dir):
            images.extend([os.path.join(r, f) for f in fs
                           if f.rsplit('.', 1)[-1].lower() in self.IMAGE_FORMATS])
        self.images = choices_unique(images, k=self.COUNT)
        self.image = None
        self.image_path = None

        for p in self.images:
            print(p)

        self.delays = [self.DELAY for _ in self.images]
        print(self.delays)
        self.step = 0

    def get_image(self, size):
        path = self.images[self.step-1]
        if self.image_path != path:
            self.image_path = path
            reader = QImageReader(path)
            reader.setScaledSize(reader.size().scaled(size, Qt.AspectRatioMode.KeepAspectRatio))
            self.image = reader.read()

        return self.image

    def init_ui(self, parent=None):
        geometry = QRect(QPoint(0,0), self.screen().size())

        print(f'frameGeometry:{geometry}')
        self.setGeometry(geometry)

        self.widgets = {}
        timer_widget = TimerWidget(100, self.format_time, parent=self)
        timer_widget.setGeometry(500, 400, 200, 50)

        font = QFont()
        font.setPixelSize(30)
        #font.setPointSize(24)
        osd_widget = OSDWidget(self.format_time,
                               OSDFormat(font,
                                         Qt.GlobalColor.yellow,
                                         OutlineFormat(QColor("#303030"), 5),
                                         0
                                         #| Qt.Alignment.AlignAbsolute
                                         #| Qt.Alignment.AlignCenter
                                         | Qt.Alignment.AlignHCenter
                                         #| Qt.Alignment.AlignLeft
                                         #| Qt.Alignment.AlignRight
                                         #| Qt.Alignment.AlignVCenter
                                         #| Qt.Alignment.AlignBaseline
                                         | Qt.Alignment.AlignTop
                                         #| Qt.Alignment.AlignBottom
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

        self.start()

    def format_time(self):
        time = self.timer.remainingTime()
        time = datetime.fromtimestamp(time / 1000, tz=timezone.utc).time()
        text = time.strftime("%H:%M:%S.%f")[:-5]
        return text

    def start(self):
        if self.step >= len(self.delays):
            QApplication.instance().quit()
            return

        self.timer.start(self.delays[self.step] * 1000)
        self.widgets['timer'].start()
        #if self.step % 2 == 0:
        #    self.widgets['timer'].start()
        #else:
        #    self.widgets['timer'].stop()

        title = f"{self.step+1:{len(str(self.COUNT))}d}/{len(self.delays)}"
        title += f" - {os.path.basename(self.images[self.step])}"
        print(title)
        self.setWindowTitle(title)

        self.step += 1

    def paintEvent(self, e=None):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        return
        qp.setBrush(Qt.GlobalColor.blue)
        qp.drawRect(self.geometry())

    def setWindowTitle(self, title):
        widget = self.parentWidget()
        if not widget:
            widget = self

        widget.setWindowTitle(title)


class ScreenSaver:
    def __init__(self, enable=False, timeout=600):
        self.display = Display()
        self.defaults = self.fix_xlib_config(self.display.get_screen_saver()._data)
        self.config = self.defaults.copy()

        if enable and not timeout:
            raise ValueError(f'Invalid timeout value: {timeout}')

        self.config['timeout'] = timeout if enable else 0

    @staticmethod
    def fix_xlib_config(config):
        config.pop('sequence_number', None)
        if 'prefer_blanking' in config:
            config['prefer_blank'] = config.pop('prefer_blanking')
        return config

    def set_config(self, config):
        #print(config)
        self.display.set_screen_saver(**config)
        assert self.display.get_screen_saver()._data['timeout'] == config['timeout']

    def apply(self):
        self.set_config(self.config)

    def restore(self):
        self.set_config(self.defaults)


def main():
    app = QApplication([])

    screensaver = ScreenSaver(enable=False)
    screensaver.apply()

    signal.signal(signal.SIGTERM, lambda signum, frame: app.quit())
    signal.signal(signal.SIGINT, lambda signum, frame: app.quit())
    # Cannot register signal handler on SIGKILL
    #signal.signal(signal.SIGKILL, lambda signum, frame: app.quit())

    app.aboutToQuit.connect(screensaver.restore)

    w = QMainWindow()
    w.setWindowFlags(Qt.WindowFlags.WindowStaysOnTopHint |
                     Qt.WindowFlags.CustomizeWindowHint |
                     Qt.WindowFlags.MaximizeUsingFullscreenGeometryHint |
                     Qt.WindowFlags.FramelessWindowHint)
    w.setGeometry(QRect(QPoint(0, 0), w.screen().size()))
    w.setCentralWidget(Window(sys.argv[1], parent=w))
    w.showFullScreen()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
