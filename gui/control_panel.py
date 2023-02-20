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

        self.large_title_font = "ArialBlack 24 bold"
        self.title_font = "ArialBlack 18 bold"
        self.small_title_font = "ArialBlack 16"
        self.window_size = (400, 510)

        sg.LOOK_AND_FEEL_TABLE['MyNewTheme'] = {'BACKGROUND': '#FFFFFF',
                                                'TEXT': '#fff4c9',
                                                'INPUT': '#c7e78b',
                                                'TEXT_INPUT': '#000000',
                                                'SCROLL': '#c7e78b',
                                                'BUTTON': ('white', '#709053'),
                                                'PROGRESS': ('#01826B', '#D0D0D0'),
                                                'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0,
                                                }

        # sg.theme('MyNewTheme')

        sg.SetOptions(
            button_color=sg.COLOR_SYSTEM_DEFAULT
            # , text_color=sg.COLOR_SYSTEM_DEFAULT
            , border_width=0
            , auto_size_text=True
        )

        self.layout = [[sg.Button("CLOSE", size=(6, 1), button_color="white on #7B7B7B", font="Impact 18 bold"),
                        sg.Text("Notice, Dynamic gestures cannot be \n longer than 2 seconds (60 frames)!",
                                font=("Helvetica", 16), text_color="#FF7878")],
                       [sg.HSeparator(pad=(0, 10))],
                       [sg.Text("Select a Record Method", font=self.large_title_font)],
                       [sg.Radio("Record Live", "RADIO0", size=(12, 1), font=self.small_title_font, default=record_live,
                                 key="-Record_Live-"),
                        sg.Radio("Import Video", "RADIO0", size=(20, 1), font=self.small_title_font,
                                 default=abs(record_live - 1), key="-Import_Video-"),
                        sg.Button("?", font=self.small_title_font, key="anno1")],
                       [sg.HSeparator(pad=(0, 10))],
                       [sg.Text("Options", font=self.large_title_font)],
                       [sg.Text("Gesture Type", font=self.title_font)],
                       [sg.Radio("Hand Poses", "RADIO1", size=(12, 1), font=self.small_title_font, default=hand_pose,
                                 key="-Hand_Pose-"),
                        sg.Radio("Body Gestures", "RADIO1", size=(20, 1), font=self.small_title_font, default=abs(hand_pose - 1),
                                 key="-Body_Gesture-"),
                        sg.Button("?", font=self.small_title_font, key="anno2")],
                       [sg.Text("Detection Sensitivity", font=self.title_font, justification="center")],
                       [sg.Slider(range=(0, 10), default_value=sensitivity, orientation="h", size=(34, 20),
                                  key='-SENSITIVITY-', font=self.small_title_font)],
                       [sg.Text("Body Focus Part", font=self.title_font)],
                       [sg.Radio("Upper Body", "RADIO2", font=self.small_title_font, default=upper_body,
                                 key="-UpBody-"),
                        sg.Radio("Lower Body", "RADIO2", font=self.small_title_font, default=abs(upper_body - 1),
                                 key="-LowBody-")],
                       [sg.HSeparator(pad=(0, 20))],
                       [sg.Text("", size=(8, 1)), sg.Button("SAVE & START", size=(15, 1), button_color="white on #F32C2C", font=self.large_title_font)]]

        self.window = sg.Window("Control Panel", self.layout, size=self.window_size, finalize=True, alpha_channel=0.9)
        # new tabs for more options can be added here

    def get_control_panel(self):
        return self.window


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
