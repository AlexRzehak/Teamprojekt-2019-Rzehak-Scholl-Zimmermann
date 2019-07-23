import time
import queue
import threading
from collections import deque

from model import BaseRobot
from Movement import Movement

# ==================================
# AI Control
# ==================================
#
# In this file, you will find functionalities for the communication
# between server and robot AI
# as well as encapsulation of the AI interface.
#
# CHANGE HERE:
# - encapsulation policies
# - supervision of AI threading
# - communication method / message types
# - helper tools accessed by the AI


class RobotControl(BaseRobot):
    """
    The interface between server and controlling AI.
    This class handles the communication
    and will provide the AI with data picked by the Server.
    Supervises the AI's calculations that will be performed in its own thread.
    Every robot unit must have a corresponding RobotControl.
    """

    MEM_SIZE = 10

    def __init__(self, base_robot: BaseRobot, movement_funct=Movement):

        # You can access all body parameters of the robot over the interface.
        super().__init__(**vars(base_robot))

        # the AI's main task: set acceleration values
        self.a = 0
        self.a_alpha = 0

        # the AI function response set
        self.movement_funct = movement_funct

        # basic communication interfaces
        self._sensor_queue = queue.Queue()
        self.gun_interface = None

        # Communication tools:
        # --------------------
        # auto-resync of the robot.
        # robot will use resync functionality when resync_flag is set to True.
        self.resync_flag = False
        self.resync_data = 0

        # AI helper tools:
        # ----------------
        # simple memory cell for destination coordinates
        self.destination = None

        # simple memory stack for incoming messages
        self.memory = deque([])

    # AI supervision:
    # ===============

    def run(self):
        """Start the AI calculation thread."""
        t = threading.Thread(target=self._thread_action,
                             args=(self._sensor_queue,))
        t.daemon = True
        t.start()

    def _thread_action(self, q):

        while True:
            # get() blocks the thread until queue is not empty anymore
            signal = q.get()
            if not signal:
                time.sleep(0)
                continue

            # auto-resync example feature
            # ADD: Here you can add more complex resyn behaviour.
            if self.resync_flag and self.resync_check(signal):
                continue

            # use your BRAIN!
            self.process_data(signal)

            # Example memory policy:
            # right now, every ALERT-message gets memorized.
            # ADD: Here you can add more complex memory policies.
            if signal.message_type == SensorData.ALERT_STRING:
                self.memorize(signal)

    def process_data(self, signal):
        """
        Evaluate data sent by the server:
        Process control data.
        Forward non-control data to the AI thread.
        """

        dicc = {SensorData.POSITION_STRING: self.movement_funct.position,
                SensorData.VISION_STRING: self.movement_funct.vision,
                SensorData.ALERT_STRING: self.movement_funct.alert}

        t = signal.message_type
        funct = self.movement_funct.default

        if t in dicc:
            funct = dicc[t]

        self.a, self.a_alpha = funct(signal.data, self)

    # Data communication path to the server:
    # ======================================

    def send_action_data(self):
        return self.a, self.a_alpha

    def receive_sensor_data(self, data):
        if self.resync_flag:
            self.resync_data = data.time_stamp

        self._sensor_queue.put(data)

    # Control interface for the server:
    # ==========================================

    def clear_input(self):
        # never use quque.join!
        self._sensor_queue.queue.clear()

    def clear_values(self):
        self.a = 0
        self.a_alpha = 0
        self.destination = None

    def setup_movement(self, movement):
        self.movement_funct = movement

    def setup_gun_interface(self, gun_interface):
        self.gun_interface = gun_interface

    # Gun management interface for the AI:
    # ====================================

    def is_reloading(self):
        """Return True if gun is reloading."""
        if self.gun_interface:
            return self.gun_interface.is_reloading()
        return False

    def is_shooting(self):
        """Return True if robot will already shoot at the next server tick."""
        if self.gun_interface:
            return self.gun_interface.is_preparing()
        return False

    def shoot(self):
        """If able, the robot will shoot at the next server tick."""
        if self.gun_interface:
            self.gun_interface.prepare_fire()

    # Examples for additional tools:
    # ==============================

    # Save a message in the memory.
    def memorize(self, signal):

        self.memory.appendleft(signal)
        if len(self.memory) > RobotControl.MEM_SIZE:
            self.memory.pop()

    # Allow resync management
    def set_resync_flag(self, value):
        self.resync_flag = value

    # Auto-Resync example feature:
    # Drop every non-alert-message, if 2 or more ticks out of sync.
    # ADD: Here you can add more complex resync conditions.
    def resync_check(self, signal):
        dif = self.resync_data - signal.time_stamp
        prio = signal.message_type in [SensorData.ALERT_STRING]
        return dif >= 2 and (not prio)


class SensorData:
    """Container object for different sensor inputs."""

    # These Strings represent the different message_types
    # ADD: Here you can add new message types!
    POSITION_STRING = 'position'
    VISION_STRING = 'vision'
    ALERT_STRING = 'alert'
    IGNORE_STRING = 'ignore'

    def __init__(self, message_type: str, data, time_stamp):

        self.message_type = message_type
        self.data = data
        self.time_stamp = time_stamp
