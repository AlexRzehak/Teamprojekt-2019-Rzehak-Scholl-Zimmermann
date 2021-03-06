import random
import math

# ==================================
# Movement
# ==================================
#
# In this file, you will find the pre-defined movement AIs.
# An AI implements responses to sensor data messages, reacting to data sent
# by the server. The AI's main taks is to determine acceleration values,
# that will be preccessed by the server, thus moving the robot.
# The AIs have access to the RobotControl object and any tool provided by it.
#
# CHANGE HERE:
# - ADD a new AI
# - Change responses of existing AIs


# Name of the target option for the config parser.
TARGET_OPTION_STRING = 'target'


class Movement:
    """Implement different movement responses."""

    # Default movement does not need to receive alert messages.
    # Movement AIs that want to receive alert messages override this.
    RECEIVE_ALERT = False
    # Default movement has no additional construction parameters.
    # Movements with additional constructor parameters add these parameters
    # in their respective list in the right order for the config parser.
    OPTIONS = []

    def default(self, data, robot):
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        return 0, 0

    def vision(self, data, robot):
        return robot.a, robot.a_alpha

    def alert(self, data, robot):
        return robot.a, robot.a_alpha


class RandomMovement(Movement):
    """Sets a and alpha to random values."""

    def position(self, data, robot):

        x, y, alpha, v, v_alpha = data

        if v < 15:
            a = 1
            a_alpha = random.randint(-20, 20)
        else:
            a = 0
            a_alpha = random.randint(-20, 20)
        return a, a_alpha


class NussschneckeMovement(Movement):
    """Accelerates to a certain speed while turning,
    then retains speed and turning speed."""

    def position(self, data, robot):

        x, y, alpha, v, v_alpha = data

        if v < 7:
            a = 0.5
            a_alpha = 1
            return a, a_alpha
        else:
            a = 0
            a_alpha = 0
        return a, a_alpha


class SpiralMovement(Movement):
    """Accelerates to a certain speed while turning,
    then keeps accelerating while retaining turn speed."""

    def position(self, data, robot):

        x, y, alpha, v, v_alpha = data

        if v < 20:
            a = 1
            a_alpha = 1
            return a, a_alpha
        else:
            a = 1
            a_alpha = 0
        return a, a_alpha


class SpinMovement(Movement):
    """Keeps accelerating to a set speed."""

    def position(self, data, robot):

        x, y, alpha, v, v_alpha = data

        a = 0
        a_alpha = math.inf
        if v_alpha > 30:
            a = 0
            a_alpha = 0
        return a, a_alpha


class FollowMovement(Movement):
    """Follows a given robot."""

    RECEIVE_ALERT = True
    OPTIONS = [TARGET_OPTION_STRING]

    def __init__(self, target):
        self.target = target

    def alert(self, data, robot):
        # setting robot destination to the coordinates of target robot
        robot.destination = data[self.target]
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha = data

        # setting the robots destination
        if not robot.destination:
            destination_x = x
            destination_y = y
        else:
            destination_x = robot.destination[0]
            destination_y = robot.destination[1]

        obj_position = (destination_x, destination_y)

        # simplifying alpha and velocity
        alpha = alpha % 360
        if v == 0:
            v = 0.00001

        # calculating velocity vector
        velocity_vector = calculate_vector(v, alpha)
        velocity_vector_magnitude = math.sqrt(
            velocity_vector[0] ** 2 + velocity_vector[1] ** 2)

        # calculating vector between robot and destination
        destination_vector = calculate_vector_between_points(
            obj_position, x, y)
        destination_vector_magnitude = math.sqrt(
            destination_vector[0] ** 2 + destination_vector[1] ** 2)

        # calculating the value of the angle_change needed
        destination_alpha_degree = calculate_destination_alpha(
            velocity_vector, destination_vector, velocity_vector_magnitude,
            destination_vector_magnitude)

        # determining direction and sign of turning angle
        direction = calculate_direction(velocity_vector, destination_vector)
        delta_alpha = set_angle_sign(destination_alpha_degree, direction)

        # setting a to accelerate to its top speed
        v_max = 15
        a = set_acceleration(v, v_max)
        # setting a_alpha values
        a_alpha = set_angle_acceleration(
            direction, delta_alpha, v_alpha, robot)

        return a, a_alpha


