# Gesture Recorder

Though technically it would be more accurate to call it a pose recorder,
this is a tool to allow users to record hand poses and detect them using Mediapipe.

Functionality could actually be extended to allow for gesture recording and detection 
using a similar approach.

## Installation

### Prerequisites

- Python 3.9
- A webcam

### Setup

1. Clone the repository
2. Install the requirements using `pip install -r requirements.txt`
3. Run the program using `python recorder.py`

## Usage

1. Run the program
2. Press `S` to save a pose
3. Press `D` to delete the last pose
4. Press `1`-`3` to switch between the 3 detection strategies
5. Press `ESC` to exit the program

## TODO

- [ ] Add a GUI
- [ ] Add a way to save/load the poses to/from a file
- [ ] Change the detection to be able to handle multiple poses
- [ ] ~~Add a way to calibrate the detection per pose / user's hand size~~
- [ ] ~~Look into KNIFT/SIFT for pose detection / on-device training?~~