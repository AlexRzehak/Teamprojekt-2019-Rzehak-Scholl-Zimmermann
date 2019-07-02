# Week 7: Give Guns to the Robots

### [<- Back](/index.md) to project overview.

### Now we stop playing around and get ready for some serious combat!

# Task: Each Robot should get a Gun
# TODO ALEX (gun-klasse, anbindung an server)

# Task: The Guns should shoot Bullets
# TODO ALEX (set-implementation)
# TODO LEANDER (calculate-bullet)

# Task: The Robots should utilize the Guns
## When to enqueue a shot?
## Implement a funtion to decide.
```python
def shoot_straight(robot, data):
    x, y, alpha, v, v_alpha = data
    if type(robot.destination) == tuple:
        coordinates = robot.destination[0]
        angle = calculate_angle_between_vectors(coordinates, x, y, v, alpha)
        ready = not (robot.is_shooting() or robot.is_reloading())
        if ready and 0.01 < angle <= 90:
            # set acceptable inaccuracy
            max_inaccuracy = robot.radius
            # calculate aim inaccuracy
            inaccuracy = calculate_inaccuracy((x, y), coordinates, alpha, v)
            # decide action
            if inaccuracy <= max_inaccuracy and angle <= 90:
                robot.shoot()
```
### If the robot is not reloading or already about to shoot the robot enqueues a shot if the target is straight ahead of the robot. 

## How to calculate the inaccuracy?
```python
def calculate_inaccuracy(position, coordinates, alpha, vel):
    # For angles < 90
    x = position[0]
    y = position[1]
    c_x = coordinates[0]
    c_y = coordinates[1]
    robot_radian = (alpha / 180 * math.pi)

    # get angle between aim direction and target, as radian
    angle = calculate_angle_between_vectors(coordinates, x, y, vel, alpha)
    angle = angle % 360
    target_radian = (angle / 180 * math.pi)

    # calculate distance between position and coordinates
    distance = math.sqrt((c_x-x)**2 + (c_y-y)**2)

    # calculate opposite's length of Triangle
    a = (math.sin(target_radian)*distance)
    b = (math.sin(robot_radian)*distance)
    opp_abs = math.sqrt(a**2 + b**2)

    # calculate inaccuracy
    inaccuracy = math.sin(target_radian) * opp_abs
    return inaccuracy
```
Using geometric maths we determine the minimal distance between the projectiles path and the targets center point.
