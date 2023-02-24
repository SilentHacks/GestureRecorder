# create a setup window for pyautogui

import PySimpleGUI as sg
# import screeninfo
import os.path
import pose_recorder as pr
import cv2


def windowSetup():
    # let window get webcam input
    sg.theme("DarkGrey9")

    sg.SetOptions(
        button_color=sg.COLOR_SYSTEM_DEFAULT
        , text_color=sg.COLOR_SYSTEM_DEFAULT
    )

    # red color RGB

    display_column = [[sg.Button("CLOSE", size=(10, 1), font="Helvetica 16 bold"), sg.Text("Notice, Dynamic gestures cannot be \n longer than 2 seconds (60 frames)!", font=("Helvetica", 16))],
                      [sg.Button("Record Live", size=(12, 1), font="Helvetica 16 bold"), sg.Button("Import Video", size=(12, 1), font="Helvetica 16 bold")],
                      [sg.Image(filename='', key='cam')]]

    control_column = [[sg.Text("Options", font=("Helvetica", 20, "bold"))],
                      [sg.Text("Gesture Type", font=("Helvetica", 16, "bold"))],
                      [sg.Radio("Static", "RADIO1", default=True, key="-STATIC-"), sg.Radio("Dynamic", "RADIO1", key="-DYNAMIC-")],
                      [sg.Text("Enable Hand Detection", font=("Helvetica", 16, "bold")), sg.Checkbox("", default=True, key="-Detect_Hand-")],
                      [sg.Text("Detection Sensitivity", font=("Helvetica", 16, "bold"))],
                      [sg.Slider(range=(1, 3), default_value=2, orientation="h", size=(34, 20), key='-SENSITIVITY-')],
                      [sg.Text("Body Focus Part", font=("Helvetica", 16, "bold"))],
                      [sg.Radio("Upper Body", "RADIO2", default=True, key="-HighBody-"), sg.Radio("Lower Body", "RADIO2", key="-LowBody-")],
                      [sg.Button("SAVE", size=(10, 1), font="Helvetica 16 bold")],
                      [sg.Button("RECORD", button_color="red", size=(10, 1), font="Helvetica 16 bold")]]
    # make
    layout = [[sg.Column(display_column), sg.VSeperator(), sg.Column(control_column)]]
    return sg.Window("Gesture Recording Panel", layout, resizable=False, finalize=True)

def run():
    relative_size = (1080, 720)
    video_frame_size = (720, 480)
    window = windowSetup()

    # get secren size and set window size
    # screen = screeninfo.get_monitors()[0]
    # window.TKroot.geometry(f"{relative_size[0]}x{relative_size[1]}+{screen.width // 2 - relative_size[0] // 2}+{screen.height // 2 - relative_size[1] // 2}")

    # get the path of super directory
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cap = cv2.VideoCapture(path + "/data/videos/relax/1.mov")
    record_live = False
    outer_record = False
    recorder = pr.PoseRecorder()

    while True:
        event, values = window.read(timeout=20)

        if event == "CLOSE" or event == sg.WIN_CLOSED:
            break
        elif event == "Record Live":
            record_live = True
            # get the cv window from pose_recorder.py
            print("record live")
        elif event == "Import Video":
            outer_record = True
            # get the cv window from pose_recorder.py
            print("import video")

        elif event == "SAVE":
            # save all options and update the recording window
            print("save")
        elif event == "RECORD":
            # start "detecting" according to the modes
            print("record")
        if record_live:
            ret, frameOrig = cap.read()
            # print(ret, frameOrig)
            # print out the fps
            print(cap.get(cv2.CAP_PROP_FPS))
            frame = cv2.resize(frameOrig, video_frame_size)
            # convert the frame color and update the window
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # print(type(frame))
            cv2.imshow("frame", frame)
            # img = Image.fromarray(frame)
            # bio = io.BytesIO()
            # img.save(bio, format= 'PNG')
            # imgbytes = bio.getvalue()
            # window['cam'].update(data=imgbytes)
        if outer_record:
            recorder.record()


    window.close()


if __name__ == '__main__':
    run()

