import cv2
import os
import glob
import sys
import yaml

# Game folders mapping
GAME_PATHS = {
    "Forza": {
        "src": "../Sources/Forza",
        "dst": "../server/Forza"
    },
    "Fortnite": {
        "src": "../Sources/Fortnite",
        "dst": "../server/Fortnite"
    },
    "Kombat": {
        "src": "../Sources/Kombat",
        "dst": "../server/Kombat"
    }
}

if len(sys.argv) != 2 or sys.argv[1] not in GAME_PATHS:
    print("Usage: python3 Frame_Resize.py <GameName>")
    print("GameName must be one of: Forza, Fortnite, Kombat")
    sys.exit(1)

game_name = sys.argv[1]
src_folder = GAME_PATHS[game_name]["src"]
dst_folder = GAME_PATHS[game_name]["dst"]

with open("../config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

resolution_width = config["encoding"]["resolution"]["width"]
resolution_height = config["encoding"]["resolution"]["height"]
target_size = (resolution_width, resolution_height)

os.makedirs(dst_folder, exist_ok=True)

for src_path in glob.glob(os.path.join(src_folder, "*.png")):
    img = cv2.imread(src_path)
    if img is None:
        continue
    resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
    fname = os.path.basename(src_path)
    dst_path = os.path.join(dst_folder, fname)
    cv2.imwrite(dst_path, resized)