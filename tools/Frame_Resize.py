import cv2
import os
import glob, yaml


def load_config(file_path="config.txt"):
    """Reads the config.txt file and returns a dictionary of settings."""
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines and comments
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=")
                key = key.strip()
                value = value.strip()
                # Parse resolution into a tuple
                if key == "resolution":
                    value = tuple(map(int, value.split(",")))
                elif key in ["fps", "bitrate", "player_port", "my_test_port", "cg_server_port"]:
                    value = int(value)  # Convert numeric values
                config[key] = value
    return config

#if __name__ == "__main__":
    
with open("../config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

resolution_width = config["encoding"]["resolution"]["width"]    # Width 
resolution_height = config["encoding"]["resolution"]["height"]  # Height

src_folder = "/home/alireza/mycg/CGReplay/Sources/Kombat"
dst_folder = "/home/alireza/mycg/CGReplay/server/Kombat"
target_size = (resolution_width, resolution_height)  # (width, height)

os.makedirs(dst_folder, exist_ok=True)

for src_path in glob.glob(os.path.join(src_folder, "*.png")):
    img = cv2.imread(src_path)
    if img is None:
        continue
    resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
    fname = os.path.basename(src_path)
    dst_path = os.path.join(dst_folder, fname)
    cv2.imwrite(dst_path, resized)