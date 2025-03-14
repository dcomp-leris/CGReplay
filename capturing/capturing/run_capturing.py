'''
Project: CGReplay
Main Module: Capturing
sub Module: Screen + Joystick
Date: 2025-03-10
Author(s): Alireza Shirmarz
Location: Lerislab
'''

import subprocess
import time
import yaml

# Load configuration from YAML file
with open("./config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Load settings from YAML file
network_interface = config["network_interface"]
capture_duration = config["duration"]
filename = config["filename_prefix"]
script1 = config["script_joystick"]
script2 = config["script_screen"]
waiting_time = config["starting_waiting_time"]

try:
    print(f"Waiting {waiting_time} seconds to start logging .... ")
    time.sleep(waiting_time)

    # Start the Python scripts
    #process1 = subprocess.Popen(['python3', script1, filename])
    process2 = subprocess.Popen(['python3', script2, filename])

    # Start tshark command to capture network traffic
    process3 = subprocess.Popen([
        'sudo', 'tshark', '-i', network_interface,
        '-a', f'duration:{capture_duration}', '-w', f'{filename}.pcap'
    ])

    # Wait for the Python scripts to finish
    #process1.wait()
    process2.wait()

    # Optionally wait for tshark to finish (if needed)
    process3.wait()

    print("All processes finished successfully.")

except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e}")
except KeyboardInterrupt:
    print("Processes interrupted by user.")
finally:
    # Make sure to terminate tshark and other processes if necessary
    #process1.terminate()
    process2.terminate()
    process3.terminate()
    print("All processes terminated.")
