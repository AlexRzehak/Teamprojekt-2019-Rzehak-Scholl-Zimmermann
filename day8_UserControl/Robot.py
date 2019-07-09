import queue
import threading
import time
import types
from collections import deque

import Utils


class BaseRobot:

    def __init__(self, radius, a_max, a_alpha_max, v_max=39, v_alpha_max=90, 
                 fov_angle=90, max_life=3, respawn_timer=3):
        # set parameters
        self.radius = radius

        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

        self.v_max = v_max
        self.v_alpha_max = v_alpha_max

        self.fov_angle = fov_angle

        self.respawn_timer = respawn_timer
        self.max_life = max_life

        # self.movement_funct = movement_funct

        # TODO maybe add v_max, v_alpha_max


class ThreadRobot(BaseRobot):
    """The autonomous robot unit performing actions in its own thread."""

    MemSize = 10

    def __init__(self, base_robot: BaseRobot, movement_funct):

        super().__init__(**vars(base_robot))

        # calculated by the robot
        # if the robot is not fast enough, he sucks
        self.a = 0
        self.a_alpha = 0

        self.thread = None
        self._sensor_queue = queue.Queue()

        # the behaviour of the robot
        self.movement_funct = movement_funct

        # use the gun_interface to tell the server when you want to shoot.
        self.gun_interface = None

        # auto-resync of the robot.
        # robot will use resync functionality when resync_flag is set to True.
        # TODO implement resync policy
        self.resync_flag = False
        self.resync_data = 0

        # simple memory stack for the robot.
        self.memory = deque([])

        # TODO implement memory policy
        # self.memory_policy = None

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

    def clear_input(self):
        # never use join
        self._sensor_queue.queue.clear()

    def clear_values(self):
        self.a = 0
        self.a_alpha = 0
        self.destination = None

    # Interface Functions
    def send_action_data(self):
        return self.a, self.a_alpha

    def receive_sensor_data(self, data):
        if self.resync_flag:
            self.resync_data = data.time_stamp

        self._sensor_queue.put(data)

    # Resync Management
    def set_resync_flag(self, value):
        self.resync_flag = value

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

    # gun stuff
    def setup_gun_interface(self, gun_interface):
        self.gun_interface = gun_interface

    def is_reloading(self):
        if self.gun_interface:
            return self.gun_interface.is_reloading()
        return False

    def is_shooting(self):
        """Return True if robot will already shoot at the next server tick."""
        if self.gun_interface:
            return self.gun_interface.is_preparing()
        return False

    # the robot will shoot at the next server tick
    def shoot(self):
        if self.gun_interface:
            self.gun_interface.prepare_fire()

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


class RoboGun:
    """Mediator object between Data representation and autonomous unit."""
    BULLET_SPEED = 12
    FIRE_QUEUE_SIZE = 20

    def __init__(self, bullet_speed=None):

        self.bullet_speed = bullet_speed
        if not bullet_speed:
            self.bullet_speed = RoboGun.BULLET_SPEED
        self.reloading = False
        self.fire_queue = queue.Queue(RoboGun.FIRE_QUEUE_SIZE)

        self.gun_access_player = False
        self.gun_access_robot = False

    def clear_input(self):
        # never use join
        self.fire_queue.queue.clear()

    def is_preparing(self):
        return not self.fire_queue.empty()

    def is_reloading(self):
        return self.reloading

    def set_gun_access_player(self, value):
        self.gun_access_player = value

    def set_gun_access_robot(self, value):
        self.gun_access_robot = value

    def prepare_fire_robot(self, data=True):
        if self.gun_access_robot:
            self.prepare_fire(data)

    def prepare_fire_player(self, data=True):
        if self.gun_access_player:
            if not (self.is_preparing() or self.is_reloading()):
                self.prepare_fire(data)

    def prepare_fire(self, data):
        # More complex data might be used later.
        try:
            self.fire_queue.put(data, block=False)
        except queue.Full:
            return False
        else:
            return True

    def trigger_fire(self):
        if self.reloading:
            return False

        task = self._get_fire_task()
        if not task:
            return False
        # get data by: _, task_data = task now.

        # bullet = dict()
        # bullet['speed'] = self.bullet_speed + data_robot.v
        # bullet['direction'] = data_robot.alpha
        # bullet['position'] = (data_robot.x, data_robot.y)

        self._initiate_reload()

        return self.bullet_speed

    def _get_fire_task(self):
        # if no item is in the queue, don't wait until it is!
        try:
            task = self.fire_queue.get(block=False)
        except queue.Empty:
            return False
        else:
            return True, task

    def _initiate_reload(self):

        def finish_reload():
            self.reloading = False

        self.reloading = True
        Utils.execute_after(1, finish_reload)

    @staticmethod
    def trigun_decorator(gun):
        """
        Amplifies a given gun to duplicate a successful fire task
        into three consecutive shots over the next server ticks.
        """
        # we need a new variable of the gun
        gun.trigun_count = 0

        # override the old fire function
        # TODO may be improved by just overloading the reload-check
        def trigger_fire_trigun(self):
            if self.reloading:
                if self.trigun_count:
                    self.trigun_count += -1
                    return self.bullet_speed
                else:
                    return False

            task = self._get_fire_task()
            if not task:
                return False
            # get data by: _, task_data = task now.

            self._initiate_reload()

            self.trigun_count = 2

            return self.bullet_speed

        gun.trigger_fire = types.MethodType(trigger_fire_trigun, gun)

        return gun


class GunInterface:
    def __init__(self, gun: RoboGun):

        self.is_preparing = gun.is_preparing
        self.is_reloading = gun.is_reloading
        self.prepare_fire = gun.prepare_fire_robot
