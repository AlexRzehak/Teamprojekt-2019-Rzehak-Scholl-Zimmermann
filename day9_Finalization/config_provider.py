import os
import functools
import configparser

from PyQt5.QtCore import QPoint

from model import BaseRobot, DataRobot
from robogun import RoboGun
from ai_control import RobotControl
from player_control import PlayerControl, ControlScheme
import movement
import utils


# ==================================
# Config Provider
# ==================================
#
# In this file, you will find a config reader for map and robots.
# In addition, this file also provides static configuration values
# like the size of the board.
#
# CHANGE HERE:
# - Static configuration values.
# - Configurations of the config reader:
#   - config validation process
#   - fallback values
#   - file path
#   - known values for complex parameters:
#     For example: If you add a new movement,
#     add it to the scope of the config reader!


# Static configuration values:
# ============================

# This app is optimized for FIELD_SIZE = 1000, TILE_SIZE = 10
# we do not take any liability for malfunctions if changed!
FIELD_SIZE = 1000
TILE_SIZE = 10
TILE_COUNT = int(FIELD_SIZE/TILE_SIZE)

# Parameters of the game: Again, no liability taken!
SECONDS_PER_TICK = 0.05
MAX_ROBOT_COUNT = 6

# Config file path:
# =================

CONFIG_FOLDER = 'configs'
ROBOT_CONFIG = 'robots.ini'
MAP_CONFIG = 'map.ini'

# Parameters for the ConfigReader:
# ================================

# Set of known key bindings from player_contol.ControlScheme:
# ADD: If you add a new key binding, also add it to this set!
AVAILABLE_KEY_BINDINGS = {'default_scheme',
                          'player_one_scheme',
                          'player_two_scheme',
                          'player_four_scheme',
                          'num_block_scheme'}

# Set of known AI-movements from movement:
# ADD If you add a new movement, also add it to this set!
AVAILABLE_MOVEMENTS = {'Movement',
                       'RandomMovement',
                       'NusschneckeMovement',
                       'SpiralMovement',
                       'SpinMovement',
                       'FollowMovement',
                       'RandomTargetMovement',
                       'SimpleAvoidMovement',
                       'RunMovement',
                       'ChaseMovement',
                       'ChaseMovementGun',
                       'SimpleAvoidMovementGun',
                       'PermanentGunMovement',
                       'ChaseAvoidMovement',
                       'ChaseAvoidMovementGun'}

# Fallback values for robot creation.
# These fallback values must be valid, since they remain unchecked,
# so please be careful changing them!
ROBOT_FALLBACK = {'radius': 3,
                  'a_max': 10,
                  'a_alpha_max': 10,
                  'v_max': 30,
                  'v_alpha_max': 45,
                  'fov_angle': 90,
                  'max_life': 3,
                  'respawn_timer': 3,
                  'immunity_timer': 1,
                  'auto_resync': False,
                  'alpha': 0,
                  'movement': 'Movement',
                  'alert_flag': True,
                  'gun': False,
                  'gun_bullet_speed': 12,
                  'gun_reload_speed': 1,
                  'gun_options': '',
                  'player_control': False,
                  'invasive_controls': False,
                  'invasive_controls_turn_rate': 10,
                  'keys': 'default_scheme'}

