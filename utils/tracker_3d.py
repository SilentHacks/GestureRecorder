"""
This module contains the 3D tracker class and related functions.
You can ignore it since we aren't actually using these anymore.
"""

import numpy as np
from matplotlib import pyplot as plt
from itertools import islice


def normalize_gesture_3d(gesture):
    x, y, z = zip(*gesture)
    x_min, x_max, y_min, y_max, z_min, z_max = min(x), max(x), min(y), max(y), min(z), max(z)
    x_axis_length = x_max - x_min
    y_axis_length = y_max - y_min
    axis_length = max(x_axis_length, y_axis_length) or 1
    x_average = sum(x) / len(x)
    y_average = sum(y) / len(y)
    z_average = sum(z) / len(z)
    normalized_x = [(x_i - x_average) / axis_length for x_i in x]
    normalized_y = [(y_i - y_average) / axis_length for y_i in y]
    normalized_z = [(z_i - z_average) / axis_length for z_i in z]
    return normalized_x, normalized_y, normalized_z


def laplacian_smoothing_3d(tracking_points: list[tuple[int, int, int]]):
    """Smooth the tracking points using the mean of each point and its neighbors"""
    smoothed_points = []
    for i in range(len(tracking_points)):
        x, y, z = tracking_points[i]
        if i == 0:
            x_prev, y_prev, z_prev = tracking_points[i]
        else:
            x_prev, y_prev, z_prev = tracking_points[i - 1]
        if i == len(tracking_points) - 1:
            x_next, y_next, z_next = tracking_points[i]
        else:
            x_next, y_next, z_next = tracking_points[i + 1]
        smoothed_points.append(((x + x_prev + x_next) / 3, (y + y_prev + y_next) / 3, (z + z_prev + z_next) / 3))

    return smoothed_points


def perpendicular_distance_3d(point, start, end):
    """Compute the perpendicular distance from the point to the line segment formed by start and end"""
    x1, y1, z1 = start
    x2, y2, z2 = end
    x0, y0, z0 = point
    if x1 == x2:
        return abs(x0 - x1)
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return abs(slope * x0 - y0 + intercept) / np.sqrt(slope ** 2 + 1)


def simplify_gesture_3d(points, tolerance):
    """Simplify the given set of points using the Ramer-Douglas-Peucker algorithm"""
    # Find the point with the maximum distance from the line segment formed by the start and end points
    dmax = 0
    index = 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance_3d(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d
    # If the maximum distance is greater than the tolerance, recursively simplify
    if dmax > tolerance:
        results1 = simplify_gesture_3d(list(islice(points, 0, index + 1)), tolerance)
        results2 = simplify_gesture_3d(list(islice(points, index, len(points))), tolerance)
        # Concatenate the simplified paths
        results = results1[:-1] + results2
    else:
        results = [points[0], points[-1]]
    return results


def gaussian_filter_3d(points: list[tuple[int, int, int]], sigma: float = 1.0):
    """Apply a Gaussian filter to the given points"""
    # Compute the Gaussian kernel
    kernel = np.exp(-np.arange(-3, 4) ** 2 / (2 * sigma ** 2))
    kernel = kernel / np.sum(kernel)

    # Apply the filter to the points
    x_values, y_values, z_values = zip(*points)
    x_values = np.convolve(x_values, kernel, mode='same')
    y_values = np.convolve(y_values, kernel, mode='same')
    z_values = np.convolve(z_values, kernel, mode='same')

    return list(zip(x_values, y_values, z_values))


def select_landmarks_3d(landmark_history: dict[int, list[tuple[int, int, int]]]):
    """Select the relevant landmarks from the tracking points based on the variance of its signal"""
    good_landmarks = set()
    thresh = 0.125
    for landmark_id, tracking_points in landmark_history.items():
        # normalized = normalize_gesture(tracking_points)
        # smoothed_points = laplacian_smoothing_3d(list(zip(*normalized)))

        smoothed_points = laplacian_smoothing_3d(tracking_points)

        # Check the variance of the signal to determine if the landmark is relevant
        x_values, y_values, z_values = zip(*smoothed_points)
        x_var = np.var(x_values)
        y_var = np.var(y_values)
        z_var = np.var(z_values)
        # print(landmark_id, x_var, y_var, z_var)
        if x_var > thresh or y_var > thresh or z_var > thresh:
            good_landmarks.add(landmark_id)

    # print(len(good_landmarks))
    return good_landmarks


def process_landmarks_3d(landmark_history: dict[..., list[tuple[int, int, int]]],
                         relevant_landmarks: set[int] = None, plot: bool = False):
    """Process the landmark history to select relevant landmarks and simplify the tracking points"""
    # Select the relevant landmarks
    good_landmarks = select_landmarks_3d(landmark_history).union(relevant_landmarks or set())

    # Simplify the tracking points for each landmark
    simplified_landmarks = {}
    ax = None
    if plot:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

    for landmark_id in good_landmarks:
        # simplified = simplify_gesture_3d(landmark_history[landmark_id], tolerance=0.01)
        simplified = landmark_history[landmark_id]

        smoothed_points = np.array(gaussian_filter_3d(simplified, sigma=1))
        smoothed_points -= np.mean(smoothed_points, axis=0)

        # smoothed_points = np.array(smooth_gesture(tracking_points))

        # Convert the smoothed points to a Python list
        smoothed_points = smoothed_points.tolist()
        simplified_landmarks[landmark_id] = smoothed_points

        if plot:
            # plot the simplified points in 3D
            ax.plot(*zip(*smoothed_points), label=f'Landmark {landmark_id}')  # type: ignore

    if plot:
        plt.legend()
        plt.show()
        plt.close()

    return simplified_landmarks
