import random
import math


class Movement:
    """Implement different movement options."""

    def default(self, data, robot):
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        return 0, 0

    def vision(self, data, robot):
        return robot.a, robot.a_alpha

    def alert(self, data, robot):
        return robot.a, robot.a_alpha

    def bonk(self, data, robot):
        return robot.a, robot.a_alpha


class RandomMovement(Movement):

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

    def position(self, data, robot):

        x, y, alpha, v, v_alpha = data

        a = 0
        a_alpha = 99999999
        if v_alpha > 30:
            a = 0
            a_alpha = 0
        return a, a_alpha


class FollowMovement(Movement):

    def __init__(self, target):
        self.target = target

    # simple variant without extrapolation

    def alert(self, data, robot):
        # setting robot destination to the coordinates of target robot
        robot.destination = data[self.target]
        return robot.a, robot.a_alpha

        # TODO devision by zero exceptions// sensordata -> position data
        # TODO Follow self error

    def position(self, data, robot):
        x, y, alpha, v, v_alpha = data

        # setting the robots destination
        if not robot.destination:
            destination_x = x
            destination_y = y
        else:
            destination_x = robot.destination[0]
            destination_y = robot.destination[1]

        # calculating angle between the velocity vector
        # and the destination vector
        alpha = alpha % 360
        radian = (alpha / 180 * math.pi)
        if v == 0:
            v = 0.00001

        # calculating movement vector
        velocity_vector_x = (v * math.sin(radian))
        velocity_vector_y = - (v * math.cos(radian))
        velocity_vector_magnitude = math.sqrt(
            velocity_vector_x**2 + velocity_vector_y**2)

        # calculating vector between robot and destination
        destination_vector_x = destination_x - x
        destination_vector_y = destination_y - y
        destination_vector_magnitude = math.sqrt(
            destination_vector_x**2 + destination_vector_y**2)

        # calculating the value of the angle_change needed
        vector_multiplication = (velocity_vector_x*destination_vector_x +
                                 velocity_vector_y*destination_vector_y)
        magnitude_multiplication = velocity_vector_magnitude * destination_vector_magnitude
        destination_alpha = math.acos(
            vector_multiplication / magnitude_multiplication) - 0.01
        destination_alpha_degree = (destination_alpha * 180 / math.pi) % 360

        # determining direction based on sign of the vectors cross product
        cross_product = FollowMovement.cross_product(
            (velocity_vector_x, velocity_vector_y),
            (destination_vector_x, destination_vector_y))
        if cross_product > 0:
            delta_alpha = destination_alpha_degree
            direction = "right"
        elif cross_product < 0:
            delta_alpha = - destination_alpha_degree
            direction = "left"
        elif cross_product == 0:
            delta_alpha = destination_alpha_degree
            direction = "None"

        # setting a to accelerate to a speed of 10
        if v <= 10:
            a = 1
        else:
            a = 0
        # setting a_alpha values
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

        if direction == "none":
            a_alpha = 0.01

        return a, a_alpha

    @staticmethod
    def cross_product(B, P):
        # calculates cross product
        b_x = B[0]
        b_y = B[1]
        p_x = P[0]
        p_y = P[1]

        cp = b_x * p_y - b_y * p_x
        return cp


