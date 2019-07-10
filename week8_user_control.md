# Week 8: Add Player Controls

### [<- Back](/index.md) to project overview.

### Up until now, we were nothing but passive observers. It's time to get cookin' as well!

## Measurement: Numbers, Facts, Data
### But before we hop intothis weeks task, let's discuss something else:<br/> Our Program has become quite big with the time and because of all the features, it got a bit laggy.<br/> Now we want to analyse this in more detail.

### We use the `default_timer()` oder python's very precise `timeit` library to check the runtime of each part of the program.
```python
from timeit import default_timer

timer1 = default_timer()
# part of the program [...]
timer2 = default_timer()
runtime_of_part = timer2 - timer1
```
### We yield the following results (unweighted average):
```python
# bullet creation and movement
0.0029460720000002993
# robot movement
0.00029446100000019015
# robot collision
0.00019252199999986175
# vision
0.00465429900000025
# sending messages
0.00009063939999993664
```
We can see that the most stressful parts are the bullets and vision calculations.
### But let's look at the total values:
```python
# calculations in one game loop
0.009213357000000144
# intended tick rate
0.033
# real tick rate - averidge value
0.04804616999999212
# real tick rate - peak value
0.09471527299999982
```
### As you can see, the actual time needed for our calculations stays way below the intended tick rate! But the real tickrate keeps exceeding this crucial value.<br/>That's not all - it yields a huge variance of values! 
### To see what's happening, we take some more closer looks at the non-main-loop parts of our program:
```python
# movement functions
7.223199999994989e-05

# this is some seriously low value. These threads will not get in the way of Qts timer!

# update draw
0.03072390700000005
```
### This looks way more like our culprit: Since we didn't separate the calculation update rate from our frame rate, the draw actions slow down the speed our our tick rate.
### But even the draw update function will not explain the huge variance with nearly equal calculation times.
### We take a closer look at Qt's structure and find our that the timers accuracy is hindered by Qt's other scheduling mechanisms. Once we entered the game loop, Qt is not able to switch context to perform other operations - therefore those operations will take a huge time between the ticks.
### That is some bad and some good news: The bad part is, that Qt's timer is not well suited for game loops of more complex games.
### The good part is that we might be able to improve the performance of our program by separating the tick rate from the frame rate, using other mechanisms like multi-threading or python timers.
### But this is another weeks task. Let's get our work done, first!

# Task: Implement User Controls
### We now want to be albe to control the robots via keyboard input.
### Let's map some different key bindings:
```python
class ControlScheme:
    ACC_STRING = 'accelerate'
    ACC_REV_STRING = 'accelerate_reverse'
    LEFT_STRING = 'left'
    RIGHT_STRING = 'right'
    SHOOT_STRING = 'shoot'

    default_scheme = {Qt.Key_W: ACC_STRING,
                      Qt.Key_S: ACC_REV_STRING,
                      Qt.Key_A: LEFT_STRING,
                      Qt.Key_D: RIGHT_STRING,
                      Qt.Key_J: SHOOT_STRING}

    player_two_scheme = {Qt.Key_Up: ACC_STRING,
                         Qt.Key_Down: ACC_REV_STRING,
                         Qt.Key_Left: LEFT_STRING,
                         Qt.Key_Right: RIGHT_STRING,
                         Qt.Key_Return: SHOOT_STRING}
```
### Now we add a new class, that can be set up in the data representation. This class will control the `data_robot` with key inputs, taking the place of the output of a `thread_robot`.
```python
class PlayerControl:
    ACCEL_AMT = 3
    ALPHA_ACCEL_AMT = 5

    def __init__(self, data_robot, control_scheme, gun, accel_amt=None,
                 alpha_accel_amt=None):

        # define key binding
        self.control_scheme = control_scheme

        # access to both gun and data robot
        self.gun = gun
        self.data_robot = data_robot

        # these values will be controlled
        self.a = 0
        self.a_alpha = 0

        # the responsiveness of our controls
        # how much do we change the values in one button press?
        if not accel_amt:
            accel_amt = PlayerControl.ACCEL_AMT
        self.accel_amt = accel_amt
        if not alpha_accel_amt:
            alpha_accel_amt = PlayerControl.ALPHA_ACCEL_AMT
        self.alpha_accel_amt = alpha_accel_amt

    # enact the different functions mapped by the key bindings
    def calculate_key_action(self, key):
        action_name = self.control_scheme[key]
        action = getattr(self, action_name)
        action()

    def accelerate(self):
        self.a += self.accel_amt

    def accelerate_reverse(self):
        self.a -= self.accel_amt

    def left(self):
        self.a_alpha -= self.alpha_accel_amt

    def right(self):
        self.a_alpha += self.alpha_accel_amt

    def shoot(self):
        self.gun.prepare_fire()

    # when the server wants to know the acceleration values (poll),
    # send these manipulated values.
    def send_action_data(self):
        return self.a, self.a_alpha
```
## Problem: Inconsistent OS Input
### Unfortunately, this solution is far from working.
### When we press a key, the OS will send a key press event. Then, after the key keeps pressed for a while, it will process to send additional key press events for the same key in some predetermined intervall.
### This is a PROBLEM, since this intervall does not align with our server tick rate!
### Even worse, if a second key is pressed, the OS will STOP SENDING these regular key press events for a pressed key AT ALL, only enacting this behaviour for the newest pressed key.
### It is obvious, that for gaming, let alone multiplayer, this behaviour is quite impractical.

