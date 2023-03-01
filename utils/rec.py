import cv2
import time
import threading
import queue

# Create a VideoCapture object
cap = cv2.VideoCapture(0)

# Check if camera opened successfully
if (cap.isOpened() == False):
    print("Unable to read camera feed")

# Default resolutions of the frame are obtained.The default resolutions are system dependent.
# We convert the resolutions from float to integer.
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

# Define the codec for output video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

# Create a VideoWriter object.The output is stored in 'output.mp4' file.
out = cv2.VideoWriter('output.mp4', fourcc, 17.0, (960, 540))

# Initialize a flag for recording status
recording = False

# Initialize a queue for storing frames
frame_queue = queue.Queue()


# Define a function for recording video in a separate thread
def record_video():
    global recording  # Use global variable for recording status
    while True:
        # Get a frame from the queue if available
        if not frame_queue.empty():
            frame = frame_queue.get()
            # Write the frame into the file 'output.mp4'
            if recording:
                out.write(frame)


# Create a thread for recording video and start it
record_thread = threading.Thread(target=record_video)
record_thread.start()

while (True):
    ret, frame = cap.read()

    if ret == True:

        # Display the resulting frame
        cv2.imshow('frame', frame)

        # Wait for user input
        key = cv2.waitKey(1) & 0xFF

        # If r is pressed, start recording after 3 seconds countdown
        if key == ord('r'):
            print("Recording will start in 3 seconds...")
            time.sleep(3)
            print("Recording...")
            recording = True

        # If q is pressed, stop recording and quit
        elif key == ord('q'):
            print("Recording stopped.")
            recording = False
            break
        elif exit(0):
            print("Recording stopped.")
            recording = False
            break

        # Put the frame into the queue for recording thread to consume
        frame_queue.put(frame)

    # Break the loop
    else:
        break

    # When everything done, release the video capture and video write objects
cap.release()
out.release()

# Closes all the frames
cv2.destroyAllWindows()