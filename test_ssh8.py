import subprocess

cmd1 = ["ssh", "-o", "StrictHostKeyChecking=no", "-i", "C:/Users/nicho/.ssh/id_ed25519", "-p", "22", "root@107.170.42.123", "echo 'hello'"]

try:
    print(subprocess.run(cmd1, capture_output=True, text=True).returncode)
except Exception as e:
    print(e)