class RandomTargetMovement(Movement):
    """Moves towards a target, which is randomly generated with every alert."""

    RECEIVE_ALERT = True

    def alert(self, data, robot):
        # setting robot destination to the coordinates of target robot
        robot.destination = (random.randint(10, 990), random.randint(10, 990))
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha = data

        # setting the robots destination
        if not robot.destination:
            destination_x = x
            destination_y = y
            return robot.a, robot.a_alpha
        else:
            destination_x = robot.destination[0]
            destination_y = robot.destination[1]
        obj_position = (destination_x, destination_y)

        # simplifying alpha and velocity
        alpha = alpha % 360
        if v == 0:
            v = 0.00001

        # calculating velocity vector
        velocity_vector = calculate_vector(v, alpha)
        velocity_vector_magnitude = math.sqrt(
            velocity_vector[0] ** 2 + velocity_vector[1] ** 2)

        # calculating vector between robot and destination
        destination_vector = calculate_vector_between_points(
            obj_position, x, y)
        destination_vector_magnitude = math.sqrt(
            destination_vector[0] ** 2 + destination_vector[1] ** 2)

        # calculating the value of the angle_change needed
        destination_alpha_degree = calculate_destination_alpha(
            velocity_vector, destination_vector, velocity_vector_magnitude,
            destination_vector_magnitude)

        # determining direction and sign of turning angle
        direction = calculate_direction(velocity_vector, destination_vector)
        delta_alpha = set_angle_sign(destination_alpha_degree, direction)

        # setting a to accelerate to its top speed
        v_max = 15
        a = set_acceleration(v, v_max)
        # setting a_alpha values
        a_alpha = set_angle_acceleration(
            direction, delta_alpha, v_alpha, robot)

        return a, a_alpha


class SimpleAvoidMovement(Movement):
    """Moves straight and avoids objects in the field of view."""

    def vision(self, data, robot):
        robot.destination = prime_object(data)
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha, = data
        if v == 0:
            v = 0.001
        v_max = 10
        tile_size = 10
        obj_position = robot.destination[0]
        obj_coordinates = (
            obj_position[0] * tile_size + 5, obj_position[1] * tile_size + 5)

        # determine object type and distance
        obj_type, obj_distance = set_object_info(robot)

        # calculate object angle
        obj_angle = calculate_angle_between_vectors(
            obj_coordinates, x, y, v, alpha)

        # calculate vectors
        velocity_vector = calculate_vector(v, alpha)
        object_vector = calculate_vector_between_points(obj_coordinates, x, y)

        # set Threshold
        threshold = calculate_threshold(
            obj_type, v, alpha, v_alpha, v_max, robot)

        # getting information about angle and direction
        turn_direction = calculate_direction(object_vector, velocity_vector)
        delta_alpha = set_delta_alpha(obj_type, obj_distance, threshold,
                                      obj_angle, turn_direction, v_alpha)

        # setting a values for a and a_alpha
        a = set_acceleration(v, v_max)
        a_alpha = set_angle_acceleration(
            turn_direction, delta_alpha, v_alpha, robot)

        return a, a_alpha


class RunMovement(Movement):
    """Turns away from closest robot or close objects."""

    RECEIVE_ALERT = True

    def __init__(self):
        self.current_threat = None

    def alert(self, data, robot):
        self.current_threat = prime_robot(data)
        return robot.a, robot.a_alpha

    def vision(self, data, robot):
        robot.destination = prime_object(data)
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha, = data
        if v == 0:
            v = 0.001
        v_max = 10
        tile_size = 10

        # calculate object data
        obj_position = robot.destination[0]
        obj_coordinates = (
            obj_position[0] * tile_size + 5, obj_position[1] * tile_size + 5)
        obj_angle = calculate_angle_between_vectors(
            obj_coordinates, x, y, v, alpha)
        # determine object type and distance
        obj_type, obj_distance = set_object_info(robot)

        # calculate robot data
        threat = self.current_threat
        if threat is None:
            threat = robot.destination

        threat_coordinates = threat[0]
        threat_angle = calculate_angle_between_vectors(
            threat_coordinates, x, y, v, alpha)

        # calculate vectors
        velocity_vector = calculate_vector(v, alpha)
        object_vector = calculate_vector_between_points(obj_coordinates, x, y)
        threat_vector = (threat_coordinates[0]-x, threat_coordinates[1]-y)

        # set Threshold
        threshold = calculate_threshold(
            obj_type, v, alpha, v_alpha, v_max, robot)

        # getting information about angle and direction
        turn_direction = calculate_direction(object_vector, velocity_vector)
        threat_turn_direction = calculate_direction(
            threat_vector, velocity_vector)
        delta_alpha = set_run_delta_alpha(obj_type, obj_distance, threshold,
                                          obj_angle, turn_direction,
                                          v_alpha, threat_angle,
                                          threat_turn_direction)

        # setting a values for a and a_alpha
        a = set_acceleration(v, v_max)
        a_alpha = set_angle_acceleration(
            turn_direction, delta_alpha, v_alpha, robot)

        return a, a_alpha


