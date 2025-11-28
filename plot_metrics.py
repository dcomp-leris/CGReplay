import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import matplotlib as mpl
import os
import sys
import argparse
import numpy as np

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

def add_missing_columns(df):
    """
    Add missing columns with default values to make the DataFrame compatible.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with all required columns
    """
    required_columns = {
        'frame_id': range(len(df)),  # Sequential frame IDs
        'received_fame_id': range(len(df)),  # Same as frame_id by default
        'my_gap': [1] * len(df),  # Default gap of 1
        'received_time': range(len(df)),  # Sequential time if not present
        'send_time': range(len(df)),  # Sequential time if not present
        'current_srv_fps': [30.0] * len(df),  # Default 30 FPS
        'received_fps': [30.0] * len(df),  # Default 30 FPS
        'current_cps': [5.0] * len(df),  # Default 5 CPS
        'received_cps': [5.0] * len(df),  # Default 5 CPS
        'current_srv_fps/received_fps': [1.0] * len(df),  # Default ratio of 1
        'received_cps/current_cps': [1.0] * len(df),  # Default ratio of 1
        'bitrate': [10368.0] * len(df)  # Default bitrate
    }
    
    # Only add missing columns (don't overwrite existing ones)
    added_columns = []
    for col, default_values in required_columns.items():
        if col not in df.columns:
            df[col] = default_values
            added_columns.append(col)
    
    if added_columns:
        print(f"Added missing columns: {added_columns}")
    else:
        print("All required columns already present")
    
    # Calculate ratio columns if base columns exist and ratio columns don't exist
    if ('current_srv_fps' in df.columns and 'received_fps' in df.columns and 
        'current_srv_fps/received_fps' not in df.columns):
        df['current_srv_fps/received_fps'] = df['current_srv_fps'] / df['received_fps'].replace(0, 1)
        print("Calculated current_srv_fps/received_fps ratio")
    
    if ('received_cps' in df.columns and 'current_cps' in df.columns and 
        'received_cps/current_cps' not in df.columns):
        df['received_cps/current_cps'] = df['received_cps'] / df['current_cps'].replace(0, 1)
        print("Calculated received_cps/current_cps ratio")
    
    return df

def detect_and_load_csv(file_path):
    """
    Detect if CSV has headers and load appropriately.
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        DataFrame with proper column names
    """
    # First, try to read a few lines to detect if there are headers
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()
    
    # Check if first line looks like headers (contains non-numeric data)
    first_line_parts = first_line.split(',')
    
    # If first line contains mostly numbers, it's likely data, not headers
    numeric_count = 0
    for part in first_line_parts:
        try:
            float(part.strip())
            numeric_count += 1
        except ValueError:
            pass
    
    has_headers = numeric_count < len(first_line_parts) * 0.8  # Less than 80% numeric = likely headers
    
    if has_headers:
        print("File appears to have headers")
        df = pd.read_csv(file_path)
    else:
        print("File appears to be headerless, using default column names")
        # Define the expected column names based on your data structure
        expected_columns = [
            'frame_id', 'received_fame_id', 'my_gap', 'received_time', 'send_time',
            'current_srv_fps', 'received_fps', 'current_cps', 'received_cps',
            'current_srv_fps/received_fps', 'received_cps/current_cps', 'bitrate'
        ]
        
        df = pd.read_csv(file_path, header=None)
        
        # Assign column names based on number of columns
        if len(df.columns) <= len(expected_columns):
            df.columns = expected_columns[:len(df.columns)]
        else:
            # If more columns than expected, use generic names for extras
            column_names = expected_columns + [f'extra_col_{i}' for i in range(len(df.columns) - len(expected_columns))]
            df.columns = column_names[:len(df.columns)]
    
    return df

