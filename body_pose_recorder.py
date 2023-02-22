from __future__ import annotations

import json
import os

import cv2
import numpy as np

from utils.config import mp_pose, mp_drawing
from utils.fps_tracker import FPSTracker

NUM_LANDMARKS = 21
INFO_TEXT = ('"S" to save the pose\n'
             '"D" to delete the pose\n'
             '"ESC" to quit')


class BodyPoseRecorder:
    def __init__(
            self,
            camera: int | str = 0,
            static_image_mode: bool = True,
            min_detection_confidence: float = 0.5,
            min_tracking_confidence: float = 0.5,
            model_complexity: int = 0,
            pose_leniency: float = 0.3,
            pose_threshold: float = 0.99,
            save_dir: str = 'data/models/body_poses'
    ):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        :param static_image_mode: whether each frame is a static image or a video
        :param min_detection_confidence: the minimum confidence for detection
        :param min_tracking_confidence: the minimum confidence for tracking
        :param pose_leniency: the leniency of the pose (0-1)
        :param pose_threshold: the threshold of the pose (0-1)
        """
        self.capture = cv2.VideoCapture(camera)
        self.static_image_mode = static_image_mode
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        self.pose_leniency = pose_leniency
        self.pose_threshold = pose_threshold
        self.save_dir = save_dir
        self.pose = ''
        self.poses = self.load_poses(save_dir=save_dir)
        self.detected = None

    def __del__(self):
        cv2.destroyAllWindows()
        self.capture.release()

    def get_color(self) -> tuple[int, int, int]:
        """
        Get the color of the hand based on whether it is detected or not.

        :return: color as a tuple of (B, G, R)
        """
        if self.detected:
            return 0, 255, 0

        return 0, 0, 255

    def draw_landmarks(self, frame, results):
        """
        Draw the landmarks on the frame.

        :param frame: frame to draw on
        :param results: results from the mediapipe hands module
        :return:
        """
        color = self.get_color()
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

        if self.detected:
            text = f'POSE {self.detected}'
            cv2.putText(image, text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(image, text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0, 0, 0), 2, cv2.LINE_AA)

        # Split INFO_TEXT on newline characters
        info_text = INFO_TEXT.split('\n')
        for i, line in enumerate(info_text):
            cv2.putText(image, line, (10, 670 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        return image

    def save_pose(self, ratios: np.ndarray):
        """
        Save the pose to be checked later.
        :param ratios: list of ratios
        :return:
        """
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        pose_name = f'{len(os.listdir(self.save_dir)) + 1}'
        with open(f'{self.save_dir}/{pose_name}.json', 'w') as f:
            json.dump(ratios.tolist(), f)

        self.poses[pose_name] = ratios

    @staticmethod
    def load_poses(save_dir: str):
        """
        Load all poses from the data/models/poses directory.
        :return:
        """
        poses = {}
        if not os.path.exists(save_dir):
            return poses

        for file in os.listdir(save_dir):
            with open(f'{save_dir}/{file}', 'r') as f:
                poses[file[:-5]] = np.array(json.load(f))

        return poses

    def clear_pose(self):
        """
        Clear the pose.
        :return:
        """
        self.poses.clear()
        self.detected = None

    def check_pose(self, ratios: np.ndarray):
        """
        Check if the pose is within the leniency and threshold of the saved pose.

        :param ratios: list of ratios
        :return: True if pose surpasses threshold, False otherwise
        """
        wrong_threshold = len(ratios) * (1 - self.pose_threshold)
        scores = []
        for name, pose in self.poses.items():
            deviations = np.abs(ratios - pose)
            wrong = np.sum(deviations > self.pose_leniency)
            if wrong <= wrong_threshold:
                scores.append((name, np.mean(deviations)))

        if scores:
            scores.sort(key=lambda x: x[1])
            return scores[0][0]

        return None

    @staticmethod
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

    def handle_key(self, key: int, ratios: np.ndarray = None, landmarks=None) -> bool:
        """
        Handle key presses.

        :param key: key pressed
        :param ratios: list of ratios
        :param landmarks: body landmarks
        :return: True if the program should exit, False otherwise
        """
        if key == 27:  # ESC
            return True

        if key == 100:  # D:
            self.clear_pose()
        elif key == 115:  # S:
            if ratios is None:
                ratios = self.calculate_ratios(landmarks=landmarks)

            self.save_pose(ratios=ratios)

        return False

    def record(self):
        """
        Record poses and save them when the user presses the "S" key.

        :return:
        """
        with mp_pose.Pose(
                static_image_mode=self.static_image_mode,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
                model_complexity=self.model_complexity
        ) as hands:
            fps_tracker = FPSTracker()
            index = 1
            while True:
                index += 1
                ret, frame = self.capture.read()

                if not ret:
                    break

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                ratios = None
                landmarks = None
                if results.pose_landmarks is not None:  # type: ignore
                    landmarks = results.pose_landmarks
                    self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if self.poses:
                        ratios = self.calculate_ratios(landmarks=landmarks)
                        self.detected = self.check_pose(ratios=ratios)

                cv2.imshow('Test Hand', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                if index == 1:
                    key = 115
                else:
                    key = cv2.waitKey(5)
                # key = 115
                if self.handle_key(key=key, ratios=ratios, landmarks=landmarks):
                    break


if __name__ == '__main__':
    recorder = BodyPoseRecorder()
    recorder.record()
