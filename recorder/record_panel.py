""" the class for recording panel, including importing video and recording live """

import utils.ThumbNailUtils as tn
import gesture_recorder as gr
import pose_recorder as pr

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
                # self.recorder = pr.PoseRecorder(capSource, pose_leniency=self.sensitivity / 10)
                print("record live pose")
            else: # gesture
                self.gestureVideoRecord()
                print("record live gesture")
        else: # import video
            capSource = self.import_path
            if self.record_mode == "pose":
                self.recorder = pr.PoseRecorder(capSource, pose_leniency=self.sensitivity / 10)
                print("import video pose")
            else: # gesture
                self.recorder = gr.GestureRecorder(capSource)  # capSource is video file path
                # tn.ThumbNailUtils.gifVideoCvt(videoFilePath=self.import_path, gestureName=self.name)
                print("import video gesture")

        # add import of output file path for record() function
        # self.recorder.record(name=self.name)
        # self.recorder.close()
        print("recorded")

    def gestureVideoRecord(self):
        pass