class ChaseMovement(Movement):
    """Moves to given robot, searches if it is not in vision."""

    OPTIONS = [TARGET_OPTION_STRING]

    def __init__(self, target):
        self.target = target

    def vision(self, data, robot):
        robot.destination = search(data, self.target)
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha, = data
        target_bot = robot.destination
        if type(target_bot) == bool:
            # set values to look around
            a = 0
            if v_alpha < 0 and abs(v_alpha) < robot.a_alpha_max:
                a_alpha = - 1
            elif v_alpha >= 0 and abs(v_alpha) < robot.a_alpha_max:
                a_alpha = 1
            elif abs(v_alpha) >= robot.a_alpha_max:
                a_alpha = 0
        else:
            a, a_alpha = position_destination_robot(self, data, robot)
            robot.destination = None

        return a, a_alpha


class ChaseMovementGun(Movement):
    """Moves to given robot, searches if it is not in vision.
    Shoots if target is straight ahead."""

    OPTIONS = [TARGET_OPTION_STRING]

    def __init__(self, target):
        self.target = target

    def vision(self, data, robot):
        robot.destination = search(data, self.target)
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha, = data
        # execute shoot behaviour
        shoot_straight(robot, data)
        target_bot = robot.destination
        if type(target_bot) == bool:
            a = 0
            if v_alpha < robot.a_alpha_max:
                a_alpha = 1
            elif v_alpha >= robot.a_alpha_max:
                a_alpha = 0
        else:
            a, a_alpha = position_destination_robot(self, data, robot)
            robot.destination = None

        return a, a_alpha


class SimpleAvoidMovementGun(Movement):
    """Moves straight and avoids objects in the field of view.
    Shoots if target is straight ahead."""

    def vision(self, data, robot):
        robot.destination = prime_object(data)
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        x, y, alpha, v, v_alpha, = data

        if v == 0:
            v = 0.001
        v_max = 10
        tile_size = 10

        obj_position = robot.destination[0]
        obj_coordinates = (
            obj_position[0] * tile_size + 5, obj_position[1] * tile_size + 5)
        # determine object type and distance
        obj_type, obj_distance = set_object_info(robot)

        # calculate object angle
        obj_angle = calculate_angle_between_vectors(
            obj_coordinates, x, y, v, alpha)

        # calculate vectors
        velocity_vector = calculate_vector(v, alpha)
        object_vector = calculate_vector_between_points(obj_coordinates, x, y)

        # set Threshold
        threshold = calculate_threshold(
            obj_type, v, alpha, v_alpha, v_max, robot)

        # getting information about angle and direction
        turn_direction = calculate_direction(object_vector, velocity_vector)
        delta_alpha = set_delta_alpha(obj_type, obj_distance, threshold,
                                      obj_angle, turn_direction, v_alpha)

        # setting a values for a and a_alpha
        a = set_acceleration(v, v_max)
        a_alpha = set_angle_acceleration(
            turn_direction, delta_alpha, v_alpha, robot)

        # execute shoot behaviour
        if obj_type == "robot":
            shoot_straight(robot, data)

        return a, a_alpha


class PermanentGunMovement(RandomTargetMovement):
    """Shoots as much as possible, while moving randomly."""

    def position(self, data, robot):
        robot.shoot()
        return super().position(data, robot)


class ChaseAvoidMovement(Movement):
    """Moves to given robot, searches if it is not in vision.
    Avoids close objects."""

    OPTIONS = [TARGET_OPTION_STRING]

    def __init__(self, target):
        self.target = target

    def vision(self, data, robot):
        # determine if a obstacle needs to be avoided
        dist_index = len(prime_object(data)) - 1
        obj_dist = prime_object(data)[dist_index]
        is_wall = (dist_index == 2)
        act_dist = 100
        if is_wall:
            avoid = (obj_dist < act_dist)
        else:
            avoid = False

        # case AvoidMovement
        if avoid:
            robot.destination = prime_object(data)
            return robot.a, robot.a_alpha
        # case ChaseMovement
        else:
            robot.destination = search(data, self.target)
            return robot.a, robot.a_alpha

    def position(self, data, robot):
        # determine whether destination is a target or obstacle
        if type(robot.destination) == bool:
            destination_type = "target"
        elif len(robot.destination) == 2:
            destination_type = "target"
        else:
            destination_type = "obstacle"
        if destination_type == "obstacle":
            a, a_alpha = SimpleAvoidMovement.position(self, data, robot)
        else:
            a, a_alpha = ChaseMovement.position(self, data, robot)
        return a, a_alpha


