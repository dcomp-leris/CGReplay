'''
# Date: 2024-11-29
# Author: Alireza Shirmarz
# This is Configured for Netsoft 2025 Conference!
# Gamer: (1) 
'''

import cv2, os, socket, time, yaml
import pandas as pd
from datetime import datetime
from pyzbar import pyzbar
from collections import deque


os.sched_setaffinity(0, {0})

# Load configuration from YAML file
# config file is:  ../config/config.yaml
with open("../config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

# game name
game_name = config["game"]

# server setup
cg_server_ip = config["server_IP"]
cg_server_port = config["server_port"]
# client (player) setup
player_ip = config["player_IP"]
player_port = config["player_streaming_port"]
my_command_port = config["palyer_command_port"]

# sync setup
folder_path = config[game_name]["frames"] 
auto_commands_file_addr = config[game_name]["sync_file"] 

# log setup 
rate_log = config[game_name]["player_rate_log"] 
time_log = config[game_name]["player_time_log"]
received_frames = config[game_name]["received_frames"]



'''
# Load settings from YAML file

# CG_player
player_ip = config["player_IP"]
player_port = config["player_streamin_port"]
my_command_port = config["palyer_command_port"]

# CG_Server
cg_server_port = config["server_port"] #5508 # 5501  # Port for receiving control data from a socket
cg_server_ipadress = config["server_IP"]  #"172.16.0.2"   # this computer IP address

# sync setup
folder_path = config[game_name]["frames"] 
my_command_frame_addr = config[game_name]["sync_file"] 

# Frame & Encoding setup 
fps = config["fps"]  # Frames per second
bitrate = config["bitrate"] #5000  # in kbps
resolution_width = config["resolution"]["width"]
resolution_height = config["resolution"]["height"]  #(1920,1080)  # (width, height)(1920,1080) (1364, 768)


# Log files address
## Logs frame rate + command rate
rate_control_log = config["log_rate_control"] #"srv_ratectl_tofino1.txt"
server_log = config["log_server"] # "srv_total_tofino1.txt"
frame_log = config["log_frame"] #"srv_frame_tofino1.txt" 

# Scream enable or disable
scream_state=config["SCReAM"]

'''

# Custom function to load autocommands.txt while handling the complex 'command' field
def load_autocommands(file_path):
    autocommands = []
    with open(file_path, 'r') as file:
        next(file)  # Skip the header line
        for line in file:
            # Split only on the last comma to avoid splitting inside the 'command' field
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                id_and_command, encrypted_cmd = parts
                # Split the ID from the command part
                id_str, command_str = id_and_command.split(',', 1)
                autocommands.append((int(id_str), command_str, encrypted_cmd.strip()))
    return pd.DataFrame(autocommands, columns=['ID', 'command', 'encrypted_cmd'])
'''
# UDP Socket setup
cg_server_ip = "172.16.0.2"
cg_server_port = 5508
player_ip = "172.16.0.1"
player_port = 5000
my_command_port = 5555

# set the game type to emulate
game = {'Forza': '/home/leris/mygamer/autocommands_forza1.txt', 
        'Kombat': '/home/leris/mygamer/autocommands_fortnite.txt' , 
        'Fortnite':'/home/leris/mygamer/autocommands_kombat.txt'}

game_name = 'Forza'
auto_commands_file_addr = game[game_name]
#'/home/alireza/CG_Simulation/autocommands_forza.txt' #"/home/alireza/CG_Simulation/Phase4_Player_Command/autocommands_forza.txt"



rate_log = "./logs/ratelog_CG.txt"
time_log = "./logs/timelog_CG.txt"
received_frames = "./received_frames"

'''


# Load autocommand.txt
autocommands_df = load_autocommands(auto_commands_file_addr)
#print("Loaded autocommands:")
#print(autocommands_df)
print(f"palyer is ready to receive {player_port} & command sent on {my_command_port}")

# Function to send command to server
def send_command(frame_id, encrypted_cmd, interface_name="enp2s0np0", type='command', number = 0, fps = 0, cps = 0): # #"enp0s31f6" wlp0s20f3
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface_name.encode()) #interface_name.encode())
    sock.bind((player_ip, player_port))
    timestamp = time.perf_counter() #time.time() * 1000
    message = f"{timestamp},{encrypted_cmd},{frame_id},{type},{number},{fps},{cps}"
    # port setup
    #my_test_port = 5555
    sock.sendto(message.encode(),(cg_server_ip, my_command_port))
    #print(f"Sent command for Frame ID {frame_id}: {message}") //commented
    sock.close()

