from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint, QBasicTimer
import sys
import math

FIELD_SIZE = 1000
TILE_SIZE = 10
BORDER_SIZE = 0


class Game(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.board = Board(self)
        self.setCentralWidget(self.board)

        # setting up Window
        window_size = FIELD_SIZE + 2 * BORDER_SIZE
        y_offset = (1080 - window_size) / 2
        self.setGeometry(300, y_offset, window_size, window_size)
        self.setWindowTitle('RobotGame')
        self.show()


class Board(QWidget):

    TileCount = int(FIELD_SIZE / TILE_SIZE)
    RefreshSpeed = 200

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = [[0] * Board.TileCount
                              for row in range(Board.TileCount)]
        self.robot = None
        self.timer = QBasicTimer()

        self.initBoardState()
        self.timer.start(Board.RefreshSpeed, self)

    def initBoardState(self):

        self.obstacleArray = Board.createExampleArray(Board.TileCount)
        self.robot = BaseRobot.createExampleRobot(Board.TileCount, TILE_SIZE)

    @staticmethod
    def createExampleArray(size: int):

        array = [[0] * size for row in range(size)]

        # setting the sidewalls by setting all the first and last Elements
        # of each row and column to 1
        for x in range(size):
            array[x][0] = 1
            array[x][size - 1] = 1
            array[0][x] = 1
            array[size - 1][x] = 1

        # individual Wall tiles:
        array[28][34] = 1
        array[54][43] = 1
        array[0][49] = 0

        return array

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        self.drawObstacles(qp)
        self.drawRobot(qp)
        qp.end()

    def drawBoard(self, qp):

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

        # painting a wallpiece when there is a 1 in the array
        # TODO make less ugly
        for row in range(Board.TileCount):
            for col in range(Board.TileCount):
                if self.obstacleArray[row][col] == 1:
                    qp.drawRect(row * TILE_SIZE, col *
                                TILE_SIZE, TILE_SIZE, TILE_SIZE)

    # TODO maybe move to BaseRobot class
    def drawRobot(self, qp):

        rb = self.robot

        # setting circle color and transparency
        qp.setBrush(QColor(133, 242, 252, 100))
        # calculating center point of the circle
        center = QPoint(rb.x * TILE_SIZE + 0.5 * TILE_SIZE,
                        rb.y * TILE_SIZE + 0.5 * TILE_SIZE)
        # drawing the circle with the position and radius of the Robot
        qp.drawEllipse(center, rb.radius, rb.radius)

        # calculating the point to draw the line that indicates alpha
        radian = ((rb.alpha - 90) / 180 * math.pi)
        direction = QPoint(math.cos(radian) * rb.radius + QPoint.x(center),
                           math.sin(radian) * rb.radius + QPoint.y(center))
        # setting color of directional line
        qp.setPen(Qt.red)
        qp.drawLine(QPoint.x(center), QPoint.y(center),
                    QPoint.x(direction), QPoint.y(direction))

        # marking center point
        # setting center color
        qp.setBrush(Qt.white)
        # drawing small circle
        qp.drawEllipse(center, 2, 2)

    def timerEvent(self, event):

        # simple movement command
        # TODO should be re-implemented to avoid working
        # directly with the robots coordinates
        if not self.robot.x >= 98:
            self.robot.moveStep('east')
        elif not self.robot.y >= 98:
            self.robot.moveStep('south')

        # update visuals
        self.update()


class BaseRobot():

    def __init__(self, x, y, radius, alpha):

        self.x = x
        self.y = y
        self.radius = radius
        self.alpha = alpha
        # self.position = [x, y]

    def moveStep(self, direction: str):

        if direction == 'north':
            self.y = self.y - 1
            self.alpha = 0

        elif direction == 'south':
            self.y = self.y + 1
            self.alpha = 180

        elif direction == 'east':
            self.x = self.x + 1
            self.alpha = 90

        elif direction == 'west':
            self.x = self.x - 1
            self.alpha = 270

    @staticmethod
    def createExampleRobot(boardSize: int, tileSize: int):

        return BaseRobot(1, 1, tileSize/2, 45)


# TODO
class Hazard():
    pass


class Wall(Hazard):
    pass


class Border(Hazard):
    pass


class Hole(Hazard):
    pass


class Teleporter(Hazard):
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
