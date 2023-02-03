import numpy as np


def collect_points(hand_landmarks, tracking_points):
    """Collect tracking points from the current frame"""
    # Extract the hand center from the hand keypoints
    hand_center = np.mean(hand_landmarks, axis=0).astype(int)
    tracking_points.append(tuple(hand_center))


def normalize_gesture(gesture):
    x, y, z = zip(*gesture)
    x_min, x_max, y_min, y_max, z_min, z_max = min(x), max(x), min(y), max(y), min(z), max(z)
    x_axis_length = x_max - x_min
    y_axis_length = y_max - y_min
    axis_length = max(x_axis_length, y_axis_length)
    x_average = sum(x) / len(x)
    y_average = sum(y) / len(y)
    z_average = sum(z) / len(z)
    normalized_x = [(x_i - x_average) / axis_length for x_i in x]
    normalized_y = [(y_i - y_average) / axis_length for y_i in y]
    normalized_z = [(z_i - z_average) / axis_length for z_i in z]
    return normalized_x, normalized_y, normalized_z


def normalize_gesture_2d(gesture):
    x, y = zip(*gesture)
    x_min, x_max, y_min, y_max = min(x), max(x), min(y), max(y)
    x_axis_length = x_max - x_min
    y_axis_length = y_max - y_min
    axis_length = max(x_axis_length, y_axis_length)
    x_average = sum(x) / len(x)
    y_average = sum(y) / len(y)
    normalized_x = [(x_i - x_average) / axis_length for x_i in x]
    normalized_y = [(y_i - y_average) / axis_length for y_i in y]
    return normalized_x, normalized_y


def smooth_gesture(tracking_points: list[tuple[int, int]], window_size: int = 2):
    """Smooth the tracking points using a moving average filter"""
    # Pad the tracking points with the first and last points
    tracking_points = [tracking_points[0]] * (window_size // 2) + tracking_points + [tracking_points[-1]] * (
            window_size // 2)
    # Apply the moving average filter
    smoothed_points = []
    for i in range(len(tracking_points) - window_size + 1):
        window = tracking_points[i:i + window_size]
        x, y = zip(*window)
        smoothed_points.append((sum(x) / window_size, sum(y) / window_size))
    return smoothed_points


def laplacian_smoothing(tracking_points: list[tuple[int, int]]):
    """Smooth the tracking points using the mean of each point and its neighbors"""
    smoothed_points = []
    for i in range(len(tracking_points)):
        x, y = tracking_points[i]
        if i == 0:
            x_prev, y_prev = tracking_points[i]
        else:
            x_prev, y_prev = tracking_points[i - 1]
        if i == len(tracking_points) - 1:
            x_next, y_next = tracking_points[i]
        else:
            x_next, y_next = tracking_points[i + 1]
        smoothed_points.append(((x + x_prev + x_next) / 3, (y + y_prev + y_next) / 3))

    return smoothed_points


def perpendicular_distance(point, start, end):
    """Compute the perpendicular distance from the point to the line segment formed by start and end"""
    x1, y1 = start
    x2, y2 = end
    x0, y0 = point
    if x1 == x2:
        return abs(x0 - x1)
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return abs(slope * x0 - y0 + intercept) / np.sqrt(slope ** 2 + 1)


def simplify_gesture(points, tolerance):
    """Simplify the given set of points using the Ramer-Douglas-Peucker algorithm"""
    # Find the point with the maximum distance from the line segment formed by the start and end points
    dmax = 0
    index = 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d
    # If the maximum distance is greater than the tolerance, recursively simplify
    if dmax > tolerance:
        results1 = simplify_gesture(points[:index + 1], tolerance)
        results2 = simplify_gesture(points[index:], tolerance)
        # Concatenate the simplified paths
        results = results1[:-1] + results2
    else:
        results = [points[0], points[-1]]
    return results


if __name__ == '__main__':
    points = [(i, i ** 2) for i in range(10)]
    tolerance = 0.5

    val_result = simplify_gesture(points, tolerance)
    print(val_result)

    from fastdtw import fastdtw
    from scipy.spatial.distance import euclidean

    x = [(i + 1, i ** 2) for i in range(10)]

    distance, path = fastdtw(points, x, dist=euclidean)
    print(distance)
