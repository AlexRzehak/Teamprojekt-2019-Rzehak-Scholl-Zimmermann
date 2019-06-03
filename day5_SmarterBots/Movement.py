import random
import math


class Movement:

    """Implement different movement options."""

    def default(self, data, robot):
        return robot.a, robot.a_alpha

    def position(self, data, robot):
        return 0, 0

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

        # calculating angle between the velocity vector and the destination vector
        #
        alpha = alpha % 360
        radian = (alpha / 180 * math.pi)
        if v == 0:
            v = 0.00001

        # calculating movement vector
        velocity_vector_x = (v * math.sin(radian))
        velocity_vector_y = - (v * math.cos(radian))
        velocity_vector_magnitude = math.sqrt(velocity_vector_x**2 + velocity_vector_y**2)

        # calculating vector between robot and destination
        destination_vector_x = destination_x - x
        destination_vector_y = destination_y - y
        destination_vector_magnitude = math.sqrt(destination_vector_x**2 + destination_vector_y**2)

        # calculating the value of the angle_change needed
        vector_multiplication = (velocity_vector_x*destination_vector_x + velocity_vector_y*destination_vector_y)
        magnitude_multiplication = velocity_vector_magnitude * destination_vector_magnitude
        destination_alpha = math.acos(vector_multiplication / magnitude_multiplication) - 0.01
        destination_alpha_degree = (destination_alpha * 180 / math.pi) % 360

        # determining direction based on sign of the vectors cross product
        cross_product = FollowMovement.cross_product((velocity_vector_x,velocity_vector_y),(destination_vector_x,destination_vector_y))
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

        # calculating angle between the velocity vector and the destination vector
        #
        alpha = alpha % 360
        radian = (alpha / 180 * math.pi)
        if v == 0:
            v = 0.00001

        # calculating movement vector
        velocity_vector_x = (v * math.sin(radian))
        velocity_vector_y = - (v * math.cos(radian))
        velocity_vector_magnitude = math.sqrt(velocity_vector_x ** 2 + velocity_vector_y ** 2)

        # calculating vector between robot and destination
        destination_vector_x = destination_x - x
        destination_vector_y = destination_y - y
        destination_vector_magnitude = math.sqrt(destination_vector_x ** 2 + destination_vector_y ** 2)

        # calculating the value of the angle_change needed
        vector_multiplication = (velocity_vector_x * destination_vector_x + velocity_vector_y * destination_vector_y)
        magnitude_multiplication = velocity_vector_magnitude * destination_vector_magnitude
        destination_alpha = math.acos(vector_multiplication / magnitude_multiplication) - 0.01
        destination_alpha_degree = (destination_alpha * 180 / math.pi) % 360

        # determining direction based on sign of the vectors cross product
        cross_product = FollowMovement.cross_product((velocity_vector_x, velocity_vector_y),
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