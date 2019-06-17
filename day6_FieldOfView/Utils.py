import numpy as np


def generate_obstacle_list(matrix, size):
    out = []
    for i in range(size):
        for j in range(size):
            if matrix[i][j]:
                out.append((i, j))
    return np.array(out)


def calculate_angles(point_list, point, angle, fov_angle):
    # normally, we would need to flip the direction here (*-1)
    # but since the coordinates later are also flipped in y-direction,
    # it is not needed

    # ang_rad = np.radians((angle - 90))
    # v = (np.cos(ang_rad), np.sin(ang_rad))

    v = vector_from_angle(angle)

    point_list = np.array(point_list)

    # this is flipped at y-axis
    vectors = point_list - point

    distances = np.linalg.norm(vectors, axis=1)

    # np.apply_along_axis(
    #     lambda vec: np.linalg.norm(vec), 1, vectors)

    vectors_norm = vectors / distances[:, None]

    angles = np.arccos(np.clip(np.dot(vectors_norm, v), -1.0, 1.0))

    diffs = angles - np.radians(fov_angle/2)

    return diffs, distances


def ray_check(point, ray_vector, circle):
    cx, cy, cr = circle
    point = np.array(point)
    center = np.array((cx, cy))

    a = np.matmul(ray_vector, ray_vector)

    dif = point - center
    b = 2 * np.matmul(ray_vector, dif)

    c = (np.matmul(point, point) + np.matmul(center, center) -
         2 * np.matmul(point, center) - cr**2)

    discriminant = b**2 - 4 * a * c

    # circle doesn't cross the line
    if discriminant < 0:
        return False

    t = (-b + np.sqrt(discriminant)) / (2 * a)

    # circle doesn't cross the ray
    return t >= 0


def distance(a, b):
    val = np.array(a) - b
    return np.linalg.norm(val)


def overlap_check(center1, center2, rad1, rad2):
    d_overlap = rad1 + rad2
    d = distance(center1, center2)

    if d == 0:
        res = 'zero'
    elif d <= d_overlap:
        res = True
    else:
        res = False

    return res, d


def vector_from_angle(angle):
    ang_rad = np.radians((angle - 90))
    v = (np.cos(ang_rad), np.sin(ang_rad))
    return v


# only here to assist collision_single_tile
# limits a value to a max and a min
def limit(value, min_limit, max_limit):
    if value > max_limit:
        return max_limit
    elif value < min_limit:
        return min_limit
    else:
        return value


def create_example_array(size: int):

    array = [[0] * size for row in range(size)]

    # setting the sidewalls by setting all the first and last Elements
    # of each row and column to 1
    for x in range(size):
        array[x][0] = 2
        array[x][size - 1] = 2
        array[0][x] = 2
        array[size - 1][x] = 2

    # individual Wall tiles:
    """array[28][34] = 1

    array[56][50] = 1
    array[56][51] = 1
    array[56][52] = 1
    array[56][53] = 1
    array[56][54] = 1
    array[56][55] = 1
    array[56][56] = 1
    array[56][57] = 1
    array[56][58] = 1
    array[56][59] = 1
    array[56][60] = 1
    array[56][61] = 1
    array[56][62] = 1
    array[56][63] = 1
    array[56][64] = 1
    array[56][65] = 1
    array[56][66] = 1
    array[56][67] = 1
    array[56][68] = 1
    array[56][69] = 1

    array[70][30] = 1
    array[43][96] = 1
    array[73][56] = 1
    array[5][49] = 3
    array[0][30] = 0
    array[99][30] = 0"""

    return array
