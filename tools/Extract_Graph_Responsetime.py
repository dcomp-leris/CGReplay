#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

# ===================== USER INPUTS =====================
CSV_PATHS = [
    "/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss0_Fortnite.csv",
    "/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss1_Fortnite.csv",
    #"/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss0_Forza.csv",
    #"/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss1_Forza.csv",
    #"/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss0_Kombat.csv",
    #"/home/alireza/mycg/CGReplay/tools/MyPCAP/4Mbit_Loss1_Kombat.csv",
]

player_ip = "10.0.0.2"
server_ip = "10.0.0.1"

# Output artifacts
SUMMARY_CSV = "./response_times_summary.csv"
FIG_LINE = "./response_times_line_overlay.png"
# ======================================================


def compute_response_times_from_csv(csv_path: str,
                                    player_ip: str,
                                    server_ip: str) -> List[float]:
    """
    Implements:
    For each packet where src==player_ip, subtract its 'time' from the first strictly later
    packet where src==server_ip and Marker==True.
    Returns list of response-time deltas (in seconds).
    """
    df = pd.read_csv(csv_path).sort_values("time").reset_index(drop=True)

    # Normalize Marker to boolean
    marker = df["Marker"].astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "t"])
    times = df["time"].to_numpy()
    srcs  = df["src"].astype(str).to_numpy()
    base_idx = np.where(srcs == player_ip)[0]  # player packets
    next_idx = np.where((srcs == server_ip) & (marker.values))[0]  # server packets with Marker=True

    if len(base_idx) == 0 or len(next_idx) == 0:
        return []

    base_times = times[base_idx]
    next_times = times[next_idx]
    # find first strictly later server/Marker=True for each player packet
    pos = np.searchsorted(next_times, base_times, side="right")

    rts = []
    for i, p in zip(base_idx, pos):
        if p < len(next_idx):
            j = next_idx[p]
            rts.append(float(times[j] - times[i]))
    return rts


def nice_label(path: str) -> str:
    """Make a short label from filename."""
    base = os.path.basename(path)
    return os.path.splitext(base)[0]


def summarize(series: List[float]) -> Dict[str, float]:
    """Compute summary stats for a list of floats."""
    if not series:
        return {"count": 0, "avg": float("nan"), "median": float("nan"),
                "p10": float("nan"), "p90": float("nan")}
    arr = np.asarray(series, dtype=float)
    return {
        "count": int(arr.size),
        "avg": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
    }


def main():
    # Compute response times for each CSV
    all_series: Dict[str, List[float]] = {}
    for path in CSV_PATHS:
        label = nice_label(path)
        try:
            rts = compute_response_times_from_csv(path, player_ip, server_ip)
        except Exception as e:
            print(f"[ERROR] Processing {path}: {e}")
            rts = []
        all_series[label] = rts
        print(f"{label}: {len(rts)} response times; "
              f"avg={np.mean(rts) if rts else float('nan'):.6f} s")

    # Build and save summary table
    rows = []
    for label, series in all_series.items():
        s = summarize(series)
        rows.append({
            "name": label,
            "count": s["count"],
            "avg_s": s["avg"],
            "median_s": s["median"],
            "p10_s": s["p10"],
            "p90_s": s["p90"],
        })
    summary_df = pd.DataFrame(rows).sort_values("name")
    summary_df.to_csv(SUMMARY_CSV, index=False)
    print(f"\nSaved summary → {SUMMARY_CSV}")
    print(summary_df.to_string(index=False))

    # Plot overlay line chart (index on x-axis, response time on y-axis)
    # Use distinct colors + linestyles + markers for readability.
    # (You asked for different patterns & colors.)
    plt.figure(figsize=(11, 6))

    # Some varied styles
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]
    linestyles = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1))]
    markers = ["o", "s", "D", "^", "v", "x"]

    for idx, (label, series) in enumerate(all_series.items()):
        if not series:
            continue
        y = np.asarray(series, dtype=float)
        x = np.arange(1, len(y) + 1, dtype=int)
        plt.plot(
            x, y,
            label=f"{label} (n={len(y)}, avg={np.mean(y):.4f}s)",
            color=colors[idx % len(colors)],
            linestyle=linestyles[idx % len(linestyles)],
            linewidth=1.8,
            marker=markers[idx % len(markers)],
            markersize=3.5,
            alpha=0.9,
        )

    plt.title("Player→Server Response Times")
    plt.xlabel("Match index (per trace)")
    plt.ylabel("Response time (s)")
    plt.grid(True, linestyle=":", alpha=0.35)
    plt.legend(loc="best", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG_LINE, dpi=150)
    print(f"Saved line chart → {FIG_LINE}")

    # If you want to show it interactively:
    # plt.show()


if __name__ == "__main__":
    main()
