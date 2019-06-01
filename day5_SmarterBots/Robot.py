import queue
import threading
import time


class BaseRobot():

    def __init__(self, radius, movement_funct, a_max, a_alpha_max):
        # set parameters
        self.radius = radius

        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

        # Movement function to apply on current position and speed.
        self.movement_funct = movement_funct

        # TODO maybe add v_max, v_alpha_max


class ThreadRobot(BaseRobot):

    def __init__(self, base_robot: BaseRobot):

        super().__init__(**vars(base_robot))

        # calculated by the robot
        # if the robot is not fast enough, he sucks
        self.a = 0
        self.a_alpha = 0

        self.thread = None
        self._sensor_queue = queue.Queue()

        # TODO give the robot a memory
        self.memory = None

        # TODO the robot will atempt to go here (x,y)
        self.destination = None

    def run(self):

        self.thread = threading.Thread(
            target=self._thread_action, args=(self._sensor_queue,))
        self.thread.daemon = True
        self.thread.start()

    def send_action_data(self):
        return self.a, self.a_alpha

    def receive_sensor_data(self, data):
        self._sensor_queue.put(data)

    # TODO implement resync method
    def resync(self):
        pass

    def _thread_action(self, q):

        while True:
            # get() blocks the thread until queue is not empty anymore
            signal = q.get()
            if not signal:
                time.sleep(0)
                continue
            # kwargs = dict(radius=self.radius,
                        #   a_max=self.a_max,
                        #   a_alpha_max=self.a_alpha_max,
                        #   # might be wrong lel
                        #   a=self.a,
                        #   a_alpha=self.a_alpha)

            self.a, self.a_alpha = self.movement_funct(signal, self)


# TODO add different Types of sensor data
# for example: regular, alert, bonk
class SensorData():
    pass
