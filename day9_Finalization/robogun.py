import queue
import types

import utils


# ==================================
# RoboGun
# ==================================
#
# In this file, you will find the data representation of gun objects.
# You can add a gun object with different properties to a robot unit
# to povide it with the ability to deal damage by attacking.
# It will be accessed by AI control as well as optional player control.
# At any time, any controller can add a fire command that will be executed
# at the next possible opportunity.
#
# CHANGE HERE:
# - gun access rights
# - gun status queries
# - thread safe enqueuement of fire commands
# - execution of fire commands
# - gun modificators
#
# ADD HERE:
# - you should add support for different gun types here


class RoboGun:
    """Controller object for thread safe yet instantaneous attack commands."""
    FIRE_QUEUE_SIZE = 20

    def __init__(self, bullet_speed, reload_speed):

        # Main relay of thread safe communication.
        self._fire_queue = queue.Queue(RoboGun.FIRE_QUEUE_SIZE)

        # Bullet properties.
        # ADD: You can add addditional bullet information here.
        self.bullet_speed = bullet_speed

        # Reload properties.
        self.reload_speed = reload_speed
        self.reloading = False

        # Access rights.
        self.gun_access_player = False
        self.gun_access_robot = False

    # Flush enqueued fire commands
    # ============================
    def clear_input(self):
        # never use join!
        self._fire_queue.queue.clear()

    # Gun status queries:
    # ===================
    def is_preparing(self):
        return not self._fire_queue.empty()

    def is_reloading(self):
        return self.reloading

    # Access right management:
    # ========================
    def set_gun_access_player(self, value):
        """Callable by AI control as well as player control."""
        self.gun_access_player = value

    def set_gun_access_robot(self, value):
        """Callable by AI control as well as player control."""
        self.gun_access_robot = value

    # Enter attack command:
    # =====================
    def prepare_fire_robot(self, data=True):
        """Called by AI controller to execute an attack."""
        if self.gun_access_robot:
            self._prepare_fire(data)

    def prepare_fire_player(self, data=True):
        """Called by player controller to execute an attack."""
        if self.gun_access_player:
            # only enqueue attack if able to fire immediately
            # to avoid unresponsive input because of buffering.
            if not (self.is_preparing() or self.is_reloading()):
                self._prepare_fire(data)

    def _prepare_fire(self, data):
        # ADD: You can add more complex data from different gun types here.
        try:
            self._fire_queue.put(data, block=False)
        except queue.Full:
            return False
        else:
            return True

    # Perform attack:
    # ===============
    def trigger_fire(self):
        """Called by server via data unit at bullet creation phase.
        Check if fire command is enqueued and gun is able to fire!
        Return False if gun doesn't shoot, else return data.
        """

        # can't shoot while reloading.
        if self.reloading:
            return False

        task = self._get_fire_task()
        if not task:
            return False
        # get data by: _, task_data = task now.
        # ADD: You can add support for different gun types here!

        self._initiate_reload()

        return self.bullet_speed

    def _get_fire_task(self):
        # if no item is in the queue, return immediately.
        # don't wait and block!
        try:
            task = self._fire_queue.get(block=False)
        except queue.Empty:
            return False
        else:
            return True, task

    def _initiate_reload(self):

        def finish_reload():
            self.reloading = False

        # enter reloading state
        self.reloading = True
        # leave reloading state after certain time has passed
        utils.execute_after(self.reload_speed, finish_reload)

    # Optional functionality decorators:
    # ==================================
    # ADD: You can add more decorators here
    # to change a gun's behaviour independent from its type.
    @staticmethod
    def available_gun_options():
        # ADD HERE: If you added more gun options,
        # enter them here so the parser knows them.
        return {'trigun': RoboGun.trigun_decorator}

    @staticmethod
    def trigun_decorator(gun):
        """
        Amplifies a given gun to duplicate a successful fire task
        into three consecutive shots over the next server ticks.
        """
        # we need a new variable of the gun
        gun.trigun_count = 0

        # override the old fire function
        # this may be improved by just overloading the reload-check
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
    """Restricted access gun interface."""

    def __init__(self, gun):

        self.is_preparing = gun.is_preparing
        self.is_reloading = gun.is_reloading
        self.prepare_fire = gun.prepare_fire_robot
