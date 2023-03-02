import threading
import time

import cv2
import os
from utils.add_transparent_img import add_transparent_image

""" simple video recorder, opens a cv window via webcam
    user press 'r' to start recording, the recording length will be <= 2 seconds """

INFO_TEXT = ('"R" to start recording\n'
             '"R" again within 2 secs to stop recording\n'
             
             '"ESC" to quit')
INFO_TEXT2 = ("The recording will start after a 3-second countdown\n"
             "Setup and do gesture\n"
              "neatly right when the recording starts\n")

class VideoRecorder:
    def __init__(self, camera = 0, name: str = None):
        """
        Initialize the video recorder.
        :param name: gesture name for the video
        """
        self.camera = camera
        self.name = name
        self.fps = 15
        self.size = (960, 720)
        self.video = None
        self.frame_count = 0
        self.recording = False
        self.dataPath = os.path.join(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), "data")), "videos")
        # self.dataPath = os.path.join(os.path.abspath(os.path.join(os.path.join(dataPath, os.pardir), os.pardir)), "videos", name)

        self.save_file = os.path.join(self.dataPath, f'{self.name}.avi')
        self.cap = cv2.VideoCapture(camera)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])
        self.capSize = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        print("prop frame height", self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.showRect = False
        self.showCountDown = False
        self.countDownNum = 3
        self.barLength = 100
        self.finishRecording = False
        self.showGuide = True

    def run(self):
        print(self.save_file)
        # print("camera: ", self.camera)
        self.start()
        while True:
            # print("recording: ", self.recording)
            _, frame = self.cap.read()
            # resized_frame = cv2.resize(frame, self.size)
            cv2.imshow('Gesture Recorder', self.draw_info(frame=cv2.flip(frame, 1), fps=self.fps))
            key = cv2.waitKey(1) & 0xFF
            if self.recording:
                self.record(frame=frame)
            if self.handle_key(key=key):
                break
            # time.sleep(0.05)


        self.cap.release()
        self.video.release()
        cv2.destroyAllWindows()

            # press 'r' to start recording press again to stop


    def draw_info(self, frame, fps: int):
        frame_height, frame_width, _ = frame.shape
        cv2.putText(frame, 'FPS:' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, "FPS:" + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2, cv2.LINE_AA)

        # Split INFO_TEXT on newline characters
        info_text = INFO_TEXT.split('\n')
        # cv2.rectangle(frame, (int(self. size[0] / 2 - self.size[0] / 5), 0), (int(self.size[0] / 2 + self.size[0] / 5), self.size[1]), (255, 0, 0), 5)
        for i, line in enumerate(info_text):
            cv2.putText(frame, line, (10, 300 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, frame_height / 1200, (255, 255, 255), 1, cv2.LINE_AA)

        info_text2 = INFO_TEXT2.split('\n')
        for i, line in enumerate(info_text2):
            cv2.putText(frame, line, (10, 450 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, frame_height / 1200, (0, 0, 255), 1, cv2.LINE_AA)

        if self.showCountDown:
            cv2.putText(frame, str(self.countDownNum), (int(frame_width / 2 - frame_width / 24), int(frame_height / 2)), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 5, cv2.LINE_AA)

        if self.showRect:
            self.showGuide = False
            cv2.rectangle(frame, (0, 0), (frame_width,frame_height), (0, 0, 255), 20)
            cv2.line(frame, (30, self.capSize[1] - 30), (self.barLength * 5 + 30, self.capSize[1] - 30), (0, 255, 0), 20)

        # put the guide picture
        img = cv2.imread('utils/assets/man.png', cv2.IMREAD_UNCHANGED)
        h, w, _ = img.shape
        h_new = int(h * frame_width / 1000)
        w_new = int(w * frame_width / 1000)
        # h_new = int(h * 2)
        # w_new = int(w * 2)
        if self.showGuide:
            img_resized = cv2.resize(img, (w_new, h_new), interpolation=cv2.INTER_AREA)
            add_transparent_image(frame, img_resized, int(frame_width / 2 - h_new / 2), int(frame_height / 36))

        return frame

    def handle_key(self, key: int) -> bool:
        if key == ord('r'):
            if self.recording:
                print('stop recording')
                self.stop()
                self.recording = False
                self.showRect = False
                return False
            else:
                threading.Thread(target=self.countDown).start()
                self.showCountDown = True
                return False
        elif key == 27:
            return True
        elif self.finishRecording:
            return True

    def start(self):
        """
        Start the video recorder.
        :return:
        """
        self.video = cv2.VideoWriter(self.save_file, cv2.VideoWriter_fourcc(*'MJPG'), 15, self.size)

    def countDown(self):
        """
        Count down for 3 seconds before recording.
        :return:
        """
        for i in range(3, 0, -1):
            print(i)
            self.countDownNum = i
            time.sleep(1)


        self.recording = True
        threading.Thread(target=self.countTime).start()
        self.showCountDown = False
        self.showRect = True
        return


    def countTime(self):
        for i in range(100, 0, -1):
            # print(i)
            self.barLength = i
            time.sleep(0.015)
        print("recording stopped")
        self.recording = False
        self.showRect = False
        self.finishRecording = True
        return

    def record(self, frame):
        """
        Record a frame.
        :param frame: frame to record
        :return:
        """
        # print("here")
        vidout = cv2.resize(frame, self.size)
        self.video.write(vidout)
        self.frame_count += 1

    def stop(self):
        """
        Stop the video recorder.
        :return:
        """
        self.video.release()
        self.frame_count = 0


if __name__ == '__main__':
    recorder = VideoRecorder(name='rotate_hand')
    recorder.run()