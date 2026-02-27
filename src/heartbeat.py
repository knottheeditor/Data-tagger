import time
import os
import subprocess

HEARTBEAT_FILE = "/tmp/worker_heartbeat"
IDLE_TIMEOUT_SECONDS = 30 * 60 # 30 minutes

def update_heartbeat():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))

def check_idle():
    if not os.path.exists(HEARTBEAT_FILE):
        return False
        
    with open(HEARTBEAT_FILE, "r") as f:
        last_beat = float(f.read())
        
    idle_time = time.time() - last_beat
    return idle_time > IDLE_TIMEOUT_SECONDS

if __name__ == "__main__":
    print(f"Heartbeat monitor started. Timeout: {IDLE_TIMEOUT_SECONDS/60} minutes.")
    while True:
        if check_idle():
            print("Worker idle for too long. Stopping services...")
            subprocess.run(["pkill", "ollama"])
            # Optionally: Use remote API to stop the pod if API key is in env
            break
        time.sleep(60)
