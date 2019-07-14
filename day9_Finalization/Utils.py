import numpy as np
import math
import time
import threading

from PyQt5.QtCore import QPoint


def generate_obstacle_list(matrix, size):
    """
    Take a matrix of a given size
    and return the index pairs of all non-zero entries in a numpy array.
    """
    out = []
    for i in range(size):
        for j in range(size):
            if matrix[i][j]:
                out.append((i, j))

    return np.array(out)


def calculate_angles(point_list, point, angle, fov_angle):
    """
    Numpy method for angle-based check if an coordinate is seen by
    the FoV described by
    point (position of viewer),
    angle (direction) in deg and
    fov_angle (width) in deg.
    Performs this check for all points in the point_list
    as well as calculating its euclidian distance to point.
    The angle value for a point will be negative or zero, if it is included
    and positive, if it cannot be seen by this method only.
    Returns a tuple of (angle_values, distances); both np-arrays.
    Their entries at index i correspond to the point in point_list at index i.

    Warning: If one point from the point_list equals point (viewer-position),
    the function will crash.

    Note: The function works with permanently inverted y-direction.
    """

    # Get a normalized direction vector from the FoV-direction angle.
    # Note, that the y-direction is inverted!
    v = vector_from_angle(angle)

    # Convert the point_list to usable vector.
    point_list = np.array(point_list)

    # Calculate direction vectors between viewer position and tested points.
    # Note, that the y-direction is inverted!
    vectors = point_list - point

    # Calculate the distances between the viewer position and tested points.
    # Since direction vectors are tuples, we need to make sure,
    # to apply the function over the right axis.
    # Note: Don't use apply_along_axis() since it is slooooooow.
    distances = np.linalg.norm(vectors, axis=1)

    # We use normalized direction vectors, that we can use arccos.
    vectors_norm = vectors / distances[:, None]

    # Use arccos to get the smallest angle between each vector
    # and the direction of view vector.
    # The result is radian and always positive.
    angles = np.arccos(np.clip(np.dot(vectors_norm, v), -1.0, 1.0))

    # The angle between one end of the FoV and the direction
    # of view is half of the whole fov_angle.
    # We convert this result to a positive radian value.
    # Now: Is an angle from the values calculated before is smaller,
    # it will be covered by the field of view - the point is seen.
    diffs = angles - np.radians(fov_angle/2)

    return diffs, distances


def ray_check(point, ray_vector, circle):
    """
    Performs numpy check if a
    ray (described by point and direction vector) is intersecting a
    circle (tuple of (xpos, ypos, radius)).

    The result is calculated via
    |point + t * ray_vector - circle-center| = radius.
    A ray only exists in the direction of the ray vector. (ray != line)
    Therefore t must be a positive real number.
    To calculate t we use the quadratic formula for calculation of roots.

    A circle that would intersect the corresponding line at two points
    with the starting point inbetween might or might not be included,
    since this functionality is not needed.

    Note: The function works with permanently inverted y-direction.
    """
    cx, cy, cr = circle
    point = np.array(point)
    center = np.array((cx, cy))

    # Find a, b, c of the quadratic fomula:
    # t = (-b +/- sqrt(b^2-4ac)) 2a

    # a = ray_vector^2
    a = np.matmul(ray_vector, ray_vector)

    # b = 2 * ray_vector * (point - circle-center)
    dif = point - center
    b = 2 * np.matmul(ray_vector, dif)

    # c = point^2 + circle-center^2 - 2 * point*circle-center + radius^2
    c = (np.matmul(point, point) + np.matmul(center, center) -
         2 * np.matmul(point, center) - cr**2)

    # the discriminant is the value under the sqare root in the formula
    discriminant = b**2 - 4 * a * c

    # if it's negative, the circle doesn't cross the line
    if discriminant < 0:
        return False

    # if it'S positive, t might be a real value, so calculate ONE possible t
    t = (-b + np.sqrt(discriminant)) / (2 * a)

    # if it's negative, the circle doesn't cross the ray
    return t >= 0


def distance(a, b):
    """Simple function to calculate the euclidian distance between to points.
    """
    val = np.array(a) - b
    return np.linalg.norm(val)


def overlap_check(center1, center2, rad1, rad2):
    """Check if two circles overlap.
    Return 'zero' if they have the same center."""
    d_overlap = rad1 + rad2
    d = distance(center1, center2)

    if d == 0:
        res = 'zero'
    elif d <= d_overlap:
        res = True
    else:
        res = False

    return res, d


def check_collision_circle_rect(circle_center, circle_radius,
                                rect_origin, rect_width, rect_height):

    # calc the closest point in the rectangle to the robot
    closest_point = QPoint(limit(circle_center.x(), rect_origin.x(), rect_origin.x() + rect_width - 1),
                           limit(circle_center.y(), rect_origin.y(), rect_origin.y() + rect_height - 1))

    # calc the x and y distance from the closest point to the center of the robot
    dx = abs(closest_point.x() - circle_center.x())
    dy = abs(closest_point.y() - circle_center.y())

    # calc the actual distance
    dist = math.sqrt(dx ** 2 + dy ** 2)

    return dist < circle_radius


def vector_from_angle(angle):
    """Calculate a radian angle from degree angle.
    Since 0 deg means heading north but 0 in radian means heading east,
    rotate by 90 deg.

    Note, that since the degree values go in clock cicle and the radian values
    in reverse clock cicle, the y-Axis value will be inverted.
    """
    ang_rad = np.radians((angle - 90))
    v = (np.cos(ang_rad), np.sin(ang_rad))
    return np.array(v)


def limit(value, min_limit, max_limit):
    if value > max_limit:
        return max_limit
    elif value < min_limit:
        return min_limit
    else:
        return value


def execute_after(secs: float, func):
    def wait_and_call(secs, func):
        time.sleep(secs)
        func()

    t = threading.Thread(target=wait_and_call, args=(secs, func))
    t.daemon = True
    t.start()


def create_example_array(size: int):

    array = [[0] * size for row in range(size)]

    text_file = open("levels/level1.txt")
    line_list = text_file.readlines()
    rows = line_list
    text_file.close()

    # translating the list of characters to tile types in the output array
    for i in range(len(line_list)):
        for j in range(len(rows[i])):
            if rows[i][j] == '0'or rows[i][j] == '1' or rows[i][j] == '2' or rows[i][j] == '3':
                array[j][i] = int(rows[i][j])

    # setting the sidewalls by setting all the first and last Elements
    # of each row and column to 1
    for x in range(size):
        array[x][0] = 2
        array[x][size - 1] = 2
        array[0][x] = 2
        array[size - 1][x] = 2

    # individual Wall tiles:
    for i in range(int(size / 4), int(size / 2)):
        array[i][int(size/2)] = 1
        array[int(size/3)][i] = 1
        array[int(size / 4 * 3)][i] = 1

    return array
