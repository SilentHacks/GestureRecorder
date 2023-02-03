from collections import deque, Counter

import cv2
import numpy as np
from matplotlib import pyplot as plt
import scipy.spatial.distance as dist
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

from recorder import Recorder, hands_module, STRATEGY_PARAMS
from utils.fps_tracker import FPSTracker
from utils.hand_tracker import normalize_gesture, smooth_gesture, laplacian_smoothing, normalize_gesture_2d, \
    simplify_gesture

MAX_POINT_HISTORY = 20


class GestureRecorder(Recorder):
    def __init__(
            self,
            camera: int = 0,
            num_hands: int = 1,
            static_image_mode: bool = False,
            min_detection_confidence: float = 0.7,
            min_tracking_confidence: float = 0.7,
            gesture_leniency: float = 0.3,
            gesture_threshold: float = 0.99,
            strategy: int = 3
    ):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        :param num_hands: number of hands to detect
        :param static_image_mode: whether each frame is a static image or a video
        :param min_detection_confidence: the minimum confidence for detection
        :param min_tracking_confidence: the minimum confidence for tracking
        :param gesture_leniency: the leniency of the gesture (0-1)
        :param gesture_threshold: the threshold of the gesture (0-1)
        :param strategy: the strategy to use for calculating points (1-3)
        """
        super().__init__(
            camera=camera,
            num_hands=num_hands,
            static_image_mode=static_image_mode,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            gesture_leniency=gesture_leniency,
            gesture_threshold=gesture_threshold,
            strategy=strategy
        )

        self.point_history: deque[tuple[int, int]] = deque(maxlen=MAX_POINT_HISTORY)
        self.gesture_history: deque[bool] = deque(maxlen=MAX_POINT_HISTORY)
        self.landmark_history = deque(maxlen=MAX_POINT_HISTORY)
        self.color_keep = 0
        self.first_frame = None
        self.last_frame = None
        self.is_recording = False
        self.ticket = False

        # self.gesture = self.calculate_points(EXAMPLE_DATA)

    @property
    def color(self) -> tuple[int, int, int]:
        """
        Get the color of the hand landmarks.

        :return: the color
        """
        if self.detected or self.color_keep > 0:
            self.color_keep -= 1
            return 0, 255, 0

        return 0, 0, 255

    def calculate_points(self, height: int, width: int, point_history: deque[tuple[int, int]] = None) -> list[float]:
        """
        Calculate the normalized points of the hand landmarks.

        :param height: the height of the image
        :param width: the width of the image
        :param point_history: the point history to use (if not provided, use the current point history)
        :return: the points
        """
        points = []
        point_history = point_history or self.point_history
        zero_x, zero_y = point_history[0]
        for point in point_history:
            # Calculate relative to the first point
            x, y = point
            x_point = (x - zero_x) / width
            y_point = (y - zero_y) / height

            points.append((x_point, y_point))

        #     # Calculate the max value
        #     max_value = max(max_value, abs(x_point), abs(y_point))
        #
        # # Normalize the points
        # for i in range(len(points)):
        #     points[i] /= max_value

        return points

    def calculate_points_sigma(self, plot: bool = False):
        normal_x, normal_y = normalize_gesture_2d(self.point_history)
        list_coords = list(zip(normal_x, normal_y))
        smoothed_x, smoothed_y = zip(*laplacian_smoothing(list_coords))
        # plot this in red

        if plot:
            plt.plot(smoothed_x, smoothed_y, 'r')
            print(len(smoothed_x), 'smooth')

            smoothed_x, smoothed_y = zip(*smooth_gesture(list_coords))
            # plot this in green
            plt.plot(smoothed_x, smoothed_y, 'g')

        simplified_x, simplified_y = zip(*simplify_gesture(list(zip(smoothed_x, smoothed_y)), tolerance=0.01))
        # plot this in blue
        if plot:
            plt.plot(simplified_x, simplified_y, 'b')
            plt.show()

        return list(zip(simplified_x, simplified_y))  # list[tuple[float, float]]

    @staticmethod
    def get_center_point(hand_landmarks, height: int, width: int) -> tuple[int, int]:
        """
        Get the center point of the hand.

        :param hand_landmarks: the hand landmarks
        :param height: the height of the image
        :param width: the width of the image
        :return: the center point
        """
        if hand_landmarks is None:
            return 0, 0

        x = min(int(hand_landmarks.landmark[0].x * width), width - 1)
        y = min(int(hand_landmarks.landmark[0].y * height), height - 1)

        return x, y

        # x = min(int(hand_landmarks.landmark[0].x * width), width - 1)
        # y = min(int(hand_landmarks.landmark[0].y * height), height - 1)
        #
        # return x, y

    def check_gesture(self, ratios: list[float]):
        """
        Check if the gesture is correct.

        :param ratios: the ratios of the hand landmarks
        """
        if len(ratios) != len(self.gesture):
            return

        wrong_threshold = len(ratios) * (1 - self.gesture_threshold)

        # Check the gesture from every cyclic permutation
        for i in range(len(self.gesture)):
            # Check if the gesture is correct
            wrong = 0
            for j in range(len(self.gesture)):
                if abs(ratios[j] - self.gesture[(i + j) % len(self.gesture)]) > self.gesture_leniency:
                    wrong += 1

                if wrong > wrong_threshold:
                    break

        return True

    @staticmethod
    def dtw_distance(seq1, seq2):
        # Initialize the DTW matrix with zeros
        dtw_matrix = np.zeros((len(seq1), len(seq2)))

        for i in range(len(seq1)):
            for j in range(len(seq2)):
                # Calculate the Euclidean distance between the two points
                cost = dist.euclidean(seq1[i], seq2[j])

                # Update the DTW matrix
                if i == 0 and j == 0:
                    dtw_matrix[i, j] = cost
                elif i == 0:
                    dtw_matrix[i, j] = dtw_matrix[i, j - 1] + cost
                elif j == 0:
                    dtw_matrix[i, j] = dtw_matrix[i - 1, j] + cost
                else:
                    dtw_matrix[i, j] = min(dtw_matrix[i - 1, j], dtw_matrix[i, j - 1], dtw_matrix[i - 1, j - 1]) + cost

        # Return the minimum cumulative distance between the two sequences
        return dtw_matrix[-1, -1]

    def check_gesture_frames(self, pose_ratios: list[float]):
        return super().check_gesture(ratios=pose_ratios, gesture=self.last_frame)

    def detect_gesture(self, ratios, pose_ratios):
        # Calculate the DTW distance between the gesture and the stored gesture
        distance = self.dtw_distance(ratios, self.gesture)
        # distance2, _ = fastdtw(ratios, self.gesture, dist=euclidean)

        threshold = 2.5
        # Update the minimum distance and gesture ID if a better match is found

        if distance < threshold:
            if self.ticket:
                if self.check_gesture_frames(pose_ratios=pose_ratios):
                    self.ticket = False
                    self.color_keep = int(MAX_POINT_HISTORY * 0.75)
                    return True

        return False

    def handle_key(self, key: int, ratios: list[float], height: int, width: int) -> bool:
        """
        Handle key presses.

        :param key: key pressed
        :param ratios: ratios of the hand landmarks
        :param height: height of the image
        :param width: width of the image
        :return: True if the program should exit, False otherwise
        """
        if key == 27:  # ESC
            return True

        if 49 <= key <= 51:  # 1-3
            self.strategy = key - 48
            self.gesture_leniency, self.gesture_threshold = STRATEGY_PARAMS[self.strategy]
            self.clear_gesture()
        elif key == 100:  # D:
            self.clear_gesture()

        return False

    def clear_gesture(self):
        """
        Clear the gesture.
        :return:
        """
        self.gesture = None
        self.detected = False
        self.point_history.clear()
        self.first_frame = None
        self.last_frame = None

    def record(self):
        """
        Record gestures and save them when the user presses the "S" key.

        :return:
        """
        with hands_module.Hands(
                static_image_mode=self.static_image_mode,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
                max_num_hands=self.num_hands
        ) as hands:
            fps_tracker = FPSTracker()
            while True:
                _, frame = self.capture.read()
                height, width, _ = frame.shape

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                hand_landmarks = None
                ratios = None
                found = False
                if results.multi_hand_landmarks is not None:  # type: ignore
                    hand_landmarks = self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if self.gesture is not None and len(self.point_history) == MAX_POINT_HISTORY:
                        if any(point == (0, 0) for point in self.point_history):
                            self.point_history.clear()
                        else:
                            pose_ratios = self.calculate_ratios(hand_landmarks)
                            if super().check_gesture(ratios=pose_ratios, gesture=self.first_frame):
                                self.ticket = True
                            ratios = self.calculate_points_sigma()
                            found = self.detect_gesture(ratios=ratios, pose_ratios=pose_ratios)

                center_point = self.get_center_point(hand_landmarks=hand_landmarks, height=height, width=width)
                self.point_history.append(center_point)
                self.gesture_history.append(found)

                # print(self.point_history)
                # print(self.gesture_history)

                cv2.imshow('Test Hand', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                key = cv2.waitKey(1)

                if key == 115:  # S:
                    self.is_recording = True
                    self.clear_gesture()

                if self.is_recording:
                    if len(self.point_history) == MAX_POINT_HISTORY:
                        if ratios:
                            self.save_gesture(ratios=ratios)
                        elif len(self.point_history) == MAX_POINT_HISTORY:
                            self.save_gesture(ratios=self.calculate_points_sigma(plot=True))

                        self.last_frame = self.calculate_ratios(hand_landmarks)
                        self.is_recording = False
                    elif len(self.point_history) == 0:
                        self.first_frame = self.calculate_ratios(hand_landmarks)

                if self.handle_key(key=key, ratios=ratios, height=height, width=width):
                    break


if __name__ == '__main__':
    recorder = GestureRecorder()
    recorder.record()