def get_data_and_suffix():
    """
    Get data from file path or use mock data. Return data and filename suffix.
    
    Returns:
        tuple: (DataFrame, suffix_string)
    """
    parser = argparse.ArgumentParser(description='Plot cloud gaming metrics')
    parser.add_argument('--file', '-f', type=str, help='Path to CSV file containing log data')
    args = parser.parse_args()
    
    if args.file:
        try:
            if not os.path.exists(args.file):
                print(f"Error: File '{args.file}' not found. Using mock data instead.")
                return get_mock_data(), "_mock"
            
            df = detect_and_load_csv(args.file)
            print(f"Successfully loaded data from: {args.file}")
            print(f"Original columns: {list(df.columns)}")
            print(f"Data shape: {df.shape}")
            
            # Show sample of actual data
            print("Sample data:")
            print(df.head(2))
            
            # Add missing columns with default values
            df = add_missing_columns(df)
            
            print(f"Final columns: {list(df.columns)}")
            
            return df, ""
            
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}")
            print("Using mock data instead.")
            return get_mock_data(), "_mock"
    else:
        print("No file specified. Using mock data.")
        return get_mock_data(), "_mock"

def get_mock_data():
    """Return the mock data as a DataFrame"""
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
    
    return pd.read_csv(StringIO(log_data))

