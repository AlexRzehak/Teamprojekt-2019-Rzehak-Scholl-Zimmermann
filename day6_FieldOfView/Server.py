import sys
import math

from PyQt5.QtCore import Qt, QPoint, QBasicTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QVector2D
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from Movement import FollowMovement, RandomTargetMovement
from Robot import BaseRobot, ThreadRobot, SensorData

FIELD_SIZE = 1000
TILE_SIZE = 10
# TODO: maybe put in robot setup (it then may differ from robot to robot)
ROBOT_FOV = 15


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

        self.obstacleArray = Board.create_example_array(Board.TileCount)
        self.timer = QBasicTimer()

        # TODO watch out that it doesn't get too big
        self.time_stamp = -1

        # A list of DataRobots
        self.robots = []

        self.create_example_robots()

        for robot in self.robots:
            robot.start()

        self.timer.start(Board.RefreshSpeed, self)

    def create_example_robots(self):
        """Task 4: Use the FollowMovement and
        RandomTargetMovement movement functions.
        """

        pos1 = (500, 500, 90, 0, 0)
        mov1 = RandomTargetMovement()
        self.construct_robot(TILE_SIZE * 4, mov1, 15, 15, pos1)

        pos2 = (45, 45, 0, 0, 0)
        mov2 = FollowMovement(0)
        self.construct_robot(TILE_SIZE * 3, mov2, 15, 15, pos2)

        pos3 = (965, 35, 240, 0, 0)
        mov3 = FollowMovement(1)
        self.construct_robot(TILE_SIZE * 2, mov3, 15, 15, pos3)

        pos4 = (500, 970, 240, 0, 0)
        mov4 = FollowMovement(2)
        self.construct_robot(TILE_SIZE * 1, mov4, 15, 15, pos4)

    # a more complex construction method is needed
    def construct_robot(self, radius, movement_funct, a_max, a_alpha_max, position):

        base_robot = BaseRobot(radius, a_max, a_alpha_max)
        thread_robo = ThreadRobot(base_robot, movement_funct)
        data_robot = DataRobot(base_robot, thread_robo)

        # a position consists of (x, y, alpha, v, v_alpha) values
        data_robot.place_robot(*position)

        self.robots.append(data_robot)

    @staticmethod
    def create_example_array(size: int):

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
        array[56][43] = 1
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

    def calculate_vision(self, poll, robot):
        # TODO: check if objects are in vision:
        #   if so give robot coordinates
        list_of_objects = []
        for obj in list_of_objects:
            object_in_triangle = self.object_in_triangle(...)
            if object_in_triangle:
                return 0

    def object_in_triangle(self, point_a, point_b, point_c, object_coordinate):
        # may be easy with ?QTriangle?
        return False


    def calculate_robot(self, poll, robot):
        """Uses current position data of robot robot and acceleration values
        polled from the robot to calculate new position values.
        """

        # unpack robot output
        a, a_alpha = poll

        # checks if acceleration is valid
        if a > robot.a_max:
            a = robot.a_max

        # checks if angle acceleration is valid
        if a_alpha > robot.a_alpha_max:
            a_alpha = robot.a_alpha_max

        # calculates velocities
        new_v = robot.v + a
        new_v_alpha = robot.v_alpha + a_alpha

        # calculates the new position - factors in collisions
        new_position_col = self.calculate_collision(robot, new_v, new_v_alpha)

        # re-place the robot on the board
        Board.place_robot(robot, *new_position_col)
        # sends tuple to be used as "sensor_data"
        return new_position_col

    def calculate_position(self, robot, new_v, new_v_alpha):
        # calculates alpha
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

        new_position = (new_x, new_y, new_alpha, new_v, new_v_alpha)
        return new_position

    def calculate_collision(self, robot, new_v, new_v_alpha):
        """Task 2: Here the collision with obstacles is calculated."""

        # calculates the new position without factoring in any collisions
        position_no_col = self.calculate_position(robot, new_v, new_v_alpha)
        current_testing_position = position_no_col

        # loop continues until the current position doesn't produce any collision
        collided = False
        while True:
            max_sub = 0

            # tests all 100x100 tiles in the array for collision
            for tile_x in range(Board.TileCount):
                for tile_y in range(Board.TileCount):
                    if self.obstacleArray[tile_x][tile_y] != 0:

                        # takes the position where it doesn't collide and the amount it backtraced
                        sub_from_v, current_position_col = self.collision_single_tile(current_testing_position,
                                                                                      robot, tile_x, tile_y)

                        # saves position with the most backtracing (the tile where it was in deepest)
                        if sub_from_v > max_sub:
                            max_sub = sub_from_v
                            final_position_col = current_position_col

            # if this iteration (one position) produced any collisions the final position gets tested again
            if max_sub:
                current_testing_position = final_position_col
                # test if this adjusted position needs more adjusting
                collided = True
            # if the position didn't produce any collisions the robot doesn't collide with anything
            else:
                break

        # if any iteration produced any collisions : v = 0
        if collided:
            final_position_col = (final_position_col[0], final_position_col[1],
                                  final_position_col[2], 0, final_position_col[4])
        # if there was na collision at all, the original position is returned
        else:
            final_position_col = position_no_col
        return final_position_col

    # checks if the robot collides with a specific tile
    def collision_single_tile(self, new_position, robot, tile_x, tile_y):
        # calc the coordinates of the given tile
        tile_left = tile_x * TILE_SIZE
        tile_upper = tile_y * TILE_SIZE

        # loop terminates when there is no collision
        sub_from_v = 0
        while True:
            # recalc the position with the adjusted v
            new_position_col = self.calculate_position(
                robot, new_position[3] - sub_from_v, new_position[4])

            # calc the closest point in the rectangle to the robot
            closest_point = QPoint(self.limit(new_position_col[0], tile_left, tile_left + TILE_SIZE),
                                   self.limit(new_position_col[1], tile_upper, tile_upper + TILE_SIZE))

            # calc the x and y distance from the closest point to the center of the robot
            dx = abs(closest_point.x() - new_position_col[0])
            dy = abs(closest_point.y() - new_position_col[1])

            # calc the actual distance
            distance = math.sqrt(dx ** 2 + dy ** 2)

            # distance >= robot.radius means no collision
            # sub_from_v >= new_position[4] means v <= 0
            if distance >= robot.radius:  # or sub_from_v >= new_position[4]:
                break

            # if there is a collision reduce v by one and try again (backtracing)
            else:
                sub_from_v += 1

        # return the amount of backtracing (0 if no collision) and the closest position that is collision free
        return sub_from_v, new_position_col

    # only here to assist collision_single_tile
    # limits a value to a max and a min
    @staticmethod
    def limit(value, min_limit, max_limit):
        if value > max_limit:
            return max_limit
        elif value < min_limit:
            return min_limit
        else:
            return value

    def timerEvent(self, event):
        """Task 1: Every tick the servers sends position data to each robot.
        """
        # TODO use delta-time to interpolate visuals

        self.time_stamp += 1

        for robot in self.robots:
            poll = robot.poll_action_data()
            self.calculate_robot(poll, robot)
            # TODO: send info from: self.calculate_vision(poll, robot)
            # if collision:
            #     m = self.create_bonk_message(collision)
            #     robot.send_sensor_data(m)

        # Task 3: Every 10th tick,
        # the server tells every robot the position of every robot.
        if self.time_stamp % 10 == 0:

            m = self.create_alert_message()
            for robot in self.robots:
                robot.send_sensor_data(m)

        for robot in self.robots:
            m = self.create_position_message(robot)
            robot.send_sensor_data(m)

        # update visuals
        self.update()

    def create_alert_message(self):
        data = []

        for robot in self.robots:
            data.append((robot.x, robot.y))

        return SensorData(SensorData.ALERT_STRING, data, self.time_stamp)

    # TODO this is just a frame implementation.
    def create_bonk_message(self, collision):
        print('hi')

        data = None
        return SensorData(SensorData.BONK_STRING, data, self.time_stamp)

    def create_position_message(self, robot):

        data = (robot.x, robot.y, robot.alpha, robot.v, robot.v_alpha)
        return SensorData(SensorData.POSITION_STRING, data, self.time_stamp)

    @staticmethod
    def place_robot(robot, x, y, alpha, v, v_alpha):
        """Re-places a robot with given position values.
        No sensor data sent.
        """
        robot.x = x
        robot.y = y
        robot.alpha = alpha
        robot.v = v
        robot.v_alpha = v_alpha


