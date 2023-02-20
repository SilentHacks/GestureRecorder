# create a setup window for pyautogui

import PySimpleGUI as sg
import control_panel as cp
import record_panel as rp
import os.path
import cv2
def file_input_window() -> str:
    file_path = ""
    layout = [[sg.Text("Please Choose a Video File: ", font="Helvetica 14 bold")],
              [sg.Text("File Path", font="Helvetica 14 bold"), sg.InputText(key="-FILE_PATH-", size=(50, 4)),
              sg.FileBrowse(initial_folder=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) +
                                            "/data/videos",
                             file_types=(("Video Files", "*.mov"), ("Video Files", "*.mp4")))],
              [sg.Button("OK", size=(10, 1), font="Helvetica 16 bold"), sg.Exit()]]

    file_window = sg.Window("File Browser", layout, keep_on_top=True)
    while True:
        event, values = file_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "OK":
            file_path = values["-FILE_PATH-"]
            break
    file_window.close()

    return file_path

def naming_window() -> str:
    name = ""
    layout = [[sg.Text("Please Enter a Name for the Gesture / Pose: ", font="Helvetica 14 bold")],
              [sg.Text("Name", font="Helvetica 14 bold"), sg.InputText(key="-NAME-", size=(50, 4))],
              [sg.Button("OK", size=(10, 1), font="Helvetica 16 bold"), sg.Exit()]]
    name_window = sg.Window("Name Input", layout, keep_on_top=True)
    while True:
        event, values = name_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "OK":
            name = values["-NAME-"]
            break
    name_window.close()
    return name

def run():
    controlPanel = cp.ControlPanel(record_live=True, hand_pose=True, sensitivity=5, upper_body=True)
    window = controlPanel.get_control_panel()

    # get secren size and set window size
    # screen = screeninfo.get_monitors()[0]
    # window.TKroot.geometry(f"{relative_size[0]}x{relative_size[1]}+{screen.width // 2 - relative_size[0] // 2}+{screen.height // 2 - relative_size[1] // 2}")
    while True:
        event, values = window.read()
        if event == "CLOSE" or event == sg.WIN_CLOSED:
            break
        elif event == "Record Live":
            # get the cv window from pose_recorder.py
            print("record live")
        elif event == "Import Video":
            # get the cv window from pose_recorder.py
            print("import video")
        elif event == "anno1":
            sg.popup("User can record a gesture/pose live via webcam, or can import an existing video containing the part of the gesture/pose. \n",
                     font="Helvetica 14", keep_on_top=True)
        elif event == "anno2":
            sg.popup("Hand Poses are stationary, user can choose a static pose and record that pose frame. \n "
                     "Body gestures are full body dynamic gestures, user can do a dynamic gesture within 2 secs to record the whold move. \n",
                     font="Helvetica 14", keep_on_top=True)
        elif event == "SAVE & START":
            # save all options and update the recording window
            print(values)
            if values["-Import_Video-"]:
                file_path = file_input_window()
                if file_path == "":
                    sg.popup("Please choose a video file!", font="Helvetica 14", keep_on_top=True)
                    continue

                values["import_path"] = file_path
                print(values)

            name = naming_window()
            if name == "":
                sg.popup("Please enter a name for the gesture / pose!", font="Helvetica 14", keep_on_top=True)
                continue

            print("here: ", name)
            selected_options: dict = controlPanel.parse_values(values)
            selected_options["name"] = name
            recordPanel = rp.RecordPanel(selected_options)
            recordPanel.initRecorder()

            print("final options are: ", selected_options)

            print("Options saved, start recording!")
    window.close()


if __name__ == '__main__':
    run()
