import os
import subprocess
import tempfile
import matplotlib.pyplot as plt
import numpy as np
'''
def compute_vmaf_per_frame(ref_folder, dst_folder):
    ref_images = sorted([f for f in os.listdir(ref_folder) if f.endswith(".png")])
    dst_images = sorted([f for f in os.listdir(dst_folder) if f.endswith(".png")])

    common_frames = sorted(set(ref_images).intersection(dst_images))
    missing_frames = sorted(set(ref_images) - set(dst_images))

    vmaf_scores = []
    frame_indices = []
    
    for frame_name in common_frames:
        ref_path = os.path.join(ref_folder, frame_name)
        dst_path = os.path.join(dst_folder, frame_name)

        with tempfile.NamedTemporaryFile(suffix=".mp4") as ref_tmp, tempfile.NamedTemporaryFile(suffix=".mp4") as dst_tmp:
            # Convert PNG to MP4 for both ref and dst (1-frame video)
            subprocess.run(["ffmpeg", "-y", "-i", ref_path, "-vf", "format=yuv420p", ref_tmp.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["ffmpeg", "-y", "-i", dst_path, "-vf", "format=yuv420p", dst_tmp.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Compute VMAF
            result = subprocess.run([
                "ffmpeg", "-i", ref_tmp.name, "-i", dst_tmp.name,
                "-lavfi", "libvmaf=model_path=/usr/share/model/vmaf_v0.6.1.pkl", "-f", "null", "-"
            ], capture_output=True, text=True)

            try:
                # Extract VMAF score from FFmpeg output
                lines = result.stderr.split('\n')
                for line in lines:
                    if "VMAF score" in line:
                        score = float(line.strip().split()[-1])
                        vmaf_scores.append(score)
                        frame_indices.append(int(frame_name.split('.')[0]))
                        break
            except Exception as e:
                print(f"Failed to compute VMAF for {frame_name}: {e}")

    return {
        "missing_frames": missing_frames,
        "vmaf_scores": vmaf_scores,
        "frame_indices": frame_indices
    }
'''

import json

def compute_vmaf_per_frame(ref_folder, dst_folder):
    ref_images = sorted([f for f in os.listdir(ref_folder) if f.lower().endswith(".png")])
    dst_images = sorted([f for f in os.listdir(dst_folder) if f.lower().endswith(".png")])

    print(f"Found {len(ref_images)} reference frames")
    print(f"Found {len(dst_images)} destination frames")

    ref_set = set(ref_images)
    dst_set = set(dst_images)

    common_frames = sorted(ref_set.intersection(dst_set))
    missing_frames = sorted(ref_set - dst_set)

    print(f"Common frames: {len(common_frames)}")
    print(f"Missing frames: {len(missing_frames)}")

    vmaf_scores = []
    frame_indices = []

    for frame_name in common_frames:
        ref_path = os.path.join(ref_folder, frame_name)
        dst_path = os.path.join(dst_folder, frame_name)

        with tempfile.NamedTemporaryFile(suffix=".mp4") as ref_tmp, tempfile.NamedTemporaryFile(suffix=".mp4") as dst_tmp, tempfile.NamedTemporaryFile(suffix=".json") as json_tmp:
            # Convert PNGs to 1-frame videos
            subprocess.run(["ffmpeg", "-y", "-i", ref_path, "-vf", "format=yuv420p", ref_tmp.name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["ffmpeg", "-y", "-i", dst_path, "-vf", "format=yuv420p", dst_tmp.name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Run FFmpeg with JSON VMAF output
            result = subprocess.run([
                "ffmpeg", "-y",
                "-i", dst_tmp.name,
                "-i", ref_tmp.name,
                #"-lavfi", f"libvmaf=model_path=/usr/share/model/vmaf_v0.6.1.pkl:log_path={json_tmp.name}:log_fmt=json",
                "-lavfi", f"libvmaf=log_path={json_tmp.name}:log_fmt=json",
                "-f", "null", "-"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[FFmpeg ERROR] VMAF failed on frame {frame_name}")
                print(result.stderr)
                continue

            try:
                with open(json_tmp.name) as f:
                    data = json.load(f)
                    score = data["pooled_metrics"]["vmaf"]["mean"]
                    vmaf_scores.append(score)
                    frame_indices.append(int(frame_name.split('.')[0]))
            except Exception as e:
                print(f"[Parse ERROR] Could not extract VMAF for {frame_name}: {e}")
                print(result.stderr)

    return {
        "missing_frames": missing_frames,
        "vmaf_scores": vmaf_scores,
        "frame_indices": frame_indices
    }


def plot_vmaf(frame_indices, scores, total_frames=120):
    all_indices = np.arange(1, total_frames + 1)
    vmaf_filled = np.zeros_like(all_indices, dtype=float)

    index_map = {idx: score for idx, score in zip(frame_indices, scores)}
    for i, idx in enumerate(all_indices):
        if idx in index_map:
            vmaf_filled[i] = index_map[idx]  # Real VMAF score
        else:
            vmaf_filled[i] = 0  # Missing

    plt.figure(figsize=(12, 6))
    plt.plot(all_indices, vmaf_filled, label="VMAF per frame")
    plt.xlabel("Frame Number")
    plt.ylabel("VMAF Score")
    plt.title("VMAF Score per Frame (missing frames = 0)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    print(f"Number of missing frames: {len([v for v in vmaf_filled if v == 0])}")
    print(f"Average VMAF: {np.mean([v for v in vmaf_filled if v > 0]):.2f}")

# Example usage
ref_folder = "/home/alireza/Downloads/acm_tomm_experiments/kaggle_reference_frames/Fortnite"
#dst_folder = "/home/alireza/Downloads/acm_tomm_experiments/2Mbit_Fortnite/received_frames"
#dst_folder = "/home/alireza/Downloads/acm_tomm_experiments/4Mbit_Fortnite/received_frames"
#dst_folder = "/home/alireza/Downloads/acm_tomm_experiments/6Mbit_Fortnite/received_frames"
dst_folder = "/home/alireza/Downloads/acm_tomm_experiments/8Mbit_Fortnite/received_frames"


result = compute_vmaf_per_frame(ref_folder, dst_folder)
plot_vmaf(result["frame_indices"], result["vmaf_scores"])
