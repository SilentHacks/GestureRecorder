from collections import deque, Counter

import cv2
import numpy as np
import mediapipe
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.spatial.distance as dist
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

from recorder import Recorder, STRATEGY_PARAMS, draw_module
from utils.fps_tracker import FPSTracker
from utils.tracking import normalize_gesture, smooth_gesture, laplacian_smoothing, normalize_gesture_2d, \
    simplify_gesture, laplacian_smoothing_3d, simplify_gesture_3d

MAX_POINT_HISTORY = 16


pose_module = mediapipe.solutions.pose


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
        self.countdown = 30
        self.point_history: deque[tuple[int, int]] = deque(maxlen=MAX_POINT_HISTORY)
        self.gesture_history: deque[bool] = deque(maxlen=MAX_POINT_HISTORY)
        self.landmark_history = deque(maxlen=MAX_POINT_HISTORY)
        self.color_keep = 0
        self.first_frame = None
        self.last_frame = None
        self.ticket = True

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

    def draw_landmarks(self, frame, results):
        """
        Draw the landmarks on the frame.

        :param frame: frame to draw on
        :param results: results from the mediapipe hands module
        :return:
        """
        color = self.color
        draw_module.draw_landmarks(
            image=frame,
            landmark_list=results.pose_landmarks,
            connections=pose_module.POSE_CONNECTIONS,
            landmark_drawing_spec=draw_module.DrawingSpec(color=color, thickness=2, circle_radius=2),
            connection_drawing_spec=draw_module.DrawingSpec(color=color, thickness=2, circle_radius=2)
        )

        return results.pose_landmarks

    def calculate_points(self, plot: bool = False):
        normal_x, normal_y, normal_z = normalize_gesture(self.point_history)
        list_coords = list(zip(normal_x, normal_y, normal_z))
        smoothed_x, smoothed_y, smoothed_z = zip(*laplacian_smoothing_3d(list_coords))
        # plot this in red

        if plot:
            # plt.plot(smoothed_x, smoothed_y, 'r')

            # smoothed_x, smoothed_y = zip(*smooth_gesture(list_coords))
            # plot this in green and 3d
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.plot(smoothed_x, smoothed_y, smoothed_z, 'g')
            plt.show()

        simplified_x, simplified_y, simplified_z = zip(*simplify_gesture_3d(
            list(zip(smoothed_x, smoothed_y, smoothed_z)), tolerance=0.01))
        # plot this in blue
        if plot:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.plot(simplified_x, simplified_y, simplified_z, 'b')
            plt.show()

        # print(f'Len smoothed: {len(smoothed_x)}')
        # print(f'Len simplified: {len(simplified_x)}')

        return list(zip(simplified_x, simplified_y))  # list[tuple[float, float, float]]

    @staticmethod
    def get_center_point(pose_landmarks, height: int, width: int) -> tuple[int, int]:
        """
        Get the center point of the hand.

        :param pose_landmarks: the hand landmarks
        :param height: the height of the image
        :param width: the width of the image
        :return: the center point
        """
        if pose_landmarks is None:
            return 0, 0, 0

        # get midpoint of landmarks 16, 18 and 20
        x = min(int((pose_landmarks.landmark[16].x + pose_landmarks.landmark[18].x + pose_landmarks.landmark[20].x) / 3 * width), width - 1)
        y = min(int((pose_landmarks.landmark[16].y + pose_landmarks.landmark[18].y + pose_landmarks.landmark[20].y) / 3 * height), height - 1)
        z = min(int((pose_landmarks.landmark[16].z + pose_landmarks.landmark[18].z + pose_landmarks.landmark[20].z) / 3 * width), width - 1)

        # x = min(int(pose_landmarks.landmark[16].x * width), width - 1)
        # y = min(int(pose_landmarks.landmark[16].y * height), height - 1)
        # z = min(int(pose_landmarks.landmark[16].z * width), width - 1)

        return x, y, z

        # x = min(int(pose_landmarks.landmark[0].x * width), width - 1)
        # y = min(int(pose_landmarks.landmark[0].y * height), height - 1)
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

    def check_gesture_frames(self, pose_ratios: list[float]):
        return super().check_gesture(ratios=pose_ratios, gesture=self.last_frame)

    def detect_gesture(self, ratios):
        # Calculate the DTW distance between the gesture and the stored gesture
        distance, _ = fastdtw(ratios, self.gesture, dist=euclidean)

        threshold = 2.2
        # Update the minimum distance and gesture ID if a better match is found

        if distance < threshold:
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
        with pose_module.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
        ) as pose:
            fps_tracker = FPSTracker()
            while True:
                _, frame = self.capture.read()
                height, width, _ = frame.shape

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                pose_landmarks = None
                ratios = None
                found = False
                if results.pose_landmarks is not None:  # type: ignore
                    pose_landmarks = self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if self.gesture is not None and len(self.point_history) == MAX_POINT_HISTORY:
                        if any(point == (0, 0) for point in self.point_history):
                            self.point_history.clear()
                        else:
                            # if super().check_gesture(ratios=pose_ratios, gesture=self.first_frame):
                            #     self.ticket = True
                            ratios = self.calculate_points()
                            found = self.detect_gesture(ratios=ratios)

                center_point = self.get_center_point(pose_landmarks=pose_landmarks, height=height, width=width)
                self.point_history.append(center_point)
                self.gesture_history.append(found)

                # print(self.point_history)
                # print(self.gesture_history)

                cv2.imshow('Test Hand', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                key = cv2.waitKey(1)

                if self.start_countdown:
                    self.countdown -= 1

                if key == 115:  # S:
                    self.start_countdown = True

                if self.countdown == 0:
                    self.is_recording = True
                    self.clear_gesture()
                    self.countdown = 30
                    self.start_countdown = False

                if self.is_recording:
                    if len(self.point_history) == MAX_POINT_HISTORY:
                        if ratios:
                            self.save_gesture(ratios=ratios)
                        elif len(self.point_history) == MAX_POINT_HISTORY:
                            self.save_gesture(ratios=self.calculate_points(plot=True))

                        # self.last_frame = self.calculate_ratios(pose_landmarks)
                        self.is_recording = False
                    # elif len(self.point_history) == 0:
                    #     self.first_frame = self.calculate_ratios(pose_landmarks)

                if self.handle_key(key=key, ratios=ratios, height=height, width=width):
                    break


if __name__ == '__main__':
    recorder = GestureRecorder()
    recorder.record()
