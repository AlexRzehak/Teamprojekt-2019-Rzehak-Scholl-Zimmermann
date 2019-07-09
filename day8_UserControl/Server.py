import sys
import math
from functools import partial
from dataclasses import dataclass

from PyQt5.QtCore import Qt, QPoint, QBasicTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from Movement import FollowMovement, RandomTargetMovement, RunMovement, ChaseMovement, ChaseMovementGun, PermanentGunMovement, SimpleAvoidMovementGun, SimpleAvoidMovement
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

        self.key_states = dict()
        self.stateless_keys = dict()

        self.create_scenario()

        self.initiate_key_listening()

        for robot in self.robots:
            robot.start()

        self.timer.start(Board.RefreshSpeed, self)

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
        # robo2.set_alert_flag()
        self.deploy_robot(robo2)

        pos3 = (965, 35, 240, 0, 0)
        mv3 = PermanentGunMovement()
        robo3 = self.construct_robot(TILE_SIZE * 2.5, mv3, 5, 15, pos3,
                                     v_max=12, v_alpha_max=30, max_life=3)
        robo3.set_alert_flag()
        pc = PlayerControl(robo3, ControlScheme.player_two_scheme,
                           invasive_controls=True, alpha_accel_amt=10)
        robo3.setup_player_control(pc)
        self.deploy_robot(robo3)

        pos4 = (300, 650, 70, 0, 0)
        mv4 = SimpleAvoidMovementGun()
        gun4 = RoboGun(bullet_speed=30)
        robo4 = self.construct_robot(
            TILE_SIZE * 2, mv4, 15, 15, pos4, gun=gun4)
        # robo4.set_alert_flag()
        self.deploy_robot(robo4)

        # Then add scenario recipes.
        # self.create_catch_recipe(0, [3, 1, 2])

    def deploy_robot(self, data_robot):
        self.robots.append(data_robot)

    # TODO we might improve that function
    def initiate_key_listening(self):
        self.setFocusPolicy(Qt.StrongFocus)
        collected_keys_states = dict()
        collected_keys_stateless = dict()
        for robot in self.robots:
            if robot.player_control:
                robot_keys = robot.player_control.control_scheme
                for key, value in robot_keys.items():
                    # TODO distinguish stateless keys from keys with state
                    if not value == ControlScheme.AUTOPILOT_STRING:
                        if key in collected_keys_states:
                            collected_keys_states[key].append(robot)
                        else:
                            collected_keys_states[key] = [robot]
                    else:
                        if key in collected_keys_stateless:
                            collected_keys_stateless[key].append(robot)
                        else:
                            collected_keys_stateless[key] = [robot]

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
        texture = QPixmap("textures/board.png")
        qp.save()
        source = QRectF(0, 0, 1125, 1125)
        target = QRectF(0, 0, 1000, 1000)
        qp.setOpacity(1)
        qp.drawPixmap(target, texture, source)
        qp.restore()

    def drawObstacles(self, qp):

        for xpos in range(Board.TileCount):
            for ypos in range(Board.TileCount):

                tileVal = self.obstacleArray[xpos][ypos]

                if tileVal == Hazard.Wall:
                    texture = QPixmap("textures/wall.png")
                    qp.save()
                    source = QRectF(0, 0, 10, 10)
                    target = QRectF(xpos * TILE_SIZE, ypos *
                                    TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    qp.drawPixmap(target, texture, source)
                    qp.restore()

                elif tileVal == Hazard.Border:
                    texture = QPixmap("textures/border.png")
                    qp.save()
                    source = QRectF(0, 0, 10, 10)
                    target = QRectF(xpos * TILE_SIZE, ypos *
                                    TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    qp.drawPixmap(target, texture, source)
                    qp.restore()

                elif tileVal == Hazard.Hole:
                    texture = QPixmap("textures/hole.png")
                    qp.save()
                    source = QRectF(0, 0, 10, 10)
                    target = QRectF(xpos * TILE_SIZE, ypos *
                                    TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    qp.drawPixmap(target, texture, source)
                    qp.restore()

    def drawRobot(self, qp, robot):
        texture = QPixmap("textures/robot.png")
        overlay = QRectF(robot.x - robot.radius, robot.y - robot.radius, 2 * robot.radius, 2 * robot.radius)
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
        texture = QPixmap("textures/bullet.png")
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
            # self.collision_scenarios[(h, fugitive)] = f

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
        a = Utils.limit(a, -robot.a_max, robot.a_max)

        # checks if angle acceleration is valid
        a_alpha = Utils.limit(a_alpha, -robot.a_alpha_max, robot.a_alpha_max)

        # calculates velocities
        new_v = Utils.limit(robot.v + a, -1 * robot.v_max, robot.v_max)
        new_v_alpha = Utils.limit(robot.v_alpha + a_alpha,
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
        # TODO confirm no bugs
        new_alpha = new_alpha % 360
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
        current_testing_pos = position_no_col

        # loop until the current position doesn't produce any collision
        collided = False

        # calculate the boundaries of the area where tiles will be tested
        robot_reach = robot.radius + abs(new_v)
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

        # if any iteration produced any collisions : v = 0
        if collided:
            if tile_type == 1:
                final_pos_col = (final_pos_col[0], final_pos_col[1],
                                 final_pos_col[2], 0, final_pos_col[4])
            else:
                # TODO: insert behavior for other tile_types
                #   (and delete this:)
                final_pos_col = (final_pos_col[0], final_pos_col[1],
                                 final_pos_col[2], 0, final_pos_col[4])
        # if there was na collision at all, the original position is returned
        else:
            final_pos_col = position_no_col
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

            colliding = Utils.check_collision_circle_rect(
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
        # for robot in self.robots:
        #     if robot.dead:
        #         pos = (robot.x, robot.y)
        #         Board.teleport_furthest_corner(pos, robot)
        #         robot.dead = False

    def col_robots_bullets(self, bullet):
        for robot in self.robots:
            robot_center = (robot.x, robot.y)
            distance = Utils.distance(robot_center, bullet.position)
            if distance <= robot.radius:
                robot.deal_damage()
                # robot.dead = True
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
    # Main Loop
    # ==================================

    def timerEvent(self, event):
        """The game's main loop.
        Called every tick by active timer attribute of the board.
        """
        # TODO use delta-time to interpolate visuals

        self.time_stamp += 1

        self.handle_keys_with_state()

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


class DataRobot(BaseRobot):
    """Data representation of the robots for the server."""

    def __init__(self, base_robot: BaseRobot, thread_robot: ThreadRobot):

        super().__init__(**vars(base_robot))

        # current position
        self.x = 0
        self.y = 0
        self.alpha = 0

        self.v = 0
        self.v_alpha = 0

        self.gun = None

        # Only some robots should receive an alert message.
        self.alert_flag = False

        self.thread_robot = thread_robot

        self.player_control = None
        self.player_control_active = False

        # Use this when respawning the robot
        self.dead = False
        self.immune = False
        self.life = self.max_life

        # Access management system:
        self.player_input_enabled = True         # inactive TODO
        self.player_output_enabled = False
        self.robot_input_enabled = True
        self.robot_output_enabled = True

        # self.player_gun_access = False
        # self.robot_gun_access = True
        self.gun_enabled = False

    def place_robot(self, x, y, alpha, v, v_alpha):

        self.x = x
        self.y = y
        self.alpha = alpha

        self.v = v
        self.v_alpha = v_alpha

        # pos = (x, y, alpha, v, v_alpha)
        # m = SensorData(SensorData.POSITION_STRING, pos, -1)
        # self.thread_robot.receive_sensor_data(m)

    def start(self):
        self.thread_robot.run()

    # Interface functions for the robot
    # TODO allow hybrid models
    def poll_action_data(self):

        if self.player_output_enabled:
            return self.player_control.send_action_data()

        if self.robot_output_enabled:
            return self.thread_robot.send_action_data()

        # maybe adapt default data?
        default_data = (0, 0)
        return default_data

    def send_sensor_data(self, data):
        if self.robot_input_enabled:
            self.thread_robot.receive_sensor_data(data)

    # damage and respawn
    def deal_damage(self, damage=1):
        # we don't deal damage to dead or immune units
        if self.immune or self.dead:
            return

        self.life = max(0, self.life - damage)
        if self.life <= 0:
            self.get_destroyed()

    def get_destroyed(self):
        self.dead = True

        self.v = 0
        self.v_alpha = 0

        self.disable_robot_control()
        self.disable_player_control()
        self.disable_gun()

        def respawn():
            self.respawn()

        Utils.execute_after(self.respawn_timer, respawn)

    def respawn(self):
        self.life = self.max_life
        self.immune = True
        point = self.x, self.y
        Board.teleport_furthest_corner(point, self)

        if self.player_control_active:
            self.hand_control_to_player()
        else:
            self.hand_control_to_robot()

        self.enable_gun()

        self.dead = False

        def disable_immunity():
            self.immune = False

        Utils.execute_after(1, disable_immunity)

    # gun stuff
    def perform_shoot_action(self):
        """Will return a valid bullet, if the robot is shooting.
        Else returns False.
        """

        maybe_bullet = False

        if not self.gun or not self.gun_enabled:
            return maybe_bullet

        maybe_data = self.gun.trigger_fire()
        if maybe_data:
            angle = self.alpha

            angle_vector = Utils.vector_from_angle(angle)
            robot_center = (self.x, self.y)
            bullet_start = robot_center + (self.radius + 1) * angle_vector
            # bullet_start = (int(bullet_start[0]), int(bullet_start[1]))

            # prevent bullets from standing still while moving backwards
            speed = max(0, self.v) + maybe_data

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

        self.enable_gun()

        if self.player_control:
            self.player_control.setup_gun(gun)

    # player control
    def enter_key_action(self, key, state=None):
        if self.player_control:
            self.player_control.calculate_key_action(key, state)

    def finish_key_actions(self):
        if self.player_control:
            self.player_control.enter_entwined_keys()

    def invasive_control(self, v_alpha):
        if self.player_output_enabled:
            self.v_alpha = v_alpha

    def setup_player_control(self, player_control=None,
                             control_scheme=None):
        if not player_control:
            if not control_scheme:
                control_scheme = ControlScheme.default_scheme
            player_control = PlayerControl(self, control_scheme)
        self.player_control = player_control

        if self.gun:
            self.player_control.setup_gun(self.gun)

        self.hand_control_to_player()

    def toggle_player_control(self):
        # we can't toggle while dead
        if self.dead:
            return

        if self.player_control_active:
            self.hand_control_to_robot()
        else:
            self.hand_control_to_player()

    # right management
    def hand_control_to_player(self):
        # withdraw the rights for the robot
        self.disable_robot_control()
        self.disable_robot_gun_access()

        # give the rights to the player
        self.enable_player_control()
        self.enable_player_gun_access()

        # notify server, set the state
        self.player_control_active = True

    def hand_control_to_robot(self):
        # withdraw rights of the player
        self.disable_player_control()
        self.disable_player_gun_acess()

        # give the rights to the robot
        self.enable_robot_control()
        self.enable_robot_gun_access()

        # notify server, set the state
        self.player_control_active = False

    def disable_robot_control(self):
        self.robot_output_enabled = False
        self.robot_input_enabled = False

        self.thread_robot.clear_input()

    def enable_robot_control(self):
        self.thread_robot.clear_input()
        self.thread_robot.clear_values()
        self.robot_input_enabled = True
        self.robot_output_enabled = True

    def disable_player_control(self):
        self.player_output_enabled = False

    def enable_player_control(self):
        self.player_output_enabled = True

    def disable_robot_gun_access(self):
        if self.gun:
            self.gun.set_gun_access_robot(False)
            # self.robot_gun_access = False
            self.gun.clear_input()

    def enable_robot_gun_access(self):
        if self.gun:
            self.gun.clear_input()
            self.gun.set_gun_access_robot(True)
            # self.robot_gun_access = True

    def disable_player_gun_acess(self):
        if self.gun:
            self.gun.set_gun_access_player(False)
            # self.player_gun_access = False
            self.gun.clear_input()

    def enable_player_gun_access(self):
        if self.gun:
            self.gun.clear_input()
            self.gun.set_gun_access_player(True)
            # self.player_gun_access = True

    def disable_gun(self):
        self.gun_enabled = False
        self.disable_player_gun_acess()
        self.disable_robot_gun_access()

    def enable_gun(self):
        self.gun_enabled = True
        if self.player_control_active:
            self.enable_player_gun_access()
        else:
            self.enable_robot_gun_access()

    # optional flags
    def set_alert_flag(self, value=True):
        self.alert_flag = value

    def set_resync_flag(self, value=True):
        self.thread_robot.set_resync_flag(value)


class PlayerControl:
    ACCEL_AMT = 3
    ALPHA_ACCEL_AMT = 5

    STATE_ACTIVE = "A"
    STATE_PUSH = "D"
    STATE_INACTIVE = "I"

    STATE_SWITCH = {(STATE_ACTIVE, True): STATE_ACTIVE,
                    (STATE_INACTIVE, True): STATE_PUSH,
                    (STATE_PUSH, True): STATE_ACTIVE,
                    (STATE_ACTIVE, False): STATE_INACTIVE,
                    (STATE_INACTIVE, False): STATE_INACTIVE,
                    (STATE_PUSH, False): STATE_INACTIVE}

    def __init__(self, data_robot, control_scheme, accel_amt=None,
                 alpha_accel_amt=None, invasive_controls=False):

        self.control_scheme = control_scheme

        self.gun = None
        self.data_robot = data_robot

        self.a = 0
        self.a_alpha = 0

        # Smoothness of controls.
        if not accel_amt:
            accel_amt = PlayerControl.ACCEL_AMT
        self.accel_amt = accel_amt
        if not alpha_accel_amt:
            alpha_accel_amt = PlayerControl.ALPHA_ACCEL_AMT
        self.alpha_accel_amt = alpha_accel_amt

        self.allow_toggle_autopilot = True

        # State Machine for acc-rev_acc entwinement
        self.acc_state = PlayerControl.STATE_INACTIVE
        self.acc_rev_state = PlayerControl.STATE_INACTIVE

        def acc():
            self.a = self.accel_amt

        def rev_acc():
            self.a = -1 * self.accel_amt

        def clear_acc():
            self.a = 0

        def acc_pass():
            pass

        self.acc_lookup = {(PlayerControl.STATE_INACTIVE, PlayerControl.STATE_INACTIVE): clear_acc,
                           (PlayerControl.STATE_INACTIVE, PlayerControl.STATE_ACTIVE): rev_acc,
                           (PlayerControl.STATE_INACTIVE, PlayerControl.STATE_PUSH): rev_acc,
                           (PlayerControl.STATE_ACTIVE, PlayerControl.STATE_INACTIVE): acc,
                           (PlayerControl.STATE_ACTIVE, PlayerControl.STATE_ACTIVE): acc_pass,
                           (PlayerControl.STATE_ACTIVE, PlayerControl.STATE_PUSH): rev_acc,
                           (PlayerControl.STATE_PUSH, PlayerControl.STATE_INACTIVE): acc,
                           (PlayerControl.STATE_PUSH, PlayerControl.STATE_ACTIVE): acc,
                           (PlayerControl.STATE_PUSH, PlayerControl.STATE_PUSH): acc}

        # State Machine for left-right entwinement
        self.left_state = PlayerControl.STATE_INACTIVE
        self.right_state = PlayerControl.STATE_INACTIVE

        def lr_left():
            if invasive_controls:
                self.data_robot.invasive_control(
                    v_alpha=-1 * self.alpha_accel_amt)
            else:
                self.a_alpha = - 1 * self.alpha_accel_amt

        def lr_right():
            if invasive_controls:
                self.data_robot.invasive_control(v_alpha=self.alpha_accel_amt)
            else:
                self.a_alpha = self.alpha_accel_amt

        def clear_lr():
            if invasive_controls:
                self.data_robot.invasive_control(v_alpha=0)
            else:
                self.a_alpha = 0

        def lr_pass():
            pass

        self.lr_lookup = {
            (PlayerControl.STATE_INACTIVE, PlayerControl.STATE_INACTIVE): clear_lr,
            (PlayerControl.STATE_INACTIVE, PlayerControl.STATE_ACTIVE): lr_right,
            (PlayerControl.STATE_INACTIVE, PlayerControl.STATE_PUSH): lr_right,
            (PlayerControl.STATE_ACTIVE, PlayerControl.STATE_INACTIVE): lr_left,
            (PlayerControl.STATE_ACTIVE, PlayerControl.STATE_ACTIVE): lr_pass,
            (PlayerControl.STATE_ACTIVE, PlayerControl.STATE_PUSH): lr_right,
            (PlayerControl.STATE_PUSH, PlayerControl.STATE_INACTIVE): lr_left,
            (PlayerControl.STATE_PUSH, PlayerControl.STATE_ACTIVE): lr_left,
            (PlayerControl.STATE_PUSH, PlayerControl.STATE_PUSH): clear_lr}

    def calculate_key_action(self, key, state):
        action_name = self.control_scheme[key]
        action = getattr(self, action_name)
        # stateless
        # TODO distinguish between stateles keys and keys with state
        if state is None:
            action()
        else:
            action(state_active=state)

    def enter_entwined_keys(self):
        self.enter_accelarate()
        self.enter_left_right()

    def accelerate(self, state_active):
        lookup_tuple = (self.acc_state, state_active)
        self.acc_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def accelerate_reverse(self, state_active):
        lookup_tuple = (self.acc_rev_state, state_active)
        self.acc_rev_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def enter_accelarate(self):
        lookup_tuple = (self.acc_state, self.acc_rev_state)
        func = self.acc_lookup[lookup_tuple]
        func()

    def left(self, state_active):
        lookup_tuple = (self.left_state, state_active)
        self.left_state = PlayerControl.STATE_SWITCH[lookup_tuple]
        # if state_active:
        #     self.a_alpha = -1 * self.alpha_accel_amt
        # else:
        #     self.a_alpha = 0
        # new_a_alpha = max(self.a_alpha - self.alpha_accel_amt, -
        #                   1 * self.data_robot.a_alpha_max)
        # self.a_alpha = new_a_alpha

    def right(self, state_active):
        lookup_tuple = (self.right_state, state_active)
        self.right_state = PlayerControl.STATE_SWITCH[lookup_tuple]
        # if state_active:
        #     self.a_alpha = self.alpha_accel_amt
        # else:
        #     self.a_alpha = 0
        # new_a_alpha = min(self.a_alpha + self.alpha_accel_amt,
        #                   self.data_robot.a_alpha_max)
        # self.a_alpha = new_a_alpha

    def enter_left_right(self):
        lookup_tuple = (self.left_state, self.right_state)
        func = self.lr_lookup[lookup_tuple]
        func()

    def shoot(self, state_active):
        if state_active:
            self.gun.prepare_fire_player()

    def toggle_autopilot(self):
        if self.allow_toggle_autopilot:
            self.data_robot.toggle_player_control()

            def enable_toggle():
                self.allow_toggle_autopilot = True

            self.allow_toggle_autopilot = False
            Utils.execute_after(0.5, enable_toggle)

    def send_action_data(self):
        return self.a, self.a_alpha

    def setup_gun(self, gun):
        self.gun = gun


class ControlScheme:
    ACC_STRING = 'accelerate'
    ACC_REV_STRING = 'accelerate_reverse'
    LEFT_STRING = 'left'
    RIGHT_STRING = 'right'
    SHOOT_STRING = 'shoot'
    AUTOPILOT_STRING = 'toggle_autopilot'

    default_scheme = {Qt.Key_W: ACC_STRING,
                      Qt.Key_S: ACC_REV_STRING,
                      Qt.Key_A: LEFT_STRING,
                      Qt.Key_D: RIGHT_STRING,
                      Qt.Key_J: SHOOT_STRING,
                      Qt.Key_P: AUTOPILOT_STRING}

    player_two_scheme = {Qt.Key_Up: ACC_STRING,
                         Qt.Key_Down: ACC_REV_STRING,
                         Qt.Key_Left: LEFT_STRING,
                         Qt.Key_Right: RIGHT_STRING,
                         Qt.Key_Return: SHOOT_STRING,
                         Qt.Key_End: AUTOPILOT_STRING}


class Bullet:
    def __init__(self, position, speed, direction):
        self.position = position
        self.speed = speed
        self.direction = direction


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    sys.exit(app.exec_())
