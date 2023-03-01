import os
import json
from recorder import record_panel as cp

class Main:
    def __init__(self):
        self.name: str = None
        self.dataFilePath: str = None
        self.camera_num: int = None
        self.sensitivity: int = None
        self.videoFilePath: str = None
        self.is_gesture: bool = None
        self.is_recordLive: bool = None


    def loadConfig(self):
        configPath = "data/backEndConfig.json"
        with open(configPath, "r") as f:
            data = json.load(f)
            self.name = data["name"]
            self.dataFilePath = "data/models" # the file could include just data/models or data/models/gesture/someGesture.json or data/models/pose/somePose.json
            # if no json is finded then it is a new gesture or pose, if json is finded then it is a gesture or pose that needs calibration
            self.camera_num = data["cameraNum"]
            self.sensitivity = data["sensitivity"]
            self.videoFilePath = data["videoFilePath"]
            self.is_gesture = data["is_gesture"]
            self.is_recordLive = data["is_recordLive"]

            print("raw data: ", data)
            self.execute()
    # load dataFile and determine whether having a new gesture

    def execute(self):
        selected_options: dict = {}

        selected_options["name"] = self.name
        selected_options["sensitivity"] = self.sensitivity

        # check if dataFilePath is existing
        if os.path.exists(self.dataFilePath):
            # check if new gesture or existing
            if os.path.isfile(self.dataFilePath) and os.path.basename(self.dataFilePath).endswith(".json"):
                # if it is a file then it is a gesture or pose that needs calibration
                # check if the name of super directory is gesture or pose
                selected_options["save_file_path"] = os.path.abspath(os.path.join(self.dataFilePath, os.pardir))

                if os.path.basename(os.path.dirname(self.dataFilePath)) == "gestures":
                    print("calibrate gesture")
                    selected_options["record_mode"] = "gesture"
                else:
                    print("calibrate pose")
                    selected_options["record_mode"] = "pose"

            elif os.path.basename(self.dataFilePath) == "models": # should be data/model/...
                # if it is a directory then it is a new gesture or pose
                # check if the name of super directory is gesture or pose
                if self.is_gesture:
                    print("new gesture")
                    # find the gestures directory
                    selected_options["save_file_path"] = os.path.join(self.dataFilePath, "gestures")
                    selected_options["record_mode"] = "gesture"
                    print(selected_options["save_file_path"])

                else:
                    print("new pose")
                    selected_options["save_file_path"] = os.path.join(self.dataFilePath, "poses")
                    selected_options["record_mode"] = "pose"
                    print(selected_options["save_file_path"])
            else:
                raise Exception("dataFilePath is not valid")


        else:
            raise Exception("dataFilePath is not existing")

        if self.is_recordLive:
            selected_options["camera_num"] = self.camera_num
            selected_options["import_path"] = None
            selected_options["is_recordLive"] = True
        else:
            selected_options["camera_num"] = None
            selected_options["import_path"] = self.videoFilePath
            selected_options["is_recordLive"] = False

        print("final selected_options: ", selected_options)
        record_panel = cp.RecordPanel(selected_options)
        record_panel.initRecorder()


    def newGesture(self):
        # record gesture
        pass

    def calibrateGesture(self):
        # calibrate gesture
        pass


if __name__ == "__main__":
    main = Main()
    main.loadConfig()