# robot.ini frame for recreation of the file.
EXAMPLE_ROBOT_CONFIG_STR = f"""[BASE]
# Fallback values for robots.
# Declare robots in later sections.

# Multiplier for base radius:
radius = {ROBOT_FALLBACK['radius']}
a_max = {ROBOT_FALLBACK['a_max']}
a_alpha_max = {ROBOT_FALLBACK['a_alpha_max']}
v_max = {ROBOT_FALLBACK['v_max']}
v_alpha_max = {ROBOT_FALLBACK['v_alpha_max']}
fov_angle = {ROBOT_FALLBACK['fov_angle']}
max_life = {ROBOT_FALLBACK['max_life']}
respawn_timer = {ROBOT_FALLBACK['respawn_timer']}
immunity_timer = {ROBOT_FALLBACK['immunity_timer']}
auto_resnyc = {ROBOT_FALLBACK['auto_resync']}

# No default position value.
# position = 500, 500
alpha = 0

# Robots must have a movement AI.
movement = {ROBOT_FALLBACK['movement']}
# If True, set alert_flag automatically, if False, deny for all robots.
# Set the value for a robot explicitly to override a flag defined this way.
alert_flag = {ROBOT_FALLBACK['alert_flag']}

# Default robot doesn't have a gun, yet defines default values for gun.
gun = {ROBOT_FALLBACK['gun']}
gun_bullet_speed = {ROBOT_FALLBACK['gun_bullet_speed']}
gun_reload_speed = {ROBOT_FALLBACK['gun_reload_speed']}
# ADD: Add config option for gun_type here.
# Available gun options: trigun
gun_options = {ROBOT_FALLBACK['gun_options']}

# Default robot doesn't have a player_control, yet defines default values.
player_control = {ROBOT_FALLBACK['player_control']}
invasive_controls = {ROBOT_FALLBACK['invasive_controls']}
invasive_controls_turn_rate = {ROBOT_FALLBACK['invasive_controls_turn_rate']}
# Add one of the privded key bindings. Create new key bindings in code.
keys = {ROBOT_FALLBACK['keys']}

# Deploy the following robots:
# Only define non-default values.
# ALWAYS define a starting position.
# Defining invalid position values will not create the robot.
[robo1]
radius = 4
a_max = 20
max_life = 5

# Define position value as x,y
# ALWAYS define a starting position.
position = 500, 700
alpha = 75

# Robots must have a movement AI.
movement = RunMovement

[robo2]
a_max = 12
max_life = 1

# Define position value as x,y
# ALWAYS define a starting position.
position = 45, 845

# Robots must have a movement AI.
# Add movement arguments separated by comma.
movement = ChaseMovementGun, robo1

# Activate and customize gun:
gun = True
gun_options = trigun

# Activate and customize player control:
player_control = True
keys = player_two_scheme

[robo3]
radius = 2.5
a_max = 5
a_alpha_max = 15
v_max = 12
v_alpha_max = 30

# Define position value as x,y
# ALWAYS define a starting position.
position = 965, 35
alpha = 240

# Robots must have a movement AI.
movement = PermanentGunMovement

# Activate the gun:
gun = True

# Activate and customize player control:
player_control = True
# Activate special invasive control mechanism:
invasive_controls = True

[robo4]
radius = 2
a_alpha_max = 15
immunity_timer = 10

# Define position value as x,y
# ALWAYS define a starting position.
position = 300, 650
alpha = 70

# Robots must have a movement AI.
movement = ChaseAvoidMovementGun, robo1

# Activate and customize gun:
gun = True
gun_bullet_speed = 30
"""


