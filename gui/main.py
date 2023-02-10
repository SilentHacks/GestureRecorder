# create a setup window for pyautogui

import PySimpleGUI as psg
import screeninfo
import cv2

def windowSetup():
    # let window get webcam input
    psg.SetOptions(
        button_color=psg.COLOR_SYSTEM_DEFAULT
        , text_color=psg.COLOR_SYSTEM_DEFAULT
    )
    layout = [
        [psg.Text("Hello World")],
        [psg.Button("Ok")],
        [psg.Button("Cancel")],
        [psg.Image(filename="check.png", key="image")]]
    return psg.Window("Setup", layout, resizable=True, finalize=True)

def run():
    relative_size = (1080, 720)
    window = windowSetup()
    # get secren size and set window size
    screen = screeninfo.get_monitors()[0]
    window.TKroot.geometry(f"{relative_size[0]}x{relative_size[1]}+{screen.width // 2 - relative_size[0] // 2}+{screen.height // 2 - relative_size[1] // 2}")
    while True:
        event, values = window.read()
        if event == "Ok" or event == psg.WIN_CLOSED:
            break
    window.close()


if __name__ == '__main__':
    run()
