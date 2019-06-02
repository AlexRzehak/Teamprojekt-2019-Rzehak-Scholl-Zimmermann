import random


class Movement():
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
