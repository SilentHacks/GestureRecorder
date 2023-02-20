import json

import cv2
import numpy as np
from matplotlib import pyplot as plt

from utils.config import FOCUS_POINTS, mp_drawing, mp_pose, draw_style
from utils.tracker_2d import process_landmarks


def plot_json(gesture: str = 'punch'):
    with open(f'data/models/gestures/{gesture}.json', 'r') as f:
        data = json.load(f)

    for landmark_id, points in data.items():
        x, y = zip(*points)

        landmark_id = int(landmark_id)
        color = np.array([landmark_id * 100 % 255, landmark_id * 200 % 255, landmark_id * 300 % 255]) / 255
        plt.plot(x, y, color=color, label=f'Landmark {landmark_id}')

    plt.legend()
    plt.show()


class GestureRecorder:
    def __init__(
            self,
            camera=None,
            min_detection_confidence: float = 0.5,
            min_tracking_confidence: float = 0.5,
            model_complexity: int = 1,
            save_dir: str = 'data/models/gestures',
    ):
        """
        Initialize the recorder.

        :param camera: camera ID to use
        :param min_detection_confidence: the minimum confidence for detection
        :param min_tracking_confidence: the minimum confidence for tracking
        :param model_complexity: the complexity of the model
        :param save_dir: the directory to save the poses
        """
        self.capture = cv2.VideoCapture(camera)
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        self.save_dir = save_dir

    def save_json(self, processed, name):
        with open(f'{self.save_dir}/{name}.json', 'w') as f:
            json.dump(processed, f, indent=4)

    def close(self):
        cv2.destroyAllWindows()
        self.capture.release()

    def record(self, name: str):
        history = {num.value: [] for num in FOCUS_POINTS}

        with mp_pose.Pose(
                static_image_mode=False,
                model_complexity=self.model_complexity,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
        ) as pose:
            while self.capture.isOpened():
                ret, image = self.capture.read()
                if not ret:
                    break

                image.flags.writeable = False
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose.process(image)

                # Draw the pose annotation on the image.
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                mp_drawing.draw_landmarks(image, results.pose_landmarks,  # type: ignore
                                          mp_pose.POSE_CONNECTIONS, landmark_drawing_spec=draw_style)

                if results.pose_world_landmarks:  # type: ignore
                    for num in FOCUS_POINTS:
                        landmark = results.pose_world_landmarks.landmark[num.value]  # type: ignore
                        history[num.value].append((landmark.x, landmark.y) if landmark else (0, 0))

                cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
                if cv2.waitKey(5) & 0xFF == 27:
                    break

            # self.capture.release()

        processed = process_landmarks(history, plot=True)
        self.save_json(processed, name)

if __name__ == '__main__':
    g = GestureRecorder()
    g.record(name='punch')
