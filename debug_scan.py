import os

root_path = r"Z:\content-for-sale\HQ PPV"

print(f"Scanning: {root_path}")
if not os.path.exists(root_path):
    print("CRITICAL: Path does not exist!")
    exit()

count = 0
for root, dirs, files in os.walk(root_path):
    print(f"Directory: {root}")
    for f in files:
        print(f"  - {f}")
        count += 1
        if count >= 10:
            print("... (limit reached)")
            exit()

if count == 0:
    print("No files found via os.walk")
