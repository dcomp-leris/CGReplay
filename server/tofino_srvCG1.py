'''
# Date: 2024-11-29
# Author: Alireza Shirmarz
# This is Configured for P4Pi
# tofino 1
'''

import os , time, socket, select 
import cv2
import qrcode
import gi
import numpy as np, pandas as pd
import hashlib



os.sched_setaffinity(0, {0})


gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

# Hash Function to encrypt the Commands
def hash_string(input_string, output_size):
    """Hashes a string using SHAKE and returns the hex digest with the given output size in bytes."""
    # Use SHAKE-128 for flexibility in output size
    shake = hashlib.shake_128()
    shake.update(input_string.encode('utf-8'))
    # Return the hex digest with the specified byte size
    return shake.hexdigest(output_size)

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

# Client or Player Configuration ______________________________________
# IP player is "200.18.102.9" for Streaming
# UDP Port for streaming on the destination (player or client) is 5000
player_ip = "172.16.0.1" 
player_port = 5000  # UDP port for streaming
my_command_port = 5555 # Command

# _______________________________________________________________________ This computer (CG Server Configuration) 
# Forza Server 
# Port listening the Traffic (commands) is 5501
# IP is  200.18.102.25 or 0.0.0.0 ________________________________________
cg_server_port = 5508 # 5501  # Port for receiving control data from a socket
cg_server_ipadress = "172.16.0.2"   # this computer IP address


# set the game type to emulate
game = {'Forza': ['/home/alireza/cgserver/processed_forza1', '/home/alireza/cgserver/autocommands_forza1.txt'], 
        'Kombat': ['/home/alireza/cgserver/processed_kombat', '/home/alireza/cgserver/autocommands_kombat.txt'] , 
        'Fortnite':['/home/alireza/cgserver/processed_fortnite','/home/alireza/cgserver/autocommands_fortnite.txt']}

game_name = 'Forza'
# Configuration Files address
folder_path = game[game_name][0] #"/home/alireza/cgserver/Processed_Frames_Forza"  # Folder containing PNG frames 
my_command_frame_addr = game[game_name][1] #'/home/alireza/cgserver/autocommands_forza.txt'
#autocommands_df = load_autocommands('/home/alireza/cgserver/autocommands_forza.txt') # Load autocommands for fram/command ordering

# Logs frame rate + command rate
rate_control_log = "srv_ratectl_tofino1.txt"
server_log = "srv_total_tofino1.txt"
frame_log = "srv_frame_tofino1.txt"
# Streaming Parameters
fps = 30  # Frames per second
bitrate = 10000 #5000  # in kbps
resolution = (1364, 768) #(1920,1080)  # (width, height)(1920,1080) (1364, 768)

# List of frame IDs where we want to pause and wait for socket input
autocommands_df = load_autocommands(my_command_frame_addr) # Load autocommands for fram/command ordering
pause_frame_ids = autocommands_df['ID'].tolist()
# Backup for Forza


def generate_qr_code(data):
    """Generate QR code as an image from the given data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20, #10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR Code instance
    qr_img = qr.make_image(fill='black', back_color='white')
    
    # Convert to numpy array for OpenCV compatibility
    qr_img = np.array(qr_img.convert('RGB'))
    
    return qr_img

# Setup Socket for Receiving the Commands
def setup_socket():
    """Set up a UDP socket to send control messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Allow reuse of the same address and port
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    #my_test_port = 5555
    # Bind the socket to the specific source port (same as GStreamer)
    sock.bind((cg_server_ipadress, my_command_port)) # cg_server_port))  # socket_port should be 5501 or the same source port as GStreamer
    
    print(f"Listening on UDP port {cg_server_port} for control data...")
    return sock

# Stream the video frames
received_fame_id = 0