class RandomTargetMovement(Movement):

    def alert(self, data, robot):
        # setting robot destination to the coordinates of target robot
        robot.destination = (random.randint(10, 990), random.randint(10, 990))
        return robot.a, robot.a_alpha

        # TODO devision by zero exceptions
        # TODO Follow self error

    def position(self, data, robot):
        x, y, alpha, v, v_alpha = data

        # setting the robots destination
        if not robot.destination:
            destination_x = x
            destination_y = y
        else:
            destination_x = robot.destination[0]
            destination_y = robot.destination[1]

        # calculating angle between the velocity vector
        #  and the destination vector
        alpha = alpha % 360
        radian = (alpha / 180 * math.pi)
        if v == 0:
            v = 0.00001

        # calculating movement vector
        velocity_vector_x = (v * math.sin(radian))
        velocity_vector_y = - (v * math.cos(radian))
        velocity_vector_magnitude = math.sqrt(
            velocity_vector_x ** 2 + velocity_vector_y ** 2)

        # calculating vector between robot and destination
        destination_vector_x = destination_x - x
        destination_vector_y = destination_y - y
        destination_vector_magnitude = math.sqrt(
            destination_vector_x ** 2 + destination_vector_y ** 2)

        # calculating the value of the angle_change needed
        vector_multiplication = (velocity_vector_x * destination_vector_x +
                                 velocity_vector_y * destination_vector_y)
        magnitude_multiplication = velocity_vector_magnitude * destination_vector_magnitude
        destination_alpha = math.acos(
            vector_multiplication / magnitude_multiplication) - 0.01
        destination_alpha_degree = (destination_alpha * 180 / math.pi) % 360

        # determining direction based on sign of the vectors cross product
        cross_product = FollowMovement.cross_product(
            (velocity_vector_x, velocity_vector_y),
            (destination_vector_x, destination_vector_y))
        if cross_product > 0:
            delta_alpha = destination_alpha_degree
            direction = "right"
        elif cross_product < 0:
            delta_alpha = - destination_alpha_degree
            direction = "left"
        elif cross_product == 0:
            delta_alpha = destination_alpha_degree
            direction = "None"

        # setting a to accelerate to a speed of 10
        if v <= 10:
            a = 1
        else:
            a = 0
        # setting a_alpha values
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

        if direction == "none":
            a_alpha = 0.01

        return a, a_alpha