class ConfigReader:
    """Config reader class will parse game data from config.
    First read the data from config, then you can create the respective object.
    Caution! Changing the level after reading data for the robots
    may cause huge trouble!
    """

    DEFAULT_SECTION = 'BASE'

    def __init__(self):
        self.fallback = ROBOT_FALLBACK

        self.config = configparser.ConfigParser(default_section=None)
        self.config.BOOLEAN_STATES['True'] = True
        self.config.BOOLEAN_STATES['False'] = False

        self.sections = None

        self.obstacle_array = utils.create_example_array(TILE_COUNT)

        self.robo_name_space = []

        self.level_read_alert = False

    def read_level(self, level_name):
        # this implementation expects hazard class in server module to
        # have the same global constant.
        HAZARD_BORDER = 2

        ConfigReader.ensure_configs_folder()

        path = os.path.join(CONFIG_FOLDER, level_name)
        if not os.path.exists(path):
            return

        result = []

        with open(path, 'r') as f:
            map_string = f.read()

        map_rows = map_string.split('\n')
        row_amount = len(map_rows)

        for row in map_rows:
            tiles = [int(tile) for tile in list(row)]

            if len(tiles) != row_amount:
                raise ValueError('Maps must be square!')

            result.append(tiles)

        # construct north and south borders!
        result[0] = [HAZARD_BORDER] * row_amount
        result[-1] = [HAZARD_BORDER] * row_amount

        # transpose constructed list of lists to allow matrix like access
        result = list(map(list, zip(*result)))

        # construct west and east borders (same thing, because transpose!)
        result[0] = [HAZARD_BORDER] * row_amount
        result[-1] = [HAZARD_BORDER] * row_amount

        self.obstacle_array = result

    def create_level(self, read_first=True):
        if read_first:
            self.read_level(MAP_CONFIG)

        return self.obstacle_array

    def read_robots(self):

        ConfigReader.ensure_configs_folder()

        path = os.path.join(CONFIG_FOLDER, ROBOT_CONFIG)
        if not os.path.exists(path):
            ConfigReader.create_robot_config(path)

        self.config.read(path)

        sect = self.config.sections()
        # We don't use a default section.
        sect.remove(ConfigReader.DEFAULT_SECTION)
        # Only parse the first N robots.
        sect = sect[:MAX_ROBOT_COUNT]

        self.sections = sect

        self.robo_name_space = []

    def create_robots(self, read_first=True):
        if read_first:
            self.read_robots()

        if not self.sections:
            return []

        robo_list = []

        for robot_name in self.sections:

            # scale radius with tile size
            radius = TILE_SIZE * self.cast_with_fallback(
                robot_name, 'radius', float, Validators.validate_radius)
            position = self.assemble_position(robot_name)
            # If the spawn position is invalid, don't create the robot.
            if not position or self.spawn_position_invalid(radius, position):
                continue

            # validate body parameters
            a_max = self.cast_with_fallback(
                robot_name, 'a_max', float, Validators.validate_gr_eq_zero)
            a_alpha_max = self.cast_with_fallback(
                robot_name, 'a_alpha_max', float,
                Validators.validate_gr_eq_zero)
            v_max = self.cast_with_fallback(
                robot_name, 'v_max', float, Validators.validate_gr_eq_zero)
            v_alpha_max = self.cast_with_fallback(
                robot_name, 'v_alpha_max', float,
                Validators.validate_gr_eq_zero)
            fov_angle = self.cast_with_fallback(
                robot_name, 'fov_angle', float, Validators.validate_fov_angle)
            max_life = self.cast_with_fallback(
                robot_name, 'max_life', int, Validators.validate_greater_zero)
            respawn_timer = self.cast_with_fallback(
                robot_name, 'respawn_timer', float,
                Validators.validate_gr_eq_zero)
            immunity_timer = self.cast_with_fallback(
                robot_name, 'immunity_timer', float,
                Validators.validate_gr_eq_zero)
            auto_resync = self.cast_with_fallback(
                robot_name, 'auto_resync', ini_bool, Validators.cast_only)

            # validate additional position parameter
            alpha = self.cast_with_fallback(
                robot_name, 'alpha', lambda s: float(s) % 360,
                Validators.cast_only)

            # validate gun parameters
            gun_exists = self.cast_with_fallback(
                robot_name, 'gun', ini_bool, Validators.cast_only)
            gun_bullet_speed = self.cast_with_fallback(
                robot_name, 'gun_bullet_speed', float,
                Validators.validate_greater_zero)
            gun_reload_speed = self.cast_with_fallback(
                robot_name, 'gun_reload_speed', float,
                Validators.validate_gr_eq_zero)
            gun_options = self.assemble_gun_options(robot_name)

            # validate player control parameters
            player_control_exists = self.cast_with_fallback(
                robot_name, 'player_control', ini_bool, Validators.cast_only)
            invasive_controls = self.cast_with_fallback(
                robot_name, 'invasive_controls', ini_bool,
                Validators.cast_only)
            invasive_controls_turn_rate = self.cast_with_fallback(
                robot_name, 'invasive_controls_turn_rate', float,
                Validators.validate_gr_eq_zero)
            # key bindings
            keys_string = self.cast_with_fallback(
                robot_name, 'keys', lambda x: x, Validators.validate_keys)
            keys = getattr(ControlScheme, keys_string)

            # Finally create the robot:
            # -------------------------
            # first create the robot's body
            base_robot = BaseRobot(radius, a_max, a_alpha_max,
                                   v_max, v_alpha_max,
                                   fov_angle, max_life,
                                   respawn_timer, immunity_timer)

            # then create the AI controller
            robot_control = RobotControl(base_robot)

            # with this, create the data representation
            data_robot = DataRobot(base_robot, robot_control)

            # create and add the defined gun object
            gun_object = RoboGun(gun_bullet_speed, gun_reload_speed)
            for decorator in gun_options:
                gun_object = decorator(gun_object)

            if gun_exists:
                data_robot.setup_gun(gun_object)

            # create and add the defined player control instance
            player_control_inst = PlayerControl(data_robot, keys,
                                                invasive_controls,
                                                invasive_controls_turn_rate)

            if player_control_exists:
                data_robot.setup_player_control(player_control_inst)

            # place the robot at the right position
            pos = (position[0], position[1], alpha, 0, 0)
            data_robot.place_robot(*pos)

            # add the robot to the list
            robo_list.append(data_robot)
            self.robo_name_space.append(robot_name)

        # after all robots are created, we can validate and add the movements
        for robot_name, robot in zip(self.robo_name_space, robo_list):
            robo_movement = self.assemble_movement(robot_name)
            robot.setup_movement(robo_movement)

        # now set the alert flags
        self.set_alert_flags(robo_list)

        return robo_list

    def cast_with_fallback(self, section, option, type_, validation):
        section_val = self.config[section].get(option, None)
        default_val = self.config[ConfigReader.DEFAULT_SECTION].get(
            option, None)
        fallback_val = self.fallback.get(option, None)

        if section_val is not None:
            try:
                section_val = type_(section_val)
                valid = validation(section_val)
            except ValueError:
                pass
            else:
                if valid:
                    return section_val

        if default_val is not None:
            try:
                default_val = type_(default_val)
                valid = validation(default_val)
            except ValueError:
                pass
            else:
                if valid:
                    return default_val

        # we expect the fallback to exist and to be valid
        return fallback_val

    def assemble_position(self, section):
        """Parse the position string at the current section.
        If the string is missing or invalid, return None."""

        position_string = self.config[section].get('position', None)
        if not position_string:
            return None

        position_list = split_string_list(position_string)
        if len(position_list) < 2:
            return None

        final_positions = []
        for entry in position_list[:2]:
            try:
                value = int(entry)
            except ValueError:
                return None
            else:
                valid = Validators.validate_position(value)
                if not valid:
                    return None

                final_positions.append(value)

        return tuple(final_positions)

    def spawn_position_invalid(self, radius, position_tuple):
        """A spawn position is valid, if the robot defined by radius
        and position_tuple doesn't overlap with in parsed obstacle_array."""
        center = QPoint(*position_tuple)

        for x in range(TILE_COUNT):
            for y in range(TILE_COUNT):
                if self.obstacle_array[x][y]:
                    rect = QPoint(x * TILE_SIZE, y * TILE_SIZE)
                    if utils.check_collision_circle_rect(center, radius, rect,
                                                         TILE_SIZE, TILE_SIZE):
                        return True

        return False

    def assemble_gun_options(self, section):
        """Parse gun options string based on RoboGun.available_gun_options().
        We expect the fallback to exist and to be valid."""
        go_dictionary = RoboGun.available_gun_options()
        go_valid = set(go_dictionary.keys())

        section_val = self.config[section].get('gun_options', None)
        if section_val is not None:
            if not section_val:
                return tuple()

            section_val_set = set(split_string_list(section_val))
            valid_list_items = tuple(go_valid.intersection(section_val_set))

            if valid_list_items:
                return tuple(go_dictionary[i] for i in valid_list_items)

        default_sect = self.config[ConfigReader.DEFAULT_SECTION]
        default_val = default_sect.get('gun_options', None)
        if default_val is not None:
            if not default_val:
                return tuple()

            default_val_set = set(split_string_list(default_val))
            valid_list_items = tuple(go_valid.intersection(default_val_set))

            if valid_list_items:
                return tuple(go_dictionary[i] for i in valid_list_items)

        fallback_val = tuple()
        fallback_string = self.fallback.get('gun_options', None)
        if fallback_string:
            fallback_list = split_string_list(fallback_string)
            fallback_val = tuple(go_dictionary[i] for i in fallback_list)

        return fallback_val

    def assemble_movement(self, section):
        """Parse movement string and movement options
        into movement class instance.
        Available movements are based on AVAILABLE_MOVEMENTS set.
        Options are validated based on OPTIONS parameter defined in movement.
        """

        section_val = self.config[section].get('movement', None)
        if section_val:
            movement_list = split_string_list(section_val)
            movement_name = movement_list[0]
            movement_option_list = movement_list[1:]
            if movement_name in AVAILABLE_MOVEMENTS:
                movement_class = getattr(movement, movement_name)
                options_valid, option_list = self.assemble_movement_options(
                    movement_class.OPTIONS, movement_option_list)
                if options_valid:
                    return movement_class(*option_list)

        default_sect = self.config[ConfigReader.DEFAULT_SECTION]
        default_val = default_sect.get('movement', None)
        if default_val:
            movement_list = split_string_list(default_val)
            movement_name = movement_list[0]
            movement_option_list = movement_list[1:]
            if movement_name in AVAILABLE_MOVEMENTS:
                movement_class = getattr(movement, movement_name)
                options_valid, option_list = self.assemble_movement_options(
                    movement_class.OPTIONS, movement_option_list)
                if options_valid:
                    return movement_class(*option_list)

        # Fallback value must exist and be valid.
        fallback_string = self.fallback.get('movement', None)
        fallback_list = split_string_list(fallback_string)
        fallback_name = fallback_list[0]
        fallback_option_list = fallback_list[1:]
        fallback_class = getattr(movement, fallback_name)
        _, parsed_option_list = self.assemble_movement_options(
            fallback_class.OPTIONS, fallback_option_list)

        return fallback_class(*parsed_option_list)

    def assemble_movement_options(self, movement_class_list, user_option_list):
        """Parse list of input movement option strings
        into list of movement arguments.
        For validation of options use movement_class_list:
        a list of needed movement options in order, defined by movement class.
        For value validations use movement_validators lookup table,
        that maps possible movement options to validator function.
        Return tuple of (bool: valid?, parsed list if valid).
        """
        # ADD: When you add a new movement option,
        # add a mapping to the validator here:
        movement_validators = {
            movement.TARGET_OPTION_STRING: self.validate_target_option}

        result_list = []

        # not enough options given by user
        if len(user_option_list) < len(movement_class_list):
            return False, None

        for user_opt, mov_opt in zip(user_option_list, movement_class_list):
            validator = movement_validators[mov_opt]
            option_valid, option_value = validator(user_opt)
            if not option_valid:
                return False, None
            result_list.append(option_value)

        return True, result_list

    def validate_target_option(self, value):
        """Validator for movement option 'target'.
        Target robo name will be mapped to robot index if valid.
        If invalid, return (False, None).
        """
        if value in self.robo_name_space:
            return (True, self.robo_name_space.index(value))
        return False, None

    def set_alert_flags(self, robo_list):
        """Set alert flags for robots in robo_list based on config
        and auto vals given by movement class."""

        fallback_val = self.fallback.get('alert_flag', None)

        default_sect = self.config[ConfigReader.DEFAULT_SECTION]
        flag_auto = default_sect.getboolean('alert_flag', None)
        if flag_auto is None:
            flag_auto = fallback_val

        for robo_name, robot in zip(self.robo_name_space, robo_list):
            section_val = self.config[robo_name].getboolean('alert_flag', None)
            if section_val is None:
                if flag_auto:
                    robot.set_alert_flag(
                        robot.robot_control.movement_funct.RECEIVE_ALERT)
            else:
                robot.set_alert_flag(section_val)

    @staticmethod
    def ensure_configs_folder():
        if not os.path.isdir(CONFIG_FOLDER):
            os.mkdir(CONFIG_FOLDER)

    @staticmethod
    def create_robot_config(path):
        with open(path, 'w') as f:
            f.write(EXAMPLE_ROBOT_CONFIG_STR)


class Validators:
    """Container class for simple validators."""
    @staticmethod
    def validate_radius(value):
        return value > 0.5

    @staticmethod
    def validate_position(value):
        return 0 <= value < FIELD_SIZE

    @staticmethod
    def validate_greater_zero(value):
        return 0 < value

    @staticmethod
    def validate_gr_eq_zero(value):
        return value >= 0

    @staticmethod
    def validate_fov_angle(value):
        return 0 <= value <= 360

    @staticmethod
    def validate_keys(value):
        return value in AVAILABLE_KEY_BINDINGS

    @staticmethod
    def cast_only(_):
        return True


# helper methods:
# ===============

def split_string_list(string: str):
    return tuple(s.strip() for s in string.strip().split(','))


def ini_bool(string: str):
    string = string.lower()
    boolean_states = configparser.ConfigParser.BOOLEAN_STATES

    if string in boolean_states:
        return boolean_states[string]

    raise ValueError
