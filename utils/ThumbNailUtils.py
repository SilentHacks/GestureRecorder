from moviepy.editor import VideoFileClip, vfx
import os
import cv2

class ThumbNailUtils:

    def gifVideoCvt(videoFilePath: str, gestureName: str = None, save_dir: str = None):
        clip = VideoFileClip(videoFilePath)
        dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))
        # fileName = videoFilePath.split("/")[-1][:-4]
        reversed_clip = clip.fx(vfx.mirror_x)
        reversed_clip.write_gif(fps=8, filename=f'{dataPath}/{"thumbnails/gestureGifs"}/' + gestureName + ".gif")

    def frameImgCvt(name=None, frame=None, save_dir=None):
        # dataPath is the second super directroy as save_dir

        dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))
        print("img cvt path: ", dataPath)
        cv2.imwrite(f'{dataPath}/{"thumbnails/posePics"}/{name}.png', cv2.flip(frame, 1))