# Function to read the QR code from the frame
def read_qr_code_from_frame(frame):
    """Reads the QR code from a given frame and extracts its data."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
    qr_codes = pyzbar.decode(blurred_frame)

    for qr in qr_codes:
        qr_data = qr.data.decode('utf-8')
        print(f"Detected QR Code Data: {qr_data}")
        data_parts = qr_data.split(',')
        frame_id = None
        for part in data_parts:
            if "ID:" in part:
                frame_id = part.split(':')[1].strip()
                break
        if frame_id:
            return int(frame_id), qr_data

    return None, None

# GStreamer pipeline to receive video stream from port 5000
gstreamer_pipeline = (
     f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "queue max-size-time=1000000000 ! rtph264depay ! avdec_h264 ! videoconvert ! appsink"

)
'''(
    f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "rtph264depay ! avdec_h264 ! videoconvert ! appsink"
)'''

# Open the video stream using OpenCV and GStreamer
cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Error: Could not open video stream")
    exit()

# frame_buffer = deque(maxlen=30)  # Buffer to store frames
frame_counter = 1
#timeout_duration = 0.0001
previous_command = None
next_frame = 1
cmd_previoustime =frm_previoustime = time.perf_counter()
currrent_cps = 0
current_fps = 0
my_try_counter = 0 

while True:

    start_time = time.perf_counter() # time.time()

    # Try to receive the next frame
    ret, frame = cap.read()
    frm_rcv = time.perf_counter() # time.time() * 1000
    #test_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
    #print("Debug:***************",test_timestamp)

    # Read QR code from the buffered frame
    frame_id, qr_data = read_qr_code_from_frame(frame)
    current_fps = 1/(frm_rcv-frm_previoustime)
    frm_previoustime = frm_rcv
    #print(f"{frame_id}-fps:{current_fps}")
    

    if frame_id:
        print(f"Detected Frame ID: {frame_id}")
        
        if (my_try_counter%30)==0:
            send_command(frame_id,current_fps,"enp2s0np0",type='Ack', fps = current_fps, cps = currrent_cps )
        else:
            pass

        #next_frame = int(frame_id) + 1

        if frame_id == frame_counter+1:
            frame_filename = f"{received_frames}/{frame_id:04d}_{frm_rcv}.png"
        else:
            frame_filename = f"{received_frames}/{frame_id:04d}_{frm_rcv}_retry.png"

        frame_counter = frame_id
        
    else:
        print("No QR code detected in this frame.")
        send_command(0,"Downgrade",type='Nack',fps = current_fps, cps = currrent_cps )   # Send NacK
        send_command(frame_counter, previous_command,type='command',fps = current_fps, cps = currrent_cps ) # Send the Previous Command
        #continue
        #frame_counter+=1
        frame_filename = f"{received_frames}/{frame_counter:04d}_{frm_rcv}_NoQR.png"
        pass 
    
    
    # Save the current frame to a file
    #frame_filename = f"{my_forza_frame_addr}/{frame_id if frame_id is not None else 0:04d}_{frm_rcv}.png"
    #frame_filename = f"{my_forza_frame_addr}/{frame_id:04d}_{frm_rcv}.png"
    cv2.imwrite(frame_filename, frame)
    #print(f"Saved {frame_filename}") /// Commented

    # Display the frame
    #cv2.imshow("CG Player Client (LERIS)", frame)
    matching_command = [] # new edit 
    # Check if there's a matching command for this frame
    matching_command = autocommands_df[autocommands_df['ID'] == frame_counter]
    cmd_number = matching_command.shape[0]
    encrypted_cmds = matching_command['encrypted_cmd'].values
    #print(f"####Debug \n {autocommands_df['ID'][1]}####")
    print('\n********************************\n')
    if not matching_command.empty:
        #print(f"Match found for Frame {frame_counter}")
        
        send_command(frame_counter, encrypted_cmds,type ='command', number = cmd_number, fps = current_fps, cps= currrent_cps)
        cmd_sent = time.perf_counter() # time.time() * 1000
        currrent_cps = 1/(cmd_sent - cmd_previoustime)
        cmd_previoustime = cmd_sent
        #matching_command.apply(lambda row: send_command(frame_counter, encrypted_cmds,number = cmd_number), axis=1)  #row['encrypted_cmd'],number = cmd_number), axis=1)
        previous_command = encrypted_cmds.copy() # matching_command.iloc[0]['encrypted_cmd']
        
            # Log frame received time
        with open(rate_log, "a") as f: # fID - fps - cps
            f.write(f"{frame_id},{current_fps},{currrent_cps}\n")


        with open(time_log, "a") as f: # FID - F timestamp - CMD Timestamp
            f.write(f"{frame_id},{frm_rcv},{cmd_sent}\n")

    #frame_counter += 1
    
    my_try_counter = my_try_counter + 1
    print(f'My counter is ###{my_try_counter}')
    if my_try_counter == 9000:
         break

    # Press 'q' to exit the video display window
    #if cv2.waitKey(1) & 0xFF == ord('q'):
        #break

cap.release()
cv2.destroyAllWindows()