def stream_frames(game_name):
    global bitrate
    bitrate = 10000
    bitrate_min = 2000
    bitrate_max = 20000
    window_min = 1 
    window_max = 4
    cmd_previous_time =  time.perf_counter()
    """
    Stream frames based on the selected game.
    This is just a mock function.
    """
    if game_name == 'Forza':
        print("Streaming frames for Forza...")
        # Add Forza-specific streaming logic here
        # Configuration Files address
        folder_path = game['Forza'][0] #"/home/alireza/cgserver/Processed_Frames_Forza"  # Folder containing PNG frames 
        my_command_frame_addr = game['Forza'][1] #'/home/alireza/cgserver/autocommands_forza.txt'

    elif game_name == 'Fortnite':
        print("Streaming frames for Fortnite...")
        # Add Fortnite-specific streaming logic here
        # Configuration Files address
        folder_path = game['Fortnite'][0] #"/home/alireza/cgserver/Processed_Frames_Forza"  # Folder containing PNG frames 
        my_command_frame_addr = game['Fortnite'][1] #'/home/alireza/cgserver/autocommands_forza.txt'
    elif game_name == 'Kombat':
        print("Streaming frames for Kombat...")
        # Add Kombat-specific streaming logic here
        # Add Forza-specific streaming logic here
        # set the game type to emulate
        # Configuration Files address
        folder_path = game['Kombat'][0] #"/home/alireza/cgserver/Processed_Frames_Forza"  # Folder containing PNG frames 
        my_command_frame_addr = game['Kombat'][1] #'/home/alireza/cgserver/autocommands_forza.txt'
    else:
        print("Game not supported!")

    
    # bitrate = 10000  # in kbps
    """Stream frames with QR code embedded over UDP using GStreamer."""
    # Set up the control socket
    control_socket = setup_socket()
    #control_socket.settimeout(1)

    #data, addr = control_socket.recvfrom(1024)
    #if data.decode() =="start":
        #print('Game Started with command!!')
    
        

    #control_socket.settimeout(5)
    #source_port = 5501
    # GStreamer pipeline for video encoding and streaming
    ''' The main which worked!'''
    pipeline_str = f"""
        appsrc name=source is-live=true block=true format=GST_FORMAT_TIME do-timestamp=true !
        videoconvert ! video/x-raw,format=I420,width={resolution[0]},height={resolution[1]},framerate={fps}/1 !
        x264enc bitrate={bitrate} speed-preset=ultrafast tune=zerolatency ! h264parse ! rtph264pay ! 
        udpsink host={player_ip} port={player_port} bind-port={cg_server_port}
    """
    
    '''pipeline_str = f"""
        appsrc name=source is-live=true block=true format=GST_FORMAT_TIME do-timestamp=true !
        videoconvert ! video/x-raw,format=I420,width={resolution[0]},height={resolution[1]},framerate={fps}/1 !
        x264enc bitrate={bitrate} speed-preset=ultrafast tune=zerolatency ! h264parse ! 
        rtph264pay config-interval=-1 pt=96 ! 
        rtpstreampay ! udpsink host={player_ip} port={player_port}
    """'''

    # Parse and create the GStreamer pipeline
    pipeline = Gst.parse_launch(pipeline_str)

    # Get the 'appsrc' element from the pipeline
    appsrc = pipeline.get_by_name("source")
    if not appsrc:
        print("Failed to retrieve appsrc element from the pipeline.")
        return

    # Set the caps for the 'appsrc' element, including FPS and resolution
    appsrc.set_property("caps", Gst.Caps.from_string(f"video/x-raw,format=BGR,width={resolution[0]},height={resolution[1]},framerate={fps}/1"))

    # Start the pipeline
    pipeline.set_state(Gst.State.PLAYING)
    
    frame_id = 1  # Frame counter (starting from 1 for human-readable frame IDs)
    png_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".png")])  # List PNG files
    # flag_lock = False
    cmd_counter = 0  #autocommands_df.shape[0] # max number 
    previous_time = time.perf_counter()
    
    '''
    for idx, file in enumerate(png_files):
        frame_path = os.path.join(folder_path, file)
        frame = cv2.imread(frame_path)  # Read the frame
        frame_id = int(file.split('.')[0])
        if frame is None:
            print(f"Could not load frame {file}")
            continue
    '''
    idx = 0
    while idx < len(png_files):
        if idx == 9000:
            break
        file = png_files[idx]  # Access the file by index

        # Construct the full file path
        frame_path = os.path.join(folder_path, file)

        # Load the frame
        frame = cv2.imread(frame_path)  # Read the image file
        frame_id = int(file.split('.')[0])  # Extract frame ID from the filename

        if frame is None:
            print(f"Could not load frame {file}")
            idx += 1  # Move to the next file if loading fails
            continue    
        
        idx= idx + 1


        
        timestamp = time.perf_counter()
        # Resize frame to the desired resolution
        frame = cv2.resize(frame, resolution)


        qr_data = f"Frame ID: {frame_id}, rcv_timestamp: {timestamp}, resolution: {resolution},bitrate:{bitrate}"
        qr_img = generate_qr_code(qr_data)
        
        #QR Size & Location
        #qr_height, qr_width, _ = qr_code_img.shape
        # Resize QR code to fit into a corner of the video frame
        qr_size = 200 #100  # QR code size in pixels
        qr_img = cv2.resize(qr_img, (qr_size, qr_size))

        # Overlay the QR code onto the bottom-right corner of the frame
        x_offset = frame.shape[1] - qr_size - 10  # 10px padding from the right edge
        y_offset = frame.shape[0] - qr_size - 10  # 10px padding from the bottom edge
        frame[y_offset:y_offset + qr_size, x_offset:x_offset + qr_size] = qr_img

        # Convert frame to bytes and push to GStreamer
        gst_buffer = Gst.Buffer.new_wrapped(frame.tobytes())

         
        appsrc.emit("push-buffer", gst_buffer)
        # fpscomputing + processing time (Rendering)
        my_fps_time = time.perf_counter() 
        current_srv_fps = 1/(my_fps_time - previous_time)
        processing_time = my_fps_time - timestamp
        previous_time = my_fps_time

        # Log the frame that is being streamed
        print(f"Streaming frame {frame_id}")
        with open(frame_log, "a") as f: f.write(f"{frame_id},{current_srv_fps},{processing_time},{bitrate}\n")
        
         # Log the frame that is being streamed
        #print(f"Streaming frame {frame_id}")
        #with open(server_rate, "a") as f: f.write(f"{frame_id},{current_srv_fps},{processing_time},{bitrate}\n")

        # new code
        timeout = 0.0001 # if not flag_lock else None
        ready_to_read, _, _ = select.select([control_socket], [], [], timeout) #0.01)  # 10 milliseconds timeout         
        received_fame_id = 0 

        if ready_to_read:
            #print('It is ready ready to receive!!!!!!')
            # Receive control data for each matching command (blocking)
            data, addr = control_socket.recvfrom(1024)
            received_data = data.decode().split(',')
            received_time = time.perf_counter() #time.time() * 1000  # Timestamp in milliseconds
            current_cps = 1/(received_time - cmd_previous_time)
            cmd_previous_time = received_time
            #print(f"Debug: Received command message {received_data}")
            # Extract both timestamps and the command
            #print(received_data)
            send_time = received_data[0]
            received_cmd = received_data[1]
            received_fame_id = int(received_data[2])
            received_type = received_data[3]
            received_cmd_number = received_data[4]
            received_fps = float(received_data[5])
            received_cps =  float(received_data[6])
            #print(received_type)
            print(f"Received control data: Type ({received_type}) Time = {send_time}, from {addr}")
            #print(f"Debug: {received_cmd} | Number: {cmd_number}")
            my_gap = frame_id - received_fame_id # to check the window 
            Nack_counter = 0
            rate_ctl = [None , None, None, None]
            if received_type=='Ack':
                rate_ctl = [None , None, None, None]
                rate_ctl[3] = 'Ack'
                Nack_counter = 0 
                if my_gap <= window_min:
                    print(f'(Ack) [Fast Increase] ==> Frame ID is {frame_id} with Gap {my_gap} \n [player fps = {received_fps}] [server fps = {current_srv_fps}] \n [player cps = {received_cps} [server cps = {current_cps}]] | bitrate = {bitrate}')
                    bitrate = bitrate + (bitrate * 0.2) if bitrate_min <= bitrate <= bitrate_max else bitrate
                    #rate_ctl[0] = 'Fast Increase', rate_ctl[1] = 0.2, rate_ctl[2] = bitrate
                    rate_ctl = ['Fast Increase', 0.2, bitrate,rate_ctl[3]]

                elif window_min < my_gap <= window_max:
                    print(f'(Ack) [Increase] ==> Frame ID is {frame_id} with Gap {my_gap} \n [player fps = {received_fps}] [server fps = {current_srv_fps}] \n [player cps = {received_cps} [server cps = {current_cps}]] | bitrate = {bitrate}')
                    bitrate = bitrate - (bitrate * 0.1) if bitrate_min <= bitrate <= bitrate_max else bitrate
                    rate_ctl = ['Increase', 0.1,bitrate,rate_ctl[3]]
                    
                elif my_gap > window_max:
                    print(f'(Ack) [Decrease] ==> Frame ID is {frame_id} with Gap {my_gap} \n [player fps = {received_fps}] [server fps = {current_srv_fps}] \n [player cps = {received_cps} [server cps = {current_cps}]] | bitrate = {bitrate}')
                    # print(f'(Ack) (**Wait**) ==> Received Frame is {received_fame_id} == current {frame_id} \n [fps = {received_fps}] [server fps = {current_srv_fps}] but Gap is {my_gap}')
                    bitrate = bitrate - (bitrate * 0.2) if bitrate_min <= bitrate <= bitrate_max else bitrate
                    rate_ctl = ['Decrease', 0.2, bitrate,rate_ctl[3]]
                    #idx = idx - my_gap

                #with open(rate_control_log, "a") as f: f.write(f"{frame_id},{rate_ctl}\n")

            elif received_type=='Nack':
                rate_ctl = [None, None, None, None]
                rate_ctl[3] = 'command'
                if Nack_counter == 0:
                    #print(f'(Nack) ==> Received Frame is {received_fame_id}')
                    print(f'(Nack) [Decrease & lagged!] ==> Frame ID is {frame_id} with Gap {my_gap} \n [player fps = {received_fps}] [server fps = {current_srv_fps}] \n [player cps = {received_cps} [server cps = {current_cps}]] | bitrate = {bitrate}')
                    bitrate = bitrate - (bitrate * 0.2) if bitrate_min <= bitrate <= bitrate_max else bitrate
                    idx = received_fame_id - my_gap
                    #time.sleep(0.0001)
                    Nack_counter = Nack_counter + 1
                    rate_ctl = ['Decrease & lagged', [0.2,1], bitrate,rate_ctl[3]]
                    

                else:
                    print(f'(Nack) [Fast Decrease & lagged!] ==> Frame ID is {frame_id} with Gap {my_gap} \n [player fps = {received_fps}] [server fps = {current_srv_fps}] \n [player cps = {received_cps} [server cps = {current_cps}]] | bitrate = {bitrate}')
                    bitrate = bitrate - (bitrate * 0.5) if bitrate_min <= bitrate <= bitrate_max else bitrate
                    idx = received_fame_id - my_gap
                    #time.sleep(0.0001)
                    Nack_counter = Nack_counter + 1
                    rate_ctl = ['Fast Decrease & lagged', [0.5,my_gap], bitrate,rate_ctl[3]]
                #with open(rate_control_log, "a") as f: f.write(f"{frame_id},{rate_ctl}\n")
                '''
                else:
                    print(f'(Nack) [Drop & lagged!] ==> Frame ID is {frame_id} with Gap {my_gap} \n [player fps = {received_fps}] [server fps = {current_srv_fps}] \n [player cps = {received_cps} [server cps = {current_cps}]] | bitrate = {bitrate}')
                    bitrate = bitrate - (bitrate * 0.5) if bitrate_min <= bitrate <= bitrate_max else bitrate
                    idx = received_fame_id - window_max
                    #time.sleep(0.0001)
                    Nack_counter = Nack_counter + 1
                '''

            elif received_type=='command':
                rate_ctl = [None, None, None, None]
                rate_ctl[3] = 'command'

                matching_commands = []
                matching_commands = autocommands_df[autocommands_df['ID'] == (received_fame_id)] #received_fame_id] #expected_command_id]
                my_cmd_number = matching_commands.shape[0]
                cmd_counter = cmd_counter + my_cmd_number


                if not matching_commands.empty:
                    state = [None , None]
                    if pause_frame_ids[cmd_counter-1] == matching_commands['ID'].iloc[0]:
                        state[0] ='Match'
                        print(f"Match***{my_gap}")
                    else:
                        print(f"Ooops***{my_gap}")
                        state[0] = 'Not Match'
                    
                    if my_gap <= window_min:
                        bitrate = bitrate + (bitrate * 0.1) if bitrate_min <= bitrate <= bitrate_max else bitrate
                        state[1] = 'Rate Fast Rise'
                        rate_ctl = ['Rate Fast Increase',  0.1,  bitrate,rate_ctl[3]]

                    elif window_min < my_gap <= window_max:
                        bitrate = bitrate - (bitrate * 0.1) if bitrate_min <= bitrate <= bitrate_max else bitrate
                        state[1] = 'Rate Smooth Fall'
                        rate_ctl = ['Rate Decrease', 0.1,  bitrate,rate_ctl[3]]

                    elif my_gap > window_max:
                        bitrate = bitrate - (bitrate * 0.2) if bitrate_min <= bitrate <= bitrate_max else bitrate
                        state[1] = 'Rate Faster Fall'
                        #idx = idx - my_gap
                        rate_ctl = ['Fast Decrease & lagged',[0.2, my_gap],  bitrate,rate_ctl[3]]
                        continue
                    
                    print(f"{state} | Gap:{my_gap} | FID:{frame_id} | player FID:{received_fame_id}"
                        f" player fps = {received_fps} | server fps = {current_srv_fps}"
                        f" player cps = {received_cps} | server cps = {current_cps}, , rate = {bitrate} ") 
                    

                    with open(server_log, "a") as f: 
                        f.write(f"{frame_id},{received_fame_id},{my_gap},{received_time},{send_time},{current_srv_fps},{received_fps},{current_cps},{received_cps},{current_srv_fps/received_fps},{received_cps/current_cps},{bitrate} \n")

            
   
                    # Log the frame that is being streamed
                    #print(f"Streaming frame {frame_id}")
                    #with open(server_rate, "a") as f: f.write(f"{frame_id},{current_srv_fps/received_fps},{received_cps/current_cps},{processing_time},{bitrate}\n")
                    state = [None , None]

            with open(rate_control_log, "a") as f: f.write(f"{frame_id},{rate_ctl}\n")        
        
            

        # Maintain the frame rate
        '''if ((time.perf_counter())-timestamp) <= ((1 / fps)):
            time.sleep((1 / fps)-((time.perf_counter())-timestamp))'''

    # End the stream
    appsrc.emit("end-of-stream")
    pipeline.set_state(Gst.State.NULL)

