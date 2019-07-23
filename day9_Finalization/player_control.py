import math

from PyQt5.QtCore import Qt

import utils

# ==================================
# Player Control
# ==================================
#
# In this file, you will find functionalities for keyboard control.
# A ControlScheme will define arbitrary key bindings.
# The PlayerControl object maps key states to the respective movement action.
#
# CHANGE HERE:
# - key bindings
# - add new key bound functionalities
# - responses to key presses


class PlayerControl:
    """
    Allow a player to take control over a robot.
    Distinguish stateless keys from keys with state.
    Respond to pressed keys with corresponding actions.
    """
    ACCEL_AMT = 1
    TURN_RATE = 1

    STATE_ACTIVE = "A"
    STATE_PUSH = "D"
    STATE_INACTIVE = "I"

    STATE_SWITCH = {(STATE_ACTIVE, True): STATE_ACTIVE,
                    (STATE_INACTIVE, True): STATE_PUSH,
                    (STATE_PUSH, True): STATE_ACTIVE,
                    (STATE_ACTIVE, False): STATE_INACTIVE,
                    (STATE_INACTIVE, False): STATE_INACTIVE,
                    (STATE_PUSH, False): STATE_INACTIVE}

    def __init__(self, data_robot, control_scheme,
                 invasive_controls=False, invasive_controls_turn_rate=10):

        # at object creation,
        # define, wheather controls should be invasive or SPACE (default).

        # key bindings of this PlayerControl
        self.control_scheme = control_scheme

        # access to data objects
        self.data_robot = data_robot
        self.gun = data_robot.gun

        # in normal mode control these values
        self.a = 0
        self.a_alpha = 0

        # define acceleration amount from key press
        self.accel_amt = PlayerControl.ACCEL_AMT
        self.turn_rate = PlayerControl.TURN_RATE

        if invasive_controls:
            self.turn_rate = invasive_controls_turn_rate

        # cooldown boolean to prevent accidental multiple actiavtions
        self.allow_toggle_autopilot = True

        # Local copy nomes for state machine definitions
        inact = PlayerControl.STATE_INACTIVE
        push = PlayerControl.STATE_PUSH
        act = PlayerControl.STATE_ACTIVE

        # State Machine for acc-rev_acc entwinement:
        # ==========================================
        self.acc_state = inact
        self.acc_rev_state = inact

        def acc():
            self.a = self.accel_amt

        def rev_acc():
            self.a = -1 * self.accel_amt

        def clear_acc():
            self.a = 0

        def acc_pass():
            pass

        self.acc_lookup = {(inact, inact): clear_acc,
                           (inact, act): rev_acc,
                           (inact, push): rev_acc,
                           (act, inact): acc,
                           (act, act): acc_pass,
                           (act, push): rev_acc,
                           (push, inact): acc,
                           (push, act): acc,
                           (push, push): acc}

        # State Machine for left-right entwinement:
        # =========================================
        self.left_state = inact
        self.right_state = inact

        def lr_left():
            if invasive_controls:
                self.data_robot.invasive_control(
                    v_alpha=-1 * self.turn_rate)
            else:
                self.a_alpha = - 1 * self.turn_rate

        def lr_right():
            if invasive_controls:
                self.data_robot.invasive_control(v_alpha=self.turn_rate)
            else:
                self.a_alpha = self.turn_rate

        def clear_lr():
            if invasive_controls:
                self.data_robot.invasive_control(v_alpha=0)
            else:
                self.a_alpha = 0

        def lr_pass():
            pass

        self.lr_lookup = {(inact, inact): clear_lr,
                          (inact, act): lr_right,
                          (inact, push): lr_right,
                          (act, inact): lr_left,
                          (act, act): lr_pass,
                          (act, push): lr_right,
                          (push, inact): lr_left,
                          (push, act): lr_left,
                          (push, push): clear_lr}

    # communication interface with server:
    # ====================================
    def send_action_data(self):
        return self.a, self.a_alpha

    # setup:
    # ======
    def setup_gun(self, gun):
        """Call this when changing or initiating the gun object."""
        self.gun = gun

    # key input handler:
    # ==================
    def calculate_key_action(self, key, state):
        action_name = self.control_scheme[key]
        action = getattr(self, action_name)
        # stateless
        if state is None:
            action()
        # keys with state
        else:
            action(state_active=state)

    def execute_entwined_keys(self):
        self.execute_accelerate()
        self.execute_left_right()

    # entwined keys accelerate / accelerate_reverse:
    # ==============================================
    def accelerate(self, state_active):
        lookup_tuple = (self.acc_state, state_active)
        self.acc_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def accelerate_reverse(self, state_active):
        lookup_tuple = (self.acc_rev_state, state_active)
        self.acc_rev_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def execute_accelerate(self):
        # get current state combination
        lookup_tuple = (self.acc_state, self.acc_rev_state)
        # look up function for current state combination
        func = self.acc_lookup[lookup_tuple]
        func()

    # entwined keys left / right:
    # ===========================
    def left(self, state_active):
        lookup_tuple = (self.left_state, state_active)
        self.left_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def right(self, state_active):
        lookup_tuple = (self.right_state, state_active)
        self.right_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def execute_left_right(self):
        # get current state combination
        lookup_tuple = (self.left_state, self.right_state)
        # look up function for current state combination
        func = self.lr_lookup[lookup_tuple]
        func()

    # other keys with state:
    # ======================
    # ADD new keys with state here!

    def shoot(self, state_active):
        if state_active:
            if self.gun:
                self.gun.prepare_fire_player()

    # stateless keys:
    # ===============
    # ADD new stateless keys here!

    def toggle_autopilot(self):
        if self.allow_toggle_autopilot:
            self.data_robot.toggle_player_control()

            def enable_toggle():
                self.allow_toggle_autopilot = True

            self.allow_toggle_autopilot = False
            utils.execute_after(0.5, enable_toggle)


