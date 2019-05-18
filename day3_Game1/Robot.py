from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt
import sys


class Robot:

    def __init__(self, x, y, radius, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.alpha = alpha
        self.position = [x, y]

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawRobot(qp)
        qp.end()

    def drawRobot(self, qp):
        qp.setBrush(Qt.magenta)
        qp.drawRect(self.position[0] * TILE_SIZE, self.position[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)


