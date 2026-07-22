from abc import ABC, abstractmethod
from pathlib import Path
import subprocess
import sys
from typing import override

from PySide6 import QtCore  # noqa: F401
from PySide6.QtGui import QFont, QFontMetricsF, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QTextEdit  # noqa: F401

class Instance(ABC):
    rows: int
    cols: int

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def set(self, data):
        pass

    @abstractmethod
    def exec(self) -> int:
        pass
    
class PySideInstance(Instance):
    app: QApplication
    window: QMainWindow
    view: QLabel

    @override
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet('''* {
                        background-color: black;
                        color: white;
        }''')
        
        # font
        font = QFont("Monospace", 8)

        # screen size (logical px)
        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        w_px, h_px = geo.width(), geo.height()

        # per-character cell size from the actual font
        fm = QFontMetricsF(font)
        char_w = fm.horizontalAdvance("M")
        line_h = fm.lineSpacing()

        # grid dimensions
        self.cols = int(w_px // char_w)
        self.rows = int(h_px // line_h)

        # image
        self.image = QImage()

        self.view = QLabel()
        self.view.setPixmap(QPixmap.fromImage(self.image))
        self.view.setScaledContents(True)
        self.view.setContentsMargins(0, 0, 0, 0)

        # window
        self.window = QMainWindow()
        self.window.setCentralWidget(self.view)
        self.window.resize(QApplication.primaryScreen().size())
        self.window.setWindowTitle("ascii-bg")
        QApplication.setDesktopFileName("ascii-bg")
    
    def set(self, data: Path):
        self.image.load(str(data))
        self.view.setPixmap(QPixmap.fromImage(self.image))
    
    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()
    
    @override
    def exec(self):
        self.show()
        return self.app.exec()

class SwayInstance(Instance):

    path: Path | None

    @override
    def __init__(self):
        self.path = None

        self.app = QApplication(sys.argv)
        font = QFont("Monospace", 8)
        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        w_px, h_px = geo.width(), geo.height()

        fm = QFontMetricsF(font)
        char_w = fm.horizontalAdvance("M")
        line_h = fm.lineSpacing()

        self.cols = int(w_px // char_w)
        self.rows = int(h_px // line_h)

    @override
    def set(self, data: Path):
        self.path = data

    @override
    def exec(self) -> int:
        if self.path is None:
            return 1
        proc = subprocess.Popen(
            ["swaybg", "-i", str(self.path), "-m", "fill"]
        )
        return proc.returncode