class ControlScheme:
    """
    Container class for default key bindings
    and global key binding helper definitions.
    """

    # key bound actions:
    # ==================
    ACC_STRING = 'accelerate'
    ACC_REV_STRING = 'accelerate_reverse'
    LEFT_STRING = 'left'
    RIGHT_STRING = 'right'
    SHOOT_STRING = 'shoot'
    AUTOPILOT_STRING = 'toggle_autopilot'

    # define wheather a key is stateless or not:
    # ==========================================
    KEYS_WITH_STATE = {ACC_STRING,
                       ACC_REV_STRING,
                       LEFT_STRING,
                       RIGHT_STRING,
                       SHOOT_STRING}
    STATELESS_KEYS = {AUTOPILOT_STRING}

    # default key bindings:
    # =====================
    # ADD: Add a new key binding here!
    # Don't forget to add it to the known bindings of the ConfigReader.
    default_scheme = {Qt.Key_W: ACC_STRING,
                      Qt.Key_S: ACC_REV_STRING,
                      Qt.Key_A: LEFT_STRING,
                      Qt.Key_D: RIGHT_STRING,
                      Qt.Key_J: SHOOT_STRING,
                      Qt.Key_P: AUTOPILOT_STRING}

    player_one_scheme = {Qt.Key_W: ACC_STRING,
                         Qt.Key_S: ACC_REV_STRING,
                         Qt.Key_A: LEFT_STRING,
                         Qt.Key_D: RIGHT_STRING,
                         Qt.Key_Space: SHOOT_STRING,
                         Qt.Key_R: AUTOPILOT_STRING}

    player_two_scheme = {Qt.Key_Up: ACC_STRING,
                         Qt.Key_Down: ACC_REV_STRING,
                         Qt.Key_Left: LEFT_STRING,
                         Qt.Key_Right: RIGHT_STRING,
                         Qt.Key_Return: SHOOT_STRING,
                         Qt.Key_End: AUTOPILOT_STRING}

    player_four_scheme = {Qt.Key_I: ACC_STRING,
                          Qt.Key_K: ACC_REV_STRING,
                          Qt.Key_J: LEFT_STRING,
                          Qt.Key_L: RIGHT_STRING,
                          Qt.Key_Period: SHOOT_STRING,
                          Qt.Key_M: AUTOPILOT_STRING}

    # since Qt is a piece of garbage, these key names can't be distinguished
    # from key presses outside of the numpad without further measurements.
    # Also, some of those measurements are actually buggy!
    num_block_scheme = {Qt.Key_8: ACC_STRING,
                        Qt.Key_5: ACC_REV_STRING,
                        Qt.Key_4: LEFT_STRING,
                        Qt.Key_6: RIGHT_STRING,
                        Qt.Key_0: SHOOT_STRING,
                        Qt.Key_Plus: AUTOPILOT_STRING}
