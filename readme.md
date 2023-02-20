# Gesture Recorder

~~Though technically it would be more accurate to call it a pose recorder,
this is a tool to allow users to record hand poses and detect them using Mediapipe.~~

~~Functionality could actually be extended to allow for gesture recording and detection 
using a similar approach.~~

Ignore that, we got both now 😎

This is a tool that allows you to record custom hand poses and gestures and detect them using Mediapipe.

Hand poses are static images of your hand. Once saved, this shape can then be detected in any rotation and even on any hand.
Data is normalised, meaning that the pose can be detected on people of different hand sizes.

Gestures are dynamic full body movements. Some complicated algorithms track coordinates over time to detect gestures.


## Installation

### Prerequisites

- Python 3.9
- A webcam

### Setup

1. Clone the repository
2. Install the requirements using `pip install -r requirements.txt`
3. Run the program using `python pose_recorder.py`

## Usage

1. Run the pose recorder program
2. Press `S` to save a pose
3. Press `D` to delete all the poses
4. Press `ESC` to exit the program

## TODO

- [ ] Add a GUI
- [x] Add a way to save/load the poses to/from a file
- [x] Change the detection to be able to handle multiple poses
- [ ] ~~Add a way to calibrate the detection per pose / user's hand size~~
- [ ] ~~Look into KNIFT/SIFT for pose detection / on-device training?~~