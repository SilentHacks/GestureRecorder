from moviepy.editor import VideoFileClip
import os
import cv2

class ThumbNailUtils:

    def gifVideoCvt(videoFilePath: str):
        clip = VideoFileClip(videoFilePath)
        dataPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gui/assets/thumbnails/gestureGifs/")
        fileName = videoFilePath.split("/")[-1][:-4]
        # print("fileName: ", fileName)
        clip.write_gif(fps=8, filename=dataPath + fileName + ".gif")

    def frameImgCvt(name=None, frame=None):
        dataPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gui/assets/thumbnails/posePics/")
        cv2.imwrite(f'{dataPath}{name}.png', cv2.flip(frame, 1))
