import json
import os

import cv2
import mediapipe as mp
import numpy as np
from fastdtw import fastdtw
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.distance import euclidean

from utils.tracking import process_landmarks, calculate_threshold, process_landmarks_3d, normalize_gesture

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

FOCUS_POINTS = {
    mp_pose.PoseLandmark.LEFT_HIP,
    mp_pose.PoseLandmark.RIGHT_HIP,
    # mp_pose.PoseLandmark.LEFT_KNEE,
    # mp_pose.PoseLandmark.RIGHT_KNEE,
    # mp_pose.PoseLandmark.LEFT_ANKLE,
    # mp_pose.PoseLandmark.RIGHT_ANKLE,
    mp_pose.PoseLandmark.LEFT_SHOULDER,
    mp_pose.PoseLandmark.RIGHT_SHOULDER,
    mp_pose.PoseLandmark.LEFT_ELBOW,
    mp_pose.PoseLandmark.RIGHT_ELBOW,
    mp_pose.PoseLandmark.LEFT_WRIST,
    mp_pose.PoseLandmark.RIGHT_WRIST
}


def record(gesture_name, video_name):
    # Set the Video stream
    cap = cv2.VideoCapture(
        os.path.join("data", "videos", gesture_name, f"{video_name}.mp4")
    )

    history = {num.value: [] for num in FOCUS_POINTS}
    index = 0

    with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5
    ) as pose:
        while cap.isOpened():
            ret, image = cap.read()
            if not ret:
                break

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            # Draw the pose annotation on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

            if results.pose_world_landmarks:
                for num in FOCUS_POINTS:
                    # calculate distance between left and right shoulder
                    # shoulder_distance = euclidean(
                    #     (results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                    #      results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y),
                    #     (results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                    #      results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y)
                    # )
                    # neck_x = (results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x +
                    #           results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x) / 2
                    # neck_y = (results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y +
                    #           results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
                    # neck_z = (results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].z +
                    #           results.pose_world_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].z) / 2
                    landmark = results.pose_world_landmarks.landmark[num.value]
                    if landmark:
                        # Normalize the coordinates to the shoulder width
                        # x = min(int((landmark.x - neck_x) / shoulder_distance * width), width - 1)
                        # y = min(int((landmark.y - neck_y) / shoulder_distance * width), height - 1)
                        # x = (landmark.x - neck_x) / shoulder_distance
                        # y = (landmark.y - neck_y) / shoulder_distance
                        # z = (landmark.z - neck_z) / shoulder_distance
                        # history[num.value].append((x, y))
                        history[num.value].append((landmark.x, landmark.y))
                    else:
                        history[num.value].append((0, 0))

            cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:
                break

            index += 1

        cap.release()

    print('Frames:', len(history[mp_pose.PoseLandmark.LEFT_HIP]))
    print(history)

    # use = results.pose_world_landmarks
    # mp_drawing.plot_landmarks(use, mp_pose.POSE_CONNECTIONS)
    #
    # tracking_points = [(landmark.x, landmark.y, landmark.z) for landmark in use.landmark]
    # x, y, z = normalize_gesture(tracking_points)
    #
    # # plot the 3d graph
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(x, y, z, c='r', marker='o')
    # ax.set_xlabel('X Label')
    # ax.set_ylabel('Y Label')
    # ax.set_zlabel('Z Label')
    # plt.show()

    return history


gesture = 'front_stroke'


def main():
    history = record(gesture, '3')
    processed = process_landmarks(history, plot=True)

    to_save = {
        "name": gesture,
        "points": processed
    }

    with open(f'data/models/{gesture}.json', 'w') as f:
        json.dump(to_save, f)


def euclidean_weighted(a, b):
    return euclidean(a, b, w=[1, 1, 0.5])


def compare():
    with open(f'data/models/{gesture}.json', 'r') as f:
        model = json.load(f)

    history = record('front_stroke', '2')
    landmark_ids = {int(idx) for idx in model['points'].keys()}
    processed = process_landmarks(history, relevant_landmarks=landmark_ids, plot=True)

    distances = []
    for landmark_id, points in model['points'].items():
        distance, _ = fastdtw(processed[int(landmark_id)], points, dist=euclidean)
        # distance = calculate_threshold(points, processed[int(landmark_id)])
        distances.append(distance)

    print(distances, sum(distances) / len(distances))
    print(sum(distances) / len(distances) < (2 * len(distances)))


if __name__ == '__main__':
    compare()
