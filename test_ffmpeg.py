import subprocess
print("1) Fetching URL...")
url_cmd = "rclone link 'do:chloe-storage/content-for-sale/STREAMVOD/April 3rd Stream pt1.mp4'"
url = subprocess.check_output(url_cmd, shell=True).decode().strip().split('\n')[-1]
print("2) Running simple ffmpeg...")
cmd = ['ffmpeg', '-v', 'debug', '-ss', '1500', '-i', url, '-frames:v', '1', '-y', 'test.jpg']
try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    print("RETURN CODE:", res.returncode)
    print("STDOUT:", res.stdout[-500:])
    print("STDERR:", res.stderr[-2000:])
except subprocess.TimeoutExpired as e:
    print("TIMEOUT EXPIRED:", e.stderr if hasattr(e, 'stderr') else e)
