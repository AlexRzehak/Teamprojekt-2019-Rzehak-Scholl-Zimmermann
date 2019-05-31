import random


# TODO use tuple unpacking to show names
class Movement():
    """Implement different movement options."""

    @staticmethod
    def random_movement(sensor_data, **kwargs):
        if sensor_data[3] < 15:
            a = 1
            a_alpha = random.randint(-20, 20)
        else:
            a = 0
            a_alpha = random.randint(-20, 20)
        return a, a_alpha

    @staticmethod
    def nussschnecke_movement(sensor_data, **kwargs):
        if sensor_data[3] < 7:
            a = 0.5
            a_alpha = 1
            return a, a_alpha
        else:
            a = 0
            a_alpha = 0
        return a, a_alpha

    @staticmethod
    def spiral_movement(sensor_data, **kwargs):
        if sensor_data[3] < 20:
            a = 1
            a_alpha = 1
            return a, a_alpha
        else:
            a = 1
            a_alpha = 0
        return a, a_alpha

    @staticmethod
    def spin_movement(sensor_data, **kwargs):

        a = 0
        a_alpha = 99999999
        if sensor_data[4] > 30:
            a = 0
            a_alpha = 0
        return a, a_alpha

    @staticmethod
    def unchanged_movement(sensor_data, **kwargs):
        a = 0
        a_alpha = 0
        return a, a_alpha