class ChaseAvoidMovementGun(ChaseAvoidMovement):
    """Moves to given robot, searches if it is not in vision.
    Shoots if target is straight ahead, avoids close objects."""

    def position(self, data, robot):
        shoot_straight(robot, data)
        return super().position(data, robot)


# ---------------
# Helper Functions
# ---------------

def calculate_distance(a_x, a_y, b_x, b_y):
    """Calculates distance between points."""
    v_x = b_x - a_x
    v_y = b_y - a_y
    distance = math.sqrt(v_x ** 2 + v_y ** 2)
    return distance


def calc_cross_product(B, P):
    """Calculates cross product."""
    b_x = B[0]
    b_y = B[1]
    p_x = P[0]
    p_y = P[1]

    cp = b_x * p_y - b_y * p_x
    return cp


def calculate_vector(magnitude, angle):
    radian = (angle / 180 * math.pi)
    vector_x = (magnitude * math.sin(radian))
    vector_y = - (magnitude * math.cos(radian))
    vector = (vector_x, vector_y)
    return vector


def calculate_vector_between_points(obj_position, x, y):
    """Calculates vector between 2 points."""
    object_vector_x = obj_position[0] - x
    object_vector_y = obj_position[1] - y
    object_vector = (object_vector_x, object_vector_y)
    return object_vector


def calculate_angle_between_vectors(obj_position, x, y, v, alpha):
    """Calculates the angle between coordinates, represented as vectors."""
    object_vector_x = obj_position[0] - x
    object_vector_y = obj_position[1] - y
    object_vector_mag = math.sqrt(
        object_vector_x ** 2 + object_vector_y ** 2)

    velocity_vector = calculate_vector(v, alpha)
    velocity_vector_x = velocity_vector[0]
    velocity_vector_y = velocity_vector[1]
    velocity_vector_mag = math.sqrt(
        velocity_vector_x ** 2 + velocity_vector_y ** 2)

    vector_multiplication = (velocity_vector_x * object_vector_x +
                             velocity_vector_y * object_vector_y)
    magnitude_multiplication = velocity_vector_mag * object_vector_mag
    if magnitude_multiplication != 0:
        if vector_multiplication / magnitude_multiplication > 1:
            ratio = 1
        elif vector_multiplication / magnitude_multiplication < -1:
            ratio = -1
        else:
            ratio = vector_multiplication / magnitude_multiplication

        if magnitude_multiplication == 0:
            obj_alpha = 0
        else:
            obj_alpha = math.acos(ratio)
    else:
        obj_alpha = 0
    obj_angle = (obj_alpha * 180 / math.pi) % 360
    return obj_angle


def calculate_direction(main_vector, second_vector):
    """Calculates in which relative direction the second vector points."""

    cross_product = calc_cross_product(
        (main_vector[0], main_vector[1]),
        (second_vector[0], second_vector[1]))

    if cross_product > 0:
        direction = "right"
    elif cross_product < 0:
        direction = "left"
    elif cross_product == 0:
        direction = "none"
    return direction


def calculate_threshold(obj_type, v, alpha, v_alpha, v_max, robot):
    """Calculate the distance to an object at which the robot starts acting."""

    if obj_type == "wall":
        delta_alpha = 90
        obj_size = 10
        obj_r = math.sqrt(2) * obj_size
    elif obj_type == "robot":
        delta_alpha = 180
        enemy_radius = 50 + v_max
        obj_r = enemy_radius
    delta_alpha_per_unit = abs(robot.a_alpha_max / v_max)
    turn_distance = (delta_alpha + abs(v_alpha)) * delta_alpha_per_unit
    threshold = turn_distance + 2 * robot.radius + obj_r
    # post processing
    threshold = threshold / 1.5
    return threshold