## Solution: Smooth gaming controls key map
### Fortunately, most games already present a solution to this problem:
### The OS does not just know how to send key press events, it can trigger key release events as well.
### We make use of this to store in a dictionary, which key is pressed right now. The game will use this accurate list to check which key is pressed and which is not instead of the unreliable OS input.
```python
class Board(QWidget):

    def __init__(self, parent):

        self.key_states = dict()
        self.initiate_key_listening()

        # [...]

    # if a key is pressed, enter it in the dictionairy
    def keyPressEvent(self, event):
        key = event.key()
        self.key_states[key] = True

    # if a key is realeased, take note in the dictionairy
    def keyReleaseEvent(self, event):
        key = event.key()
        self.key_states[key] = False

    # For all tracked keys relay the state to the player control
    def handle_keys_with_state(self):
        for key, value in self.key_stats.items():
            if value:
                for robot in self.robots:
                    robot.enter_key_action(key)

    # call the functions each game loop
    def timerEvent(self, event):

        self.handle_keys_with_state()

        self.calculate_shoot_action()

        # [...]    
```
### Now at every server tick, we will enter the actual currently pressed keys and perform the corresponding action.
### Yet, the game still doesn't feel right. We encounter another Problem:

## Problem: Lost Key Presses
### This method only notices, if a key is hold down at a full server tick.
### If we press a key fast enough, it might happen 'in between the ticks' - the key press event and key release event will pass without the server noticing and player input will be lost!
### We might decide that this is just how the game works and that we need to hold down the keys for a bit longer. But let's do the test first...
### We implement a counter that will keep track of lost key inputs:
```python
class Board(QWidget):

    def __init__(self, parent):
        self.total_key_presses = 0
        self.known_key_presses = 0

    def keyPressEvent(self, event):
        key = event.key()
        
        # These key presses will actually happen
        self.total_key_presses += 1
        self.key_states[key] = True

    def handle_keys_with_state(self):
        for key, value in self.key_stats.items():
            if value:
                # The server will notice these key presses
                self.known_key_presses += 1
                for robot in self.robots:
                    robot.enter_key_action(key)
```
### Now we play the game, maybe trying to tap the keys a bit quicke and shorter as usual.
### The results are shocking:
```python
# On average, we measure for about 100 key presses:
self.total_key_presses = 103
self.known_key_presses = 46
```
## More than HALF OF THE PLAYER INPUT will get lost!
That's why I couldn't manage my robot properly - it's not because I suck at the controls, it's because the controls just ignore my input!

