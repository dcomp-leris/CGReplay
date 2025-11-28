import os
import subprocess
import tempfile
import matplotlib.pyplot as plt
import numpy as np
import json

def make_mp4_from_png(png_path, mp4_path):
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "1",
        "-i", png_path,
        "-frames:v", "1",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        mp4_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def compute_vmaf_per_frame(ref_folder, dst_folder):
    ref_images = sorted([f for f in os.listdir(ref_folder) if f.lower().endswith(".png")])
    dst_images = sorted([f for f in os.listdir(dst_folder) if f.lower().endswith(".png")])

    ref_set = set(ref_images)
    dst_set = set(dst_images)

    common_frames = sorted(ref_set.intersection(dst_set))
    missing_frames = sorted(ref_set - dst_set)

    print(f"\nComparing → {dst_folder}")
    print(f"  ✅ Common frames: {len(common_frames)}")
    print(f"  ❌ Missing frames: {len(missing_frames)}")

    vmaf_scores = []
    frame_indices = []

    for frame_name in common_frames:
        ref_path = os.path.join(ref_folder, frame_name)
        dst_path = os.path.join(dst_folder, frame_name)

        with tempfile.NamedTemporaryFile(suffix=".mp4") as ref_tmp, \
             tempfile.NamedTemporaryFile(suffix=".mp4") as dst_tmp, \
             tempfile.NamedTemporaryFile(suffix=".json") as json_tmp:

            # ✅ Proper MP4 creation
            make_mp4_from_png(ref_path, ref_tmp.name)
            make_mp4_from_png(dst_path, dst_tmp.name)

            # ✅ Reliable VMAF command (NO model_path)
            cmd = [
                "ffmpeg", "-y",
                "-i", dst_tmp.name,
                "-i", ref_tmp.name,
                "-lavfi", f"libvmaf=log_path={json_tmp.name}:log_fmt=json",
                "-f", "null", "-"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[FFmpeg ERROR] Frame {frame_name}")
                print(result.stderr)
                continue

            try:
                with open(json_tmp.name) as f:
                    data = json.load(f)
                    score = data["pooled_metrics"]["vmaf"]["mean"]
                    vmaf_scores.append(score)
                    frame_indices.append(int(frame_name.split('.')[0]))
            except Exception as e:
                print(f"[Parse ERROR] {frame_name}: {e}")

    return {
        "vmaf_scores": vmaf_scores,
        "frame_indices": frame_indices,
        "missing_count": len(missing_frames)
    }

def compare_multiple_destinations(ref_folder, dst_folders, labels):
    all_results = []

    for dst_folder in dst_folders:
        result = compute_vmaf_per_frame(ref_folder, dst_folder)
        all_results.append(result)

    total_frames = 120
    frame_numbers = np.arange(1, total_frames + 1)

    plt.figure(figsize=(14, 7))

    for result, label in zip(all_results, labels):
        vmaf_line = np.zeros_like(frame_numbers, dtype=float)
        index_map = {idx: score for idx, score in zip(result["frame_indices"], result["vmaf_scores"])}

        for i, idx in enumerate(frame_numbers):
            if idx in index_map:
                vmaf_line[i] = index_map[idx]
            else:
                vmaf_line[i] = 0  # missing frame

        valid_scores = [v for v in vmaf_line if v > 0]
        avg_vmaf = np.mean(valid_scores) if valid_scores else 0

        plt.plot(frame_numbers, vmaf_line, label=f"{label} (avg={avg_vmaf:.2f})")

    plt.xlabel("Frame Number")
    plt.ylabel("VMAF Score")
    plt.title("VMAF Comparison of 4 Destination Folders")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


# === USAGE ===

ref_folder = "/home/alireza/Downloads/acm_tomm_experiments/kaggle_reference_frames/Fortnite"
dst_folders = [
    "/home/alireza/Downloads/acm_tomm_experiments/2Mbit_Fortnite/received_frames",
    "/home/alireza/Downloads/acm_tomm_experiments/4Mbit_Fortnite/received_frames",
    "/home/alireza/Downloads/acm_tomm_experiments/6Mbit_Fortnite/received_frames",
    "/home/alireza/Downloads/acm_tomm_experiments/8Mbit_Fortnite/received_frames"
]
labels = ["BW: 2Mbps", "BW: 4Mbps", "BW: 6Mbps", "BW: 8Mbps"]

compare_multiple_destinations(ref_folder, dst_folders, labels)