def calculate_destination_alpha(vec1, vec2, vec1_magnitude, vec2_magnitude):
    vector_multiplication = (vec1[0] * vec2[0] +
                             vec1[1] * vec2[1])
    magnitude_multiplication = vec1_magnitude * vec2_magnitude
    if magnitude_multiplication != 0:
        if -1 < vector_multiplication / magnitude_multiplication < 1:
            destination_alpha = math.acos(
                vector_multiplication / magnitude_multiplication) - 0.01
        else:
            destination_alpha = 0
    elif magnitude_multiplication == 0:
        destination_alpha = 0
    destination_alpha_degree = (destination_alpha * 180 / math.pi) % 360
    return destination_alpha_degree


def set_object_info(robot):
    """Interprets destination to determine object type and distance."""
    if (robot.destination[1] == 1 or
        robot.destination[1] == 2 or
            robot.destination[1] == 3):

        obj_type = "wall"
        obj_distance = robot.destination[2]
    else:
        obj_type = "robot"
        obj_distance = robot.destination[1]
    return obj_type, obj_distance


def set_delta_alpha(obj_type, distance, threshold,
                    obj_angle, turn_direction, v_alpha):
    """Set delta_alpha based on obstacle type and distance."""

    absolute_delta_alpha = 10
    if obj_type == "wall":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = absolute_delta_alpha
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - absolute_delta_alpha
        else:
            delta_alpha = 0
    if obj_type == "robot":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = (180 - abs(obj_angle))
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - (180 - abs(obj_angle))
        else:
            delta_alpha = 0
    return delta_alpha


def set_run_delta_alpha(obj_type, distance, threshold, obj_angle,
                        turn_direction, v_alpha,
                        threat_angle, threat_turn_direction):
    """Set delta_alpha based on obstacle and threat."""

    absolute_delta_alpha = 20
    if obj_type == "wall":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = absolute_delta_alpha
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - absolute_delta_alpha
        elif distance <= threshold and turn_direction == "none":
            delta_alpha = 0

    if obj_type == "robot":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = (180 - abs(obj_angle))
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - (180 - abs(obj_angle))
        elif distance <= threshold and turn_direction == "none":
            delta_alpha = 0

    smoothifier = (180 - threat_angle)/180
    if distance > threshold:
        if threat_turn_direction == "right":
            delta_alpha = 20 * smoothifier
        elif threat_turn_direction == "left":
            delta_alpha = - 20 * smoothifier
        elif threat_turn_direction == "none":
            delta_alpha = 0

    return delta_alpha


def set_angle_sign(angle, direction):
    """Gives a sign to the angle based on turning direction."""

    if direction == "right":
        signed_angle = angle
    elif direction == "left":
        signed_angle = - angle
    elif direction == "none":
        signed_angle = angle
    return signed_angle


def set_angle_acceleration(direction, delta_alpha, v_alpha, robot):
    """Setting a_alpha values."""

    a_alpha_max = robot.a_alpha_max
    if direction == "right":
        if delta_alpha >= a_alpha_max + v_alpha:
            a_alpha = a_alpha_max
        elif delta_alpha < a_alpha_max + v_alpha:
            a_alpha = delta_alpha - v_alpha

    elif direction == "left":
        if abs(delta_alpha) >= abs(a_alpha_max - v_alpha):
            a_alpha = - a_alpha_max
        elif abs(delta_alpha) < abs(a_alpha_max - v_alpha):
            a_alpha = -(abs(delta_alpha)) + abs(v_alpha)

    elif direction == "none":
        a_alpha = 0.01

    return a_alpha


def set_acceleration(velocity, v_max):
    """Setting a to accelerate to a speed of v_max."""

    if velocity < v_max:
        a = 1
    else:
        a = 0
    return a


def search(array_tuple, pos):
    """Takes robot out of array of robots.
    Returns false if the robot is not in the robot array."""
    robot_array = array_tuple[1]
    found_bot = robot_array[pos]
    return found_bot


def prime_object(array_tuple):
    """Identifies the most significant object of an object array."""

    robot_array = array_tuple[1]
    obstacle_array = array_tuple[0]
    significance = math.inf
    index_of_obj = 0
    type_of_obj = 0
    robot_multiplier = 1

    for i in range(len(obstacle_array)):
        obj_distance = obstacle_array[i][2]
        if obj_distance < significance and obj_distance:
            significance = obj_distance
            index_of_obj = i
            type_of_obj = 0

    for i in range(len(robot_array)):
        if type(robot_array[i]) == tuple:
            obj_significance = robot_array[i][1] * robot_multiplier
            if obj_significance < significance and obj_significance > 0:
                significance = obj_significance
                index_of_obj = i
                type_of_obj = 1

    significant_object = array_tuple[type_of_obj][index_of_obj]
    return significant_object


