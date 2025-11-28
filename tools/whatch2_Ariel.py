import subprocess
# /home/alireza/mycg/CGReplay/player/logs/my.pcap
Source_PCAP = "../player/logs/my.pcap"
My_PCAP = "./pcap_cache/"+Source_PCAP.split("/")[-1]

# Step 1: Change permissions
subprocess.run(['sudo', 'chmod', '777', Source_PCAP])

#sudo_password = "844464"
#subprocess.run(['sudo', '-S', 'chmod', '777', '../player/logs/my.pcap'], input=f"{sudo_password}\n", text=True)

#print("(1) Access is done!")

# Step 2: Convert PCAPNG to PCAP
subprocess.run(['editcap', '-F', 'libpcap', Source_PCAP, My_PCAP])
print("(2) Converting happened!")

# Step 3: Run GStreamer pipeline

subprocess.run([
    'gst-launch-1.0', '-v',
    'filesrc', 'location=' + My_PCAP,
    '!', 'pcapparse',
    '!', 'application/x-rtp,encoding-name=H264,payload=96',
    '!', 'rtph264depay',
    '!', 'avdec_h264',
    '!', 'autovideosink'
])
print("(3) Displaying!")



subprocess.run([
    "gst-launch-1.0", "-e", "-v",
    "filesrc", "location=" + My_PCAP,
    "!", "pcapparse",
    "!", "application/x-rtp,encoding-name=H264,payload=96",
    "!", "rtph264depay",
    "!", "h264parse",
    "!", "mp4mux",
    "!", "filesink", "location=" + My_PCAP.replace(".pcap",".mp4")
])

print("(3) Displaying!")