# from moviepy.video.io.VideoFileClip import VideoFileClip
# from moviepy.video.fx.mirror_x import mirror_x
import imageio
import os
import cv2


class ThumbNailUtils:

    # @staticmethod
    # def gifVideoCvt(videoFilePath: str, gestureName: str = None, save_dir: str = None):
    #     clip = VideoFileClip(videoFilePath)
    #     dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))
    #     # fileName = videoFilePath.split("/")[-1][:-4]
    #     reversed_clip = clip.fx(mirror_x)
    #     reversed_clip.write_gif(fps=8, filename=f'{dataPath}/{"thumbnails/gestureGifs"}/' + gestureName + ".gif")

    @staticmethod
    def frameImgCvt(name=None, frame=None, save_dir=None):
        # dataPath is the second super directroy as save_dir

        dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))
        print("img cvt path: ", dataPath)
        cv2.imwrite(f'{dataPath}/{"thumbnails/posePics"}/{name}.png', cv2.flip(frame, 1))

    @staticmethod
    def gifVideoCvt2(videoFilePath=None, gestureName=None, save_dir=None):

        print("video file path: ", videoFilePath)
        cap = cv2.VideoCapture(videoFilePath)
        image_lst = []
        dataPath = os.path.abspath(os.path.join(os.path.join(save_dir, os.pardir), os.pardir))


        while cap.isOpened():
            ret, frame = cap.read()
            # cv2.imshow('a', frame)
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_lst.append(cv2.flip(frame_rgb, 1))



        cap.release()
        cv2.destroyAllWindows()

        # Convert to gif using the imageio.mimsave method
        imageio.mimsave(f'{dataPath}/{"thumbnails/gestureGifs"}/' + gestureName + ".gif", image_lst, fps=8)
