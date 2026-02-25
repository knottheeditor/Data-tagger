import subprocess

cmd1 = [
    "ssh", "-o", "StrictHostKeyChecking=no",
    "-i", "C:/Users/nicho/.ssh/id_ed25519", "-p", "22", "root@107.170.42.123",
    "pkill -f 'rclone serve' || true"
]

cmd2 = [
    "ssh", "-o", "StrictHostKeyChecking=no",
    "-i", "C:/Users/nicho/.ssh/id_ed25519", "-p", "22", "root@107.170.42.123",
    "pkill -f \"rclone serve\" || true"
]

print("Test 1:")
try:
    print(subprocess.run(cmd1, capture_output=True, text=True).returncode)
except Exception as e:
    print(e)
    
print("Test 2:")
try:
    print(subprocess.run(cmd2, capture_output=True, text=True).returncode)
except Exception as e:
    print(e)
