import os
from collections import deque, Counter
import json

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
    simplify_gesture, laplacian_smoothing_3d, simplify_gesture_3d, process_landmarks

mp_pose = mediapipe.solutions.pose

MAX_POINT_HISTORY = 25

FOCUS_POINTS = {
    mp_pose.PoseLandmark.LEFT_HIP,
    mp_pose.PoseLandmark.RIGHT_HIP,
    mp_pose.PoseLandmark.LEFT_KNEE,
    mp_pose.PoseLandmark.RIGHT_KNEE,
    mp_pose.PoseLandmark.LEFT_ANKLE,
    mp_pose.PoseLandmark.RIGHT_ANKLE,
    mp_pose.PoseLandmark.LEFT_SHOULDER,
    mp_pose.PoseLandmark.RIGHT_SHOULDER,
    mp_pose.PoseLandmark.LEFT_ELBOW,
    mp_pose.PoseLandmark.RIGHT_ELBOW,
    mp_pose.PoseLandmark.LEFT_WRIST,
    mp_pose.PoseLandmark.RIGHT_WRIST
}


class GestureTracker:
    def __init__(self, camera: int = 0):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        """
        self.capture = cv2.VideoCapture(camera)
        self.point_history = {num.value: deque(maxlen=MAX_POINT_HISTORY) for num in FOCUS_POINTS}
        self.gesture_history: deque[str] = deque(maxlen=MAX_POINT_HISTORY)
        self.landmark_history = deque(maxlen=MAX_POINT_HISTORY)
        self.color_keep = 0
        self.first_frame = None
        self.last_frame = None
        self.ticket = True
        self.detected = ''

        self.gestures = self.load_gestures()

        # self.gesture = self.calculate_points(EXAMPLE_DATA)

    @staticmethod
    def load_gestures():
        gestures = []
        for file in os.listdir("data/models"):
            if file.endswith(".json"):
                with open(os.path.join("data/models", file), "r") as f:
                    gestures.append(json.load(f))

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
        draw_module.draw_landmarks(
            image=frame,
            landmark_list=results.pose_landmarks,
            connections=mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=draw_module.DrawingSpec(color=color, thickness=2, circle_radius=2),
            connection_drawing_spec=draw_module.DrawingSpec(color=color, thickness=2, circle_radius=2)
        )

    def draw_info(self, image, fps: int):
        cv2.putText(image, 'FPS:' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(image, "FPS:" + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(image, f'Gesture: {self.detected or None}', (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                    cv2.LINE_AA)

        # if self.gesture:
        #     text = 'GESTURE STORED'
        # else:
        #     text = 'NO GESTURE STORED'
        #
        # cv2.putText(image, text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Split INFO_TEXT on newline characters
        # info_text = INFO_TEXT.split('\n')
        # for i, line in enumerate(info_text):
        #     cv2.putText(image, line, (10, 150 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        return image

    @staticmethod
    def get_centre_point(results, num):
        # calculate distance between left and right shoulder
        landmark = results.pose_landmarks.landmark[num]

        if not landmark:
            return 0, 0

        shoulder_distance = euclidean(
            (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
             results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y),
            (results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
             results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y)
        )
        neck_x = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x +
                  results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x) / 2
        neck_y = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y +
                  results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
        # Normalize the coordinates to the shoulder width
        # x = min(int((landmark.x - neck_x) / shoulder_distance * width), width - 1)
        # y = min(int((landmark.y - neck_y) / shoulder_distance * width), height - 1)
        x = (landmark.x - neck_x) / shoulder_distance
        y = (landmark.y - neck_y) / shoulder_distance

        return x, y

    def detect_gesture(self):
        scores = []
        for gesture in self.gestures:
            landmark_ids = {int(idx) for idx in gesture['points'].keys()}
            processed = process_landmarks(self.point_history, relevant_landmarks=landmark_ids)

            distances = []
            for landmark_id, points in gesture['points'].items():
                distance, _ = fastdtw(processed[int(landmark_id)], points, dist=euclidean)
                # distance = calculate_threshold(points, processed[int(landmark_id)])
                distances.append(distance)

            mean = sum(distances) / len(distances)
            # print(gesture['name'], distances, mean)
            if mean < 15:
                scores.append((gesture['name'], mean))

        if scores:
            scores.sort(key=lambda x: x[1])
            self.color_keep = 20
            self.detected = scores[0][0]

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

    def run(self):
        """
        Record gestures and save them when the user presses the "S" key.

        :return:
        """
        with mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
        ) as pose:
            fps_tracker = FPSTracker()
            while True:
                _, frame = self.capture.read()

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                if results.pose_landmarks is not None:  # type: ignore
                    self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if len(self.point_history[23]) == MAX_POINT_HISTORY:
                        self.detect_gesture()

                    for num in FOCUS_POINTS:
                        self.point_history[num.value].append(self.get_centre_point(results=results, num=num.value))

                # print(self.point_history)
                # print(self.gesture_history)

                cv2.imshow('Test Hand', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                key = cv2.waitKey(1)

                if self.handle_key(key=key):
                    break


if __name__ == '__main__':
    recorder = GestureTracker()
    recorder.run()
