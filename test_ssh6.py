import subprocess

cmd_str = "ssh -o StrictHostKeyChecking=no -i C:/Users/nicho/.ssh/id_ed25519 -p 22 root@107.170.42.123 \"export PYTHONPATH=/workspace && pkill -f 'rclone serve' ; python3 /workspace/src/scanner.py 'do:chloe-storage/content-for-sale/STREAMVOD'\""
try:
    process = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        print(f"POD: {line.strip()}")
    process.wait()
    print(f"Return code: {process.returncode}")
except Exception as e:
    print(f"Exception: {e}")