def smart_sample(dataframe, target_points=1000):
    """
    Intelligently sample dataframe to get approximately target_points while preserving trends.
    Uses multiple strategies based on data length.
    
    Args:
        dataframe: Pandas DataFrame to sample from
        target_points: Target number of points to return
    
    Returns:
        Sampled DataFrame
    """
    total_points = len(dataframe)
    
    # If dataset is already small enough, return as-is
    if total_points <= target_points:
        return dataframe.copy()
    
    # Calculate sampling strategy based on data size
    if total_points <= target_points * 2:
        # Light sampling - take every other point
        step = 2
        return dataframe.iloc[::step].copy()
    
    elif total_points <= target_points * 10:
        # Medium sampling - uniform sampling
        step = max(1, total_points // target_points)
        return dataframe.iloc[::step].copy()
    
    else:
        # Heavy sampling for very large datasets
        # Use a combination of uniform sampling and key point preservation
        step = max(1, total_points // target_points)
        
        # Take uniform samples
        uniform_sample = dataframe.iloc[::step].copy()
        
        # If still too many points, take every other point from the sample
        if len(uniform_sample) > target_points:
            final_step = max(1, len(uniform_sample) // target_points)
            uniform_sample = uniform_sample.iloc[::final_step].copy()
        
        return uniform_sample

def get_adaptive_sampling_levels(df_length):
    """
    Get adaptive sampling levels based on dataframe length.
    
    Args:
        df_length: Length of the dataframe
    
    Returns:
        Dictionary with sampling levels and their target point counts
    """
    if df_length <= 100:
        return {
            "Light (50 pts)": 50,
            "Medium (25 pts)": 25,
            "Heavy (10 pts)": 10,
            "All points": df_length
        }
    elif df_length <= 1000:
        return {
            "Light (200 pts)": 200,
            "Medium (100 pts)": 100,
            "Heavy (50 pts)": 50,
            "All points": df_length
        }
    elif df_length <= 10000:
        return {
            "Light (500 pts)": 500,
            "Medium (200 pts)": 200,
            "Heavy (100 pts)": 100,
            "All points": df_length
        }
    else:
        return {
            "Light (1000 pts)": 1000,
            "Medium (500 pts)": 500,
            "Heavy (200 pts)": 200,
            "Ultra (100 pts)": 100
        }

def preprocess_data(df):
    """
    Preprocess the data to make it more suitable for plotting.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Processed DataFrame
    """
    df_processed = df.copy()
    
    # Normalize time to start from 0 if received_time values are very large
    if 'received_time' in df_processed.columns:
        min_time = df_processed['received_time'].min()
        df_processed['received_time_normalized'] = df_processed['received_time'] - min_time
        print(f"Normalized received_time: original range {df_processed['received_time'].min():.2f} to {df_processed['received_time'].max():.2f}")
        print(f"Normalized to: 0.00 to {df_processed['received_time_normalized'].max():.2f} seconds")
        
        # Use normalized time for plotting
        df_processed['plot_time'] = df_processed['received_time_normalized']
    else:
        # Use row index as time if no time column
        df_processed['plot_time'] = range(len(df_processed))
    
    # Clean up any invalid values
    numeric_columns = ['current_srv_fps', 'received_fps', 'current_cps', 'received_cps', 'bitrate']
    for col in numeric_columns:
        if col in df_processed.columns:
            # Replace any non-finite values with median
            if df_processed[col].isnull().any() or not df_processed[col].replace([float('inf'), -float('inf')], float('nan')).notna().all():
                median_val = df_processed[col].replace([float('inf'), -float('inf')], float('nan')).median()
                df_processed[col] = df_processed[col].replace([float('inf'), -float('inf')], median_val).fillna(median_val)
                print(f"Cleaned invalid values in {col}")
    
    return df_processed

def main():
    # Get data and determine suffix
    df, suffix = get_data_and_suffix()
    
    # Preprocess the data
    df = preprocess_data(df)
    
    print(f"Dataset contains {len(df)} data points")
    if 'plot_time' in df.columns:
        print(f"Time range: {df['plot_time'].min():.2f} to {df['plot_time'].max():.2f} seconds")
    
    # Show some statistics
    if 'current_srv_fps' in df.columns:
        print(f"Server FPS range: {df['current_srv_fps'].min():.2f} to {df['current_srv_fps'].max():.2f}")
    if 'received_fps' in df.columns:
        print(f"Client FPS range: {df['received_fps'].min():.2f} to {df['received_fps'].max():.2f}")
    
    # Get adaptive sampling levels based on data length
    sampling_levels = get_adaptive_sampling_levels(len(df))
    print(f"Using adaptive sampling levels: {list(sampling_levels.keys())}")
    
    # Plot with adaptive sampling levels
    plt.figure(figsize=(15, 10))

    for i, (level_name, target_points) in enumerate(sampling_levels.items()):
        # Sample the data
        if level_name == "All points":
            sampled_df = df
        else:
            sampled_df = smart_sample(df, target_points)
        
        # Create subplot
        plt.subplot(2, 2, i+1)
        
        # Plot the sampled data using scatter plots (points only)
        plt.scatter(sampled_df["plot_time"], sampled_df["current_srv_fps"], 
                   label=f"Server FPS", marker='o', s=20, alpha=0.7)
        plt.scatter(sampled_df["plot_time"], sampled_df["received_fps"], 
                   label=f"Client FPS", marker='x', s=20, alpha=0.7)
        
        plt.xlabel("Time (seconds)")
        plt.ylabel("Frames Per Second (FPS)")
        plt.title(f"FPS Over Time ({level_name})")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add text showing actual point count
        actual_points = len(sampled_df)
        plt.text(0.02, 0.98, f"Points: {actual_points}", transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle("Cloud Gaming Server vs Client FPS Over Time with Adaptive Sampling", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(output_dir, f"cloud_gaming_fps_plot{suffix}.png"), dpi=150, bbox_inches='tight')
    plt.close()

    # Create a single plot with multiple sampling levels for comparison
    plt.figure(figsize=(14, 8))

    colors = ['blue', 'green', 'red', 'orange', 'purple']
    for i, (level_name, target_points) in enumerate(sampling_levels.items()):
        if level_name == "All points":
            sampled_df = df
            plt.scatter(sampled_df["plot_time"], sampled_df["current_srv_fps"], 
                       label=f"Server FPS (all {len(sampled_df)} pts)", 
                       s=15, color=colors[i % len(colors)], alpha=0.6)
        else:
            sampled_df = smart_sample(df, target_points)
            plt.scatter(sampled_df["plot_time"], sampled_df["current_srv_fps"], 
                       label=f"Server FPS ({len(sampled_df)} pts)", 
                       marker='o', s=25, color=colors[i % len(colors)], alpha=0.7)

    plt.xlabel("Time (seconds)")
    plt.ylabel("Frames Per Second (FPS)")
    plt.title("Server FPS Over Time with Different Sampling Levels")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"cloud_gaming_fps_sampling_comparison{suffix}.png"), dpi=150, bbox_inches='tight')
    plt.close()

    # Plot 1: Bitrate over time with adaptive sampling
    plt.figure(figsize=(15, 10))
    for i, (level_name, target_points) in enumerate(sampling_levels.items()):
        sampled_df = df if level_name == "All points" else smart_sample(df, target_points)
        
        plt.subplot(2, 2, i + 1)
        plt.scatter(sampled_df["plot_time"], sampled_df["bitrate"], 
                   label=f"Bitrate", marker='s', s=20, alpha=0.7)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Bitrate (bps)")
        plt.title(f"Bitrate Over Time ({level_name})")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add point count
        actual_points = len(sampled_df)
        plt.text(0.02, 0.98, f"Points: {actual_points}", transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle("Bitrate Over Time with Adaptive Sampling", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(output_dir, f"bitrate_sampling_plot{suffix}.png"), dpi=150, bbox_inches='tight')
    plt.close()

    # Plot 2: Server vs Client CPS
    plt.figure(figsize=(15, 10))
    for i, (level_name, target_points) in enumerate(sampling_levels.items()):
        sampled_df = df if level_name == "All points" else smart_sample(df, target_points)
        
        plt.subplot(2, 2, i + 1)
        plt.scatter(sampled_df["plot_time"], sampled_df["current_cps"], 
                   label=f"Server CPS", marker='^', s=20, alpha=0.7)
        plt.scatter(sampled_df["plot_time"], sampled_df["received_cps"], 
                   label=f"Client CPS", marker='v', s=20, alpha=0.7)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Cycles Per Second (CPS)")
        plt.title(f"CPS Over Time ({level_name})")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add point count
        actual_points = len(sampled_df)
        plt.text(0.02, 0.98, f"Points: {actual_points}", transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle("Cloud Gaming Server vs Client CPS Over Time", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(output_dir, f"cloud_gaming_cps_plot{suffix}.png"), dpi=150, bbox_inches='tight')
    plt.close()

    # Plot 3: Ratios over time
    plt.figure(figsize=(15, 10))
    for i, (level_name, target_points) in enumerate(sampling_levels.items()):
        sampled_df = df if level_name == "All points" else smart_sample(df, target_points)

        plt.subplot(2, 2, i + 1)
        plt.scatter(sampled_df["plot_time"], sampled_df["current_srv_fps/received_fps"], 
                   label="FPS Ratio", marker='o', s=20, alpha=0.7)
        plt.scatter(sampled_df["plot_time"], sampled_df["received_cps/current_cps"], 
                   label="CPS Ratio", marker='x', s=20, alpha=0.7)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Ratio")
        plt.title(f"Server/Client Ratios ({level_name})")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add point count
        actual_points = len(sampled_df)
        plt.text(0.02, 0.98, f"Points: {actual_points}", transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle("Server/Client FPS and CPS Ratios Over Time", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(output_dir, f"fps_cps_ratio_plot{suffix}.png"), dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\nAll plots saved to '{output_dir}' directory with suffix '{suffix}'")
    print("Generated files:")
    plot_files = [
        f"cloud_gaming_fps_plot{suffix}.png",
        f"cloud_gaming_fps_sampling_comparison{suffix}.png", 
        f"bitrate_sampling_plot{suffix}.png",
        f"cloud_gaming_cps_plot{suffix}.png",
        f"fps_cps_ratio_plot{suffix}.png"
    ]
    for file in plot_files:
        print(f"  - {file}")
    
    print(f"\nSampling summary:")
    for level_name, target_points in sampling_levels.items():
        if level_name == "All points":
            actual_points = len(df)
        else:
            actual_points = len(smart_sample(df, target_points))
        print(f"  - {level_name}: {actual_points} points")

if __name__ == "__main__":
    main()