class SimpleAvoidMovement(Movement):
    # TODO testing

    def vision(self, data, robot):
        robot.destination = SimpleAvoidMovement.prime_object(data)
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        # TODO get obj_coordinates, obj_type, obj_distance
        x, y, alpha, v, v_alpha, = data
        if v == 0:
            v = 0.001
        v_max = 10
        tile_size = 10
        obj_position = robot.destination[0]
        obj_coordinates = (obj_position[0] * tile_size + 5, obj_position[1] * tile_size + 5)

        if robot.destination[1] == 1 or robot.destination[1] == 2 or robot.destination[1] == 3:
            obj_type = "wall"
            obj_distance = robot.destination[2]
        else:
            obj_type = "robot"
            obj_distance = robot.destination[1]

        # calculate object angle
        obj_angle = SimpleAvoidMovement.calculate_angle_between_vectors(obj_coordinates, x, y, v, alpha)

        # calculate vectors
        velocity_vector = SimpleAvoidMovement.calculate_vector(v, alpha)
        object_vector = SimpleAvoidMovement.calculate_vector_between_points(obj_coordinates, x, y)

        # set Threshold
        threshold = SimpleAvoidMovement.calculate_threshold(obj_type, v, alpha, v_alpha, v_max, robot)

        # getting information about angle and direction
        turn_direction = SimpleAvoidMovement.calculate_direction(object_vector, velocity_vector)
        delta_alpha = SimpleAvoidMovement.set_delta_alpha(obj_type, obj_distance, threshold, obj_angle, turn_direction, v_alpha)

        # setting a values for a and a_alpha
        a = SimpleAvoidMovement.set_acceleration(v, v_max)
        a_alpha = SimpleAvoidMovement.set_angle_acceleration(turn_direction, delta_alpha, v_alpha, robot)

        # print info
        SimpleAvoidMovement.print_info(True, velocity_vector, object_vector, threshold, turn_direction,
                                       delta_alpha, a, a_alpha, obj_distance, obj_angle, robot)
        return a, a_alpha

    @staticmethod
    def prime_object(array_tuple):
        robot_array = array_tuple[1]
        obstacle_array = array_tuple[0]
        significance = math.inf
        index_of_obj = 0
        type_of_obj = 0
        robot_multiplier = 1

        for i in range(len(obstacle_array)):
            # print("obstacle " + str(i) + " distance = " + str(obstacle_array[i][2]))
            obj_distance = obstacle_array[i][2]
            if obj_distance < significance and obj_distance:
                significance = obj_distance
                index_of_obj = i
                type_of_obj = 0

        for i in range(len(robot_array)):
            if type(robot_array[i]) == tuple:
                # print("robot " + str(i) + " distance = " + str(robot_array[i][1]))
                obj_significance = robot_array[i][1] * robot_multiplier
                if obj_significance < significance and obj_significance > 0:
                    significance = obj_significance
                    # print(significance)
                    index_of_obj = i
                    type_of_obj = 1
            # else:
            #    print(f"robot {i} not found")

        significant_object = array_tuple[type_of_obj][index_of_obj]
        # print("significant_object = " + str(significant_object))
        return significant_object

    @staticmethod
    def calculate_angle_between_vectors(obj_position, x, y, v, alpha):
        object_vector_x = obj_position[0] - x
        object_vector_y = obj_position[1] - y
        object_vector_magnitude = math.sqrt(
            object_vector_x ** 2 + object_vector_y ** 2)

        velocity_vector = SimpleAvoidMovement.calculate_vector(v, alpha)
        velocity_vector_x = velocity_vector[0]
        velocity_vector_y = velocity_vector[1]
        velocity_vector_magnitude = math.sqrt(
            velocity_vector_x ** 2 + velocity_vector_y ** 2)

        vector_multiplication = (velocity_vector_x * object_vector_x +
                                 velocity_vector_y * object_vector_y)
        magnitude_multiplication = velocity_vector_magnitude * object_vector_magnitude
        if magnitude_multiplication == 0:
            obj_alpha = 0
        else:
            obj_alpha = math.acos(vector_multiplication / magnitude_multiplication)
        obj_angle = (obj_alpha * 180 / math.pi) % 360
        return obj_angle

    @staticmethod
    def calculate_vector_between_points(obj_position, x, y):
        object_vector_x = obj_position[0] - x
        object_vector_y = obj_position[1] - y
        object_vector = (object_vector_x, object_vector_y)
        return object_vector

    @staticmethod
    def calculate_vector(magnitude, angle):
        radian = (angle / 180 * math.pi)
        vector_x = (magnitude * math.sin(radian))
        vector_y = - (magnitude * math.cos(radian))
        vector = (vector_x, vector_y)
        return vector

    @staticmethod
    def calculate_threshold(obj_type, v, alpha, v_alpha, v_max, robot):
        # distance to object at which the robot starts acting
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
        threshold = turn_distance + 2*robot.radius + obj_r
        # prototyping only
        threshold = threshold / 1.5
        return threshold

    @staticmethod
    def calculate_direction(main_vector, second_vector):
        cross_product = FollowMovement.cross_product(
            (main_vector[0], main_vector[1]),
            (second_vector[0], second_vector[1]))

        if cross_product > 0:
            direction = "right"
        elif cross_product < 0:
            direction = "left"
        elif cross_product == 0:
            direction = "none"
        return direction

    @staticmethod
    def set_delta_alpha(obj_type, distance, threshold, obj_angle, turn_direction, v_alpha):
        # set delta_alpha based on obstacle type and distance
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
            elif distance > threshold:
                delta_alpha = 0
        return delta_alpha

    @staticmethod
    def set_acceleration(velocity, v_max):
        # setting a to accelerate to a speed of v_max
        if velocity < v_max:
            a = 1
        else:
            a = 0
        return a

    @staticmethod
    def set_angle_acceleration(direction, delta_alpha, v_alpha, robot):
        # setting a_alpha values
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

    @staticmethod
    def print_info(boolean,velocity_vector, object_vector, threshold, turn_direction, delta_alpha, a, a_alpha, obj_distance, obj_angle, robot):
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