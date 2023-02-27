import time

import cv2
import os
import threading
import queue
""" simple video recorder, opens a cv window via webcam
    user press 'r' to start recording, the recording length will be <= 2 seconds """

class VideoRecorder:
    def __init__(self, camera = 0, name: str = None):
        """
        Initialize the video recorder.
        :param name: gesture name for the video
        """
        self.camera = camera
        self.name = name
        self.fps = 17
        self.size = (960, 720)
        self.frame_count = 0
        self.recording = False
        self.dataPath = os.path.join(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), "data")), "videos")
        # self.dataPath = os.path.join(os.path.abspath(os.path.join(os.path.join(dataPath, os.pardir), os.pardir)), "videos", name)

        self.save_file = os.path.join(self.dataPath, f'{self.name}.avi')
        self.cap = cv2.VideoCapture(camera)
        # cv2.resizeWindow('Gesture Recorder', self.size[0], self.size[1])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
        self.video = None
        self.frame_queue = queue.Queue()

    def record_video(self, frame_queue):
        global recording  # Use global variable for recording status
        while True:
            # Get a frame from the queue if available
            if not frame_queue.empty():
                frame = frame_queue.get()
                vidout = cv2.resize(frame, self.size)
                # Write the frame into the file 'output.mp4'
                if recording:
                    print("writing")
                    self.video.write(vidout)

    def run(self):
        self.start()
        print(self.save_file)
        record_thread = threading.Thread(target=self.record_video(frame_queue=self.frame_queue))
        record_thread.start()

        while True:
            # print("recording: ", self.recording)
            _, frame = self.cap.read()
            cv2.imshow('Gesture Recorder', cv2.flip(frame, 1))
            key = cv2.waitKey(1)

            if key == ord('r'):
                print("Recording will start in 3 seconds...")
                time.sleep(1)
                print("Recording will start in 2 seconds...")
                time.sleep(1)
                print("Recording will start in 1 seconds...")
                time.sleep(1)

                print("Recording...")
                self.recording = True

                # If q is pressed, stop recording and quit
            elif key == ord('q'):
                print("Recording stopped.")
                self.recording = False
                break

            elif key == 27:
                break
            self.frame_queue.put(frame)

        self.cap.release()
        self.video.release()
        cv2.destroyAllWindows()

            # press 'r' to start recording press again to stop


    # def handle_key(self, key: int) -> bool:
    #     if key == ord('r'):
    #         if self.recording:
    #             print('stop recording')
    #             self.stop()
    #             self.recording = False
    #             return False
    #         else:
    #             time.sleep(1)
    #             print("recording starts in 3")
    #             time.sleep(1)
    #             print("recording starts in 2")
    #             time.sleep(1)
    #             print("recording starts in 1")
    #             time.sleep(1)
    #             self.recording = True
    #             return False
    #     elif key == 27:
    #         return True
    def start(self):
        self.video = cv2.VideoWriter(self.save_file, cv2.VideoWriter_fourcc(*'MJPG'), self.fps, self.size)

    def record(self, frame):
        """
        Record a frame.
        :param frame: frame to record
        :return:
        """
        print("here")
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