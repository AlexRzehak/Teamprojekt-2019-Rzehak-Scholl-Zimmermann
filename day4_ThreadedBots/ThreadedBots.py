import sys
import math
import queue
import threading
import time
import random

from PyQt5.QtCore import Qt, QPoint, QBasicTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

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
    RefreshSpeed = 40

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = Board.createExampleArray(Board.TileCount)
        self.robots = []
        self.timer = QBasicTimer()

        self.create_example_robots()

        for robot in self.robots:
            robot.run()

        self.timer.start(Board.RefreshSpeed, self)

    def create_example_robots(self):
        """Task 3: Initialize four different robots
        and place them on the battlefield.
        """
        robo1 = BaseRobot(TILE_SIZE, Movement.random_movement, 1000, 1000)
        Board.place_robot(robo1, 400, 400, 90)
        robo1.receive_sensor_data((400, 400, 90, 0, 0))
        self.robots.append(robo1)

        robo2 = BaseRobot(TILE_SIZE * 5, Movement.spin_movement, 100, 0.2)
        Board.place_robot(robo2, 900, 800, 0)
        robo2.receive_sensor_data((900, 800, 0, 0, 0))
        self.robots.append(robo2)

        robo3 = BaseRobot(TILE_SIZE * 2, Movement.spiral_movement, 100, 100)
        Board.place_robot(robo3, 200, 150, 240)
        robo3.receive_sensor_data((200, 150, 240, 0, 0))
        self.robots.append(robo3)

        robo4 = BaseRobot(TILE_SIZE * 2,
                          Movement.nussschnecke_movement, 100, 100)
        Board.place_robot(robo4, 600, 500, 240)
        robo4.receive_sensor_data((600, 500, 240, 0, 0))
        self.robots.append(robo4)

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

    def drawRobot(self, qp, robot):

        # setting color of border
        qp.setPen(Qt.black)

        # setting circle color and transparency
        qp.setBrush(QColor(133, 242, 252, 100))
        # calculating center point of the circle
        center = QPoint(robot.x, robot.y)
        # drawing the circle with the position and radius of the Robot
        qp.drawEllipse(center, robot.radius, robot.radius)

        # calculating the point to draw the line that indicates alpha
        radian = ((robot.alpha - 90) / 180 * math.pi)
        direction = QPoint(math.cos(radian) * robot.radius + QPoint.x(center),
                           math.sin(radian) * robot.radius + QPoint.y(center))
        # setting color of directional line
        qp.setPen(Qt.red)
        qp.drawLine(QPoint.x(center), QPoint.y(center),
                    QPoint.x(direction), QPoint.y(direction))

        # marking center point
        # setting center color
        qp.setBrush(Qt.white)
        # drawing small circle
        qp.drawEllipse(center, 2, 2)

    def calculate_robot(self, poll, robot):
        """Uses current position data of robot robot and acceleration values
        polled from the robot to calculate new position values and create new
        sensor input.
        """

        # TODO (much optional) some time implement collision management

        # checks if acceleration is valid
        a = poll[0]
        if a > robot.a_max:
            a = robot.a_max
        # checks if angle acceleration is valid
        a_alpha = poll[1]
        if a_alpha > robot.a_alpha_max:
            a_alpha = robot.a_alpha_max

        # calculates new values
        new_v = robot.v + a
        new_v_alpha = robot.v_alpha + a_alpha
        new_alpha = robot.alpha + new_v_alpha
        radian = ((new_alpha - 90) / 180 * math.pi)

        # calculates x coordinate, only allows values inside walls
        new_x = (robot.x + new_v * math.cos(radian))
        if new_x < TILE_SIZE:
            new_x = TILE_SIZE
        if new_x > 99 * TILE_SIZE:
            new_x = 99 * TILE_SIZE
        else:
            new_x = new_x

        # calculates y coordinate, only allows values inside walls
        new_y = (robot.y + new_v * math.sin(radian))
        if new_y < TILE_SIZE:
            new_y = TILE_SIZE
        if new_y > 99 * TILE_SIZE:
            new_y = 99 * TILE_SIZE
        else:
            new_y = new_y

        # sets new values for the robot
        robot.v = new_v
        robot.v_alpha = new_v_alpha
        # places the robot on the board
        Board.place_robot(robot, new_x, new_y, new_alpha)
        # sends tuple to be used as "sensor_date"
        return (new_x, new_y, new_alpha, new_v, new_v_alpha)

    def timerEvent(self, event):
        """Task 5: The Server will ask each robot about its parameters
        and re-calculate the board state.
        """

        for robot in self.robots:
            poll = robot.send_action_data()
            new_data = self.calculate_robot(poll, robot)
            robot.receive_sensor_data(new_data)

        # update visuals
        self.update()

    @staticmethod
    def place_robot(robot, x, y, alpha):
        robot.x = x
        robot.y = y
        robot.alpha = alpha


