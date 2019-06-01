import queue
import threading
import time
from collections import deque


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

    MemSize = 10

    def __init__(self, base_robot: BaseRobot):

        super().__init__(**vars(base_robot))

        # calculated by the robot
        # if the robot is not fast enough, he sucks
        self.a = 0
        self.a_alpha = 0

        self.thread = None
        self._sensor_queue = queue.Queue()

        # simple memory stack for the robot.
        self.memory = deque([])

        # TODO the robot will atempt to go here (x,y)
        self.destination = None

        # TODO collision management
        self.bonk_flag = False

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

    def decode_input(self, signal):

        if signal.message_type == SensorData.POSITION_STRING:
            funct = self.movement_funct.position

        elif signal.message_type == SensorData.ALERT_STRING:
            funct = self.movement_funct.alert

        elif signal.message_type == SensorData.BONK_STRING:
            funct = self.movement_funct.bonk

        else:
            funct = self.movement_funct.default

        return funct

    def _thread_action(self, q):

        while True:
            # get() blocks the thread until queue is not empty anymore
            signal = q.get()
            if not signal:
                time.sleep(0)
                continue

            funct = self.decode_input(signal)
            self.a, self.a_alpha = funct(signal.data, self)

            # TODO adapt memory policy:
            # right now, every ALERT-message gets memorized.
            if signal.message_type == SensorData.ALERT_STRING:
                self.memorize(signal)

    def memorize(self, signal):
        self.memory.appendleft(signal)
        if len(self.memory) > ThreadRobot.MemSize:
            self.memory.pop()


class SensorData():
    """Container object for different sensor inputs."""

    POSITION_STRING = 'position'
    ALERT_STRING = 'alert'
    BONK_STRING = 'bonk'
    IGNORE_STRING = 'ignore'

    def __init__(self, message_type: str, data, time_stamp):

        self.message_type = message_type
        self.data = data
        self.time_stamp = time_stamp
