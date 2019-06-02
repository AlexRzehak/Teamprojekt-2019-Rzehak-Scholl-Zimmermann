import random
import math

class Movement():
    """Implement different movement options."""

    @staticmethod
    def default(data, robot):
        return robot.a, robot.a_alpha

    @staticmethod
    def position(data, robot):
        return 0, 0

    @staticmethod
    def alert(data, robot):
        return robot.a, robot.a_alpha

    @staticmethod
    def bonk(data, robot):
        return robot.a, robot.a_alpha


class RandomMovement(Movement):

    @staticmethod
    def position(data, robot):

        x, y, alpha, v, v_alpha = data

        if v < 15:
            a = 1
            a_alpha = random.randint(-20, 20)
        else:
            a = 0
            a_alpha = random.randint(-20, 20)
        return a, a_alpha


class NussschneckeMovement(Movement):

    @staticmethod
    def position(data, robot):

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

    @staticmethod
    def position(data, robot):

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

    @staticmethod
    def position(data, robot):

        x, y, alpha, v, v_alpha = data

        a = 0
        a_alpha = 99999999
        if v_alpha > 30:
            a = 0
            a_alpha = 0
        return a, a_alpha

class FollowMovement(Movement):

        # TODO devision by zero exceptions// sensordata -> position data
    @staticmethod
    def position(data, robot):
        x, y, alpha, v, v_alpha = data

        if not robot.destination:
            destination_x = x
            destination_y = y
        else:
            destination_x = robot.destination[0]
            destination_y = robot.destination[1]

        # calculating angle between the velocity vector and the destination vector
        alpha = alpha  % 360 # correct
        radian = (alpha / 180 * math.pi) # correct
        if v == 0:
            v = 1
        velocity_vector_x = (v * math.sin(radian)) # correct
        velocity_vector_y = - (v * math.cos(radian)) # correct
        velocity_vector_magnitude = math.sqrt(velocity_vector_x**2 + velocity_vector_y**2) # correct

        destination_vector_x = destination_x - x # correct
        destination_vector_y = destination_y - y # correct
        destination_vector_magnitude = math.sqrt(destination_vector_x**2 + destination_vector_y**2) # correct

        vector_multiplication = (velocity_vector_x*destination_vector_x + velocity_vector_y*destination_vector_y) # correct
        magnitude_multiplication = velocity_vector_magnitude * destination_vector_magnitude # correct
        destination_alpha = math.acos(vector_multiplication / magnitude_multiplication) - 0.00001# correct
        destination_alpha_degree = (destination_alpha * 180 / math.pi) % 360
        # print(str(alpha) + " : " + str(radian))
        # print(velocity_vector_y)
        # print(velocity_vector_magnitude)
        # print(destination_vector_magnitude)
        # print(str(destination_alpha) + "---"+ str(destination_alpha_degree))

        # determining direction
        cross_product = FollowMovement.cross_product((velocity_vector_x,velocity_vector_y),(destination_vector_x,destination_vector_y)) # correct

        if cross_product > 0:
            delta_alpha = destination_alpha_degree
            direction = "right"
        elif cross_product < 0:
            delta_alpha = - destination_alpha_degree
            direction = "left"
        elif cross_product == 0:
            delta_alpha = destination_alpha_degree
            direction = "None"
        # print(f"Cross product: {cross_product} => {direction}")

        # setting a and a_alpha
        if v <= 10:
            a = 1
        else:
            a = 0

        a_alpha_max = robot.a_alpha_max
        if direction == "right":
            if delta_alpha >= a_alpha_max + v_alpha:
                a_alpha = a_alpha_max
                print("maxR")
            elif delta_alpha < a_alpha_max + v_alpha:
                a_alpha = delta_alpha - v_alpha
                print("R")

        if direction == "left":
            if delta_alpha >= a_alpha_max + v_alpha:
                a_alpha = - a_alpha_max
                print("maxL")
            elif delta_alpha < a_alpha_max - v_alpha:
                a_alpha = - 2
                print("L")

        if direction == "None":
            a_alpha = 1
            print("N")
        return a, a_alpha

    @staticmethod
    def cross_product(B,P):
        b_x = B[0]
        b_y = B[1]
        p_x = P[0]
        p_y = P[1]

        b_x = b_x
        b_y = b_y
        p_x = p_x
        p_y = p_y

        cp = b_x * p_y - b_y * p_x
        return cp