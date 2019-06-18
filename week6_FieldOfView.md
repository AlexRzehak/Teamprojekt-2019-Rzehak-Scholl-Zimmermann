# Week 6: Fiel of View 

### [<- Back](/index.md) to project overview.

# Movement
## Problem: Avoiding Objects
### Selecting the object to avoid next
```python
def vision(self, data, robot):
    robot.destination = SimpleAvoidMovement.prime_object(data)
    return robot.a, robot.a_alpha
```
```python
def prime_object(array_tuple):
    robot_array = array_tuple[1]
    obstacle_array = array_tuple[0]
    significance = math.inf
    index_of_obj = 0
    type_of_obj = 0
    robot_multiplier = 1
    for i in range(len(obstacle_array)):
        obj_distance = obstacle_array[i][2]
        if obj_distance < significance and obj_distance:
            significance = obj_distance
            index_of_obj = i
            type_of_obj = 0
    for i in range(len(robot_array)):
        if type(robot_array[i]) == tuple:
            obj_significance = robot_array[i][1] * robot_multiplier
            if obj_significance < significance and obj_significance > 0:
                significance = obj_significance
                index_of_obj = i
                type_of_obj = 1
    significant_object = array_tuple[type_of_obj][index_of_obj]
    return significant_object
```
### Via iteration over the Arrays and comparing the distances to the robot we can determine the most significant object 

## Problem: Making a decision
### Setting the wanted angle_change 
```python
def set_delta_alpha(obj_type, distance, threshold, obj_angle, turn_direction, v_alpha):
    # set delta_alpha based on obstacle type and distance
    absolute_delta_alpha = 10
    if obj_type == "wall":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = absolute_delta_alpha
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - absolute_delta_alpha
        else:
            delta_alpha = 0
    if obj_type == "robot":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = (180 - abs(obj_angle))
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - (180 - abs(obj_angle))
        elif distance > threshold:
            delta_alpha = 0
    return delta_alpha
```
Using data of the robot and the selected object a sensible wanted angle_change for this tick can be determined. For objects it is enought to get them out of the FOV, however to get away from a robot creating a angle of 180° away from it is good.

## Problem: When to act?
### Setting a Threshold
```python
def calculate_threshold(obj_type, v, alpha, v_alpha, v_max, robot):
    # distance to object at which the robot starts acting
    if obj_type == "wall":
        delta_alpha = 90
        obj_size = 10
        obj_r = math.sqrt(2) * obj_size
    elif obj_type == "robot":
        delta_alpha = 180
        enemy_radius = 50 + v_max
        obj_r = enemy_radius
    delta_alpha_per_unit = abs(robot.a_alpha_max / v_max)
    turn_distance = (delta_alpha + abs(v_alpha)) * delta_alpha_per_unit
    threshold = turn_distance + 2 * robot.radius + obj_r
    return threshold
```
The value calculated for the worst case scenario of space a robot needs to turn, is used as a threshold. If the distance is lower than this threshold the robot acts.

## Problem getting the right acceleration values
### Logic
```python
def set_angle_acceleration(direction, delta_alpha, v_alpha, robot):
    # setting a_alpha values
    a_alpha_max = robot.a_alpha_max
    if direction == "right":
        if delta_alpha >= a_alpha_max + v_alpha:
            a_alpha = a_alpha_max
        elif delta_alpha < a_alpha_max + v_alpha:
            a_alpha = delta_alpha - v_alpha
    elif direction == "left":
        if abs(delta_alpha) >= abs(a_alpha_max - v_alpha):
            a_alpha = - a_alpha_max
        elif abs(delta_alpha) < abs(a_alpha_max - v_alpha):
            a_alpha = -(abs(delta_alpha)) + abs(v_alpha)
    elif direction == "none":
        a_alpha = 0.01
    return a_alpha
```
With this the robot sets it's a and a_alpha values.

