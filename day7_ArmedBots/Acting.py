import math
from Movement import SimpleAvoidMovement


# TODO: Find a place for it
# TODO: adjust for it's new place
def shoot_straight(robot, data):
    x, y, alpha, v, v_alpha, = data
    coordinates = robot.target

    angle = SimpleAvoidMovement.calculate_angle_between_vectors(coordinates, x, y, v, alpha)
    ready = not (robot.is_shooting or robot.is_reloading)
    if ready:
        # set acceptable inaccuracy
        max_inaccuracy = 20
        # calculate aim inaccuracy
        inaccuracy = calculate_inaccuracy((x, y), coordinates, alpha, v)
        # decide action
        if inaccuracy <= max_inaccuracy and angle <= 90:
            robot.shoot()


# For angles < 90
def calculate_inaccuracy(position, coordinates, alpha, vel):
    x = position[0]
    y = position[1]
    c_x = coordinates[0]
    c_y = coordinates[1]
    robot_radian = (alpha / 180 * math.pi)

    # get angle between aim direction and target, as radian
    angle = SimpleAvoidMovement.calculate_angle_between_vectors(coordinates, x, y, vel, alpha)
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

