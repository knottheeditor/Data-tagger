import subprocess

cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
    "-i", "C:/Users/nicho/.ssh/id_ed25519", "-p", "22", "root@107.170.42.123",
    "export PYTHONPATH=/workspace && pkill -f 'rclone serve' || true && python3 /workspace/src/scanner.py 'do:chloe-storage/content-for-sale/STREAMVOD'"
]

try:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        print(f"POD: {line.strip()}")
    process.wait()
    print(f"Return code: {process.returncode}")
except Exception as e:
    print(f"Exception: {e}")