## Solution: Dual-State-Check
### Since the button presses 'between the ticks' get lost, we need an additional method to track them down as well.
### We modify our key state dictionary, to also remember, if the key WAS PRESSED (but maybe released again) between the ticks:
```python
    # structure of the key_state dictionary: it maps a Qt.Key to a state_dictionary
    self.key_states = {key : {'is_pressed': bool,
                              'was_pressed' : bool,
                              'target_robots' : tuple}}
```
### While doing this, we find out, that some key actions require this state information, while other key actions just want to know, if they were pressed once.
### We distinguish KEYS WITH STATE from SINGLE SHOT KEYS or STATELESS KEYS.
### Since this dictionary is more complex, we need a function to perform the setup at the start of our game:
```python
class Board(QWidget):
     def __init__(self, parent):

        self.key_states = dict()
        self.stateless_keys = dict()

         self.initiate_key_listening()

    def initiate_key_listening(self):
        # here, we activate key control at all
        self.setFocusPolicy(Qt.StrongFocus)

        # the target robots will be stored in tuples later
        # (they are the fastest data container type to iterate)
        # But since they are immutable, we need to construct them as lists first.
        collected_keys_states = dict()
        collected_keys_stateless = dict()

        # track down all the keys used
        for robot in self.robots:
            if robot.player_control:
                robot_keys = robot.player_control.control_scheme
                for key, value in robot_keys.items():
                    # distinguish stateless keys from keys with state
                    if value.is_stateless()
                        # add robot to collected_keys_stateless
                    else:
                        # add robot to collected_keys_states

        # set up both dictionaries
        for key, value in collected_keys_states.items():
            self.key_states[key] = dict(is_pressed=False,
                                        was_pressed=False,
                                        targets=tuple(value))

        for key, value in collected_keys_stateless.items():
            self.stateless_keys[key] = tuple(value)
```
### Now we need to modify the key listeners as well:
```python
class Board(QWidget):

    def keyPressEvent(self, event):
        key = event.key()

        # we send stateless key presses directly to the robot
        if key in self.stateless_keys:
            for robot in self.stateless_keys[key]:
                # here state is None
                robot.enter_key_action(key)

        # set state variables for keys with state
        if key in self.key_states:
            key_dict = self.key_states[key]
            key_dict['is_pressed'] = True
            key_dict['was_pressed'] = True
    
    def keyReleaseEvent(self, event):
        key = event.key()

        # set state variables for keys with state
        if key in self.key_states:
            key_dict = self.key_states[key]
            key_dict['is_pressed'] = False

    def handle_keys_with_state(self):
        for key, value in self.key_states.items():
            # state is acitve
            if value['is_pressed'] or value['was_pressed']:
                value['was_pressed'] = False
                for robot in value['targets']:
                    robot.enter_key_action(key, state=True)
            # state is inactive
            else:
                for robot in value['targets']:
                robot.enter_key_action(key, state=False)
```
### The PlayerControl object also needs to distinguish stateless keys and keys with state:
```python
class DataRobot(BaseRobot):

    def enter_key_action(self, key, state=None):
        if self.player_control:
            self.player_control.calculate_key_action(key, state)

class PlayerControl:

    def calculate_key_action(self, key, state):
        action_name = self.control_scheme[key]
        action = getattr(self, action_name)
        # stateless
        if state is None:
            action()
        # key with state
        else:
            action(state_active=state)
```
### With this problem being fixed, we straight up encounter the next one!

## Problem: Entwined Keys
### Some key actions appear to be in a close relation with each other (like accelerate and accelerate reverse).
What happens to the other one if one of the keys is pressed.<br/>
What happens, if BOTH keys are pressed at the same time!

### This is a non-trivial matter, since because `handle_keys_with_state` calls the mapped functions one by one and not at the same time, improper handling might lead to major bugs like key input being ignored completely!

