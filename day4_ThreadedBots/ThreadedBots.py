from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint, QBasicTimer
import sys
import math

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
    """Task 1: This class represents the game board."""

    TileCount = int(FIELD_SIZE / TILE_SIZE)
    RefreshSpeed = 150

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = [[0] * Board.TileCount
                              for row in range(Board.TileCount)]
        self.robot = None
        self.timer = QBasicTimer()

        # Recognize input froum mouse and keyboard.
        self.setFocusPolicy(Qt.StrongFocus)

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
        self.drawRobot(qp)
        qp.end()

    def drawBoard(self, qp):
        """"Task 2: Draw the board and its tiles."""

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
        """Task 3: Paint the different hazards given by obstacleArray."""
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

    def drawRobot(self, qp):
        """Task 5: Paint the robot on the board. Mind its direction."""

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
        """Task 6: A timer moving the Robot step by step
         while follwing its current command.
        """

        self.robot.followCommand(self.obstacleArray)

        # update visuals
        self.update()

    def mousePressEvent(self, event):
        mouseX = int((event.x()) / TILE_SIZE)
        mouseY = int((event.y()) / TILE_SIZE)
        dx = self.robot.x - mouseX
        dy = self.robot.y - mouseY

        if abs(dx) > abs(dy):
            if dx > 0:
                self.robot.command = ('west', abs(dx))
            else:
                self.robot.command = ('east', abs(dx))
        else:
            if dy > 0:
                self.robot.command = ('north', abs(dy))
            else:
                self.robot.command = ('south', abs(dy))

    # TODO this should not exist.
    def keyPressEvent(self, event):

        key = event.key()

        if key == Qt.Key_Left:
            self.robot.moveStep('west', self.obstacleArray)

        elif key == Qt.Key_Right:
            self.robot.moveStep('east', self.obstacleArray)

        elif key == Qt.Key_Up:
            self.robot.moveStep('north', self.obstacleArray)

        elif key == Qt.Key_Down:
            self.robot.moveStep('south', self.obstacleArray)

        self.update()


class Hazard():
    """ A namespace for the different types of tiles on the board.
    Might contain additional functionality later.
    """
    Empty = 0
    Wall = 1
    Border = 2
    Hole = 3


class BaseRobot():
    """Task 4: A class representing a robot with positioning parameters.
     We added some control logic.
    """

    def __init__(self, x, y, radius, alpha):

        self.x = x
        self.y = y
        self.radius = radius
        self.alpha = alpha

        # the current command executed by the robot
        self.command = ('stay', 0)

    def followCommand(self, obstacleArray):
        direction, distance = self.command

        if distance:
            self.moveStep(direction, obstacleArray)
            self.command = (direction, distance - 1)

    def moveStep(self, direction: str, obstacleArray):

        directions = dict(north=(0, -1, 0),
                          south=(0, 1, 180),
                          east=(1, 0, 90),
                          west=(-1, 0, 270))

        x_add, y_add, new_alpha = directions[direction]
        new_x, new_y = self.x + x_add, self.y + y_add

        # robot will do the pacman
        new_x, new_y = new_x % Board.TileCount, new_y % Board.TileCount

        tileVal = obstacleArray[new_x][new_y]

        if tileVal == Hazard.Empty:
            self.x = new_x
            self.y = new_y

        elif tileVal == Hazard.Wall:
            pass

        elif tileVal == Hazard.Border:
            pass

        elif tileVal == Hazard.Hole:
            self.x = 1
            self.y = 1

        self.alpha = new_alpha

    @staticmethod
    def createExampleRobot(boardSize: int, tileSize: int):

        return BaseRobot(1, 1, tileSize/2, 45)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())