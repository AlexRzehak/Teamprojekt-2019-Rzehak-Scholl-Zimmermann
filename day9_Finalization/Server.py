import sys
import math
import time
import threading
from functools import partial
from timeit import default_timer
from collections import defaultdict

from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from Movement import FollowMovement, RandomTargetMovement, RunMovement, ChaseMovement, ChaseMovementGun, PermanentGunMovement, SimpleAvoidMovementGun, SimpleAvoidMovement, ChaseAvoidMovementGun
from model import BaseRobot, DataRobot
from ai_control import RobotControl, SensorData
from player_control import PlayerControl, ControlScheme
from robogun import RoboGun, GunInterface
import scenario
import utils

# ==================================
# Server
# ==================================
#
# In this file, you will find the main game:
# The Game class will define properties of the window.
# The board class controls the execution of the game.
# After the board state is initiated with help of the configparser,
# start the main loop of the game, performing actions with a certain tick rate.
# These actions include:
# - Forwarding / execution of key inputs.
# - Calculation and selection of data to send to robot units.
# - Sending and enquiring data to and from robot units.
# - Physics engine calculations.
# Also, paint the game with help of Qt.
#
# CHANGE HERE:
# - the main loop
# - window and paint functions
# - physics of movement
# - collision mechanics
# - bullet movement and collision
# - Qt key events and key state lists
# - creation of message data & vision
# - control over the board's obstacles


GAME_TITLE = 'SpaceBaseRobots'
FIELD_SIZE = scenario.FIELD_SIZE
TILE_SIZE = scenario.TILE_SIZE


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
        self.setWindowTitle(GAME_TITLE)
        self.show()


