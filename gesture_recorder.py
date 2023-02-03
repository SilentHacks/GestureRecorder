from collections import deque

from recorder import Recorder

MAX_POINT_HISTORY = 20


class GestureRecorder(Recorder):
    def __init__(
            self,
            camera: int = 0,
            num_hands: int = 1,
            static_image_mode: bool = False,
            min_detection_confidence: float = 0.7,
            min_tracking_confidence: float = 0.7,
            gesture_leniency: float = 0.40,
            gesture_threshold: float = 0.95,
            num_points: int = 2,
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
        :param num_points: the number of points to record for a gesture
        """
        super().__init__(
            camera=camera,
            num_hands=num_hands,
            static_image_mode=static_image_mode,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            gesture_leniency=gesture_leniency,
            gesture_threshold=gesture_threshold,
            strategy=2,
            use_default_params=False
        )

        self.num_points = num_points
        self.gesture = []
        self.gesture_history = deque(maxlen=MAX_POINT_HISTORY)
        self.color_history = 0

    @property
    def color(self) -> tuple[int, int, int]:
        """
        Get the color of the hand based on whether it is detected or not.

        :return: color as a tuple of (B, G, R)
        """
        if self.detected or self.color_history > 0:
            self.color_history -= 1
            return 0, 255, 0

        return 0, 0, 255

    def check_gesture(self, ratios: list[float], gesture: list[float] = None):
        """
        Check if the gesture is within the leniency and threshold of the saved gesture.

        :param ratios: list of ratios
        :param gesture: the gesture to check
        :return: True if gesture surpasses threshold, False otherwise
        """
        # correct = 0
        # for i in range(len(ratios)):
        #     if abs(ratios[i] - self.gesture[i]) < self.gesture_leniency:
        #         correct += 1
        #
        # return correct > self.gesture_threshold * len(ratios)

        for index, gesture in enumerate(self.gesture, start=1):
            if super().check_gesture(ratios=ratios, gesture=gesture):
                self.gesture_history.append(index)
                break
            else:
                self.gesture_history.append(0)

        # Checks if the gesture history has the correct sequence
        found = 0
        for num in self.gesture_history:
            if num == 0:
                continue

            if num == found + 1:
                found = num
            elif num == 1:
                found = 1
            else:
                found = 0

            if found == self.num_points:
                self.gesture_history.clear()
                self.color_history = 10
                break

        return found == self.num_points

    def save_gesture(self, ratios: list[float]):
        """
        Save the gesture.

        :param ratios: the ratios to save
        """
        if len(self.gesture) < self.num_points:
            self.gesture.append(ratios)

    def clear_gesture(self):
        """
        Clear the gesture.
        """
        self.gesture.clear()
        self.gesture_history.clear()
        self.detected = False


if __name__ == '__main__':
    recorder = GestureRecorder()
    recorder.record()
