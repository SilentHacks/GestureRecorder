import json
import os
import time
from collections import deque

import cv2
from fastdtw import fastdtw
from pynput.mouse import Controller
from pynput.keyboard import Key, Controller as KeyboardController
from scipy.spatial.distance import euclidean

from pose_recorder import mp_drawing
from utils.config import FOCUS_POINTS, mp_pose
from utils.fps_tracker import FPSTracker
from utils.tracker_2d import process_landmarks

BUFFER_SIZE = 25
MOVE_MOUSE = False


class GestureTracker:
    def __init__(self, camera: int = 0):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        """
        self.capture = cv2.VideoCapture(camera)
        self.point_history = {num.value: deque(maxlen=BUFFER_SIZE) for num in FOCUS_POINTS}
        self.color_keep = 0
        self.detected = ''
        self.mouse = Controller()
        self.keyboard = KeyboardController()

        self.gestures = self.load_gestures()

    @staticmethod
    def load_gestures():
        gestures = []
        include = ["testRecord"]
        for file in os.listdir("data/models/gestures"):
            if file.endswith(".json") and file[:-5] in include:
                with open(os.path.join("data/models/gestures", file), "r") as f:
                    points = json.load(f)
                    # points = {int(k): v for k, v in points.keys()}
                    gestures.append({
                        "name": points.get('name') or file[:-5],
                        "points": points.get('points') or points
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

    @staticmethod
    def get_centre_point(results, num):
        landmark = results.pose_world_landmarks.landmark[num]

        if landmark.visibility < 0.7:
            return 0, 0

        return landmark.x, landmark.y

    def detect_gesture(self):
        scores = []
        for gesture in self.gestures:
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
            if mean < threshold:
                scores.append((gesture['name'], mean))

        if scores:
            scores.sort(key=lambda x: x[1])
            self.color_keep = 10
            self.detected = scores[0][0]
            # print(self.detected, scores[0][1])
            # self.handle_input()
            if self.detected != 'front_stroke':
                self.clear_history()

    def clear_history(self):
        for k in self.point_history.keys():
            self.point_history[k].clear()

    def handle_input(self):
        """Before you freak out, this is just for testing."""
        if self.detected == 'baseball_swing':
            self.mouse.position = (1100, 800)
            time.sleep(0.03)

            # Drag mouse to the left with deceleration
            for i in range(60, 25, -1):
                self.mouse.move(-i, -i)
                time.sleep(0.01)

        elif self.detected == 'tennis_swing':
            # Drag mouse to the left with deceleration
            self.mouse.position = (1200, 400)
            time.sleep(0.03)

            for i in range(60, 25, -1):
                self.mouse.move(-i, -i // 2)
                time.sleep(0.01)

        elif self.detected == 'back_swing':
            # Drag mouse to the right with deceleration
            self.mouse.position = (400, 400)
            time.sleep(0.03)

            for i in range(60, 25, -1):
                self.mouse.move(i, -i // 2)
                time.sleep(0.01)

        elif self.detected == 'serve':
            self.keyboard.press('i')
            time.sleep(0.03)
            self.keyboard.release('i')

            self.keyboard.press('s')
            time.sleep(0.03)
            self.keyboard.release('s')

            self.keyboard.press('i')
            time.sleep(0.03)
            self.keyboard.release('i')

            self.keyboard.press('s')
            time.sleep(0.03)
            self.keyboard.release('s')

        elif self.detected == 'punch':
            self.keyboard.press(Key.enter)
            time.sleep(0.04)
            self.keyboard.release(Key.enter)

        elif self.detected == 'punch_left':
            self.keyboard.press('a')
            time.sleep(0.04)
            self.keyboard.release('a')

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
                _, frame = self.capture.read()

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                if results.pose_landmarks is not None:  # type: ignore
                    if display:
                        self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if len(self.point_history[list(self.point_history.keys())[0]]) == BUFFER_SIZE:
                        self.detect_gesture()

                    for num in FOCUS_POINTS:
                        self.point_history[num.value].append(
                            self.get_centre_point(results=results, num=num.value))  # type: ignore

                if display:
                    cv2.imshow('Gesture Tracker', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                    key = cv2.waitKey(1)
                    if self.handle_key(key=key):
                        break


if __name__ == '__main__':
    recorder = GestureTracker()
    recorder.run()
