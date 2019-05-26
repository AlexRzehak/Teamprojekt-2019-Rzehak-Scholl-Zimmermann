from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QRunnable, QObject
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint, QBasicTimer, QThreadPool, pyqtSignal, pyqtSlot
import sys
import math
import threading
import time

FIELD_SIZE = 1000
TILE_SIZE = 10


class Game(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.board = Board(self)
        self.setCentralWidget(self.board)

        # setting up Window
        y_offset = (1080 - FIELD_SIZE) / 2
        self.setGeometry(300, y_offset, FIELD_SIZE, FIELD_SIZE)
        self.setWindowTitle('RobotGame')
        self.show()


class Board(QWidget):

    TileCount = int(FIELD_SIZE / TILE_SIZE)
    RefreshSpeed = 33

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = [[0] * Board.TileCount
                              for row in range(Board.TileCount)]
        self.robots = []
        self.timer = QBasicTimer()

        self.initObstacles()
        self.initRobots()
        self.timer.start(Board.RefreshSpeed, self)

    def initObstacles(self):

        self.obstacleArray = Board.createExampleArray(Board.TileCount)

    def initRobots(self):
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" %
              self.threadpool.maxThreadCount())

        robo1 = BaseRobot(TILE_SIZE/2, Movement.straight, 100000, 100000)
        robo1.placeRobot(0, 300, 90)
        robo1.signals.finished.connect(self.robot_finished)
        self.robots.append(robo1)

    def robot_finished(self):
        print('Calculations finished.')

    @staticmethod
    def createExampleArray(size: int):

        array = [[0] * size for row in range(size)]

        # setting the sidewalls by setting all the first and last Elements
        # of each row and column to 1
        for x in range(size):
            array[x][0] = 2
            array[x][size - 1] = 2
            array[0][x] = 2
            array[size - 1][x] = 2

        # individual Wall tiles:
        array[28][34] = 1
        array[54][43] = 1
        array[5][49] = 3
        array[0][30] = 0
        array[99][30] = 0

        return array

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        self.drawObstacles(qp)
        for robot in self.robots:
            self.drawRobot(qp, robot)
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

        for xpos in range(Board.TileCount):
            for ypos in range(Board.TileCount):

                tileVal = self.obstacleArray[xpos][ypos]

                if tileVal == Hazard.Wall:
                    brush = QBrush(Qt.Dense2Pattern)
                    brush.setColor(Qt.red)
                    qp.setBrush(brush)
                    qp.drawRect(xpos * TILE_SIZE,
                                ypos * TILE_SIZE,
                                TILE_SIZE, TILE_SIZE)

                elif tileVal == Hazard.Border:
                    brush = QBrush(Qt.Dense2Pattern)
                    brush.setColor(Qt.blue)
                    qp.setBrush(brush)
                    qp.drawRect(xpos * TILE_SIZE,
                                ypos * TILE_SIZE,
                                TILE_SIZE, TILE_SIZE)

                elif tileVal == Hazard.Hole:
                    qp.setBrush(Qt.black)
                    center = QPoint(xpos * TILE_SIZE + 0.5 * TILE_SIZE,
                                    ypos * TILE_SIZE + 0.5 * TILE_SIZE)
                    qp.drawEllipse(center, 0.5 * TILE_SIZE, 0.25 * TILE_SIZE)

    def drawRobot(self, qp, rb):

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

    # TODO
    def calculate_robot(self, robot):
        pass

    def timerEvent(self, event):

        for robot in self.robots:
            # create proper connection:
            # thread should wait until server sends data, then start calc
            self.calculate_robot(robot)
            self.threadpool.start(robot)

        # update visuals
        self.update()


class Hazard():
    """ A namespace for the different types of tiles on the board.
    Might contain additional functionality later.
    """
    Empty = 0
    Wall = 1
    Border = 2
    Hole = 3


class RobotSignals(QObject):

    # TODO Something
    finished = pyqtSignal()


class Movement():

    @staticmethod
    def straight(robot):
        if robot.x < FIELD_SIZE/2:
            return (10, 0)
        else:
            return (-10, 0)


class BaseRobot(QRunnable):

    def __init__(self, radius, movement_funct, a_max, a_alpha_max):
        super().__init__()

        # set parameters
        self.radius = radius

        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

        # current position
        self.x = 0
        self.y = 0
        self.alpha = 0

        self.v = 0
        self.v_alpha = 0

        # calculated by the robot
        self.a = 0
        self.a_alpha = 0

        # # the current command executed by the robot
        # self.command = ('stay', 0)
        self.signals = RobotSignals()

        # Movement function to apply on current position and speed.
        self.movement_funct = movement_funct

    @pyqtSlot()
    def run(self):
        a, a_alpha = self.movement_funct(self)
        self.a = a
        self.a_alpha = a_alpha

        # here is no exception handling
        self.signals.finished.emit()

    def placeRobot(self, x, y, alpha):
        self.x = x
        self.y = y
        self.alpha = alpha


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