def prime_robot(array):
    """Identifies the most significant robot of a robot array."""

    distance_array = []
    robot_x = array[0][0]
    robot_y = array[0][1]
    for i in range(len(array)):
        distance_array.append(calculate_distance(
            robot_x, robot_y, array[i][0], array[i][1]))
    significance = math.inf
    significant_index = 1
    for i in range(len(distance_array)):
        if distance_array[i] < significance and distance_array[i] > 0:
            significance = distance_array[i]
            significant_index = i
    significant_robot = (array[significant_index],
                         distance_array[significant_index])
    return significant_robot


def print_info(boolean, velocity_vector, object_vector, threshold,
               turn_direction, delta_alpha, a, a_alpha,
               obj_distance, obj_angle, robot):

    if boolean:
        print("Object: " + str(robot.destination))
        print("Vv: " + str(velocity_vector))
        print("Ov: " + str(object_vector))
        print("obj_angle: " + str(obj_angle))
        print("distance: " + str(obj_distance))
        print("threshold: " + str(threshold))
        print("turn_direction: " + str(turn_direction))
        print("delta_alpha: " + str(delta_alpha))
        print("a: " + str(a))
        print("a_alpha: " + str(a_alpha))
        print("-------------------------")


def position_destination_robot(self, data, robot):
    """Sets acceleration and angle_acceleration to move towards a robot,
    that is stored in destination."""

    x, y, alpha, v, v_alpha = data

    # setting the robots destination
    if not robot.destination:
        destination_x = x
        destination_y = y
    else:
        destination_x = robot.destination[0][0]
        destination_y = robot.destination[0][1]
    obj_position = (destination_x, destination_y)
    if v == 0:
        v = 0.00001

    # calculating velocity vector
    velocity_vector = calculate_vector(v, alpha)
    velocity_vector_magnitude = math.sqrt(
        velocity_vector[0] ** 2 + velocity_vector[1] ** 2)

    # calculating vector between robot and destination
    destination_vector = calculate_vector_between_points(obj_position, x, y)
    destination_vector_magnitude = math.sqrt(
        destination_vector[0] ** 2 + destination_vector[1] ** 2)

    # calculating the value of the angle_change needed
    destination_alpha_degree = calculate_destination_alpha(
        velocity_vector, destination_vector, velocity_vector_magnitude,
        destination_vector_magnitude)

    # determining direction and sign of turning angle
    direction = calculate_direction(velocity_vector, destination_vector)
    delta_alpha = set_angle_sign(destination_alpha_degree, direction)

    # setting a to accelerate to its top speed
    v_max = 15
    a = set_acceleration(v, v_max)
    # setting a_alpha values
    a_alpha = set_angle_acceleration(direction, delta_alpha, v_alpha, robot)

    return a, a_alpha


# Shooting behaviours:
# ====================

def shoot_straight(robot, data):
    """Enqueues a shot if aim is crosses target robot."""

    x, y, alpha, v, v_alpha = data
    if type(robot.destination) == tuple:
        coordinates = robot.destination[0]
        angle = calculate_angle_between_vectors(coordinates, x, y, v, alpha)
        ready = not (robot.is_shooting() or robot.is_reloading())
        if ready and 0.01 < angle <= 90:
            # set acceptable inaccuracy
            max_inaccuracy = robot.radius
            # calculate aim inaccuracy
            inaccuracy = calculate_inaccuracy((x, y), coordinates, alpha, v)
            # decide action
            if inaccuracy <= max_inaccuracy and angle <= 90:
                robot.shoot()


def calculate_inaccuracy(position, coordinates, alpha, vel):
    """Calculates inaccuracy of position, angle and target coordinates."""

    x = position[0]
    y = position[1]
    c_x = coordinates[0]
    c_y = coordinates[1]
    robot_radian = (alpha / 180 * math.pi)

    # get angle between aim direction and target, as radian
    angle = calculate_angle_between_vectors(coordinates, x, y, vel, alpha)
    angle = angle % 360
    target_radian = (angle / 180 * math.pi)

    # calculate distance between position and coordinates
    distance = math.sqrt((c_x-x)**2 + (c_y-y)**2)

    # calculate opposite's length of Triangle
    a = (math.sin(target_radian)*distance)
    b = (math.sin(robot_radian)*distance)
    opp_abs = math.sqrt(a**2 + b**2)

    # calculate inaccuracy
    inaccuracy = math.sin(target_radian) * opp_abs
    return inaccuracy
