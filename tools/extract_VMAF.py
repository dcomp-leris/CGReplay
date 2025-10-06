import subprocess

result = subprocess.run( 
    [
        "ffmpeg", "-i", "/home/alireza/mycg/CGReplay/tools/pcap_cache/my_2Mbps.mp4", 
        "-i", "/reference_resized.mp4",
        "-lavfi", "[0:v][1:v]libvmaf", "-f", "null", "-"
    ],

    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

output = result.stdout + result.stderr
print(output)  # Debug: print all output

score_found = False
for line in output.splitlines():
    if "VMAF score" in line:
        with open("./vmaf_score.txt", "w") as f:
            f.write(line + "\n")
        print(line)
        score_found = True
        break

if not score_found:
    print("No VMAF score found. Check above output for errors.")



