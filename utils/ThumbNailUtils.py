from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.mirror_x import mirror_x
import os
import cv2


class ThumbNailUtils:

    @staticmethod
    def gifVideoCvt(videoFilePath: str, gestureName: str = None, save_dir: str = None):
        clip = VideoFileClip(videoFilePath)
        dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))
        # fileName = videoFilePath.split("/")[-1][:-4]
        reversed_clip = clip.fx(mirror_x)
        reversed_clip.write_gif(fps=8, filename=f'{dataPath}/{"thumbnails/gestureGifs"}/' + gestureName + ".gif")

    @staticmethod
    def frameImgCvt(name=None, frame=None, save_dir=None):
        # dataPath is the second super directroy as save_dir

        dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))
        print("img cvt path: ", dataPath)
        cv2.imwrite(f'{dataPath}/{"thumbnails/posePics"}/{name}.png', cv2.flip(frame, 1))