class Board(QWidget):
    TILE_COUNT = int(FIELD_SIZE / TILE_SIZE)
    SECONDS_PER_TICK = 0.05

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = utils.create_example_array(Board.TILE_COUNT)

        # Create an additional obstacle list from array
        # storing the position values of every obstacle.
        # Since we don't change the obstacleArray,
        # this call is only needed once.
        self.obstacle_list = utils.generate_obstacle_list(
            self.obstacleArray, Board.TILE_COUNT)

        self.time_stamp = -1

        self.init_textures()

        # Store data representations of all involved robot units.
        self.robots = []

        # Data representations of bullets.
        self.bullets = set()

        self.collision_scenarios = dict()

        # Initiate board state and game parameters.
        self.create_scenario()

        # Inititate key listener.
        self.key_states = dict()
        self.stateless_keys = dict()
        self.initiate_key_listening()
        self.setFocusPolicy(Qt.StrongFocus)

        # Start the calculation process of the AI.
        for robot in self.robots:
            robot.start()

        # Start the game loop.
        self.game_loop_barrier = threading.Barrier(2)
        self.init_game_loop()

    def init_textures(self):
        self.board_texture = QPixmap("textures/board.png")
        self.wall_texture = QPixmap("textures/wall.png")
        self.border_texture = QPixmap("textures/border.png")
        self.hole_texture = QPixmap("textures/hole.png")
        self.robot_texture = QPixmap("textures/robot.png")
        self.bullet_texture = QPixmap("textures/bullet.png")

    def init_game_loop(self):

        def game_loop_scheduler():
            # get local reference
            spt = Board.SECONDS_PER_TICK

            previous = default_timer()
            lag = 0.0

            while 1:
                current = default_timer()
                elapsed = current - previous
                previous = current

                lag += elapsed
                while lag >= spt:
                    # blocking
                    self.trigger_game_loop()
                    lag -= spt

                # non-blocking
                QTimer.singleShot(0.0, self.update)

        t = threading.Thread(target=game_loop_scheduler)
        t.daemon = True
        t.start()

    def trigger_game_loop(self):
        QTimer.singleShot(0.0, self.game_loop)

        # restore barrier
        self.game_loop_barrier.reset()

        self.game_loop_barrier.wait()

    # ==================================
    # Main Loop
    # ==================================

    def game_loop(self):
        """The game's main loop."""

        # control part

        self.time_stamp += 1

        self.handle_keys_with_state()

        # physics part

        self.calculate_shoot_action()

        self.calculate_bullets()

        for robot in self.robots:
            poll = robot.poll_action_data()
            self.calculate_robot(poll, robot)

        self.check_collision_robots()

        # message part

        if self.time_stamp % 10 == 0:
            m = self.create_alert_message()
            for robot in self.robots:
                if robot.alert_flag:
                    robot.send_sensor_data(m)

        for robot in self.robots:
            v = self.create_vision_message(robot)
            robot.send_sensor_data(v)
            m = self.create_position_message(robot)
            robot.send_sensor_data(m)

        # signal that calculations are done
        self.game_loop_barrier.wait()

    def create_scenario(self):
        """Here, you can implement the scenario on the board.
        """

        # First add the robots.
        pos1 = (500, 750, 75, 0, 0)
        mv1 = RunMovement()
        robo1 = self.construct_robot(TILE_SIZE * 4, mv1, 20, 10, pos1,
                                     max_life=5)
        robo1.set_alert_flag()
        self.deploy_robot(robo1)

        pos2 = (45, 845, 0, 0, 0)
        mv2 = ChaseMovementGun(0)
        gun = RoboGun()
        RoboGun.trigun_decorator(gun)
        robo2 = self.construct_robot(
            TILE_SIZE * 3, mv2, 12, 10, pos2, gun=gun, max_life=1)
        robo2.setup_player_control(
            control_scheme=ControlScheme.player_two_scheme)
        # robo2.set_alert_flag()
        self.deploy_robot(robo2)

        pos3 = (965, 35, 240, 0, 0)
        mv3 = PermanentGunMovement()
        robo3 = self.construct_robot(TILE_SIZE * 2.5, mv3, 5, 15, pos3,
                                     v_max=12, v_alpha_max=30)
        robo3.set_alert_flag()
        pc = PlayerControl(robo3, ControlScheme.default_scheme,
                           invasive_controls=True)
        robo3.setup_player_control(pc)
        self.deploy_robot(robo3)

        pos4 = (300, 650, 70, 0, 0)
        mv4 = ChaseAvoidMovementGun(0)
        gun4 = RoboGun(bullet_speed=30)
        robo4 = self.construct_robot(
            TILE_SIZE * 2, mv4, 15, 15, pos4, gun=gun4)
        # robo4.set_alert_flag()
        self.deploy_robot(robo4)

        # Then add scenario recipes.
        # self.create_catch_recipe(0, [3, 1, 2])

    def deploy_robot(self, data_robot):
        self.robots.append(data_robot)

    def initiate_key_listening(self):
        collected_keys_states = defaultdict(list)
        collected_keys_stateless = defaultdict(list)

        for robot in self.robots:
            if not robot.player_control:
                continue

            robot_keys = robot.player_control.control_scheme
            for key, value in robot_keys.items():
                if value in ControlScheme.STATELESS_KEYS:
                    collected_keys_stateless[key].append(robot)
                if value in ControlScheme.KEYS_WITH_STATE:
                    collected_keys_states[key].append(robot)

        for key, value in collected_keys_states.items():
            self.key_states[key] = dict(is_pressed=False,
                                        was_pressed=False,
                                        targets=tuple(value))

        for key, value in collected_keys_stateless.items():
            self.stateless_keys[key] = tuple(value)

    def construct_robot(self, radius, movement_funct, a_max, a_alpha_max,
                        position, fov_angle=90, v_max=50, v_alpha_max=90,
                        max_life=3, respawn_timer=3, gun=None):
        """
        Create a new robot with given parameters.
        You can add it to the board using deploy_robot().
        """

        # Create robot body with its set parameters.
        base_robot = BaseRobot(radius, a_max, a_alpha_max, fov_angle=fov_angle,
                               v_max=v_max, v_alpha_max=v_alpha_max,
                               max_life=max_life, respawn_timer=respawn_timer)

        # Create autonomous robot unit.
        thread_robot = RobotControl(base_robot, movement_funct)

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
        texture = self.board_texture
        qp.save()
        # TODO DO NOT HARD CODE
        source = QRectF(0, 0, 1125, 1125)
        target = QRectF(0, 0, 1000, 1000)
        qp.setOpacity(1)
        qp.drawPixmap(target, texture, source)
        qp.restore()

    def drawObstacles(self, qp):

        for xpos in range(Board.TILE_COUNT):
            for ypos in range(Board.TILE_COUNT):

                tileVal = self.obstacleArray[xpos][ypos]

                if tileVal == Hazard.Wall:
                    texture = self.wall_texture
                    qp.save()
                    source = QRectF(0, 0, 10, 10)
                    target = QRectF(xpos * TILE_SIZE, ypos *
                                    TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    qp.drawPixmap(target, texture, source)
                    qp.restore()

                elif tileVal == Hazard.Border:
                    texture = self.border_texture
                    qp.save()
                    source = QRectF(0, 0, 10, 10)
                    target = QRectF(xpos * TILE_SIZE, ypos *
                                    TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    qp.drawPixmap(target, texture, source)
                    qp.restore()

                elif tileVal == Hazard.Hole:
                    texture = self.hole_texture
                    qp.save()
                    source = QRectF(0, 0, 10, 10)
                    target = QRectF(xpos * TILE_SIZE, ypos *
                                    TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    qp.drawPixmap(target, texture, source)
                    qp.restore()

    def drawRobot(self, qp, robot):
        texture = self.robot_texture
        overlay = QRectF(robot.x - robot.radius, robot.y -
                         robot.radius, 2 * robot.radius, 2 * robot.radius)
        qp.save()

        if robot.life / robot.max_life == 0:
            life_frac = 0.01
        elif robot.life / robot.max_life >= 0:
            life_frac = robot.life / robot.max_life
        # setting opacity
        robot_op = 1
        overlay_op = 1
        if robot.dead or robot.immune:
            robot_op = 0.7
            overlay_op = 1

        # painting overlay:
        # setting the color to represent health
        if robot.immune:
            R = 0
            G = 0
            B = 255
            A = 100
        elif not robot.dead:
            R = 255 * (1 - life_frac)
            G = 255 * life_frac
            B = 0
            A = 255
        elif robot.dead:
            R = 10
            G = 10
            B = 10
            A = 255
        qp.setBrush(QColor(R, G, B, A))
        # drawing overlay
        qp.setOpacity(overlay_op)
        qp.drawEllipse(overlay)

        # painting robot:
        # mapping the texture to the robot
        qp.translate(robot.x, robot.y)
        qp.rotate(robot.alpha)
        source = QRectF(0, 0, 567, 566)
        target = QRectF(-robot.radius, -robot.radius,
                        2 * robot.radius, 2 * robot.radius)
        # drawing the robot
        qp.setOpacity(robot_op)
        qp.drawPixmap(target, texture, source)

        qp.restore()

    def drawBullets(self, qp):
        texture = self.bullet_texture
        for bullet in self.bullets:
            bullet_radius = 10
            qp.save()
            qp.translate(bullet.position[0], bullet.position[1])
            source = QRectF(0, 0, 715, 715)
            target = QRectF(-bullet_radius, -bullet_radius,
                            2*bullet_radius, 2 * bullet_radius)
            qp.drawPixmap(target, texture, source)
            qp.restore()

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
            Board.teleport_furthest_corner(fugitive_pos, hunter_bot)

        for h in hunters:
            f = partial(callee, h)
            self.collision_scenarios[(fugitive, h)] = f

    def perform_collision_scenario(self, col_tuple):
        """Collision scenario handler.
        Looks if a collision scenario occured and performs the actions needed.
        """
        if col_tuple in self.collision_scenarios:
            self.collision_scenarios[col_tuple](self)

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
        diffs, dists = utils.calculate_angles(points, point,
                                              robot.alpha, robot.fov_angle)

        out = []
        for obst, dif, dist in zip(self.obstacle_list, diffs, dists):
            # if angle difference is greater zero, the obejct will not be seen
            if dif <= 0:
                x, y = obst
                data = (obst, self.obstacleArray[x][y], dist)
                out.append(data)

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
        The array index equals the robot's position in the server's array.
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
            check, d = utils.overlap_check(pos, point, rb.radius, robot.radius)
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
            angles, _ = utils.calculate_angles(calc_list, point,
                                               robot.alpha, robot.fov_angle)

        for index, dif in zip(calc_indices, angles):
            # if the difference value is positive, the center is not seen.
            if dif <= 0:
                result[index] = point_list[index]

        # ray-check
        # calculate the two border rays of the fov
        ray1 = utils.vector_from_angle(robot.alpha - robot.fov_angle/2)
        ray2 = utils.vector_from_angle(robot.alpha + robot.fov_angle/2)

        for index, val in enumerate(result):
            # only check robots that are not already seen
            if not val:
                rb = self.robots[index]
                circle = (rb.x, rb.y, rb.radius)
                # again, python helps us out!
                if (utils.ray_check(point, ray1, circle) or
                        utils.ray_check(point, ray2, circle)):
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
        a = utils.limit(a, -robot.a_max, robot.a_max)

        # checks if angle acceleration is valid
        a_alpha = utils.limit(a_alpha, -robot.a_alpha_max, robot.a_alpha_max)

        # calculates velocities
        new_v = utils.limit(robot.v + a, -1 * robot.v_max, robot.v_max)
        new_v_alpha = utils.limit(robot.v_alpha + a_alpha,
                                  -1 * robot.v_alpha_max, robot.v_alpha_max)

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
        new_alpha = new_alpha % 360
        radian = ((new_alpha - 90) / 180 * math.pi)

        # calculates x coordinate, only allows values inside walls
        new_x = utils.limit(robot.x + new_v * math.cos(radian), 0, FIELD_SIZE)

        # calculates y coordinate, only allows values inside walls
        new_y = utils.limit(robot.y + new_v * math.sin(radian), 0, FIELD_SIZE)
        new_position = (new_x, new_y, new_alpha, new_v, new_v_alpha)
        return new_position

    def col_robots_walls(self, robot, new_v, new_v_alpha):
        """Task 2: Here the collision with obstacles is calculated."""

        # calculates the new position without factoring in any collisions
        position_no_col = self.calculate_position(robot, new_v, new_v_alpha)
        current_testing_pos = position_no_col

        # loop until the current position doesn't produce any collision
        collided = False

        # calculate the boundaries of the area where tiles will be tested
        robot_reach = robot.radius + abs(new_v)
        leftmost_tile = utils.limit(
            int((robot.x - robot_reach) / TILE_SIZE), 0, Board.TILE_COUNT)
        rightmost_tile = utils.limit(
            int((robot.x + robot_reach) / TILE_SIZE) + 1, 0, Board.TILE_COUNT)
        upmost_tile = utils.limit(
            int((robot.y - robot_reach) / TILE_SIZE), 0, Board.TILE_COUNT)
        downmost_tile = utils.limit(
            int((robot.y + robot_reach) / TILE_SIZE) + 1, 0, Board.TILE_COUNT)

        while True:
            max_sub = 0

            # tests all 100x100 tiles in the array for collision
            for tile_x in range(leftmost_tile, rightmost_tile):
                for tile_y in range(upmost_tile, downmost_tile):
                    tile_type = self.obstacleArray[tile_x][tile_y]
                    if tile_type:
                        # takes the position where it doesn't collide
                        # and the amount it backtracked
                        sub, current_pos_col = self.col_robots_walls_helper(
                            current_testing_pos, robot, tile_x, tile_y)

                        # saves position with the most backtracking
                        if abs(sub) > abs(max_sub):
                            max_sub = sub
                            final_pos_col = current_pos_col
                            final_tile_type = tile_type

            # if this iteration (one position) produced any collisions
            # the final position gets tested again
            if max_sub:
                current_testing_pos = final_pos_col
                # test if this adjusted position needs more adjusting
                collided = True
            else:
                break

        # if there was na collision at all, the original position is returned
        if not collided:
            final_pos_col = position_no_col

        elif final_tile_type == 3:
            # TODO: change behavior for hitting a hole here
            robot.deal_damage()

        return final_pos_col

    def col_robots_walls_helper(self, new_position, robot, tile_x, tile_y):
        max_v = new_position[3]
        # checks if the robot collides with a specific tile

        # calc the coordinates of the given tile
        tile_origin = QPoint(tile_x * TILE_SIZE, tile_y * TILE_SIZE)

        # loop terminates when there is no collision
        sub_from_v = 0
        while True:
            # recalculate the position with the adjusted v
            new_position_col = self.calculate_position(
                robot, max_v - sub_from_v, new_position[4])
            robot_center = QPoint(new_position_col[0], new_position_col[1])

            colliding = utils.check_collision_circle_rect(
                robot_center, robot.radius, tile_origin, TILE_SIZE, TILE_SIZE)
            if abs(sub_from_v) <= abs(max_v) and colliding:
                if max_v > 0:
                    sub_from_v += 1
                else:
                    sub_from_v -= 1
            else:
                break

        # return the amount of backtracking (0 if no collision)
        # and the closest position that is collision free
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
                    r1 = bot1.radius
                    c2 = (bot2.x, bot2.y)
                    r2 = bot2.radius
                    check, _ = utils.overlap_check(c1, c2, r1, r2)
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

                direction_vec = utils.vector_from_angle(bullet.direction)
                movement_vec = direction_vec * test_speed
                new_position = initial_position + movement_vec
                bullet.position = new_position

                # perform collision with walls and robots
                if (self.col_bullet_walls(bullet) or
                        self.col_robots_bullets(bullet)):
                    break

    def col_robots_bullets(self, bullet):
        for robot in self.robots:
            robot_center = (robot.x, robot.y)
            distance = utils.distance(robot_center, bullet.position)
            if distance <= robot.radius:
                robot.deal_damage()
                # robot.dead = True
                self.bullets.remove(bullet)
                return True
        return False

    def col_bullet_walls(self, bullet):
        position = bullet.position

        tile_x = int(position[0] / TILE_SIZE)
        tile_x = utils.limit(tile_x, 0, Board.TILE_COUNT - 1)

        tile_y = int(position[1] / TILE_SIZE)
        tile_y = utils.limit(tile_y, 0, Board.TILE_COUNT - 1)

        if self.obstacleArray[tile_x][tile_y] != 0:
            self.bullets.remove(bullet)
            return True

        return False

    # ==================================
    # Key input Area
    # ==================================

    def keyPressEvent(self, event):
        key = event.key()

        # handle stateless keys
        if key in self.stateless_keys:
            for robot in self.stateless_keys[key]:
                robot.enter_key_action(key)

        # set state variables for keys with state
        if key in self.key_states:
            key_dict = self.key_states[key]
            key_dict['is_pressed'] = True
            key_dict['was_pressed'] = True

    def keyReleaseEvent(self, event):
        key = event.key()

        # set state variables for keys with state
        if key in self.key_states:
            key_dict = self.key_states[key]
            key_dict['is_pressed'] = False

    def handle_keys_with_state(self):
        for key, value in self.key_states.items():
            # state is acitve
            if value['is_pressed'] or value['was_pressed']:
                # TODO maybe only call when needed
                value['was_pressed'] = False
                for robot in value['targets']:
                    robot.enter_key_action(key, state=True)
            # state is inactive
            else:
                for robot in value['targets']:
                    robot.enter_key_action(key, state=False)

        # perform actions for entwined keys
        for robot in self.robots:
            robot.finish_key_actions()

    # ==================================
    # Message Area
    # ==================================

    def create_alert_message(self):
        data = []

        for robot in self.robots:
            data.append((robot.x, robot.y))

        return SensorData(SensorData.ALERT_STRING, data, self.time_stamp)

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

    # ==================================
    # Static positioning methods
    # ==================================

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

    @staticmethod
    def teleport_furthest_corner(point, robot):
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


class Hazard:
    """ A namespace for the different types of tiles on the board.
    Might contain additional functionality later.
    """
    Empty = 0
    Wall = 1
    Border = 2
    Hole = 3


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
