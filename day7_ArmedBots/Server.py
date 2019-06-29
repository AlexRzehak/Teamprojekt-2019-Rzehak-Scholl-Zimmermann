import sys
import math
from functools import partial

from PyQt5.QtCore import Qt, QPoint, QBasicTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from Movement import FollowMovement, RandomTargetMovement, RunMovement, ChaseMovement
from Robot import BaseRobot, ThreadRobot, SensorData
import Utils, Robot

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

        self.obstacleArray = Utils.create_example_array(Board.TileCount)

        # Create an additional obstacle list from array
        # storing the position values of every obstacle.
        # Since we don't change the obstacleArray,
        # this call is only needed once.
        self.obstacle_list = Utils.generate_obstacle_list(
            self.obstacleArray, Board.TileCount)

        self.timer = QBasicTimer()

        # TODO watch out that it doesn't get too big
        self.time_stamp = -1

        # A list of DataRobots
        self.robots = []

        # TODO insert datarep for bullets here
        self.bullets = []

        self.collision_scenarios = dict()

        self.create_scenario()

        for robot in self.robots:
            robot.start()

        self.timer.start(Board.RefreshSpeed, self)

    def create_scenario(self):
        """Here, you can implement the scenario on the board.
        """

        # First add the robots.
        pos1 = (500, 500, 75, 0, 0)
        mv1 = RunMovement()
        self.construct_robot(TILE_SIZE * 4, mv1, 15, 10, pos1, alert_flag=True)

        pos2 = (45, 45, 0, 0, 0)
        mv2 = ChaseMovement()
        self.construct_robot(TILE_SIZE * 3, mv2, 15, 10, pos2, alert_flag=True)

        pos3 = (965, 35, 240, 0, 0)
        mv3 = FollowMovement(0)
        self.construct_robot(TILE_SIZE * 2, mv3, 15,
                             7.5, pos3, alert_flag=True)

        pos4 = (300, 650, 70, 0, 0)
        mv4 = RandomTargetMovement()
        self.construct_robot(TILE_SIZE * 1, mv4, 15, 15, pos4, alert_flag=True)

        # Then add scenario recipes.
        self.create_catch_recipe(0, [3, 1, 2])

    def construct_robot(self, radius, movement_funct, a_max, a_alpha_max,
                        position, fov_angle=90, alert_flag=False):
        """Create a new robot with given parameters and add it to the board.
        """

        # We also need to set the fov_angle now.
        base_robot = BaseRobot(radius, a_max, a_alpha_max, Robot.RoboGun(), fov_angle)
        thread_robot = ThreadRobot(base_robot, movement_funct)
        data_robot = DataRobot(base_robot, thread_robot)
        if alert_flag:
            data_robot.set_alert_flag()

        # a position consists of (x, y, alpha, v, v_alpha) values
        data_robot.place_robot(*position)

        self.robots.append(data_robot)

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

    def drawBullet(self, qp, bullet):
        qp.setPen(Qt.red)
        qp.setBrush(Qt.red)
        qp.drawEllipse(bullet['position'], 3, 3)

    def create_catch_recipe(self, fugitive, hunters):
        """Adds a new concrete scenario recipe.
        If fugitive is caught, teleport catcher away.
        """

        # TODO make abstract with external callee

        def callee(hunter, board):
            fugitive_bot = board.robots[fugitive]
            fugitive_pos = (fugitive_bot.x, fugitive_bot.y)
            hunter_bot = board.robots[hunter]
            board.teleport_furthest_corner(fugitive_pos, hunter_bot)

        for h in hunters:
            f = partial(callee, h)
            self.collision_scenarios[(fugitive, h)] = f
            # self.collision_scenarios[(h, fugitive)] = f

    def perform_collision_scenario(self, col_tuple):
        """Collision scenario handler.
        Looks if a collision scenario occured and performs the actions needed.
        """
        if col_tuple in self.collision_scenarios:
            self.collision_scenarios[col_tuple](self)

    def teleport_furthest_corner(self, point, robot):
        """Teleports the robot to a position in the corner
        with the largest distance from point.
        """

        # TODO make less ugly

        # first free pixel in every corner
        corner1 = (TILE_SIZE, TILE_SIZE)
        corner2 = (FIELD_SIZE - TILE_SIZE - 1, TILE_SIZE)
        corner3 = (FIELD_SIZE - TILE_SIZE - 1, FIELD_SIZE - TILE_SIZE - 1)
        corner4 = (TILE_SIZE, FIELD_SIZE - TILE_SIZE - 1)

        rad = robot.radius
        pos1 = (corner1[0] + rad + 1, corner1[1] + rad + 1)
        pos2 = (corner2[0] - rad - 1, corner2[1] + rad + 1)
        pos3 = (corner3[0] - rad - 1, corner3[1] - rad - 1)
        pos4 = (corner4[0] + rad + 1, corner4[1] - rad - 1)

        positions = [pos1, pos2, pos3, pos4]

        d = 0
        p = -1

        for i in range(4):
            dist = Utils.distance(point, positions[i])
            if dist > d:
                d = dist
                p = i

        position = (robot.x, robot.y, robot.alpha, robot.v, robot.v_alpha)

        if p == 0:
            position = (pos1[0], pos1[1], 135, 0, 0)
        elif p == 1:
            position = (pos2[0], pos2[1], 225, 0, 0)
        elif p == 2:
            position = (pos3[0], pos3[1], 315, 0, 0)
        elif p == 3:
            position = (pos4[0], pos4[1], 45, 0, 0)

        robot.place_robot(*position)

    def calculate_vision_board(self, robot):
        """Calculate a list of all obejcts seen by a robot.
        The objects are reduced to their center points for this calculation.
        Returns a list of tuple values for obejcts seen:
        (index in obstacle_Array, obstacle type, distance from robot's center)
        """

        # get the objects representative points
        points = self.obstacle_list * 10 + 5
        point = (robot.x, robot.y)

        # use calculate_angles for the maths
        diffs, dists = Utils.calculate_angles(points, point,
                                              robot.alpha, robot.fov_angle)

        out = []
        for obst, dif, dist in zip(self.obstacle_list, diffs, dists):
            # if angle difference is greater zero, the obejct will not be seen
            if dif <= 0:
                x, y = obst
                data = (obst, self.obstacleArray[x][y], dist)
                out.append(data)

        # out = [[0] * 100 for row in range(100)]
        # for pair in zip(self.obstacle_list, diffs):
        #     if pair[1] <= 0:
        #         x, y = pair[0]
        #         out[x][y] = self.obstacleArray[x][y]

        return out

    def calculate_vision_robots(self, robot):
        """Calculate a list of robots seen by a robot.
        A robot (a) can be seen by robot (x) if:
        - (a) touches (x)
        - (a)s center is in the direct FoV-angle of (x)
        - a point of (a)s radius is in the direct FoV-angle of (x)

        For the last criteria, we check, if (a) intersects one of the rays,
        marking the outline of the FoV.

        Returns an array with entries for each robot:
        The array index equals the robot's serial number.
        Array entries:
        False, if the robot can not be seen.
        A tuple, if the robot is seen:
        (position, distance between the robot's centers)
        """
        point = (robot.x, robot.y)

        # no robot is seen per default.
        result = [False] * len(self.robots)
        point_list = []

        # robots in this list must undergo the angle-check
        # since they don't overlap.
        # this also stops invalid point values
        # from being inserted in calculate_angle.
        calc_list = []
        calc_indices = []

        # distance-check
        for index, rb in enumerate(self.robots):
            # for each robot, get its distance to (x) and calculate,
            # wheather they overlap.
            pos = (rb.x, rb.y)
            check, d = Utils.overlap_check(pos, point, rb.radius, robot.radius)
            # create a list of position and distance for EVERY robot.
            point_list.append((pos, d))

            # the actual overlap-check:
            if check:
                result[index] = (pos, d)
            # add more cases, if you want to propagate the angles as well
            else:
                calc_list.append(pos)
                calc_indices.append(index)

        # angle-check
        angles = []
        if calc_list:
            angles, _ = Utils.calculate_angles(calc_list, point,
                                               robot.alpha, robot.fov_angle)

        for index, dif in zip(calc_indices, angles):
            # if the difference value is positive, the center is not seen.
            if dif <= 0:
                result[index] = point_list[index]

        # ray-check
        # calculate the two border rays of the fov
        ray1 = Utils.vector_from_angle(robot.alpha - robot.fov_angle/2)
        ray2 = Utils.vector_from_angle(robot.alpha + robot.fov_angle/2)

        for index, val in enumerate(result):
            # only check robots that are not already seen
            if not val:
                rb = self.robots[index]
                circle = (rb.x, rb.y, rb.radius)
                # again, python helps us out!
                if (Utils.ray_check(point, ray1, circle) or
                        Utils.ray_check(point, ray2, circle)):
                    result[index] = point_list[index]

        # now the list is complete
        return result

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
        new_position_col = self.col_robots_walls(
            robot, new_v, new_v_alpha)

        # re-place the robot on the board
        Board.place_robot(robot, *new_position_col)
        # sends tuple to be used as "sensor_data"
        return new_position_col

    def calculate_position(self, robot, new_v, new_v_alpha):
        # calculates alpha
        new_alpha = robot.alpha + new_v_alpha
        radian = ((new_alpha - 90) / 180 * math.pi)

        # calculates x coordinate, only allows values inside walls
        new_x = Utils.limit(robot.x + new_v * math.cos(radian), 0, FIELD_SIZE)

        # calculates y coordinate, only allows values inside walls
        new_y = Utils.limit(robot.y + new_v * math.sin(radian), 0, FIELD_SIZE)
        new_position = (new_x, new_y, new_alpha, new_v, new_v_alpha)
        return new_position

    def calculate_bullet(self, bullet):
        position = bullet['position']
        new_bullet = bullet
        direction_vec = Utils.vector_from_angle(bullet['direction'])
        movement_vec = direction_vec * bullet['speed']
        new_position = (position[0] + movement_vec[0],
                        position[1] + movement_vec[1])
        new_bullet['position'] = new_position
        return new_bullet

    def col_robots_walls(self, robot, new_v, new_v_alpha):
        """Task 2: Here the collision with obstacles is calculated."""

        # calculates the new position without factoring in any collisions
        position_no_col = self.calculate_position(robot, new_v, new_v_alpha)
        current_testing_position = position_no_col

        # loop continues until the current position doesn't produce any collision
        collided = False

        # calculate the boundaries of the area where tiles will be tested
        robot_reach = robot.radius + new_v
        leftmost_tile = Utils.limit(
            int((robot.x - robot_reach) / TILE_SIZE), 0, Board.TileCount)
        rightmost_tile = Utils.limit(
            int((robot.x + robot_reach) / TILE_SIZE) + 1, 0, Board.TileCount)
        upmost_tile = Utils.limit(
            int((robot.y - robot_reach) / TILE_SIZE), 0, Board.TileCount)
        downmost_tile = Utils.limit(
            int((robot.y + robot_reach) / TILE_SIZE) + 1, 0, Board.TileCount)

        while True:
            max_sub = 0

            # tests all 100x100 tiles in the array for collision
            for tile_x in range(leftmost_tile, rightmost_tile):
                for tile_y in range(upmost_tile, downmost_tile):
                    if self.obstacleArray[tile_x][tile_y] != 0:

                        # takes the position where it doesn't collide and the amount it backtracked
                        sub_from_v, current_position_col = self.col_robots_walls_helper(current_testing_position,
                                                                                      robot, tile_x, tile_y)

                        # saves position with the most backtracking (the tile where it was in deepest)
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

    def col_robots_walls_helper(self, new_position, robot, tile_x, tile_y):
        # checks if the robot collides with a specific tile

        # calc the coordinates of the given tile
        tile_origin = QPoint(tile_x * TILE_SIZE, tile_y * TILE_SIZE)

        # loop terminates when there is no collision
        sub_from_v = 0
        while True:
            # recalc the position with the adjusted v
            new_position_col = self.calculate_position(
                robot, new_position[3] - sub_from_v, new_position[4])
            robot_center = QPoint(new_position_col[0], new_position_col[1])

            if Utils.check_collision_circle_rect(robot_center, robot.radius,
                                                 tile_origin, TILE_SIZE, TILE_SIZE):
                sub_from_v += 1
            else:
                break

        """
        # loop terminates when there is no collision
        lower = 0
        upper = new_position[3]
        robot_center = QPoint(new_position[0], new_position[1])
        tile_origin = QPoint(tile_x * TILE_SIZE, tile_y * TILE_SIZE)
        if self.check_collision_circle_rect(robot_center, robot.radius,
                                            tile_origin, TILE_SIZE, TILE_SIZE):
            while upper >= lower:
                mid = int((lower + upper) / 2)
                new_position_col = self.calculate_position(
                    robot, mid, new_position[4])
                robot_center = QPoint(new_position_col[0], new_position_col[1])
                # if there is a collision v has to be lower than mid
                if self.check_collision_circle_rect(robot_center, robot.radius,
                                                    tile_origin, TILE_SIZE, TILE_SIZE):
                    upper = mid - 1
                # if there is no collision v has to be higher than mid
                else:
                    lower = mid + 1
            # return the amount of backtracking (0 if no collision) and the closest position that is collision free
            return new_position[3] - lower, new_position_col
        else:
            return 0, new_position
        """

        # return the amount of backtracing (0 if no collision) and the closest position that is collision free
        return sub_from_v, new_position_col

    # TODO we might improve that function
    def col_robots(self):
        for robot1 in self.robots:
            for robot2 in self.robots:
                index_robot1 = self.robots.index(robot1)
                index_robot2 = self.robots.index(robot2)
                if index_robot1 != index_robot2:
                    center_robot1 = (robot1.x, robot1.y)
                    center_robot2 = (robot2.x, robot2.y)
                    colliding, _ = Utils.overlap_check(center_robot1, center_robot2,
                                                       robot1.radius, robot2.radius)
                    if colliding:
                        self.perform_collision_scenario((index_robot2, index_robot2))

    def col_robots_bullets(self):
        for robot in self.robots:
            hit = False
            robot_center = (robot.x, robot.y)
            for bullet in self.bullets:
                distance = Utils.distance(robot_center, bullet['position'])
                if distance <= robot.radius:
                    # TODO delete Bullet
                    hit = True
            if hit:
                # TODO implement proper respawn procedure
                self.teleport_furthest_corner(robot_center, robot)

    def col_bullets_walls(self):
        for bullet in self.bullets:
            position = bullet['position']
            tile_x = int(position[1] / TILE_SIZE)
            tile_y = int(position[2] / TILE_SIZE)
            if self.obstacleArray[tile_x][tile_y] != 0:
                # TODO delete Bullet
                a = 1







    def timerEvent(self, event):
        """The game's main loop.
        Called every tick by active timer attribute of the board.
        """
        # TODO use delta-time to interpolate visuals

        self.time_stamp += 1

        for robot in self.robots:
            poll = robot.poll_action_data()
            self.calculate_robot(poll, robot)
            # if collision:
            #     m = self.create_bonk_message(collision)
            #     robot.send_sensor_data(m)
        for bullet in self.bullets:
            self.calculate_bullet(bullet)

        if self.time_stamp % 10 == 0:

            m = self.create_alert_message()
            for robot in self.robots:
                if robot.alert_flag:
                    robot.send_sensor_data(m)

        # TODO we might improve that function
        self.col_robots()
        self.col_robots_bullets()
        self.col_bullets_walls()

        # Task 2: Now also send vision messages each tick.
        for robot in self.robots:
            v = self.create_vision_message(robot)
            robot.send_sensor_data(v)
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
        print('B O N K')

        data = None
        return SensorData(SensorData.BONK_STRING, data, self.time_stamp)

    def create_position_message(self, robot):

        data = (robot.x, robot.y, robot.alpha, robot.v, robot.v_alpha)
        return SensorData(SensorData.POSITION_STRING, data, self.time_stamp)

    def create_vision_message(self, robot):
        "New message type for FoV-data of a robot."

        # list of wall object tuples:
        # ((xpos, ypos), type, distance)
        board_data = self.calculate_vision_board(robot)

        # list of robot object tuples:
        # ((xpos, ypos), distance)
        robot_data = self.calculate_vision_robots(robot)

        data = (board_data, robot_data)
        return SensorData(SensorData.VISION_STRING, data, self.time_stamp)

    # gun stuff
    def calculate_shoot_action(self):
        for robot in self.robots:
            maybe_bullet = robot.perform_shoot_action()
            if maybe_bullet:
                # TODO perform bullet stuff
                pass

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

        # Only some robots should receive an alert message.
        self.alert_flag = False

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

    # gun stuff
    def perform_shoot_action(self):
        maybe_bullet = self.gun.trigger_fire(self)
        return maybe_bullet

    def set_alert_flag(self, value=True):
        self.alert_flag = value


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
