import sys
import timeit

import numpy as np
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QWidget, QApplication

import Utils

FIELD_SIZE = 1000
TILE_SIZE = 10
COLOR_ME = QColor(133, 242, 252, 100)


def main():
    """
    Test file to check out the vision functionalities.
    """
    np.set_printoptions(threshold=sys.maxsize)
    # array = [[1] * 100 for row in range(100)]
    # obst_list = generate_obstacle_list(array)
    # time = timeit.timeit(timer_fun, number=10)
    # print(time/10)

    app = QApplication(sys.argv)
    board = Board()
    sys.exit(app.exec_())


class Board(QWidget):

    def __init__(self):
        super().__init__()

        self.point = (500, 250)
        self.radius = 20
        self.angle = 0
        self.fov = 270
        self.field = np.zeros([100, 100])
        self.robots = []
        self.robots_shown = []

        self.init_robots()
        self.fov_obstacles()
        self.fov_robots()

        self.initUI()

    def initUI(self):
        y_offset = (1080 - FIELD_SIZE) / 2
        self.setGeometry(300, y_offset, FIELD_SIZE, FIELD_SIZE)
        self.setWindowTitle('RoboVision')
        self.show()

    def init_robots(self):
        r1 = Robot(480, 100, 15)
        r2 = Robot(471, 250, 10)
        r3 = Robot(500, 300, 10)
        r4 = Robot(300, 100, 60)
        r5 = Robot(700, 400, 60)

        self.robots = [r1, r2, r3, r4, r5]

    def fov_obstacles(self):
        # array = np.ones([100, 100])
        array = np.zeros([100, 100])
        array[:, 1] = 1

        obst_list = Utils.generate_obstacle_list(array, 100)
        print(obst_list)
        points = obst_list * 10 + 5
        diffs, dists = Utils.calculate_angles(points, self.point,
                                              self.angle, self.fov)

        print(diffs)
        for pos, dif in zip(obst_list, diffs):
            if dif <= 0:
                x, y = pos
                self.field[x][y] = 1

    def fov_robots(self):
        result = [False] * len(self.robots)
        point_list = []

        calc_list = []
        calc_indices = []

        # distance-check
        for index, rb in enumerate(self.robots):
            pos = (rb.x, rb.y)
            check, d = Utils.overlap_check(
                pos, self.point, rb.radius, self.radius)
            point_list.append((pos, d))

            if check:
                result[index] = (pos, d)
            # add more cases, if you want to propagate the angles as well
            else:
                calc_list.append(pos)
                calc_indices.append(index)

        # angle-check
        angles = []
        if calc_list:
            angles, _ = Utils.calculate_angles(calc_list, self.point,
                                               self.angle, self.fov)

        for index, dif in zip(calc_indices, angles):
            if dif <= 0:
                result[index] = point_list[index]

        # ray-check
        ray1 = Utils.vector_from_angle(self.angle - self.fov/2)
        ray2 = Utils.vector_from_angle(self.angle + self.fov/2)

        for index, val in enumerate(result):
            if not val:
                rb = self.robots[index]
                circle = (rb.x, rb.y, rb.radius)
                if (Utils.ray_check(self.point, ray1, circle) or
                        Utils.ray_check(self.point, ray2, circle)):
                    result[index] = point_list[index]

        self.robots_shown = result

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        self.drawObstacles(qp)

        me = (self.point[0], self.point[1], self.radius)
        self.drawCircle(qp, me, COLOR_ME)

        for index, data in enumerate(self.robots_shown):
            if data:
                pos, _ = data
                rb = self.robots[index]
                circ = (pos[0], pos[1], rb.radius)
                self.drawCircle(qp, circ, Qt.green)

        # r4 = self.robots[3]
        # c4 = (r4.x, r4.y, r4.radius)
        # self.drawCircle(qp, c4, Qt.green)

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

        for xpos in range(100):
            for ypos in range(100):
                if self.field[xpos][ypos]:
                    brush = QBrush(Qt.Dense2Pattern)
                    brush.setColor(Qt.red)
                    qp.setBrush(brush)
                    qp.drawRect(xpos * TILE_SIZE,
                                ypos * TILE_SIZE,
                                TILE_SIZE, TILE_SIZE)

    def drawCircle(self, qp, circle, color):
        x, y, r = circle

        # setting color of border
        qp.setPen(Qt.black)

        # setting circle color and transparency
        qp.setBrush(color)
        # calculating center point of the circle
        center = QPoint(x, y)
        # drawing the circle with the position and radius of the Robot
        qp.drawEllipse(center, r, r)

        # calculating the point to draw the line that indicates alpha
        radian = ((self.angle - 90) / 180 * np.pi)
        direction = QPoint(np.cos(radian) * 10 + QPoint.x(center),
                           np.sin(radian) * 10 + QPoint.y(center))
        # setting color of directional line
        qp.setPen(Qt.red)
        qp.drawLine(QPoint.x(center), QPoint.y(center),
                    QPoint.x(direction), QPoint.y(direction))

        # marking center point
        # setting center color
        qp.setBrush(Qt.white)
        # drawing small circle
        qp.drawEllipse(center, 2, 2)


class Robot:

    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius


if __name__ == '__main__':
    main()
