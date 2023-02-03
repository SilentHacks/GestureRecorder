import cv2
import mediapipe

from utils.fps_tracker import FPSTracker

draw_module = mediapipe.solutions.drawing_utils
hands_module = mediapipe.solutions.hands

NUM_LANDMARKS = 21
INFO_TEXT = ('"S" to save the gesture\n'
             '"D" to delete the gesture\n'
             '"ESC" to quit\n\n'
             '"1", "2", or "3" to change the strategy.')

STRATEGY_PARAMS = {
    1: (0.5, 0.8),
    2: (0.4, 0.95),
    3: (0.3, 0.99)
}


class Recorder:
    def __init__(
            self,
            camera: int = 0,
            num_hands: int = 1,
            static_image_mode: bool = False,
            min_detection_confidence: float = 0.7,
            min_tracking_confidence: float = 0.7,
            gesture_leniency: float = 0.5,
            gesture_threshold: float = 0.8,
            strategy: int = 1
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
        :param strategy: the strategy to use for calculating ratios (1-3)
        """
        self.capture = cv2.VideoCapture(camera)
        self.num_hands = num_hands
        self.static_image_mode = static_image_mode
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.gesture_leniency = gesture_leniency
        self.gesture_threshold = gesture_threshold
        self.strategy = strategy
        self.gesture = None
        self.detected = False
        self.is_recording = False
        self.start_countdown = False

    def __del__(self):
        cv2.destroyAllWindows()
        self.capture.release()

    @property
    def color(self) -> tuple[int, int, int]:
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
        hand_landmarks = None
        color = self.color
        for hand_landmarks in results.multi_hand_landmarks:
            draw_module.draw_landmarks(
                image=frame,
                landmark_list=hand_landmarks,
                connections=hands_module.HAND_CONNECTIONS,
                landmark_drawing_spec=draw_module.DrawingSpec(color=color, thickness=2, circle_radius=2),
                connection_drawing_spec=draw_module.DrawingSpec(color=color, thickness=2, circle_radius=2)
            )

        return hand_landmarks

    def draw_info(self, image, fps: int):
        cv2.putText(image, 'FPS:' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(image, "FPS:" + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(image, f'STRATEGY: {self.strategy}', (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                    cv2.LINE_AA)

        if self.gesture:
            color = (0, 255, 0)
        else:
            if self.countdown < 30:
                if self.countdown == 0:
                    color = (0, 255, 0)
                else:
                    color = (0, 255, 255)
            else:
                color = (0, 0, 255)

        cv2.circle(image, (image.shape[1] - 30, 30), 20, color, -1)

        if self.gesture:
            text = 'GESTURE STORED'
        else:
            text = 'NO GESTURE STORED'

        cv2.putText(image, text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Split INFO_TEXT on newline characters
        info_text = INFO_TEXT.split('\n')
        for i, line in enumerate(info_text):
            cv2.putText(image, line, (10, 150 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        return image

    def save_gesture(self, ratios: list[float]):
        """
        Save the gesture to be checked later.
        :param ratios: list of ratios
        :return:
        """
        self.gesture = ratios

    def clear_gesture(self):
        """
        Clear the gesture.
        :return:
        """
        self.gesture = None
        self.detected = False

    def check_gesture(self, ratios: list[float], gesture=None):
        """
        Check if the gesture is within the leniency and threshold of the saved gesture.

        :param ratios: list of ratios
        :param gesture: gesture to check against
        :return: True if gesture surpasses threshold, False otherwise
        """
        # correct = 0
        # for i in range(len(ratios)):
        #     if abs(ratios[i] - self.gesture[i]) < self.gesture_leniency:
        #         correct += 1
        #
        # return correct > self.gesture_threshold * len(ratios)

        # This is a more optimized version of the above code
        gesture = gesture or self.gesture
        wrong = 0
        wrong_threshold = len(ratios) * (1 - self.gesture_threshold)
        for i in range(len(ratios)):
            if abs(ratios[i] - gesture[i]) > self.gesture_leniency:
                wrong += 1

            if wrong > wrong_threshold:
                return False

        return True

    def calculate_ratios(self, hand_landmarks) -> list[float]:
        """
        Helper function to calculate the ratios based on the strategy.
        :param hand_landmarks: hand landmarks
        :return: list of ratios
        """
        if self.strategy == 1:
            return self.calculate_ratios_1(hand_landmarks)
        elif self.strategy == 2:
            return self.calculate_ratios_2(hand_landmarks)

        return self.calculate_distances(hand_landmarks)

    @staticmethod
    def calculate_ratios_1(hand_landmarks) -> list[float]:
        """
        Calculate ratios of x and y coordinates to and from all landmarks.
        This does not work with rotation of the hand and creates an array of size 210.
        Has good accuracy with gesture_leniency ~0.5 and threshold ~0.8.

        Does not allow for rotations. Despite having the best accuracy, it is not recommended
        as the array is too large and the accuracy is too precise anyway.

        :param hand_landmarks: hand landmarks
        :return: list of ratios
        """
        ratios = []
        for i in range(NUM_LANDMARKS):
            for j in range(i + 1, NUM_LANDMARKS):
                ratios.append(
                    (hand_landmarks.landmark[i].x - hand_landmarks.landmark[j].x) / (
                            hand_landmarks.landmark[i].y - hand_landmarks.landmark[j].y))

        return ratios

    @staticmethod
    def calculate_ratios_2(hand_landmarks) -> list[float]:
        """
        Calculate ratios of x and y coordinates from landmark 0.
        Works well with gesture_leniency 0.4 and threshold 0.95.
        This does not work with rotation of the hand.
        Creates an array of size 42.

        :param hand_landmarks: hand landmarks
        :return: list of ratios
        """
        ratios = []
        max_value = 0
        zero_x = hand_landmarks.landmark[0].x
        zero_y = hand_landmarks.landmark[0].y
        for landmark in hand_landmarks.landmark:
            # Convert to relative coordinate from landmark 0
            x = landmark.x - zero_x
            y = landmark.y - zero_y
            ratios.append(x)
            ratios.append(y)

            # Find max value
            max_value = max(max_value, x, y)

        # Normalize to 0-1
        max_value = abs(max_value)
        for i in range(len(ratios)):
            ratios[i] /= max_value

        return ratios

    @staticmethod
    def calculate_distances(hand_landmarks) -> list[float]:
        """
        Similar to calculate_ratios_2, but instead of ratios,
        we calculate distances from landmark 0, normalized to 0-1.
        This works pretty well with gesture_leniency 0.3 and threshold 0.99.
        The advantage of this method is that it allows for any rotation of the hand, in any plane.
        Creates an array of size 21.

        :param hand_landmarks: hand landmarks
        :return: list of distances from landmark 0, normalized to 0-1
        """
        distances = []
        max_value = 0
        zero_x = hand_landmarks.landmark[0].x
        zero_y = hand_landmarks.landmark[0].y
        for landmark in hand_landmarks.landmark:
            # Find distance from landmark 0
            x = landmark.x - zero_x
            y = landmark.y - zero_y
            dist = x ** 2 + y ** 2  # For optimization, we don't need to sqrt
            distances.append(dist)

            # Find max value
            max_value = max(max_value, dist)

        # Normalize to 0-1
        max_value = abs(max_value)
        for i in range(len(distances)):
            distances[i] /= max_value

        return distances

    # The following methods are for the SIFT method
    # These are provided just for testing, it's pretty hard to get it working

    @staticmethod
    def normalize_landmark_to_pixel(landmark, image):
        height, width, _ = image.shape
        # Cap to max height and width
        x = min(int(landmark.x * width), width - 1)
        y = min(int(landmark.y * height), height - 1)

        return x, y

    @staticmethod
    def calculate_sift_descriptors(image, hand_landmarks):
        sift = cv2.SIFT_create()
        kp = []
        for landmark in hand_landmarks.landmark:
            x, y = Recorder.normalize_landmark_to_pixel(landmark, image)
            kp.append(cv2.KeyPoint(x=x, y=y, size=1))

        kp, des = sift.compute(image, kp)

        return des

    def detect_sift(self, image, hand_landmarks):
        des = self.calculate_sift_descriptors(image, hand_landmarks)
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des, self.gesture, k=2)
        good = []
        for m, n in matches:
            if m.distance < self.gesture_leniency * n.distance:
                good.append([m])

        self.detected = len(good) > self.gesture_threshold * len(matches)

    def detect_pose(self, image, hand_landmarks):
        descriptors = self.calculate_sift_descriptors(image=image, hand_landmarks=hand_landmarks)

        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)

        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(descriptors, self.gesture, k=2)

        good = []
        for m, n in matches:
            if m.distance < self.gesture_leniency * n.distance:
                good.append(m)

        self.detected = len(good) > self.gesture_threshold * len(matches)

    def handle_key(self, key: int, ratios: list[float] = None, hand_landmarks=None) -> bool:
        """
        Handle key presses.

        :param key: key pressed
        :param ratios: list of ratios
        :param hand_landmarks: hand landmarks
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
        elif key == 115:  # S:
            self.save_gesture(ratios=ratios or self.calculate_ratios(hand_landmarks=hand_landmarks))
            # if hand_landmarks:
            #     self.gesture = self.calculate_sift_descriptors(image=frame, hand_landmarks=hand_landmarks)

        return False

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

                # To improve performance, mark the image as not writeable to pass by reference
                frame.flags.writeable = False
                results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame.flags.writeable = True

                hand_landmarks = None
                ratios = None
                if results.multi_hand_landmarks is not None:  # type: ignore
                    hand_landmarks = self.draw_landmarks(frame=frame, results=results)  # type: ignore
                    if self.gesture is not None:
                        # self.detect_pose(image=frame, hand_landmarks=hand_landmarks)
                        ratios = self.calculate_ratios(hand_landmarks=hand_landmarks)
                        self.detected = self.check_gesture(ratios=ratios)

                cv2.imshow('Test Hand', self.draw_info(image=cv2.flip(frame, 1), fps=fps_tracker.get()))

                key = cv2.waitKey(1)
                if self.handle_key(key=key, ratios=ratios, hand_landmarks=hand_landmarks):
                    break


if __name__ == '__main__':
    recorder = Recorder()
    recorder.record()
