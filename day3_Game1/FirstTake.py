from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint
import sys
import math
import Robot

FIELD_SIZE = 1000
TILE_SIZE = 10


class PlayingField(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def setupArray(self, arraysize):
        obstacleArray = [[0 for col in range(arraysize)] for row in range(arraysize)]

        # setting the sidewalls by setting all the first and last Elements of each row and column to 1
        for x in range(arraysize):
            obstacleArray[x][0] = 1
            obstacleArray[x][arraysize - 1] = 1
            obstacleArray[0][x] = 1
            obstacleArray[arraysize - 1][x] = 1

        # individual Wall tiles:
        obstacleArray[28][34] = 1
        obstacleArray[54][43] = 1
        obstacleArray[0][49] = 0

        return obstacleArray

    def initUI(self):
        # setting up Window
        self.setGeometry(0, 0, FIELD_SIZE, FIELD_SIZE)
        self.setWindowTitle('Game')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawGrid(qp)
        self.drawObstacles(qp)
        self.drawRobot(Robot.TestRobot, qp)
        qp.end()

    def drawGrid(self, qp):

        # painting a grid to showcase the tiles
        # using the constants TILE_SIZE and FIELD_SIZE to determine the size
        pen = QPen(Qt.black, .1, Qt.SolidLine)
        qp.setPen(pen)
        # horizontal lines
        for horizontal in range(0, FIELD_SIZE, TILE_SIZE):
            qp.drawLine(0, horizontal, FIELD_SIZE, horizontal)

        # vertical lines
        for vertical in range(0, FIELD_SIZE, TILE_SIZE):
            qp.drawLine(vertical, 0, vertical, FIELD_SIZE)

    def drawObstacles(self, qp):

        # setting Wallcolor
        qp.setBrush(Qt.black)

        # creating the array
        # its size depends on FIELD_SIZE and TILE_SIZE
        arraysize = int(FIELD_SIZE / TILE_SIZE)
        obstacleArray = self.setupArray(arraysize)

        # painting a wallpiece when there is a 1 in the array
        for row in range(arraysize):
            for col in range(arraysize):
                if obstacleArray[row][col] == 1:
                    qp.drawRect(row * TILE_SIZE, col * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def drawRobot(self, Robot, qp):

        # setting circle color and transparency
        qp.setBrush(QColor(133, 242, 252, 100))
        # calculating center point of the circle
        center = QPoint(Robot.x * TILE_SIZE, Robot.y * TILE_SIZE)
        # drawing the circle with the position and radius of the Robot
        qp.drawEllipse(center, Robot.radius, Robot.radius)

        # calculating the point to draw the line that indicates alpha
        radian = ((Robot.alpha - 90) / 180 * math.pi)
        direction = QPoint(math.cos(radian) * Robot.radius + QPoint.x(center), math.sin(radian) * Robot.radius + QPoint.y(center))
        # setting color of directional line
        qp.setPen(Qt.red)
        qp.drawLine(QPoint.x(center), QPoint.y(center), QPoint.x(direction),QPoint.y(direction))

        # marking center point
        # setting center color
        qp.setBrush(Qt.white)
        # drawing small circle
        qp.drawEllipse(center, 2, 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PlayingField()
    sys.exit(app.exec_())
