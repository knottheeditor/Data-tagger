import subprocess

cmd_str = "ssh -o StrictHostKeyChecking=no -i C:/Users/nicho/.ssh/id_ed25519 -p 22 root@107.170.42.123 \"echo hello\""
try:
    process = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    process.wait()
    print(f"Return code: {process.returncode}")
except Exception as e:
    print(f"Exception: {e}")
