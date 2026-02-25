import subprocess
import json

with open("config.json", "r") as f:
    config = json.load(f)

host = config["do_droplet_ip"]
ssh_key = config.get("ssh_key", "~/.ssh/id_ed25519")

extract_cmd = (
    f'python3 -c "'
    f'import sys; sys.path.insert(0, \\"/workspace\\"); '
    f'from src.scanner import extract_random_thumbnail; '
    f'r = extract_random_thumbnail(\\"do:chloe-storage/content-for-sale/STREAMVOD/April 3rd Stream pt1.mp4\\"); '
    f'print(\\"SUCCESS:\\" + r if r else \\"FAILED\\")'
    f'"'
)

ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-i", ssh_key, f"root@{host}", extract_cmd]
print("Running:", " ".join(ssh_cmd))
result = subprocess.run(ssh_cmd, capture_output=True, text=True)

print("--- STDOUT ---")
print(result.stdout)
print("--- STDERR ---")
print(result.stderr)
