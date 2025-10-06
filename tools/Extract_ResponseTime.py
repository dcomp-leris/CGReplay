import pandas as pd
import numpy as np

# Params
csv_path = "/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss1_Fortnite.csv" #"./mypcap.csv"
player_ip = "10.0.0.2"
server_ip = "10.0.0.1"

# Load & prep
df = pd.read_csv(csv_path).sort_values("time").reset_index(drop=True)
df["_marker_bool"] = df["Marker"].astype(str).str.strip().str.lower().isin(["true","1","yes","y","t"])

times = df["time"].to_numpy()
srcs  = df["src"].astype(str).to_numpy()
mark  = df["_marker_bool"].to_numpy()

# Base: all player packets (src=player)
base_idx = np.where(srcs == player_ip)[0]
base_times = times[base_idx]

# Next: first strictly later server packet with Marker=True
next_idx = np.where((srcs == server_ip) & (mark == True))[0]
next_times = times[next_idx]

pos = np.searchsorted(next_times, base_times, side="right")

response_times = []
for i, p in zip(base_idx, pos):
    if p < len(next_idx):
        j = next_idx[p]
        response_times.append(float(times[j] - times[i]))


print("Response times (s):")
for v in response_times:
    print(v)


avg = float(np.mean(response_times)) if response_times else float("nan")
print("\nAverage (s):", avg, "No:", response_times.__len__())