## Solution: Entwined Keys Finite State Machine
### We keep track of the different key states of each of the entwined key pairs:
```python
class PlayerControl:

    # Extended state control:
    # We only need 'not-pressed', 'down-flank' and 'pressed' for this task.
    # The "up-flank" migth be needed later.
    STATE_ACTIVE = "A"
    STATE_PUSH = "D"
    STATE_INACTIVE = "I"
    # STATE_RELEASE = "U"
```
### Instead of performing the key action when `handle_keys_with_state` calls it, we just change the state of the key.
```python
class PlayerControl:

    # This sictionary maps former states and tracked states
    # to the extended state control.
    STATE_SWITCH = {(STATE_ACTIVE, True): STATE_ACTIVE,
                    (STATE_INACTIVE, True): STATE_PUSH,
                    (STATE_PUSH, True): STATE_ACTIVE,
                    (STATE_ACTIVE, False): STATE_INACTIVE,
                    (STATE_INACTIVE, False): STATE_INACTIVE,
                    (STATE_PUSH, False): STATE_INACTIVE}

    def __init__(self, data_robot, control_scheme, gun, accel_amt=None,
                 alpha_accel_amt=None):

        # State Machine for acc-rev_acc entwinement
        self.acc_state = PlayerControl.STATE_INACTIVE
        self.acc_rev_state = PlayerControl.STATE_INACTIVE

        # State Machine for left-right entwinement
        self.left_state = PlayerControl.STATE_INACTIVE
        self.right_state = PlayerControl.STATE_INACTIVE

    def accelerate(self, state_active):
        lookup_tuple = (self.acc_state, state_active)
        self.acc_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def accelerate_reverse(self, state_active):
        lookup_tuple = (self.acc_rev_state, state_active)
        self.acc_rev_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def left(self, state_active):
        lookup_tuple = (self.left_state, state_active)
        self.left_state = PlayerControl.STATE_SWITCH[lookup_tuple]

    def right(self, state_active):
        lookup_tuple = (self.right_state, state_active)
        self.right_state = PlayerControl.STATE_SWITCH[lookup_tuple]
```
### After all states are set, a second function will run above the state pairs, evaluating what action should be performed.
### The function will use the lookup-dictionaries, implementing the following state-function-mappings:
Acceleration:
| acc | acc_rev| function |
| :-: |:-:| :- |
| I | I | a = 0 |
| I | A | acc_rev |
| I | D | acc_rev |
| A | I | acc |
| A | A | keep_current | 
| A | D | acc_rev |
| D | I | acc |
| D | A | acc |
| D | D | acc |

Angle Rotation:
| left | right | function |
| :-: |:-:| :- |
| I | I | a_alpha = 0 |
| I | A | right |
| I | D | right |
| A | I | left |
| A | A | keep_current | 
| A | D | right |
| D | I | left |
| D | A | left |
| D | D | a_alpha = 0 |

### That way, we always give priority to the most recent pressed key.
### We can also handle, what happens, if we press both keys at the same time.
### Let's take a look at those functions to call:
```python
    def __init__(self, *args):

        def acc():
            self.a = self.accel_amt

        def rev_acc():
            self.a = -1 * self.accel_amt

        def clear_acc():
            self.a = 0

        def acc_pass():
            pass

        # the functions for left and right are analogous:
        def lr_left():
            self.a_alpha = - 1 * self.alpha_accel_amt

        def lr_right():
            self.a_alpha = self.alpha_accel_amt

        def clear_lr():
            self.a_alpha = 0

        def lr_pass():
            pass
```
### Now the control flow for the state machine:
```python
class Board(QWidget):

    def handle_keys_with_state(self):
        for key, value in self.key_states.items():
            # [...]

        # at the end of the function, evaluate the current state
        # and perform the respective functions
        for robot in self.robots:
            robot.finish_key_actions()

class DataRobot(BaseRobot):

    def finish_key_actions(self):
        if self.player_control:
            self.player_control.enter_entwined_keys()

class PlayerControl:

    def enter_entwined_keys(self):
        self.enter_accelarate()
        self.enter_left_right()

    # use lookup table dictionaries for the states
    def enter_accelarate(self):
        lookup_tuple = (self.acc_state, self.acc_rev_state)
        func = self.acc_lookup[lookup_tuple]
        func()

    def enter_left_right(self):
        lookup_tuple = (self.left_state, self.right_state)
        func = self.lr_lookup[lookup_tuple]
        func()
```
### Finally, we can drive the robots around with some neat floaty space control.

