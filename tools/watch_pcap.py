import subprocess

# Step 1: Change permissions
'''
subprocess.run(['sudo', 'chmod', '777', '../player/logs/*.*'])
/home/alireza/mycg/CGReplay/player/logs/my.pcap
'''
sudo_password = "844464"
subprocess.run(['sudo', '-S', 'chmod', '777', '../player/logs/my.pcap'], input=f"{sudo_password}\n", text=True)

print("(1) Access is done!")

# Step 2: Convert PCAPNG to PCAP
# /home/alireza/Desktop/Joysticklogs
#subprocess.run(['editcap', '-F', 'libpcap', '/home/alireza/Desktop/Joysticklogs/out.pcap', './my_converted.pcap'])
subprocess.run(['editcap', '-F', 'libpcap', '../player/logs/my.pcap', './my_converted.pcap'])
print("(2) Converting happened!")

# Step 3: Run GStreamer pipeline

subprocess.run([
    'gst-launch-1.0', '-v',
    'filesrc', 'location=./my_converted.pcap',
    '!', 'pcapparse',
    '!', 'application/x-rtp,encoding-name=H264,payload=96',
    '!', 'rtph264depay',
    '!', 'avdec_h264',
    '!', 'autovideosink'
])
print("(3) Displaying!")

'''
# Ariel PC
subprocess.run([
    "gst-launch-1.0", "-e", "-v",
    "filesrc", "location=./my_converted.pcap",
    "!", "pcapparse",
    "!", "application/x-rtp,media=video,encoding-name=H264,payload=96,clock-rate=90000",
    "!", "rtpjitterbuffer", "latency=50",
    "!", "rtph264depay",
    "!", "h264parse", "config-interval=-1", "set-timestamps=true",
    "!", "mp4mux", "faststart=true",
    "!", "filesink", "location=output.mp4"
])

'''

subprocess.run([
    "gst-launch-1.0", "-e", "-v",
    "filesrc", "location=./my_converted.pcap",
    "!", "pcapparse",
    "!", "application/x-rtp,encoding-name=H264,payload=96",
    "!", "rtph264depay",
    "!", "h264parse",
    "!", "mp4mux",
    "!", "filesink", "location=output(1mbps).mp4"
])

print("(3) Displaying!")