import cv2

input_video_path = '/Users/zhangweiyi/Documents/GitHub/GestureRecorder/data/videos/testNewGifCvt.avi'

cap = cv2.VideoCapture(input_video_path)

while(cap.isOpened()):
    ret, frame = cap.read()
    print(frame, ret)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if ret:
        cv2.imshow("frame", frame_rgb)
        cv2.waitKey(1)
    else:
        break

cap.release()
cv2.destroyAllWindows()