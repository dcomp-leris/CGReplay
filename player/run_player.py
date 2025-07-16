'''
# 

'''

import os, time
import subprocess
import multiprocessing, yaml


def run_player1():
    """Run the player Python script."""
    print("Player1 is running ....")
    subprocess.run(["sudo","python3", "./cg_gamer1.py"], check=True)

'''
def run_player2():
    """Run the player Python script."""
    print("Player2 is running ....")
    subprocess.run(["sudo","python3", "/home/leris/mygamer/tofino/player_tofino2.py"], check=True)


def run_player3():
    """Run the player Python script."""
    print("Player3 is running ....")
    subprocess.run(["sudo","python3", "/home/leris/mygamer/tofino/player_tofino3.py"], check=True)
'''
def run_tshark(inter = "player-eth0", file_path = "./my.pcap"):
    """Run tshark command that requires sudo privileges."""
    cmd = ["tshark", "-i", inter, "-w", file_path]
    subprocess.run(cmd, check=True)
    print("Tshark is running ....")

'''
def run_kill_ports():
    subprocess.run(["sudo","/home/leris/mygamer/tofino/port_clean1.sh"], check=True)
    print("killed the ports ***")
    time.sleep(1)

def run_delete_frames1():
    subprocess.run(["sudo","rm", "-f", "/home/leris/mygamer/tofino/rcv_forza_f/*.*"], check=True)
    print("Removed RCV Frames1 ***")
    time.sleep(1)

def run_delete_frames2():
    subprocess.run(["sudo","rm", "-f", "/home/leris/mygamer/tofino/rcv_forza_s/*.*"], check=True)
    print("Removed RCV Frames2 ***")
    time.sleep(1)

def run_delete_frames3():
    subprocess.run(["sudo","rm", "-f", "/home/leris/mygamer/tofino/rcv_forza_t/*.*"], check=True)
    print("Removed RCV Frames3 ***")    
    time.sleep(1)


def run_delete_pcap():
    subprocess.run(["sudo","rm", "-f", "/home/leris/mygamer/tofino/mypcap/my.pcap"], check=True)
    print("Removed PCAP Files ***")
''' 

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
    #run_kill_ports()
    #run_delete_pcap()
    #run_delete_frames1()
    #run_delete_frames2()
    #run_delete_frames3()
    # Load configuration from YAML file
    with open("../config/config.yaml", "r") as file:
        config = yaml.safe_load(file)

    NIC = config["gamer"]["player_interface"]
    pcap_file = config["gamer"]["pcap_file"]

    player1_process = multiprocessing.Process(target=run_player1)
    #player2_process = multiprocessing.Process(target=run_player2)
    #player3_process = multiprocessing.Process(target=run_player3)
    tshark_process = multiprocessing.Process(target=run_tshark, args=(NIC,pcap_file))
    
    print('\n')
    print('+++++++++++++++++++++++++')
    # Create processes
    
    #scream_process = multiprocessing.Process(target=run_scream_command)
    
    # Start processes
    player1_process.start()
    #player2_process.start()
    #player3_process.start()
    tshark_process.start()
    
    #scream_process.start()

    # Wait for both to complete
    player1_process.join()
    #player2_process.join()
    #player3_process.join()
    tshark_process.join()
    #scream_process.join()
