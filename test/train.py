import json
import os

import cv2
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

from gesture_tracker import calculate_ratios
from utils.config import FOCUS_POINTS, mp_pose, mp_drawing, draw_style
from utils.tracker_2d import process_landmarks


def record(path):
    MAX_FRAMES = 30
    cap = cv2.VideoCapture(path)
    # get the number of frames
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    diff = num_frames - MAX_FRAMES
    # set the frame position to the middle
    if diff > 1:
        cap.set(cv2.CAP_PROP_POS_FRAMES, diff // 2)

    history = {num.value: [] for num in FOCUS_POINTS}
    first = None

    with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5
    ) as pose:
        frame = 0
        while cap.isOpened():
            # Read only the middle 30 frames
            ret, image = cap.read()
            if not ret:
                break

            frame += 1
            if frame >= MAX_FRAMES:
                break

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            # Draw the pose annotation on the image.
            # image.flags.writeable = True
            # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            # mp_drawing.draw_landmarks(image, results.pose_landmarks,  # type: ignore
            #                           mp_pose.POSE_CONNECTIONS, landmark_drawing_spec=draw_style)

            if results.pose_world_landmarks:  # type: ignore
                for num in FOCUS_POINTS:
                    landmark = results.pose_world_landmarks.landmark[num.value]  # type: ignore
                    history[num.value].append((landmark.x, landmark.y) if landmark else (0, 0))

            # cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
            # if cv2.waitKey(5) & 0xFF == 27:
            #     break

            if frame == 1:
                first = calculate_ratios(results.pose_landmarks)

        cap.release()

    return history, first


def main():
    path = 'dataset'
    for gesture in os.listdir(path):
        if gesture == '.DS_Store' or gesture != 'front_kick':
            continue

        data = []
        for file in os.listdir(os.path.join(path, gesture)):
            if file == '.DS_Store':
                continue
            print(f'Gesture: {gesture}, File: {file}')
            history, first = record(path=os.path.join(path, gesture, file))
            processed = process_landmarks(history)
            data.append((file, processed, first))

        # Find the data that has the smallest distance to the other data
        min_distance = float('inf')
        min_file = None
        best_data = None
        for i in range(len(data)):
            for j in range(i + 1, len(data)):
                if len(data[i][1]) != len(data[j][1]):
                    continue

                distances = 0
                key_error = False
                for landmark_id, points in data[j][1].items():
                    try:
                        distance, _ = fastdtw(data[i][1][landmark_id], points, dist=euclidean)
                    except KeyError:
                        key_error = True
                        continue
                    distances += distance

                if key_error:
                    continue

                if distances < min_distance:
                    min_distance = distances
                    min_file = data[i][0]
                    best_data = data[i][1], data[i][2]

        print(f'Gesture: {gesture}, Min Distance: {min_distance}, Min File: {min_file}')
        with open(f'models/gestures/{gesture}.json', 'w') as f:
            json.dump({'points': best_data[0], 'first': best_data[1].tolist()}, f)


if __name__ == '__main__':
    main()