def load_config(file_path="config.txt"):
    """Reads the config.txt file and returns a dictionary of settings."""
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines and comments
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=")
                key = key.strip()
                value = value.strip()
                # Parse resolution into a tuple
                if key == "resolution":
                    value = tuple(map(int, value.split(",")))
                elif key in ["fps", "bitrate", "player_port", "my_test_port", "cg_server_port"]:
                    value = int(value)  # Convert numeric values
                config[key] = value
    return config

if __name__ == "__main__":
    # Load configurations from the config.txt file
    '''config = load_config("/home/alireza/cgserver/CG_server/config.txt")
    
    # Update global variables based on the configuration
    game_name = config.get("game_name", "Forza")
    player_ip = config.get("player_ip", "200.18.102.7")
    player_port = config.get("player_port", 5000)
    my_test_port = config.get("my_test_port", 5555)
    cg_server_ipadress = config.get("cg_server_ipadress", "200.18.102.25")
    cg_server_port = config.get("cg_server_port", 5508)
    fps = config.get("fps", 30)
    bitrate = config.get("bitrate", 5000)
    resolution = config.get("resolution", (1364, 768))
    
    print(f"Loaded configuration: {config}")'''
    '''
    game = {'Forza': ['/home/alireza/cgserver/processed_forza', '/home/alireza/cgserver/autocommands_forza.txt'], 
    'Kombat': ['/home/alireza/cgserver/processed_kombat', '/home/alireza/cgserver/autocommands_kombat.txt'] , 
    'Fortnite':['/home/alireza/cgserver/processed_fortnite','/home/alireza/cgserver/autocommands_fortnite.txt']}
    
    '''
    # Call the stream_frames function
    game_name = 'Forza'
    print('Started ... ')
    stream_frames(game_name)
'''
if __name__ == "__main__":
    #print('Waiting 1 second....')
    #global game_name
    #time.sleep(1)
    game_name = 'Forza' # 'Forza'/'Fortnite'/'Kombat'
    print('Started ... ')
    stream_frames(game_name)
'''
    

