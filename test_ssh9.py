import subprocess

cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no", "-i", "C:/Users/nicho/.ssh/id_ed25519", "-p", "22", "root@107.170.42.123",
    "export PYTHONPATH=/workspace && python3 /workspace/src/scanner.py 'do:chloe-storage/content-for-sale/STREAMVOD'"
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"STDOUT: {res.stdout}")
    print(f"STDERR: {res.stderr}")
    print(f"Return code: {res.returncode}")
except Exception as e:
    print(f"Exception: {e}")