class Hazard:
    """ A namespace for the different types of tiles on the board.
    Might contain additional functionality later.
    """
    Empty = 0
    Wall = 1
    Border = 2
    Hole = 3


class DataRobot(BaseRobot):
    """Data representation of the robots for the server."""

    NextSerialNumber = 0

    def __init__(self, base_robot: BaseRobot, thread_robot: ThreadRobot):

        super().__init__(**vars(base_robot))

        # current position
        self.x = 0
        self.y = 0
        self.alpha = 0

        self.v = 0
        self.v_alpha = 0

        self.serial_number = DataRobot.NextSerialNumber
        DataRobot.NextSerialNumber += 1

        self.thread_robot = thread_robot

    def place_robot(self, x, y, alpha, v, v_alpha):

        self.x = x
        self.y = y
        self.alpha = alpha

        self.v = v
        self.v_alpha = v_alpha

        # pos = (x, y, alpha, v, v_alpha)
        # m = SensorData(SensorData.POSITION_STRING, pos, -1)
        # self.thread_robot.receive_sensor_data(m)

    # Interface functions
    def poll_action_data(self):
        return self.thread_robot.send_action_data()

    def send_sensor_data(self, data):
        self.thread_robot.receive_sensor_data(data)

    def start(self):
        self.thread_robot.run()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())

