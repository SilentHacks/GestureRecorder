""" the class for the control panel of the gui, which contains the buttons and sliders
 when class being called it will be shown as a group of GUIs on the left with initialized values
 it returns a list of values that can be used to control the main GUI
 """
import PySimpleGUI as sg
import math


class ControlPanel:
    def __init__(self,
                 record_live: bool = True,
                 hand_pose: bool = True,
                 sensitivity: int = 5,
                 upper_body: bool = True):

        self.large_title_font = "Helvetica 20 bold"
        self.title_font = "Helvetica 18 bold"
        self.small_title_font = "Helvetica 16"
        self.window_size = (400, 550)

        self.layout = [[sg.Button("CLOSE", size=(10, 1), font="Helvetica 16 bold"),
                        sg.Text("Notice, Dynamic gestures cannot be \n longer than 2 seconds (60 frames)!",
                                font=("Helvetica", 16))],
                       [sg.Text("Select a Record Method", font=self.large_title_font)],
                       [sg.Radio("Record Live", "RADIO0", size=(12, 1), font=self.small_title_font, default=record_live,
                                 key="-Record_Live-"),
                        sg.Radio("Import Video", "RADIO0", size=(12, 1), font=self.small_title_font,
                                 default=abs(record_live - 1), key="-Import_Video-"),
                        sg.Button("?", font=self.small_title_font, key="anno1")],
                       [sg.Text("Options", font=self.large_title_font)],
                       [sg.Text("Gesture Type", font=self.title_font)],
                       [sg.Radio("Hand Poses", "RADIO1", font=self.small_title_font, default=hand_pose,
                                 key="-Hand_Pose-"),
                        sg.Radio("Body Gestures", "RADIO1", font=self.small_title_font, default=abs(hand_pose - 1),
                                 key="-Body_Gesture-"),
                        sg.Button("?", font=self.small_title_font, key="anno2")],
                       [sg.Text("Detection Sensitivity", font=self.title_font)],
                       [sg.Slider(range=(0, 10), default_value=sensitivity, orientation="h", size=(34, 20),
                                  key='-SENSITIVITY-')],
                       [sg.Text("Body Focus Part", font=self.title_font)],
                       [sg.Radio("Upper Body", "RADIO2", font=self.small_title_font, default=upper_body,
                                 key="-UpBody-"),
                        sg.Radio("Lower Body", "RADIO2", font=self.small_title_font, default=abs(upper_body - 1),
                                 key="-LowBody-")],
                       [sg.Button("SAVE & START", size=(15, 1),button_color="red", font=self.large_title_font)]]
        # new tabs for more options can be added here

    def get_control_panel(self):
        sg.theme("DarkGrey8")
        sg.SetOptions(
            button_color=sg.COLOR_SYSTEM_DEFAULT
            , text_color=sg.COLOR_SYSTEM_DEFAULT
        )

        return sg.Window("Gesture Recording Panel", self.layout, size=self.window_size,
                         resizable=False, finalize=True)

    def parse_values(self, values: dict):
        selected_options: dict = {}
        if values["-Record_Live-"]:
            selected_options["import_path"] = None
        else:
            selected_options["import_path"] = values["import_path"]

        if values["-Hand_Pose-"]:
            selected_options["record_mode"] = "hand"
        else:
            selected_options["record_mode"] = "body"

        if values["-UpBody-"]:
            selected_options["body_focus"] = "upper"
        else:
            selected_options["body_focus"] = "lower"

        selected_options["sensitivity"] = values["-SENSITIVITY-"]

        return selected_options
