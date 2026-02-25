import subprocess

cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
    "-i", "C:/Users/nicho/.ssh/id_ed25519", "-p", "22", "root@107.170.42.123",
    "export PYTHONPATH=/workspace && pkill -f 'rclone serve' || true && python3 /workspace/src/scanner.py 'do:chloe-storage/content-for-sale/STREAMVOD'"
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Stdout: {res.stdout}")
    print(f"Stderr: {res.stderr}")
    print(f"Return code: {res.returncode}")
except Exception as e:
    print(f"Exception: {e}")
