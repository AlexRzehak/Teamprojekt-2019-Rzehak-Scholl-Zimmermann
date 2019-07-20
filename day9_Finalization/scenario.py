import os
import configparser

FIELD_SIZE = 1000
TILE_SIZE = 10


# TODO Completely ignore this file for now.

CONFIG_FOLDER = 'configs'
GLOBAL_CONFIG = 'global.ini'
ROBOT_CONFIG = 'robots.ini'
MAP_CONFIG = 'map.ini'


def read_configs():
    if os.path.isdir(CONFIG_FOLDER):
        read_config_file()
    else:
        create_configs_folder()


def read_config_file():
    print('hanzo')


def create_configs_folder():
    os.mkdir(CONFIG_FOLDER)


# bullshit. so much bullshit
RADIUS_STRING = 'radius'  # TODO tile_Size * multiplier?
A_MAX_STRING = 'a_max'
A_ALPHA_MAX_STRING = 'a_alpha_max'
V_MAX_STRING = 'v_max'
V_ALPHA_MAX_STRING = 'v_alpha_max'
FOV_ANGLE_STRING = 'fov_angle'
RESPAWN_TIMER_STRING = 'respawn_timer'
IMMUNITY_TIMER_STRING = 'immunity_timer'
MAX_LIFE_STRING = 'max_life'

AUTO_RESYNC_STRING = 'auto_resync'


PLAYER_CONTROL_STRING = 'player_control'
GUN_STRING = 'gun'
POSITION_STRING = 'position'
MOVEMENT_STRING = 'movement'

ALERT_FLAG_STRING = 'alert_flag'

TICKRATE_STRING = 'tickrate'
TILE_SIZE_STTRING = 'tile_size'
FIELD_SIZE_STRING = 'field_size'

INVASIVE_CONTROL_STRING = 'invasive_control'
INVASIVE_CONTROL_TR_STRING = 'invasive_control_turn_rate'

BULLET_SPEED_STRING = 'bullet_speed'
RELOAD_SPEED_STRING = 'reload_speed'
GUN_TYPE_STRING = 'type'
GUN_OPTIONS_STRING = 'options'

# MOVEMENT???????


if __name__ == "__main__":
    read_configs()
