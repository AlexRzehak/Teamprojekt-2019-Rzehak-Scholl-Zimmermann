import queue
import threading
import time
from collections import deque


class BaseRobot:

    def __init__(self, radius, a_max, a_alpha_max, fov_angle=90):
        # set parameters
        self.radius = radius

        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

        self.fov_angle = fov_angle

        # self.movement_funct = movement_funct

        # TODO maybe add v_max, v_alpha_max


class ThreadRobot(BaseRobot):
    """The autonomous robot unit performing actions in its own thread."""

    MemSize = 10

    def __init__(self, base_robot: BaseRobot, movement_funct,
                 resync_flag=False):

        super().__init__(**vars(base_robot))

        # calculated by the robot
        # if the robot is not fast enough, he sucks
        self.a = 0
        self.a_alpha = 0

        self.thread = None
        self._sensor_queue = queue.Queue()

        # auto-resync of the robot.
        # robot will use resync functionality when resync_flag is set to True.
        # TODO implement resync policy
        self.resync_flag = resync_flag
        self.resync_data = 0

        # the behaviour of the robot
        self.movement_funct = movement_funct
        # TODO implement memory poliy
        # self.memory_policy = None

        # simple memory stack for the robot.
        self.memory = deque([])

        # the robot will atempt to go here (x,y)
        self.destination = None

        # TODO BONK management
        # self.bonk_flag = False
        # self.bonk_stack = None

    def run(self):

        self.thread = threading.Thread(
            target=self._thread_action, args=(self._sensor_queue,))
        self.thread.daemon = True
        self.thread.start()

    # Interface Functions
    def send_action_data(self):
        return self.a, self.a_alpha

    def receive_sensor_data(self, data):
        if self.resync_flag:
            self.resync_data = data.time_stamp

        self._sensor_queue.put(data)

    # Static resync policy
    def resync_check(self, signal):
        dif = self.resync_data - signal.time_stamp
        prio = signal.message_type in [SensorData.ALERT_STRING,
                                       SensorData.BONK_STRING]
        return dif >= 2 and (not prio)

    # Use your BRAIN
    def process_data(self, signal):

        dicc = {SensorData.POSITION_STRING: self.movement_funct.position,
                SensorData.VISION_STRING: self.movement_funct.vision,
                SensorData.ALERT_STRING: self.movement_funct.alert,
                SensorData.BONK_STRING: self.movement_funct.bonk}

        t = signal.message_type
        funct = self.movement_funct.default

        if t in dicc:
            funct = dicc[t]

        self.a, self.a_alpha = funct(signal.data, self)

    def _thread_action(self, q):

        while True:
            # get() blocks the thread until queue is not empty anymore
            signal = q.get()
            if not signal:
                time.sleep(0)
                continue

            # auto-resync
            if self.resync_flag and self.resync_check(signal):
                continue

            self.process_data(signal)

            # TODO adapt memory policy:
            # right now, every ALERT-message gets memorized.
            if signal.message_type == SensorData.ALERT_STRING:
                self.memorize(signal)

    # Save a message in the memory.
    def memorize(self, signal):

        self.memory.appendleft(signal)
        if len(self.memory) > ThreadRobot.MemSize:
            self.memory.pop()


class SensorData:
    """Container object for different sensor inputs."""

    # These Strings represent the different message_types
    POSITION_STRING = 'position'
    VISION_STRING = 'vision'
    ALERT_STRING = 'alert'
    BONK_STRING = 'bonk'
    IGNORE_STRING = 'ignore'

    def __init__(self, message_type: str, data, time_stamp):

        self.message_type = message_type
        self.data = data
        self.time_stamp = time_stamp
