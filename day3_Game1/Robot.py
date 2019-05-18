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
        
TestRobot = Robot (10,20, 5, 45)