# Task: Add an Access Right System
### Our robots can now be controlled by both, player or `thread_robot`.<br/>To prevent potential side effects, we need to make sure, that the data robot always knows who is in charge and only passes information to and from that control mechanism.
### This might also come in handy to conpletely disable controls when a robot gets destroyed!
### We need to make some changes to the `data_robot` to manage control access and gun acces:
```python
class DataRobot(BaseRobot):

    def __init__(self, base_robot: BaseRobot, thread_robot: ThreadRobot):

        # Access management system:
        self.player_input_enabled = True  # inactive for now
        self.player_output_enabled = False
        self.robot_input_enabled = True
        self.robot_output_enabled = True

        self.gun_enabled = False
```
### These booleans should be put to work!
```python
class DataRobot(BaseRobot):

    # send values for a and a_alpha to the server
    def poll_action_data(self):

        # note, that the player output will overwrite thread_robot output
        if self.player_output_enabled:
            return self.player_control.send_action_data()

        if self.robot_output_enabled:
            return self.thread_robot.send_action_data()

        # both outputs are disabled
        default_data = (0, 0)
        return default_data

    # only send input to the robot, if it is enabled!
    def send_sensor_data(self, data):
        if self.robot_input_enabled:
            self.thread_robot.receive_sensor_data(data)

    def perform_shoot_action(self):

        maybe_bullet = False

        # if the gun is disabled, no bullet will be shot
        if not self.gun or not self.gun_enabled:
            return maybe_bullet

        maybe_data = self.gun.trigger_fire()        
        # [...]
```
### Now we only need the matching functions to perform the access right management:
```python
class DataRobot(BaseRobot):
    
    def disable_robot_control(self):
        self.robot_output_enabled = False
        self.robot_input_enabled = False

        self.thread_robot.clear_input()

    def enable_robot_control(self):
        self.thread_robot.clear_input()
        self.thread_robot.clear_values()
        self.robot_input_enabled = True
        self.robot_output_enabled = True

    def disable_player_control(self):
        self.player_output_enabled = False

    def enable_player_control(self):
        self.player_output_enabled = True

    def disable_robot_gun_access(self):
        if self.gun:
            self.gun.set_gun_access_robot(False)
            self.gun.clear_input()

    def enable_robot_gun_access(self):
        if self.gun:
            self.gun.clear_input()
            self.gun.set_gun_access_robot(True)


    def disable_player_gun_acess(self):
        if self.gun:
            self.gun.set_gun_access_player(False)
            self.gun.clear_input()

    def enable_player_gun_access(self):
        if self.gun:
            self.gun.clear_input()
            self.gun.set_gun_access_player(True)

    def disable_gun(self):
        self.gun_enabled = False
        self.disable_player_gun_acess()
        self.disable_robot_gun_access()

    def enable_gun(self):
        self.gun_enabled = True
        if self.player_control:
            self.enable_player_gun_access()
        else:
            self.enable_robot_gun_access()
```
### Note, that we clear the input queues for robot and gun whenever we enable/disable the access to prevent execution of outdated commands as well as multi-threading issues.
### We just need to implement the missing functions in the gun. For this, we need to route the robot's and player's gun access over additional interface functions:
```python
class RoboGun:
    
    def __init__(self, bullet_speed=None):

        self.gun_access_player = False
        self.gun_access_robot = False

    def set_gun_access_player(self, value):
        self.gun_access_player = value

    def set_gun_access_robot(self, value):
        self.gun_access_robot = value

    def clear_input(self):
        # never use join
        self.fire_queue.queue.clear()

    def prepare_fire_robot(self, data=True):
        if self.gun_access_robot:
            self.prepare_fire(data)

    def prepare_fire_player(self, data=True):
        if self.gun_access_player:
            # make sure to only enqueue one shot at a time
            # to always shoot at button press!
            if not (self.is_preparing() or self.is_reloading()):
                self.prepare_fire(data)

    def prepare_fire(self, data):
        # will enqueue the fire command [...]

# make sure that the GunInterface also points to the right function!
class GunInterface:
    def __init__(self, gun: RoboGun):

        self.is_preparing = gun.is_preparing
        self.is_reloading = gun.is_reloading
        self.prepare_fire = gun.prepare_fire_robot
```

