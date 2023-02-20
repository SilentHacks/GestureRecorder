""" the class for recording panel, including importing video and recording live """

import utils.ThumbNailUtils as tn
import gesture_recorder as gr
import pose_recorder as pr

class RecordPanel:
    def __init__(self, selected_options: dict):
        self.record_mode = selected_options.get("record_mode")  # hand or body
        self.import_path = selected_options.get("import_path")  # file path or none
        self.sensitivity = selected_options.get("sensitivity")  # 1-10
        self.focus_part = selected_options.get("focus_part")  # upper or lower
        self.name = selected_options.get("name")  # name of the gesture / pose
        self.recorder = None

    def parseFocusPart(self):
        # TODO parse the focus part to certain value that can be shared with the recorder
        pass

    def initRecorder(self):
        if self.import_path is not None:
            camera = self.import_path
        else:
            camera = 0  # default camera is 0

        if self.record_mode == "hand":
            self.recorder = pr.PoseRecorder(camera, pose_leniency=self.sensitivity / 10) # default camera is 0
        else:
            if camera == 0:
                self.gestureVideoRecord()
            else:
                self.recorder = gr.GestureRecorder(camera)
                # tn.ThumbNailUtils.gifVideoCvt(videoFilePath=self.import_path, gestureName=self.name)


        self.recorder.record(name=self.name)
        self.recorder.close()
        print("recorded")

    def gestureVideoRecord(self):
        pass


