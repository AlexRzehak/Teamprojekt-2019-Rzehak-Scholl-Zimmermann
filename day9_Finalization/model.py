import utils
from player_control import PlayerControl, ControlScheme
from robogun import GunInterface
# from config_provider import FIELD_SIZE, TILE_SIZE

# ==================================
# Model
# ==================================
#
# In this file, you will find the data representation of the robots.
# Robot objects will be stored by the server
# to represent the robots' current states.
# The robot object also controls certain calculation functionalities,
# such as management of damage and creation of bullets.
#
# CHANGE HERE:
# - body parameters of the robots
# - player/AI access right management
# - damage and respawn of the robots
# - bullet creation


class BaseRobot:
    """Defines set parameters of the robots body."""

    def __init__(self, radius, a_max, a_alpha_max, v_max=39, v_alpha_max=90,
                 fov_angle=90, max_life=3, respawn_timer=3, immunity_timer=1):

        self.radius = radius

        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

        self.v_max = v_max
        self.v_alpha_max = v_alpha_max

        self.fov_angle = fov_angle

        self.max_life = max_life
        self.respawn_timer = respawn_timer
        self.immunity_timer = immunity_timer


class DataRobot(BaseRobot):
    """
    Data representation of the robots for the server.
    Performes I/O management for player/AI-control.
    Controls player/AI access right system.
    Performes gun management/control for the server.
    Performes damage/respawn management for the server.
    """

    def __init__(self, base_robot: BaseRobot, robot_control):

        super().__init__(**vars(base_robot))

        # current position
        self.x = 0
        self.y = 0
        self.alpha = 0

        self.v = 0
        self.v_alpha = 0

        # Every robot must have an AI controller.
        self.robot_control = robot_control

        # Optional player control.
        self.player_control = None
        self.player_control_active = False

        # Damage / respawn parameters.
        self.dead = False
        self.immune = False
        self.life = self.max_life

        # Optional gun object.
        self.gun = None

        # Only some robots should receive an alert message.
        self.alert_flag = False

        # Access management system:
        # self.player_input_enabled = True         # currently inactive
        self.player_output_enabled = False
        self.robot_input_enabled = True
        self.robot_output_enabled = True

        # self.player_gun_access = False
        # self.robot_gun_access = True
        self.gun_enabled = False

    # Set-up functions:
    # =================

    # the most important function!
    def setup_movement(self, movement):
        self.robot_control.setup_movement(movement)

    # optional flags
    def set_alert_flag(self, value=True):
        self.alert_flag = value

    def set_resync_flag(self, value=True):
        self.robot_control.set_resync_flag(value)

    # optional setups
    def setup_gun(self, gun):
        """Add a gun object to the robot unit.
        Setup gun access for AI-control and optional player control.
        """
        # Gain control over new gun object.
        self.gun = gun

        # Add interface for AI.
        gun_interface = GunInterface(gun)
        self.robot_control.setup_gun_interface(gun_interface)

        # Add interface for player.
        if self.player_control:
            self.player_control.setup_gun(gun)

        # Get started!
        self.enable_gun()

    def setup_player_control(self, player_control):
        """Add player control to the robot unit.
        If robot unit owns a gun, add gun interface for player."""

        self.player_control = player_control

        # Add gun interface for player.
        if self.gun:
            self.player_control.setup_gun(self.gun)

        # By adding player control, we immediately start with active player.
        self.hand_control_to_player()

    # Interface for AI_Control:
    # =========================

    def start(self):
        """Tell the AI control to initiate calculations."""
        self.robot_control.run()

    def send_sensor_data(self, data):
        """Send selected data to the AI control, if enabled."""
        if self.robot_input_enabled:
            self.robot_control.receive_sensor_data(data)

    # Interface for Server:
    # =====================

    def poll_action_data(self):
        """
        Server asks for acceleration data of this robot unit.
        Send data from human player or AI, according to current access rights.
        """

        # ADD: Here you can add player/AI-hybrid models!

        # controlling player gets priority
        if self.player_output_enabled:
            return self.player_control.send_action_data()

        if self.robot_output_enabled:
            return self.robot_control.send_action_data()

        # maybe adapt default data?
        default_data = (0, 0)
        return default_data

    def perform_shoot_action(self):
        """
        Server asks for shoot action data of this robot unit.
        Will return a valid bullet, if the robot is shooting.
        Else returns False.
        """

        maybe_bullet = False

        # don't shoot, if gun is disabled or doesn't exist.
        if not self.gun or not self.gun_enabled:
            return maybe_bullet

        # get gun data to create bullet.
        maybe_data = self.gun.trigger_fire()
        if maybe_data:
            angle = self.alpha

            # prevent bullets from spawning inside of the robot.
            angle_vector = utils.vector_from_angle(angle)
            robot_center = (self.x, self.y)
            bullet_start = robot_center + (self.radius + 1) * angle_vector

            # prevent bullets from standing still while moving backwards
            speed = max(0, self.v) + maybe_data

            # create bullet
            maybe_bullet = Bullet(position=bullet_start,
                                  speed=speed,
                                  direction=angle)
        return maybe_bullet

    # robot movement
    def place_robot(self, x, y, alpha, v, v_alpha):
        """Place the robot at given position.
        Called by the server to move the robot unit.
        """

        self.x = x
        self.y = y
        self.alpha = alpha

        self.v = v
        self.v_alpha = v_alpha

    def teleport_furthest_corner(self, point):
        """Teleports the robot to a position in the corner
        with the largest distance from point.
        """
        import config_provider

        tile_size = config_provider.TILE_SIZE
        field_size = config_provider.FIELD_SIZE

        lower_limit = tile_size + self.radius + 1
        upper_limit = field_size - tile_size - self.radius - 2

        top_left_corner = (lower_limit, lower_limit, 135, 0, 0)
        bot_left_corner = (lower_limit, upper_limit, 45, 0, 0)
        top_right_corner = (upper_limit, lower_limit, 225, 0, 0)
        bot_right_corner = (upper_limit, upper_limit, 315, 0, 0)

        if point[0] > (field_size / 2):
            if point[1] > (field_size / 2):
                position = top_left_corner
            else:
                position = bot_left_corner
        else:
            if point[1] > (field_size / 2):
                position = top_right_corner
            else:
                position = bot_right_corner

        self.place_robot(*position)

    # Damage and respawn system:
    # ==========================

    def deal_damage(self, damage=1):
        """Called by server if damage is dealt to the robot unit.
        If robot looses all of its life, destroy it."""

        # we don't deal damage to dead or immune units
        if self.immune or self.dead:
            return

        self.life = max(0, self.life - damage)
        if self.life <= 0:
            self.get_destroyed()

    def get_destroyed(self):
        """Gets called, if robot looses all of its life.
        Enter dead-state and initiate respawn.
        """
        self.dead = True

        self.v = 0
        self.v_alpha = 0

        self.disable_robot_control()
        self.disable_player_control()
        self.disable_gun()

        def respawn():
            self.respawn()

        utils.execute_after(self.respawn_timer, respawn)

    def respawn(self):
        """Respawn the robot unit at different location.
        Enter immunity-state for short time period.
        """
        self.life = self.max_life
        self.immune = True
        point = self.x, self.y
        self.teleport_furthest_corner(point)

        # Return control to former controller.
        if self.player_control_active:
            self.hand_control_to_player()
        else:
            self.hand_control_to_robot()

        self.enable_gun()

        self.dead = False

        def disable_immunity():
            self.immune = False

        utils.execute_after(self.immunity_timer, disable_immunity)

    # Player control interface:
    # =========================

    # called by server
    def enter_key_action(self, key, state=None):
        """Forward a key action to the player control.
        If no state is given, the key is stateless."""
        if self.player_control:
            self.player_control.calculate_key_action(key, state)

    def finish_key_actions(self):
        """Server will call this at the end of the key action calculation.
        Tells the player control to execute entered state for entwined keys.
        """
        if self.player_control:
            self.player_control.execute_entwined_keys()

    # called by player control
    def invasive_control(self, v_alpha):
        """Invasive player control will use this
        to directly alter speed values."""
        if self.player_output_enabled:
            self.v_alpha = v_alpha

    def toggle_player_control(self):
        """Change current control over the robot unit.
        Unit can be controlled by player or AI."""

        # we can't toggle while dead
        if self.dead:
            return

        if self.player_control_active:
            self.hand_control_to_robot()
        else:
            self.hand_control_to_player()

    # Right management system:
    # ========================

    def hand_control_to_player(self):
        # withdraw the rights for the robot
        self.disable_robot_control()
        self.disable_robot_gun_access()

        # give the rights to the player
        self.enable_player_control()
        self.enable_player_gun_access()

        # notify server, set the state
        self.player_control_active = True

    def hand_control_to_robot(self):
        # withdraw rights of the player
        self.disable_player_control()
        self.disable_player_gun_acess()

        # give the rights to the robot
        self.enable_robot_control()
        self.enable_robot_gun_access()

        # notify server, set the state
        self.player_control_active = False

    def disable_robot_control(self):
        self.robot_output_enabled = False
        self.robot_input_enabled = False

        self.robot_control.clear_input()

    def enable_robot_control(self):
        self.robot_control.clear_input()
        self.robot_control.clear_values()
        self.robot_input_enabled = True
        self.robot_output_enabled = True

    def disable_player_control(self):
        self.player_output_enabled = False

    def enable_player_control(self):
        self.player_output_enabled = True

    def disable_robot_gun_access(self):
        if self.gun:
            self.gun.set_gun_access_robot(False)
            # self.robot_gun_access = False
            self.gun.clear_input()

    def enable_robot_gun_access(self):
        if self.gun:
            self.gun.clear_input()
            self.gun.set_gun_access_robot(True)
            # self.robot_gun_access = True

    def disable_player_gun_acess(self):
        if self.gun:
            self.gun.set_gun_access_player(False)
            # self.player_gun_access = False
            self.gun.clear_input()

    def enable_player_gun_access(self):
        if self.gun:
            self.gun.clear_input()
            self.gun.set_gun_access_player(True)
            # self.player_gun_access = True

    def disable_gun(self):
        self.gun_enabled = False
        self.disable_player_gun_acess()
        self.disable_robot_gun_access()

    def enable_gun(self):
        self.gun_enabled = True
        if self.player_control_active:
            self.enable_player_gun_access()
        else:
            self.enable_robot_gun_access()


class Bullet:
    """Data container class for bullet representation."""

    def __init__(self, position, speed, direction):
        self.position = position
        self.speed = speed
        self.direction = direction