### What kind of stuff can we do with this improved security now?

## Feature: Toggle Autopilot
### To put these functions to good use, we add a new functionality that allows us to switch controls over a robot between player and `thread_robot`!
```python
class DataRobot(BaseRobot):

    def __init__(self, base_robot: BaseRobot, thread_robot: ThreadRobot):

        # keep track if a player or a robot is in charge!
        self.player_control_active = False

    def toggle_player_control(self):
        # we can't toggle while dead
        if self.dead:
            return

        if self.player_control_active:
            self.hand_control_to_robot()
        else:
            self.hand_control_to_player()

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

    # now we can implement the enable_gun function properly as well:
    def enable_gun(self):
        self.gun_enabled = True
        # either hand control to the robot or to the player
        if self.player_control_active:
            self.enable_player_gun_access()
        else:
            self.enable_robot_gun_access()

```
### This functionality should be reachable via keyboard controls as well:
```python
class PlayerControl:

    def __init__(self, *args):

        self.allow_toggle_autopilot = True

    # to prevent a player from switching like a madman,
    # we add a small cooldown to the key
    def toggle_autopilot(self):
        if self.allow_toggle_autopilot:
            self.data_robot.toggle_player_control()

            def enable_toggle():
                self.allow_toggle_autopilot = True

            self.allow_toggle_autopilot = False
            Utils.execute_after(0.5, enable_toggle)
```
### With the right system in place, we can now re-implement the setup functions for `PlayerControl` and guns:
```python
class DataRobot(BaseRobot):

    def setup_player_control(self, player_control=None,
                             control_scheme=None):
        if not player_control:
            if not control_scheme:
                control_scheme = ControlScheme.default_scheme
            player_control = PlayerControl(self, control_scheme)
        self.player_control = player_control

        if self.gun:
            self.player_control.setup_gun(self.gun)

        self.hand_control_to_player()

    def setup_gun(self, gun=None):
        if not gun:
            gun = RoboGun()

        self.gun = gun

        gun_interface = GunInterface(gun)
        self.thread_robot.setup_gun_interface(gun_interface)

        self.enable_gun()

        if self.player_control:
            self.player_control.setup_gun(gun)
```
### Now we can take a break maneuvering while leaving all the work to the robot-AI.

