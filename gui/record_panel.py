""" the class for recording panel, including importing video and recording live """
import gesture_recorder as gr
import pose_recorder as pr

class RecordPanel:
    def __init__(self, selected_options: dict):
        self.record_mode = selected_options.get("record_mode")  # hand or body
        self.import_path = selected_options.get("import_mode")  # file path or none
        self.sensitivity = selected_options.get("sensitivity")  # 1-10
        self.focus_part = selected_options.get("focus_part")  # upper or lower
        self.recorder = None

    def parseSensivitity(self):
        # TODO parse the sensitivity to a range of values that can be shared with the recorder
        pass
    def parseFocusPart(self):
        # TODO parse the focus part to certain value that can be shared with the recorder
        pass
    def initRecorder(self):
        if self.record_mode == "hand":
            if self.import_path is not None:
                self.recorder = pr.PoseRecorder(camera=self.import_path)
            else:
                self.recorder = pr.PoseRecorder(camera=0)
            self.recorder = pr.PoseRecorder()
        elif self.record_mode == "body":
            self.recorder = gr.GestureRecorder()

    # import mode being set as camera num or file path
    def setImportMode(self, recorder):
        pass


    def save(self):
        pass

    def close(self):
        pass