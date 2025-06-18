import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import matplotlib as mpl
import os

# Create folder if it does not exist
output_dir = "visualizations"
os.makedirs(output_dir, exist_ok=True)

# Set better default styles
plt.style.use('ggplot')
mpl.rcParams['font.family'] = 'DejaVu Sans'
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['axes.titlesize'] = 16
mpl.rcParams['figure.titlesize'] = 20

# Raw CSV input as string
log_data = """frame_id,received_fame_id,my_gap,received_time,send_time,current_srv_fps,received_fps,current_cps,received_cps,current_srv_fps/received_fps,received_cps/current_cps,bitrate
11,10,1,88397.694373267,88397.685364364,14.808666475931227,14.089983084454888,1.5042226809851091,0.0,1.0510066894451595,0.0,7200.0 
14,13,1,88397.890200063,88397.877960716,15.116206441627117,15.774865161809743,7.558459582813173,1.3832254356390294,0.9582463169462007,0.18300361607863605,10368.0 
18,17,1,88398.157111843,88398.143674326,14.3627109322702,15.64347885820171,3.7465562592065345,5.192637423781177,0.9181276787892984,1.3859760976553175,10368.0 
23,22,1,88398.496013647,88398.486555542,14.316030730944735,14.222517140346236,14.313835859552345,3.7634500341260084,1.006575037996138,0.26292393395125235,10368.0 
26,25,1,88398.69274255,88398.683579614,15.454055925237789,15.474498892255687,5.083137173801757,2.9165784511222372,0.9986789254269081,0.573775279202407,10368.0 
31,30,1,88399.021370922,88399.010187988,14.697476908429348,14.092780297514441,3.0429508990162324,5.075078735739923,1.0429082550177524,1.6678148626652718,10368.0 
35,34,1,88399.287400142,88399.27536735,15.149568430162132,14.151812864769628,4.993099312077632,3.061545752079029,1.0705037280330618,0.613155389213582,10368.0 
39,38,1,88399.557559726,88399.543771248,14.627564651340055,14.601712448457494,3.7015159158062483,3.7715166058949148,1.0017704911649108,1.0189113573143773,10368.0 
43,42,1,88399.824317897,88399.81626766,15.123460901839584,15.043508687048709,15.126517664929272,3.7252662485245507,1.0053147318523974,0.24627388345709963,10368.0 
47,46,1,88400.093654689,88400.084930341,14.490223504283982,13.75323916310567,3.7128236085904476,3.670265101070502,1.0535862375719707,0.9885374281122655,10368.0 
"""

# Read into a DataFrame
df = pd.read_csv(StringIO(log_data))

# Function to sample data based on percentage
def sample_by_percentage(dataframe, percentage=10):
    """
    Sample dataframe rows based on a percentage of total points.
    
    Args:
        dataframe: Pandas DataFrame to sample from
        percentage: Percentage of points to sample (e.g., 10 means every 10%)
    
    Returns:
        Sampled DataFrame
    """
    total_points = len(dataframe)
    # Calculate N (number of points that represents the given percentage)
    n = max(1, int(total_points * percentage / 100))
    # Sample every N points
    return dataframe.iloc[::n]

# Plot with different sampling percentages
percentages = [10, 20, 50, 100]  # 100% means all points
plt.figure(figsize=(15, 10))

for i, percentage in enumerate(percentages):
    # Skip 100% as a special case (all points)
    if percentage == 100:
        sampled_df = df
    else:
        sampled_df = sample_by_percentage(df, percentage)
    
    # Create subplot
    plt.subplot(2, 2, i+1)
    
    # Plot the sampled data
    plt.plot(sampled_df["received_time"], sampled_df["current_srv_fps"], 
             label=f"Server FPS (sampled at {percentage}%)", marker='o')
    plt.plot(sampled_df["received_time"], sampled_df["received_fps"], 
             label=f"Client FPS (sampled at {percentage}%)", marker='x')
    
    plt.xlabel("Received Time (s)")
    plt.ylabel("Frames Per Second (FPS)")
    plt.title(f"FPS Over Time (Sampled at {percentage}%)")
    plt.legend()
    plt.grid(True)

