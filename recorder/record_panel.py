""" the class for recording panel, including importing video and recording live """

import utils.ThumbNailUtils as tn
import gesture_recorder as gr
import pose_recorder as pr
from utils import VideoRecorder as vr
import os

class RecordPanel:
    def __init__(self, selected_options: dict):
        self.record_mode = selected_options.get("record_mode")  # hand or body
        self.import_path = selected_options.get("import_path")  # file path of the imported video
        self.camera_num = selected_options.get("camera_num")  # camera number
        self.sensitivity = selected_options.get("sensitivity")  # 1-10
        self.save_file_path = selected_options.get("save_file_path")  # save file path
        self.name = selected_options.get("name")  # name of the gesture / pose
        self.is_recordLive = selected_options.get("is_recordLive")  # if record live
        self.recorder = None

    def initRecorder(self):
        if self.is_recordLive:
            capSource = self.camera_num
            if self.record_mode == "pose":
                self.recorder = pr.PoseRecorder(camera=capSource, pose_leniency=self.sensitivity / 10, save_dir=self.save_file_path)
                self.recorder.record(name=self.name)
                self.recorder.close()
                print("record live pose")
            else: # gesture
                print("record live gesture")
                self.gestureVideoRecord()

                tempDir = os.path.join(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), "data")), "videos")
                capSource = os.path.join(tempDir, f'{self.name}.avi')
                gr.main(name=self.name, videoFileName=capSource, save_file_name=self.save_file_path)
                tn.ThumbNailUtils.gifVideoCvt2(videoFilePath=capSource, gestureName=self.name,
                                              save_dir=self.save_file_path)
        else: # import video
            capSource = self.import_path
            if self.record_mode == "pose":
                self.recorder = pr.PoseRecorder(camera=capSource, pose_leniency=self.sensitivity / 10, save_dir=self.save_file_path)
                self.recorder.record(name=self.name)
                self.recorder.close()
                print("import video pose")
            else: # gesture
                print("video file is: ", capSource)
                gr.main(name=self.name, videoFileName=capSource, save_file_name=self.save_file_path)
                tn.ThumbNailUtils.gifVideoCvt2(videoFilePath=self.import_path, gestureName=self.name, save_dir=self.save_file_path)
                print("import video gesture")

        print("recorded")

    def gestureVideoRecord(self):
        videoRecorder = vr.VideoRecorder(name=self.name, camera=self.camera_num)
        videoRecorder.run()
        pass


