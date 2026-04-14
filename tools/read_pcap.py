from scapy.all import *
from scapy.layers.inet import IP, UDP
from scapy.layers.rtp import RTP
import csv

PCAP_FILE = "/home/alireza/mycg/CGReplay/Experiment/logs/FreeKombat_higher Quality/player_logs/my.pcap"
SRC_IP = "10.0.0.1"
SRC_PORT = 5000
DST_IP = "10.0.0.2"
DST_PORT = 5002
CSV_FILE = "/home/alireza/mycg/CGReplay/Experiment/logs/FreeKombat_higher Quality/player_logs/rtp_features.csv"

# Read packets
packets = rdpcap(PCAP_FILE)

# Filter UDP packets from SRC to DST
filtered = []
for pkt in packets:
    if IP in pkt and UDP in pkt:
        if (pkt[IP].src == SRC_IP and pkt[IP].dst == DST_IP and
            pkt[UDP].sport == SRC_PORT and pkt[UDP].dport == DST_PORT):
            filtered.append(pkt)

# Decode RTP
rtp_packets = []
for pkt in filtered:
    try:
        rtp = RTP(pkt[UDP].payload.load)
        rtp_packets.append({
            "pkt": pkt,
            "rtp": rtp,
            "size": len(pkt),
            "time": pkt.time
        })
    except Exception:
        continue

# Extract RTP frames (packets with marker=True)
rows = []
prev_marker_idx = None
for idx, entry in enumerate(rtp_packets):
    rtp = entry["rtp"]
    if rtp.marker == 1:
        # Find packets belonging to this frame
        if prev_marker_idx is not None:
            frame_packets = rtp_packets[prev_marker_idx+1:idx+1]
            sizes = [p["size"] for p in frame_packets]
            seqs = [p["rtp"].sequence for p in frame_packets]
            times = [p["time"] for p in frame_packets]
            # Features
            max_ps = max(sizes[:-1]) if len(sizes) > 1 else 0
            min_ps = sizes[-1] if sizes else 0
            num_pkts = seqs[-1] - seqs[0] + 1 if len(seqs) > 1 else 1
            frame_size = sum(sizes)
            ifi = (entry["time"] - rtp_packets[prev_marker_idx]["time"]) * 1e9 if prev_marker_idx is not None else 0
            seq_num = rtp.sequence
            timestamp = rtp.timestamp
            # RTP FPS
            rtp_fps = 0
            if prev_marker_idx is not None:
                ts_diff = rtp.timestamp - rtp_packets[prev_marker_idx]["rtp"].timestamp
                rtp_fps = 90000 / ts_diff if ts_diff != 0 else 0  # RTP default clock rate for video is 90000
            rows.append([max_ps, min_ps, num_pkts, frame_size, ifi, seq_num, timestamp, rtp_fps])
        else:
            # First frame, set defaults
            rows.append([0, 0, 0, 0, 0, rtp.sequence, rtp.timestamp, 0])
        prev_marker_idx = idx

# Write to CSV
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Max PS", "Min PS", "Number of Packets", "Frame Size (Byte)", "IFI (ns)", "SEQ Number", "Timestamp", "RTP FPS"])
    writer.writerows(rows)

print(f"Saved features to {CSV_FILE}")