# CGReplay

## Requirements
* Python 3.10+
* pip
* ffmpeg
* tshark



## Abstract
Cloud Gaming (CG) research faces challenges due to the unpredictability of game engines and restricted access to commercial platforms and their logs.

This creates major obstacles to conducting fair experimentation and evaluation.

_CGReplay_ captures and replays player commands and the corresponding video frames in an ordered and synchronized action-reaction loop, ensuring reproducibility and fairness.

It enables Quality of Experience/Service (QoE/QoS) assessment under varying network conditions and serves as a foundation for broader CG research.

## Introduction
CGReplay is divided into two main phases. First, it is necessary to capture the user's frames. Then, the platform comes into play, synchronizing the received commands (server-side) and the frames (user-side).

## Setup

Here’s a step-by-step guide to setting up a Python virtual environment (venv) for Python 3.10 or later:

### **Step 0: Joystick Configuration**

Make sure you have a joystick that can be connected via USB. Otherwise, you will only be able to collect frames without the commands (buttons, axes).

#### If you have a joystick:
```bash
sudo apt install joystick
```

#### If you don't have a joystick:
Go to the file `capturing/capturing/run_capturing.py` and comment out all the lines related to `process1` - i.e., the process created to monitor the joystick commands. - in blocks `try` and `finally`. 



### **Step 1: Ensure Python 3.10+ is Installed**

Run the following command to check if Python 3.10+ is installed:

```bash
python3 --version
```
or
```bash
python --version
```

If you don’t have Python 3.10+, download and install it from the official website:
[https://www.python.org/downloads/](https://www.python.org/downloads/)



### **Step 2: Create a Virtual Environment at /home/\<username\>**
Run the following command to create a virtual environment named `venv`:

```bash
cd
```

```bash
python3 -m venv venv
```
or

```bash
cd
```

```bash
python -m venv venv
```

This will create a folder named `venv` in your _/home/\<username\>_ containing the necessary files for the virtual environment.

### **Step 3: Activate the Virtual Environment**
#### **On macOS/Linux:**
```bash
source venv/bin/activate
```

Once activated, you should see `(venv)` in your terminal prompt, indicating that the virtual environment is active.

### **Step 4: Navigate to Your Project Directory**
Open a terminal and navigate to the directory where you want to create your virtual environment:

```bash
cd /path/to/the/folder/you/cloned/CGReplay
```


### (Optional) **Step 5: Upgrade `pip`**
After activating the virtual environment, upgrade `pip` to the latest version:

```bash
pip install --upgrade pip
```

### **Step 6: Install Dependencies**
Now you can install your project's dependencies using `pip`.

If you have a `requirements.txt` file, install all dependencies with:

```bash
pip install -r requirements.txt
```


### **Step 7: Generate a recording**
We need to generate a video file (e.g., mp4) before replaying it (of course).

To do that, go to `CGReplay/capturing/capturing` and run `run_capturing.py

```python
python3 run_capturing.py
```

This command will run for 5 min (300 seg) to generate a file named `capture.mp4`. 

> NOTE: We can interrupt the screen recording anytime. The faster you do it, the less frames are capture.

### **Step 8: Genenerate frames/commands**
After generating the `capture.mp4` file, we need to generate the frames (png images, in this case).

```bash
ffmpeg -i ./capture.mp4 -vf "fps=10" ./captured_frames/frm_%04d.png
```

The command above creates a number of images corresponding to a 10 FPS video. You can increase the `fps` variable, but this will increasing the number of images considerably.

The generated frames are stored in `CGReplay/capturing/capturing/captured_frames` folder.


### **Step 9: Sync frames/commands

At this point, we already have the frames and commands logs. However, we still need to sync them:

Go to `CGReplay/capturing/synching` and run:
```python
python3 sync.py
```


After the syncronization is done, we can see the ordered frames in `CGReplay/capturing/synching/output/frames`, the log of how this ordering happened on `CGReplay/capturing/synching/output/frames_log.txt` and `CGReplay/capturing/synching/output/mix.txt`
## Replay
TODO...