class Hazard():
    """ A namespace for the different types of tiles on the board.
    Might contain additional functionality later.
    """
    Empty = 0
    Wall = 1
    Border = 2
    Hole = 3


class Movement():
    """Implement different movement options."""

    @staticmethod
    def random_movement(sensor_data, **kwargs):
        if sensor_data[3] < 15:
            a = 1
            a_alpha = random.randint(-20, 20)
        else:
            a = 0
            a_alpha = random.randint(-20, 20)
        return a, a_alpha

    @staticmethod
    def nussschnecke_movement(sensor_data, **kwargs):
        if sensor_data[3] < 7:
            a = 0.5
            a_alpha = 1
            return a, a_alpha
        else:
            a = 0
            a_alpha = 0
        return a, a_alpha

    @staticmethod
    def spiral_movement(sensor_data, **kwargs):
        if sensor_data[3] < 20:
            a = 1
            a_alpha = 1
            return a, a_alpha
        else:
            a = 1
            a_alpha = 0
        return a, a_alpha

    @staticmethod
    def spin_movement(sensor_data, **kwargs):

        a = 0
        a_alpha = 99999999
        if sensor_data[4] > 30:
            a = 0
            a_alpha = 0
        return a, a_alpha

    @staticmethod
    def unchanged_movement(sensor_data, **kwargs):
        a = 0
        a_alpha = 0
        return a, a_alpha


class BaseRobot():
    """Task 2: The BaseRobot class now has the attributes needed."""

    def __init__(self, radius, movement_funct, a_max, a_alpha_max):

        # set parameters
        self.radius = radius

        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

        # Movement function to apply on current position and speed.
        self.movement_funct = movement_funct

        # current position
        self.x = 0
        self.y = 0
        self.alpha = 0

        self.v = 0
        self.v_alpha = 0

        # calculated by the robot
        # if the robot is not fast enough, he sucks
        self.a = 0
        self.a_alpha = 0

        # # the current command executed by the robot
        # self.command = ('stay', 0)
        # self.signals = RobotSignals()

        self.thread = None
        self._sensor_queue = queue.Queue()

    def run(self):
        """Task 1: Every robot will now perform calculations in its own thread."""

        self.thread = threading.Thread(
            target=self._thread_action, args=(self._sensor_queue,))
        self.thread.daemon = True
        self.thread.start()

    def send_action_data(self):
        return self.a, self.a_alpha

    def receive_sensor_data(self, data):
        self._sensor_queue.put(data)

    def _thread_action(self, q):
        """Task 4: The robot will change a and a_alpha within its thread"""

        while True:
            # get() blocks the thread until queue is not empty anymore
            signal = q.get()
            if not signal:
                time.sleep(0)
                continue
            kwargs = dict(radius=self.radius,
                          a_max=self.a_max,
                          a_alpha_max=self.a_alpha_max,
                          # might be wrong lel
                          a=self.a,
                          a_alpha=self.a_alpha)

            self.a, self.a_alpha = self.movement_funct(signal, **kwargs)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
