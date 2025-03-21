# CGReplay
Cloud Gaming (CG) research faces challenges due to the unpredictability of game engines and restricted access to commercial platforms and their logs.

This creates major obstacles to conducting fair experimentation and evaluation.

_CGReplay_ captures and replays gamer commands and the corresponding video frames in an ordered and synchronized action-reaction loop, ensuring reproducibility and fairness.

It enables Quality of Experience/Service (QoE/QoS) assessment under varying network conditions and serves as a foundation for broader CG research.

![image](https://github.com/user-attachments/assets/6efcadd2-4e63-497a-a5f3-03ae0cca1ad9)


___

### Requirements
* [Python 3.10 or higher](https://www.python.org/downloads/)
* [GStreamer](https://gstreamer.freedesktop.org/download/#linux)
* pip (22.0.2 or higher)
* ffmpeg 4.4.2 or higher (sudo apt install ffmpeg)
* tshark (3.6.2 or higher)


### Repository Structure

```
├── capturing
│   ├── capturing
│   │   ├── config.yaml
│   │   ├── joystick_log.txt
│   │   ├── modules
│   │   │   ├── capture_joystick.py
│   │   │   └── capture_screen.py
│   │   └── run_capturing.py
│   ├── install.txt
│   └── synching
│       ├── config.yaml
│       ├── frame_log.txt
│       ├── frames
│       ├── mix.txt
│       ├── modules
│       │   ├── mixing.py
│       │   ├── ordering.py
│       │   └── read_frames.py
│       ├── sync.py
│       └── sync.txt
├── config
│   └── config.yaml
├── gamer
│   ├── cg_gamer1.py
│   ├── logs
│   │   └── received_frames
│   ├── run_multi_cg_gamer.py
│   └── syncs
│       ├── sync_fortnite.txt
│       ├── sync_forza.txt
│       └── sync_kombat.txt
├── port_clean.sh
├── README.md
├── requirements.txt
├── run_CG_mininet.py
└── server
    ├── cg_server1.py
    ├── command.txt
    ├── logs
    │   ├── srv_frame.txt
    │   ├── srv_ratectl.txt
    │   └── srv_total.txt
    ├── my_scream_send_log_0.csv
    ├── srv_frame.txt
    ├── srv_ratectl.txt
    ├── srv_total.txt
    └── syncs
        ├── sync_fortnite.txt
        ├── sync_forza.txt
        └── sync_kombat.txt
```

___

## Setup

### Introduction
CGReplay records the behavior of gamer and CG server in each cloud gaming (CG) platform and replay the CG and gamer behavior to generate the traffic; so it has two general phases: *(a) Capturing* and *(b) Replaying*. 

**(a) Capturing**: Capture and record system commands along with video frames, ensuring proper synchronization between the sequence of commands and the corresponding video frames.

**(b) Replaying**: Replay the captured video frames from the CG server while simultaneously executing the corresponding commands from the gamer in the correct order.

Here’s a step-by-step guide to setting up a Python virtual environment (venv) for Python 3.10 or later:

### **Step 1: Joystick Configuration**

Make sure you have a joystick that can be connected via USB. Otherwise, you will only be able to collect frames without the commands (buttons, axes).

#### If you have a joystick:
```bash
sudo apt install joystick
```

#### If you don't have a joystick:
Go to the file `capturing/capturing/config.yaml` and `set  enable_joystick: False` to disable the Joystick capturing. 



### **Step 2: Ensure Python 3.10+ is Installed**

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


### **Step 3: Create a Virtual Environment at /home/\<username\>**
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

### **Step 4: Activate the Virtual Environment**
#### **On macOS/Linux:**
```bash
source venv/bin/activate
```

Once activated, you should see `(venv)` in your terminal prompt, indicating that the virtual environment is active.

### **Step 5: Navigate to Your Project Directory**
Open a terminal and navigate to the directory where you want to create your virtual environment:

```bash
cd /path/to/the/folder/you/cloned/CGReplay
```


### (Optional) **Upgrade `pip`**
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

___

## (a) Capture phase


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
sudo ffmpeg -i ./capture.mp4 -vf "fps=10" ./captured_frames/frm_%04d.png
```

The command above creates a number of images corresponding to a 10 FPS video. You can increase the `fps` variable, but this will increasing the number of images considerably.

The generated frames are stored in `CGReplay/capturing/capturing/captured_frames` folder.


### Step 9: Sync frames/commands

At this point, we already have the frames and commands logs. However, we still need to sync them:

Go to `CGReplay/capturing/synching` and run:
```python
sudo python3 sync.py
```


After the syncronization is done, we can see the ordered frames in `CGReplay/capturing/synching/output/frames`, the log of how this ordering happened on `CGReplay/capturing/synching/output/frames_log.txt` and `CGReplay/capturing/synching/output/mix.txt` These logs were generated and used to create the `sync.txt` which will be used for synchronization in both *CG server* and *CG Gamer*!

___

## (b) Replay phase
In this section, we explore how to replay the capture frames and joystick commands.

CGReplay allows to run on real networks. For instance, we could run the experiment on Tofino switches. However, for this tutorial we will install Mininet to allow the user to run everything on a single computer.


### Mininet experiment

### **Step 1: Install Mininet**

Before we start to replay the captured frames, we must make sure Mininet is installed. You can follow the guidelines [here](https://mininet.org/download/). We recommend you install from source (Option 2) or from package (Option 3).

### Step 2: Create a mininet topology
As we are using Mininet, we can create a simple Mininet topology using MiniEdit that should look like this: `H1 <-> S1 <-> H2`, where `H1` is the server, `S1` is the switch in the middle, and `H2` is the client (gamer). To do that, follow the steps below: 


#### A. Open MiniEdit
```bash=
sudo python3 ./mininet/examples/miniedit.py
```

![image](https://github.com/user-attachments/assets/2c97a0fe-0afd-4af2-b552-54fbf265c0e8)



#### B. Create a switch object

Go to the left panel and select the switch object. Then, click anywhere in the MiniEdit workspace (e.g., middle) to create the object (as shown below):

![image](https://github.com/user-attachments/assets/3fea2ccd-5a27-45c4-872c-32a5a3c1fa3d)



#### C. Create the hosts
We want the simplest topology we can get. So, let's create two hosts. Similarly to the previous step, go to the left and select the host icon:

![image](https://github.com/user-attachments/assets/45250afc-dcd9-4040-b0e2-0f8d2502aaf5)



Then, create the objects close to the switch `S1`:

![image](https://github.com/user-attachments/assets/67f0269e-2a01-480d-b3b8-36c1f421d426)


#### D. Connect the hosts and switch
After creating the hosts and the switch, we still need to connect those objects. To do that, select the 'blue line' icon and drag from `H1` to `S1` and from `S1` to `H2`, as the red arrows illustrated below. 
![image](https://github.com/user-attachments/assets/99d01efa-56f6-493b-96e9-dbe8213023d3)




#### E. Rename hosts

This is more optional, but we recommend to rename the hosts and keep the default network Mininet provides.

To do that, right click on `H1` object

![image](https://github.com/user-attachments/assets/e23a7860-1666-42f8-aa20-bd0dff3ed8f5)



Then, at the _Hostname_ field, rename `h1` -> `cgserver` 


![image](https://github.com/user-attachments/assets/d2dff121-6b29-447c-886d-4903c926dcbe)


Finally, repeat the process for `h2` and rename it `h2` -> `cgplayer`


![image](https://github.com/user-attachments/assets/8f76dbc7-91fa-4160-8ca9-9161467d2753)



### Step 3: Run the Mininet topology

After creating the objects on MiniEdit, press run (left bottom), as shown:

![image](https://github.com/user-attachments/assets/652325c5-1912-4700-abe2-9e842635de06)



At this moment, you should see the terminal where we called MiniEdit initializing the Mininet topology:

![image](https://github.com/user-attachments/assets/1d682ba3-23c0-40bf-adc9-ff0b13636c79)



### Step 3: Understanding CGReplay default configuration 

Now, go to [**config.yaml**](https://github.com/dcomp-leris/CGReplay/blob/main/config/config.yaml) (`CGReplay->config->[config.yaml]`), where the main _server_ and _player_ configured is customized.

In `config.yaml` file, we find the default configuration to make CGReplay work:

```bash=
# CGReplay Configuration File
# -------------------------------------------------------------------------#

# CG server configuration
server:
    server_IP: "10.0.0.1"                # Server computer IP address
    server_port: 5000                    # UDP Port for receiving control (Joystick) commands from player
    server_command_port: 5001            # not used yet!
    server_interface: "server-eth0"      # Not Mandatory!
    ##CGServerLog
    log_rate_control: "./logs/srv_ratectl.txt"
    log_server: "./logs/srv_total.txt"
    log_frame: "./logs/srv_frame.txt"
# -------------------------------------------------------------------------#

# CG  player configuration
gamer:
    player_IP: "10.0.0.2"                 # CG Gamer (or player) IP address
    player_streaming_port: 5002           # UDP port for streaming (receiving) the frames of the video games!
    palyer_command_port: 5003             # UDP Port for is binded in the server and used to send the command in the gamer system!
    player_interface:  "player-eth0"      # Gamer interface name!
    ## CG Player Log CGReplay/player/logs (rate/time logs + video frames in png)
    player_rate_log: "./logs/ratelog_CG.txt"
    player_time_log: "./logs/timelog_CG.txt"
    received_frames: "./logs/received_frames"
# -------------------------------------------------------------------------#

# Game Data Setup 
Forza:  # possible values: Fortnite  or  Kombat
    name: "Forza"
    sync_file: "./syncs/sync_forza.txt"
    frames: "./Forza"

Fortnite: 
    name: "Fortnite"
    sync_file: "./syncs/sync_fortnite.txt"
    frames: "./Fortnite"

Kombat: 
    name: "Kombat"
    sync_file: "./syncs/sync_kombat.txt"
    frames: "./Kombat"
# -------------------------------------------------------------------------#

# Encoding setup 
encoding:
    name: "H.264" # Default 
    fps: 30  # Frames per second
    resolution:
        width: 600 # default 1364
        height: 400 # default 768
    starting_bitrate: 5000
    bitrate_min: 4000
    bitrate_max: 10000
# -------------------------------------------------------------------------#
# Synchronization Sliding Window
sync: 
    window_min: 1 
    window_max: 4
    ack_freq: 30 # Send Ack after receiving 30 frames!
    ## Automatically increase and decrease the encoding rate
    ## (in CG server) based on frame quality and retransmission!
    jump: 0.2
    rise: 0.1
    decrese: 0.2
    fall: 0.2

# -------------------------------------------------------------------------#
# CGReplay Running Setup
Running:
    game: "Kombat"     # Set it to start the CGReplay specific Game
    live_watching: True    # If you want to watch live gameplay set 'True'
                           # else set 'False'
    duration: 300   # in seconds
    stop_frm_number: 100

# ------------------------------------------------------------------------#
# ScreAM Setup
protocols:
    SCReAM: False # False = 0 / True = 1
    sender: "../scream/scream/gstscream/scripts/sender.sh"
    receiver: "../scream/scream/gstscream/scripts/receiver.sh"

```


Lines 5-25 cover the CG _server_ and _gamer_ configuration. As we do not change the IPs, we always assume `H1` is named as `cgserver` (10.0.0.1) while `H2` is `cgplayer` (10.0.0.2). With those names, the `eth0` interface of the components will be named as `cgserver-eth0` and `cgplayer-eth0`, respectively. For each component (server and gamer) we have different logs. For both components we also have default ports and logs. On the server side, we set the UDP port as 5000 to receive the commands from the user. Similarly, on the gamer side, we receive the incoming frames from the server on port 5002 and send the commands to server through UDP 5003.

> NOTE: Port 5001 is not used yet, but we intend to leverage it in the future.

As mentioned, each component generate different logs after we run the experiment.

**Server logs**

`rate_control_log.txt` --> (Frame_ID, rate_ctl) [It shows Frame_ID and its sync status: High sync, Sync, Critical Sync, and Non-sync with each state encoding rate actions which can be jump, rise, decrease and fall]

`server_log.txt` --> {frame_id},{received_fame_id},{my_gap},{received_time},{send_time} {current_srv_fps},{received_fps},{current_cps},{received_cps} {current_srv_fps/received_fps},{received_cps/current_cps},{bitrate}

`frame_log` --> (f"{frame_id},{current_srv_fps},{processing_time},{bitrate}

> NOTE: processing time is the time wasted in the server. Bitrate in all logs refers to the frame rate and cps refers to command per second


**Gamer logs**

`rate_log` --> {frame_id},{current_fps},{currrent_cps}\
`time_log` --> {frame_id},{frm_rcv},{cmd_sent}\
`received_frames` --> it refers all frames received in the gamer side!

> NOTE: cmd is command, frm is frame, and rcv is received.


Lines 24-37 encompasses the game setup. For now, we can choose between 3 games: Forza Horizon 5, Mortal Kombat 11 or Fortnite. For each of the games, we have a `sync_file`. This file tries to order frames arriving out-of-order (of course), synchronizing them with their respective commands.

Lines 40-46 are the encoding settings. We first set a target `fps`. For instance, 30. Also, we have the game screen resolution as 600x480, which is downscaled, because the default is 1364x768.

> NOTE: The target FPS is achieved (or not) depending on the hardware running the experiment.

Finally, lines 60-69 allows us to tweak synchronization and sliding window configuration. For instance, `ack_freq` determines after how many packets, we should receive an ACK. The variable `game` is where we select which of the game profiles/replays we want to run (e.g., `game: "Kombat"`).

> NOTE: if you want to enable SCREAM protocol or not by setting the variable `SCReAM` as _True_ or _False_.




### Step 4: Run the experiment


**On MiniEdit and Xterm** 
After the configuration file is set, we can run the experiment. To do it, open two xterm terminals: one for `cgserver` and another for `cgplayer`. To do this, right-click on the objects and open a terminal for each of them:

![image](https://github.com/user-attachments/assets/2ba8324c-4ba1-411b-a69a-036c8f87ddd0)


![image](https://github.com/user-attachments/assets/02f1091d-a125-4b55-b899-5f55365d7a25)



**Host-side (cgplayer terminal)**

Then, on the host-side, go to `CGReplay/player` on _cgplayer_'s terminal (right - image below) and run:

```python
python3 cg_gamer1.py
```

At this moment, the player/gamer will be ready to receive data on ports UDP:5002 and UDP:5003, (image below)

![image](https://github.com/user-attachments/assets/5df925ba-200d-46ad-8277-52fadd24576a)


> NOTE: the cgplayer's script should always be run first!

**Server-side (cgserver terminal)**

Go to `CGReplay/server/` and run the script below on server-side (_cgserver_'s terminal):

```python
python3 cg_server_1.py
```

Immediately after we run the script on the server, a screen will show up and start replaying the frame. Meanwhile, we can see both the server and player's terminal exchanging frames and commands.

![image](https://github.com/user-attachments/assets/ee4d9a1f-cdf1-4b5a-8de7-22d195b9ea67)


The experiment stops after 300 frames, because the default configuration sets the variable `stop_frm_number` is `300`. However, you can choose whatever frame numbers you want -- assuming, it is less or equal than the total number of frames for recorded game session.


After we run the experiment, we can have access to the logs discussed earlier on both the server- (`CGReplay/server/logs/`) and player-side (`CGReplay/player/logs/`). Also, the received frames at the user (player) will be availabled in `CGReplay/player/logs/received_frames`.
