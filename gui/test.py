import PySimpleGUI as sg
sg.SetOptions(
                 button_color = sg.COLOR_SYSTEM_DEFAULT
               , text_color = sg.COLOR_SYSTEM_DEFAULT
             )
layout = [ [sg.Submit('Submit')] ]
window = sg.Window('Test window').Layout(layout)
event = window.Read()