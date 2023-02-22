import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter


def normalize_gesture(gesture: np.ndarray):
    """Normalize the gesture by translating it to the origin and scaling it to fit in a unit square"""
    axis_length = max(gesture[:, 0].ptp(), gesture[:, 1].ptp()) or 1
    return (gesture - gesture.mean(axis=0)) / axis_length


def smooth_gesture(tracking_points: np.ndarray, window_size: int = 2):
    """Smooth the tracking points using a moving average filter"""
    window = np.ones(window_size) / window_size
    return (
        np.convolve(tracking_points[:, 0], window, mode='same'),
        np.convolve(tracking_points[:, 1], window, mode='same')
    )


def laplacian_smoothing(tracking_points: np.ndarray):
    """Smooth the tracking points using the mean of each point and its neighbors"""
    smoothed_points = np.zeros(tracking_points.shape)
    smoothed_points[1:-1] = (tracking_points[:-2] + tracking_points[1:-1] + tracking_points[2:]) / 3
    smoothed_points[0] = (tracking_points[0] + tracking_points[1]) / 2
    smoothed_points[-1] = (tracking_points[-1] + tracking_points[-2]) / 2

    return smoothed_points


def simplify_gesture(points: np.ndarray, tolerance: float, start=None, end=None):
    """Simplify the given set of points using the Ramer-Douglas-Peucker algorithm"""
    if start is None:
        start = 0
    if end is None:
        end = len(points) - 1

    if end <= start + 1:
        return points[start:end]

    d_max = 0
    index = start
    for i in range(start + 1, end):
        d = (np.abs(np.cross(points[end] - points[start], points[i] - points[start])) /
             np.linalg.norm(points[end] - points[start]))
        if d > d_max:
            index = i
            d_max = d

    if d_max > tolerance:
        res1 = simplify_gesture(points, tolerance, start, index)
        res2 = simplify_gesture(points, tolerance, index, end)
        return np.concatenate((res1[:-1], res2))
    else:
        return np.array([points[start], points[end]])


def gaussian_filter(points: np.ndarray, sigma: float = 1.0):
    """Apply a Gaussian filter to the given points"""
    # Compute the Gaussian kernel
    kernel = np.exp(-np.arange(-3, 4) ** 2 / (2 * sigma ** 2))
    kernel = kernel / np.sum(kernel)

    # Apply the filter to the points
    x_values, y_values = points.T
    x_values = np.convolve(x_values, kernel, mode='same')
    y_values = np.convolve(y_values, kernel, mode='same')

    return np.column_stack((x_values, y_values))


def savgol_filter_points(points: np.ndarray, window_length: int, polyorder: int):
    """Apply a Savitzky-Golay filter to the given points"""
    x_values, y_values = points.T
    x_values = savgol_filter(x_values, window_length, polyorder, mode='nearest')
    y_values = savgol_filter(y_values, window_length, polyorder, mode='nearest')

    return np.column_stack((x_values, y_values))


def select_landmarks(landmark_history: dict[int, list[tuple[int, int]]]):
    """Select the relevant landmarks from the tracking points based on the variance of its signal"""
    good_landmarks = set()
    numpy_landmarks = {}

    for landmark_id, tracking_points in landmark_history.items():
        tracking_points = np.array(tracking_points)
        numpy_landmarks[landmark_id] = tracking_points
        # Smooth the tracking points using a median filter with r=3
        # smoothed_points = laplacian_smoothing(tracking_points)

        normalized = normalize_gesture(tracking_points)
        smoothed_points = laplacian_smoothing(normalized)

        # Check the variance of the signal to determine if the landmark is relevant
        x_var = np.var(smoothed_points[:, 0])
        y_var = np.var(smoothed_points[:, 1])
        # print(landmark_id, x_var, y_var)
        if x_var > 0.1 or y_var > 0.1:
            good_landmarks.add(landmark_id)

    return good_landmarks, numpy_landmarks


def process_landmarks(landmark_history: dict[..., list[tuple[int, int]]], include_landmarks: set[int] = None,
                      exclude_landmarks: set[int] = None, plot: bool = False):
    """Process the landmark history to select relevant landmarks and simplify the tracking points"""
    # Select the relevant landmarks
    good_landmarks, numpy_landmarks = select_landmarks(landmark_history)

    if include_landmarks:
        good_landmarks |= include_landmarks
    if exclude_landmarks:
        good_landmarks -= exclude_landmarks

    # Simplify the tracking points for each landmark
    simplified_landmarks = {}
    for landmark_id in good_landmarks:
        smoothed_points = gaussian_filter(numpy_landmarks[landmark_id], sigma=2)
        smoothed_points -= np.mean(smoothed_points, axis=0)

        # smoothed_points = np.array(smooth_gesture(tracking_points))
        # savgol the smoothed points
        smoothed_points = savgol_filter_points(smoothed_points, 8, 3)
        smoothed_points = simplify_gesture(smoothed_points, 0.007)

        if isinstance(smoothed_points, np.ndarray):
            smoothed_points = smoothed_points.tolist()

        simplified_landmarks[landmark_id] = smoothed_points

        if plot:
            # Plot with a deterministic color based on the landmark id
            color = np.array([landmark_id * 100 % 255, landmark_id * 200 % 255, landmark_id * 300 % 255]) / 255
            plt.plot(*zip(*smoothed_points), color=color, label=f'Landmark {landmark_id}')

    if plot:
        plt.legend()
        plt.show()

    return simplified_landmarks