plt.suptitle("Cloud Gaming Server vs Client FPS Over Time with Different Sampling Rates", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for the suptitle
plt.savefig(os.path.join(output_dir, "cloud_gaming_fps_plot.png"))

# Also create a single plot with all sampling rates for comparison
plt.figure(figsize=(12, 6))

for percentage in percentages:
    # Skip 100% as a special case (all points)
    if percentage == 100:
        sampled_df = df
        plt.plot(sampled_df["received_time"], sampled_df["current_srv_fps"], 
                 label=f"Server FPS (all points)", linestyle='-')
    else:
        sampled_df = sample_by_percentage(df, percentage)
        plt.plot(sampled_df["received_time"], sampled_df["current_srv_fps"], 
                 label=f"Server FPS ({percentage}%)", marker='o')


# Plot 1: Bitrate over time with different sampling
plt.figure(figsize=(15, 10))
for i, percentage in enumerate(percentages):
    sampled_df = df if percentage == 100 else sample_by_percentage(df, percentage)
    
    plt.subplot(2, 2, i + 1)
    plt.plot(sampled_df["received_time"], sampled_df["bitrate"], label=f"Bitrate ({percentage}%)", marker='s')
    plt.xlabel("Received Time (s)")
    plt.ylabel("Bitrate (bps)")
    plt.title(f"Bitrate Over Time (Sampled at {percentage}%)")
    plt.legend()
    plt.grid(True)

plt.suptitle("Bitrate Over Time with Different Sampling Rates", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(os.path.join(output_dir, "bitrate_sampling_plot.png"))


# Plot 2: Server vs Client CPS
plt.figure(figsize=(15, 10))
for i, percentage in enumerate(percentages):
    sampled_df = df if percentage == 100 else sample_by_percentage(df, percentage)
    
    plt.subplot(2, 2, i + 1)
    plt.plot(sampled_df["received_time"], sampled_df["current_cps"], label=f"Server CPS ({percentage}%)", marker='^')
    plt.plot(sampled_df["received_time"], sampled_df["received_cps"], label=f"Client CPS ({percentage}%)", marker='v')
    plt.xlabel("Received Time (s)")
    plt.ylabel("Cycles Per Second (CPS)")
    plt.title(f"CPS Over Time (Sampled at {percentage}%)")
    plt.legend()
    plt.grid(True)

plt.suptitle("Cloud Gaming Server vs Client CPS Over Time", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(os.path.join(output_dir, "cloud_gaming_cps_plot.png"))

# Plot 3: Ratios over time
plt.figure(figsize=(15, 10))
for i, percentage in enumerate(percentages):
    sampled_df = df if percentage == 100 else sample_by_percentage(df, percentage)

    plt.subplot(2, 2, i + 1)
    plt.plot(sampled_df["received_time"], sampled_df["current_srv_fps/received_fps"], 
             label="FPS Ratio", marker='o')
    plt.plot(sampled_df["received_time"], sampled_df["received_cps/current_cps"], 
             label="CPS Ratio", marker='x')
    plt.xlabel("Received Time (s)")
    plt.ylabel("Ratio")
    plt.title(f"Server/Client Ratios (Sampled at {percentage}%)")
    plt.legend()
    plt.grid(True)

plt.suptitle("Server/Client FPS and CPS Ratios Over Time", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(os.path.join(output_dir, "fps_cps_ratio_plot.png"))

plt.xlabel("Received Time (s)")
plt.ylabel("Frames Per Second (FPS)")
plt.title("Server FPS Over Time with Different Sampling Rates")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cloud_gaming_fps_sampling_comparison.png"))
