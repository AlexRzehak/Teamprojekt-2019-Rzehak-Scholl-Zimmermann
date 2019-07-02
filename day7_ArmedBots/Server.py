import sys
import math
from functools import partial
from dataclasses import dataclass

from PyQt5.QtCore import Qt, QPoint, QBasicTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from Movement import FollowMovement, RandomTargetMovement, RunMovement, ChaseMovement, ChaseMovementGun, PermanentGunMovement, SimpleAvoidMovementGun
from Robot import BaseRobot, ThreadRobot, SensorData, RoboGun, GunInterface
import Utils

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

        self.bullets = set()

        self.collision_scenarios = dict()

        self.create_scenario()

        for robot in self.robots:
            robot.start()

        self.timer.start(Board.RefreshSpeed, self)

    def create_scenario(self):
        """Here, you can implement the scenario on the board.
        """

        # First add the robots.
        pos1 = (500, 750, 75, 0, 0)
        mv1 = RunMovement()
        robo1 = self.construct_robot(TILE_SIZE * 4, mv1, 20, 10, pos1)
        robo1.set_alert_flag()
        self.deploy_robot(robo1)

        pos2 = (45, 845, 0, 0, 0)
        mv2 = ChaseMovementGun(0)
        gun = RoboGun()
        RoboGun.trigun_decorator(gun)
        robo2 = self.construct_robot(
            TILE_SIZE * 3, mv2, 12, 10, pos2, gun=gun)
        # robo2.set_alert_flag()
        self.deploy_robot(robo2)

        pos3 = (965, 35, 240, 0, 0)
        mv3 = PermanentGunMovement()
        robo3 = self.construct_robot(TILE_SIZE * 2.5, mv3, 5, 15, pos3)
        robo3.set_alert_flag()
        self.deploy_robot(robo3)

        pos4 = (300, 650, 70, 0, 0)
        mv4 = SimpleAvoidMovementGun()
        gun4 = RoboGun(bullet_speed=30)
        robo4 = self.construct_robot(TILE_SIZE * 2, mv4, 15, 15, pos4, gun=gun4)
        # robo4.set_alert_flag()
        self.deploy_robot(robo4)

        # Then add scenario recipes.
        # self.create_catch_recipe(0, [3, 1, 2])

    def deploy_robot(self, data_robot):
        self.robots.append(data_robot)

    def construct_robot(self, radius, movement_funct, a_max, a_alpha_max,
                        position, fov_angle=90, gun=None):
        """
        Create a new robot with given parameters.
        You can add it to the board using deploy_robot().
        """

        # Create robot body with its set parameters.
        base_robot = BaseRobot(radius, a_max, a_alpha_max, fov_angle)

        # Create autonomous robot unit.
        thread_robot = ThreadRobot(base_robot, movement_funct)

        # Create data representation to be added to tracking of the server.
        data_robot = DataRobot(base_robot, thread_robot)
        # set up communication with thread robot about gun data
        data_robot.setup_gun(gun)
        # a position consists of (x, y, alpha, v, v_alpha) values
        data_robot.place_robot(*position)

        return data_robot

    # ==================================
    # Painter Area
    # ==================================

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        self.drawObstacles(qp)
        for robot in self.robots:
            self.drawRobot(qp, robot)
        self.drawBullets(qp)
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

    def drawBullets(self, qp):
        qp.setPen(Qt.red)
        qp.setBrush(Qt.red)
        for bullet in self.bullets:
            pos = QPoint(bullet.position[0], bullet.position[1])
            qp.drawEllipse(pos, 3, 3)

    # ==================================
    # Scenario Area
    # ==================================

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

        lower_limit = TILE_SIZE + robot.radius + 1
        upper_limit = FIELD_SIZE - TILE_SIZE - robot.radius - 2

        top_left_corner = (lower_limit, lower_limit, 135, 0, 0)
        bot_left_corner = (lower_limit, upper_limit, 45, 0, 0)
        top_right_corner = (upper_limit, lower_limit, 225, 0, 0)
        bot_right_corner = (upper_limit, upper_limit, 315, 0, 0)

        if point[0] > (FIELD_SIZE / 2):
            if point[1] > (FIELD_SIZE / 2):
                position = top_left_corner
            else:
                position = bot_left_corner
        else:
            if point[1] > (FIELD_SIZE / 2):
                position = top_right_corner
            else:
                position = bot_right_corner

        robot.place_robot(*position)

    # ==================================
    # Vision Area
    # ==================================

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

    # ==================================
    # Collision Area
    # ==================================

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

    def col_robots_walls(self, robot, new_v, new_v_alpha):
        """Task 2: Here the collision with obstacles is calculated."""

        # calculates the new position without factoring in any collisions
        position_no_col = self.calculate_position(robot, new_v, new_v_alpha)
        current_testing_position = position_no_col

        # loop until the current position doesn't produce any collision
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

        # return the amount of backtracing (0 if no collision) and the closest position that is collision free
        return sub_from_v, new_position_col

    # TODO we might improve that function
    def check_collision_robots(self):
        s = len(self.robots)
        for i in range(s):
            for j in range(s):
                if not i == j:
                    bot1 = self.robots[i]
                    bot2 = self.robots[j]
                    c1 = (bot1.x, bot1.y)
                    r1 = (bot1.radius)
                    c2 = (bot2.x, bot2.y)
                    r2 = (bot2.radius)
                    check, _ = Utils.overlap_check(c1, c2, r1, r2)
                    if check:
                        self.perform_collision_scenario((i, j))

    # ==================================
    # Gun/Bullet Area
    # ==================================

    def calculate_shoot_action(self):
        for robot in self.robots:
            maybe_bullet = robot.perform_shoot_action()
            if maybe_bullet:
                self.bullets.add(maybe_bullet)

    def calculate_bullets(self):
        """
        Here, the bullet movement happens.
        Check for collision with walls and despawn the bullet.
        Check for collision with robots and kill the robot (despawn the bullet)
        """

        for bullet in self.bullets.copy():
            # move
            initial_position = bullet.position
            for test_speed in range(int(bullet.speed)):

                direction_vec = Utils.vector_from_angle(bullet.direction)
                movement_vec = direction_vec * test_speed
                new_position = initial_position + movement_vec
                bullet.position = new_position

                # perform collision with walls and robots
                if (self.col_bullet_walls(bullet) or
                        self.col_robots_bullets(bullet)):
                    break

        # respawn the robots
        for robot in self.robots:
            if robot.dead:
                pos = (robot.x, robot.y)
                self.teleport_furthest_corner(pos, robot)
                robot.dead = False

    def col_robots_bullets(self, bullet):
        for robot in self.robots:
            robot_center = (robot.x, robot.y)
            distance = Utils.distance(robot_center, bullet.position)
            if distance <= robot.radius:
                robot.dead = True
                self.bullets.remove(bullet)
                return True
        return False

    def col_bullet_walls(self, bullet):
        position = bullet.position

        tile_x = int(position[0] / TILE_SIZE)
        tile_x = Utils.limit(tile_x, 0, Board.TileCount - 1)

        tile_y = int(position[1] / TILE_SIZE)
        tile_y = Utils.limit(tile_y, 0, Board.TileCount - 1)

        if self.obstacleArray[tile_x][tile_y] != 0:
            self.bullets.remove(bullet)
            return True

        return False

    # ==================================
    # Main Loop
    # ==================================

    def timerEvent(self, event):
        """The game's main loop.
        Called every tick by active timer attribute of the board.
        """
        # TODO use delta-time to interpolate visuals

        self.time_stamp += 1

        self.calculate_shoot_action()

        self.calculate_bullets()

        for robot in self.robots:
            poll = robot.poll_action_data()
            self.calculate_robot(poll, robot)
            # if collision:
            #     m = self.create_bonk_message(collision)
            #     robot.send_sensor_data(m)

        if self.time_stamp % 10 == 0:

            m = self.create_alert_message()
            for robot in self.robots:
                if robot.alert_flag:
                    robot.send_sensor_data(m)

        # TODO we might improve that function
        self.check_collision_robots()

        # Task 2: Now also send vision messages each tick.
        for robot in self.robots:
            v = self.create_vision_message(robot)
            robot.send_sensor_data(v)
            m = self.create_position_message(robot)
            robot.send_sensor_data(m)

        # update visuals
        self.update()

    # ==================================
    # Message Area
    # ==================================

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

        self.gun = None

        # Use this when respawning the robot
        self.dead = False

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
        """Will return a valid bullet, if the robot is shooting.
        Else returns False.
        """

        maybe_bullet = False

        if not self.gun:
            return maybe_bullet

        maybe_data = self.gun.trigger_fire()
        if maybe_data:
            angle = self.alpha

            angle_vector = Utils.vector_from_angle(angle)
            robot_center = (self.x, self.y)
            bullet_start = robot_center + (self.radius + 1) * angle_vector
            # bullet_start = (int(bullet_start[0]), int(bullet_start[1]))

            speed = self.v + maybe_data

            maybe_bullet = Bullet(position=bullet_start,
                                  speed=speed,
                                  direction=angle)
        return maybe_bullet

    def setup_gun(self, gun=None):
        """Set up gun communication between autonomous unit and server."""
        if not gun:
            gun = RoboGun()

        self.gun = gun

        gun_interface = GunInterface(gun)
        self.thread_robot.setup_gun_interface(gun_interface)

    # optional flags
    def set_alert_flag(self, value=True):
        self.alert_flag = value

    def set_resync_flag(self, value=True):
        self.thread_robot.set_resync_flag(value)


class Bullet:
    def __init__(self, position, speed, direction):
        self.position = position
        self.speed = speed
        self.direction = direction


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