# Task: Death and Respawn
### Until now, our robots don't really feel the impact of the bullets. They just plöpp up again at another point of the battlefield.
### We now add a new heal attribute to the robot!
```python
class BaseRobot:

    def __init__(self, radius, a_max, a_alpha_max, v_max=39, v_alpha_max=90, 
                 fov_angle=90, max_life=3, respawn_timer=3):

        # define new set parameters of the robot's base
        self.respawn_timer = respawn_timer
        self.max_life = max_life

class DataRobot(BaseRobot):

    def __init__(self, base_robot: BaseRobot, thread_robot: ThreadRobot):

        # current health
        self.life = self.max_life
        # and two new status flags
        self.dead = False
        self.immune = False
```
### A robot should survive multiple hits:
### What happens if a robot is dealt damage?
```python
class DataRobot(BaseRobot):

    def deal_damage(self, damage=1):
        # we don't deal damage to dead or immune units
        if self.immune or self.dead:
            return

        self.life = max(0, self.life - damage)
        if self.life <= 0:
            self.get_destroyed()

    def get_destroyed(self):
        # fatal status
        self.dead = True

        # the right management system comes in handy again!
        self.disable_robot_control()
        self.disable_player_control()
        self.disable_gun()

        # stop moving, u dead
        self.v = 0
        self.v_alpha = 0

        # these dead things should not stay dead
        def respawn():
            self.respawn()

        Utils.execute_after(self.respawn_timer, respawn)
```
### Now implement the respawn function. Be careful, it will be called in another thread!
```python

    def respawn(self):
        # get back to life at the respawn location
        self.life = self.max_life
        self.immune = True
        point = self.x, self.y
        Board.teleport_furthest_corner(point, self)

        # hand controls to the former controller via right system
        if self.player_control_active:
            self.hand_control_to_player()
        else:
            self.hand_control_to_robot()

        # this is the best part
        self.enable_gun()

        self.dead = False

        # with this we stop the immunity status
        def disable_immunity():
            self.immune = False

        Utils.execute_after(1, disable_immunity)
```
### Now we just need to call the damage function when hit insted of receiving oneshots by everthing.
```python
class Board(QWidget):

    def col_robots_bullets(self, bullet):
        for robot in self.robots:
            robot_center = (robot.x, robot.y)
            distance = Utils.distance(robot_center, bullet.position)
            if distance <= robot.radius:

                # the magical line
                robot.deal_damage()

                self.bullets.remove(bullet)
                return True
        return False

    def calculate_bullets(self):
        for bullet in self.bullets.copy():
            # move
            initial_position = bullet.position
            for test_speed in range(int(bullet.speed)):

                direction_vec = Utils.vector_from_angle(bullet.direction)
                movement_vec = direction_vec * test_speed
                new_position = initial_position + movement_vec
                bullet.position = new_position

                # perform collision with walls and robots
                if (self.col_bullet_walls(bullet) or
                        self.col_robots_bullets(bullet)):
                    break
        
        # we don't need to clear up the dead robots anymore
        # they clean up after themselves.
```
### Now damage, health and respawn mechanics are online as well!

# Task: Polish the Game
### Considering our new found powers, it is really time to make the game a bit more... pretty <3!
# TODO TIM

# Task: Fixes and Improvements
### There was also a lot of space for bug fixes encountered while setting up the player control as well as general code improvements.
# TODO TIM
# TODO LEANDER

# Additional Features
## Invasive Controls
### Moving a robot only via acceleration might be a bit clunky. For those of you who don't like space sims, we want to get you covered now!
### For this, we would like to be able to change the speed and angle velocity of a robot directly:
```python
class DataRobot(BaseRobot):

    def invasive_control(self, v_alpha):
        # this should only happen while the player is in charge.
        # we don't want to overwrite the physics engine of the game. :O
        if self.player_output_enabled:
            self.v_alpha = v_alpha
```
### We add a new option flag to the `PlayerControl`:
```python
class PlayerControl:

    def __init__(self, data_robot, control_scheme, accel_amt=None,
                 alpha_accel_amt=None, invasive_controls=False):
    
    # no need to save the boolean
    # the functions that need to know the control type
    # are defined here for later usage
        def lr_left():
            if invasive_controls:
                self.data_robot.invasive_control(
                    v_alpha=-1 * self.alpha_accel_amt)
            else:
                self.a_alpha = - 1 * self.alpha_accel_amt

        def lr_right():
            if invasive_controls:
                self.data_robot.invasive_control(v_alpha=self.alpha_accel_amt)
            else:
                self.a_alpha = self.alpha_accel_amt

        def clear_lr():
            if invasive_controls:
                self.data_robot.invasive_control(v_alpha=0)
            else:
                self.a_alpha = 0

        def lr_pass():
            pass

        # define the lookup with the functions of the correct control type
        self.lr_lookup = { # [...] }
```
### With this option set, we now have much simpler access to the robot's movement.

# Are we controlling the robots or are the robots controlling us, Elon?