## Putting everything together
```python
x, y, alpha, v, v_alpha, = data
obj_position = robot.destination[0]
obj_coordinates = (obj_position[0] * tile_size + 5, obj_position[1] * tile_size + 5)
if robot.destination[1] == 1 or robot.destination[1] == 2 or robot.destination[1] == 3:
    obj_type = "wall"
    obj_distance = robot.destination[2]
else:
    obj_type = "robot"
    obj_distance = robot.destination[1]
# calculate object angle
obj_angle = SimpleAvoidMovement.calculate_angle_between_vectors(obj_coordinates, x, y, v, alpha)
# calculate vectors
velocity_vector = SimpleAvoidMovement.calculate_vector(v, alpha)
object_vector = SimpleAvoidMovement.calculate_vector_between_points(obj_coordinates, x, y)
# set Threshold
threshold = SimpleAvoidMovement.calculate_threshold(obj_type, v, alpha, v_alpha, v_max, robot)
# getting information about angle and direction
turn_direction = SimpleAvoidMovement.calculate_direction(object_vector, velocity_vector)
delta_alpha = SimpleAvoidMovement.set_delta_alpha(obj_type, obj_distance,
                                                  threshold, obj_angle, turn_direction, v_alpha)
# setting a values for a and a_alpha
a = SimpleAvoidMovement.set_acceleration(v, v_max)
a_alpha = SimpleAvoidMovement.set_angle_acceleration(turn_direction, delta_alpha, v_alpha, robot)

return a, a_alpha
```
# Fleeing from Robots
## Problem: Which robot is the biggest ?
## Checking for Significance
```python
def alert(self, data, robot):
    robot.robomap = data
    robot.threat = RunMovement.prime_robot(data)
    return robot.a, robot.a_alpha#
```
```python
def prime_robot(array):
    distance_array = []
    robot_x = array[0][0]
    robot_y = array[0][1]
    for i in range(len(array)):
        distance_array.append(RunMovement.calculate_distance(robot_x, robot_y, array[i][0], array[i][1]))
    significance = math.inf
    significant_index = 1
    for i in range(len(distance_array)):
        if distance_array[i] < significance and distance_array [i] > 0:
            significance = distance_array[i]
            significant_index = i
    significant_robot = (array[significant_index], distance_array[significant_index])
    return significant_robot
```
So we choose the robot with the smallest distance.

## Where to steer?
```python
def set_delta_alpha(obj_type, distance, threshold, obj_angle, turn_direction, v_alpha,
                    threat_angle, threat_turn_direction):
    # set delta_alpha based on obstacle and threat
    absolute_delta_alpha = 20
    if obj_type == "wall":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = absolute_delta_alpha
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - absolute_delta_alpha
    if obj_type == "robot":
        if distance <= threshold and turn_direction == "right":
            delta_alpha = (180 - abs(obj_angle))
        elif distance <= threshold and turn_direction == "left":
            delta_alpha = - (180 - abs(obj_angle))
    smoothifier= (180 - threat_angle)/180
    if distance > threshold:
        if threat_turn_direction == "right":
            delta_alpha = 20 * smoothifier
        elif threat_turn_direction == "left":
            delta_alpha = - 20 * smoothifier
        elif threat_turn_direction == "none":
            delta_alpha = 0
    return delta_alpha
```
If there is something in the way, we move out of the way as we did before. If not we turn away from the threat.

# Chasing Robots
## Checking the Vision
```python
def vision(self, data, robot):
    robot.destination = ChaseMovement.search(data)
    return robot.a, robot.a_alpha
```
```python
def search(array_tuple):
    robot_array = array_tuple[1]
    found_bot = robot_array[0]
    return found_bot
```
found_robot is Flase if the robot is not in the Array. If the robot is in the FOV we store it as destination.

## Problem: Robot not in sight
## Spin!
```python
def position(self, data, robot):
    x, y, alpha, v, v_alpha, = data
    target_bot = robot.destination
    if type(target_bot) == bool:
        a = 0
        if v_alpha < robot.a_alpha_max:
            a_alpha = 1
        elif v_alpha >= robot.a_alpha_max:
            a_alpha = 0
...
```
## Robot in sight
## Chase
```python
else:
    a, a_alpha = ChaseMovement.position_destination_robot(self, data, robot)
    robot.destination = None
```
position_destination_robot is the equivalent to FollowMovement.position from last week.
