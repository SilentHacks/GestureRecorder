import json
import os

import cv2
import numpy as np

from utils.config import mp_hands, mp_drawing
from utils.fps_tracker import FPSTracker

from utils.ThumbNailUtils import ThumbNailUtils as tn

NUM_LANDMARKS = 21
INFO_TEXT = ('"S" to save the pose\n'
             '"D" to delete the pose\n'
             '"ESC" to quit')


class PoseRecorder:
    def __init__(
            self,
            camera=0,
            num_hands: int = 1,
            static_image_mode: bool = False,
            min_detection_confidence: float = 0.7,
            min_tracking_confidence: float = 0.7,
            model_complexity: int = 0,
            pose_leniency: float = 0.3,
            pose_threshold: float = 0.99,
            save_dir: str = 'data/models/poses'
    ):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        :param num_hands: number of hands to detect
        :param static_image_mode: whether each frame is a static image or a video
        :param min_detection_confidence: the minimum confidence for detection
        :param min_tracking_confidence: the minimum confidence for tracking
        :param pose_leniency: the leniency of the pose (0-1)
        :param pose_threshold: the threshold of the pose (0-1)
        """
        self.capture = cv2.VideoCapture(camera)
        self.num_hands = num_hands
        self.static_image_mode = static_image_mode
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        self.pose_leniency = pose_leniency
        self.pose_threshold = pose_threshold
        self.pose_threshold = pose_threshold
        self.save_dir = save_dir
        self.pose = ''
        self.poses = self.load_poses(save_dir=save_dir)
        self.detected = {num: None for num in range(num_hands)}

    def close(self):
        cv2.destroyAllWindows()
        self.capture.release()

    def get_color(self, hand: int) -> tuple[int, int, int]:
        """
        Get the color of the hand based on whether it is detected or not.

        :return: color as a tuple of (B, G, R)
        """
        if self.detected[hand]:
            return 0, 255, 0

        return 0, 0, 255

    def draw_landmarks(self, frame, results):
        """
        Draw the landmarks on the frame.

        :param frame: frame to draw on
        :param results: results from the mediapipe hands module
        :return:
        """
        for index, hand_landmarks in enumerate(results.multi_hand_landmarks):
            color = self.get_color(index)
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=hand_landmarks,
                connections=mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
            )

    def draw_info(self, image, fps: int):
        cv2.putText(image, 'FPS:' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(image, "FPS:" + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2, cv2.LINE_AA)

        index = 1
        for hand, pose in self.detected.items():
            if not pose:
                continue

            text = f'HAND {index} - POSE {pose}'
            cv2.putText(image, text, (10, 110 + hand * 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(image, text, (10, 110 + hand * 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0, 0, 0), 2, cv2.LINE_AA)

            index += 1

        # Split INFO_TEXT on newline characters
        info_text = INFO_TEXT.split('\n')
        for i, line in enumerate(info_text):
            cv2.putText(image, line, (10, 300 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        return image

    def save_pose(self, ratios: np.ndarray, name: str):
        """
        Save the pose to be checked later.
        :param ratios: list of ratios
        :param name: name of the pose
        :return:
        """
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        with open(f'{self.save_dir}/{name}.json', 'w') as f:
            json.dump(ratios.tolist(), f)

        self.poses[name] = ratios

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
        for key in self.detected:
            self.detected[key] = None

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
    def calculate_ratios(hand_landmarks) -> np.ndarray:
        """
        Similar to calculate_ratios_2, but instead of ratios,
        we calculate distances from landmark 0, normalized to 0-1.
        This works pretty well with pose_leniency 0.3 and threshold 0.99.
        The advantage of this method is that it allows for any rotation of the hand, in any plane.
        Creates an array of size 21.

        :param hand_landmarks: hand landmarks
        :return: numpy array of distances from landmark 0, normalized to 0-1
        """
        x = []
        y = []
        for landmark in hand_landmarks.landmark:
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

    def handle_key(self, key: int, ratios: np.ndarray = None, hand_landmarks=None, name=None, frame=None) -> bool:
        """
        Handle key presses.

        :param key: key pressed
        :param ratios: list of ratios
        :param hand_landmarks: hand landmarks
        :param name: name of the pose
        :return: True if the program should exit, False otherwise
        """
        if key == 27:  # ESC
            return True

        if key == 100:  # D:
            self.clear_pose()
        elif key == 115:  # S:
            if ratios is None:
                ratios = self.calculate_ratios(hand_landmarks=hand_landmarks)

            self.save_pose(ratios=ratios, name=name)
            tn.frameImgCvt(name=name, frame=frame, save_dir=self.save_dir)

        return False

    def record(self, name: str = None):
        """
        Record poses and save them when the user presses the "S" key.

        :return:
        """
        with mp_hands.Hands(
                static_image_mode=self.static_image_mode,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
                max_num_hands=self.num_hands,
                model_complexity=self.model_complexity
        ) as hands:
            fps_tracker = FPSTracker()
            while True:
                ret, frame = self.capture.read()
                # print("here to do the loop")
                if ret:
                    # To improve performance, mark the image as not writeable to pass by reference
                    frame.flags.writeable = False
                    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    frame.flags.writeable = True

                    hand_landmarks = None
                    ratios = None
                    if results.multi_hand_landmarks is not None:  # type: ignore
                        self.draw_landmarks(frame=frame, results=results)  # type: ignore
                        if self.poses:
                            for index in range(self.num_hands):
                                try:
                                    hand_landmarks = results.multi_hand_landmarks[index]  # type: ignore
                                except IndexError:
                                    self.detected[index] = None
                                    continue

                                ratios = self.calculate_ratios(hand_landmarks=hand_landmarks)
                                self.detected[index] = self.check_pose(ratios=ratios)
                    cv2.imshow('Test Hand', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))
                else:
                    print("ready to do again")
                    # If the video is over, start again
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                key = cv2.waitKey(1)
                if self.handle_key(key=key, ratios=ratios, hand_landmarks=hand_landmarks, name=name, frame=frame):
                    break
