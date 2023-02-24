from __future__ import annotations

import json
import os
import multiprocessing
from collections import deque

import cv2
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

from pose_recorder import mp_drawing
from utils.config import FOCUS_POINTS, mp_pose
from utils.fps_tracker import FPSTracker
from utils.tracker_2d import process_landmarks

BUFFER_SIZE = 25
MOVE_MOUSE = False


gesture = 'single_wave'


def calculate_ratios(landmarks) -> np.ndarray:
    """
    Similar to calculate_ratios_2, but instead of ratios,
    we calculate distances from landmark 0, normalized to 0-1.
    This works pretty well with pose_leniency 0.3 and threshold 0.99.
    The advantage of this method is that it allows for any rotation of the hand, in any plane.
    Creates an array of size 21.

    :param landmarks: body landmarks
    :return: numpy array of distances from landmark 0, normalized to 0-1
    """
    x = []
    y = []
    for landmark in landmarks.landmark:
        x.append(landmark.x)
        y.append(landmark.y)

    x = np.array(x)
    y = np.array(y)

    zero_x, zero_y = x[0], y[0]
    x -= zero_x
    y -= zero_y

    distances = np.square(x) + np.square(y)
    distances /= np.max(distances)

    return distances


class GestureTracker:
    def __init__(self, camera: int | str = 0, pose_leniency: float = 0.05, pose_threshold: float = 0.99):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        """
        self.capture = cv2.VideoCapture(camera)
        self.point_history = {num.value: deque(maxlen=BUFFER_SIZE) for num in FOCUS_POINTS}
        self.color_keep = 0
        self.detected = ''

        self.pose_leniency = pose_leniency
        self.pose_threshold = pose_threshold
        self.landmarks = None

        self.gestures = self.load_gestures()
        self.scores = []

    @staticmethod
    def load_gestures():
        gestures = []
        include = ['throw', 'clap', 'front_kick', 'single_wave']
        path = "test/models/gestures"
        for file in os.listdir(path):
            if file.endswith(".json") and file[:-5] in include:
                with open(os.path.join(path, file), "r") as f:
                    points = json.load(f)
                    first = points.get('first')
                    if first:
                        first = np.array(first)

                    gestures.append({
                        "name": points.get('name') or file[:-5],
                        "points": points.get('points') or points,
                        "first": first
                    })

        return gestures

    @property
    def color(self) -> tuple[int, int, int]:
        """
        Get the color of the hand landmarks.

        :return: the color
        """
        if self.detected and self.color_keep > 0:
            self.color_keep -= 1
            return 0, 255, 0

        self.detected = ''
        return 0, 0, 255

    def draw_landmarks(self, frame, results):
        """
        Draw the landmarks on the frame.

        :param frame: frame to draw on
        :param results: results from the mediapipe hands module
        :return:
        """
        color = self.color
        mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=results.pose_landmarks,
            connections=mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
        )

    def draw_info(self, image, fps: int):
        cv2.putText(image, 'FPS:' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(image, "FPS:" + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(image, f'Gesture: {self.detected or None}', (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 4,
                    cv2.LINE_AA)
        cv2.putText(image, f'Gesture: {self.detected or None}', (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 2,
                    cv2.LINE_AA)

        return image

    def check_pose(self, ratios: np.ndarray, pose):
        """
        Check if the pose is within the leniency and threshold of the saved pose.

        :param ratios: list of ratios
        :return: True if pose surpasses threshold, False otherwise
        """
        wrong_threshold = len(ratios) * (1 - self.pose_threshold)
        deviations = np.abs(ratios - pose)
        wrong = np.sum(deviations > self.pose_leniency)
        return wrong <= wrong_threshold

    @staticmethod
    def get_centre_point(results, num):
        landmark = results.pose_world_landmarks.landmark[num]

        if landmark.visibility < 0.7:
            return 0, 0

        return landmark.x, landmark.y

    def detect_gesture(self):
        scores = []
        for gesture in self.gestures:
            if gesture['first'] is not None and not self.check_pose(calculate_ratios(self.landmarks), gesture['first']):
                continue
            landmark_ids = {int(idx) for idx in gesture['points'].keys()}
            processed = process_landmarks(self.point_history, include_landmarks=landmark_ids)

            distances = []
            num_points = 0
            for landmark_id, points in gesture['points'].items():
                count = 0
                for coord in self.point_history[int(landmark_id)]:
                    if coord[0] == 0 and coord[1] == 0:
                        count += 1
                        if count >= BUFFER_SIZE // 2:
                            return

                num_points += len(points)
                distance, _ = fastdtw(processed[int(landmark_id)], points, dist=euclidean)
                distances.append(distance)

            mean = sum(distances) / len(distances)
            threshold = 0.77 + 0.01 * num_points
            # print(gesture['name'], mean, threshold)
            self.scores.append((gesture['name'], mean))
            if mean < threshold:
                scores.append((gesture['name'], mean))

        if scores:
            scores.sort(key=lambda x: x[1])
            self.color_keep = 10
            self.detected = scores[0][0]
            # if self.detected != 'double_wave':
            #     self.clear_history()

    def clear_history(self):
        for k in self.point_history.keys():
            self.point_history[k].clear()

    @staticmethod
    def handle_key(key: int) -> bool:
        """
        Handle key presses.

        :param key: key pressed
        :return: True if the program should exit, False otherwise
        """
        if key == 27:  # ESC
            return True

        return False

    def run(self, display: bool = True):
        """
        Record gestures and save them when the user presses the "S" key.

        :param display: whether to display the video feed
        :return:
        """

        with mp_pose.Pose(
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
        ) as pose:
            fps_tracker = FPSTracker()
            while True:
                ret, frame = self.capture.read()
                if not ret:
                    break

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                if results.pose_landmarks is not None:  # type: ignore
                    self.landmarks = results.pose_landmarks  # type: ignore
                    if display:
                        self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if len(self.point_history[list(self.point_history.keys())[0]]) == BUFFER_SIZE:
                        self.detect_gesture()

                    for num in FOCUS_POINTS:
                        self.point_history[num.value].append(
                            self.get_centre_point(results=results, num=num.value))  # type: ignore

                if display:
                    cv2.imshow('Gesture Tracker', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                    key = cv2.waitKey(5)
                    if self.handle_key(key=key):
                        break


def calc(path):
    recorder = GestureTracker(camera=path)
    recorder.run(display=False)
    recorder.scores.sort(key=lambda x: x[1])

    return recorder.scores[0]


def confusion_matrix():
    # run the program for each vid in test/dataset/tick
    vid_path = f'test/dataset/{gesture}'
    matrix = {}
    paths = []
    for vid in os.listdir(vid_path):
        if not vid.endswith('.mp4'):
            continue

        paths.append(os.path.join(vid_path, vid))

    with multiprocessing.Pool(8) as p:
        results = p.map(calc, paths)

    for result in results:
        if result[0] not in matrix:
            matrix[result[0]] = 0

        matrix[result[0]] += 1

    print(matrix)


def main():
    # run the program for each vid in test/dataset/tick
    vid_path = f'test/dataset/{gesture}'
    for vid in os.listdir(vid_path):
        if not vid.endswith('.mp4'):
            continue

        recorder = GestureTracker(camera=os.path.join(vid_path, vid))
        recorder.run(display=True)


if __name__ == '__main__':
    confusion_matrix()
