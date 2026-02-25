import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src.utils import parse_filename

test_cases = [
    # Success cases from screenshot
    ("Trailer & Twitter - November 28th 29th 2025 - S1.mp4", "TRAILER"),
    ("Trailer & Twitter - November 28th 29th 2025 - S2.mp4", "TRAILER"),
    
    # Failure cases from previous version
    ("Trailer & Twitter - December 31st 2025 - Scene 1.mp4", "TRAILER"),
    ("Trailer & Twitter- November 21st 2025 - Scene 1.mp4", "TRAILER"),
    ("Twitter & Trailer December 6th 2025 - Scene 1.mp4", "TRAILER"),
    
    # Meaningless "Nightmare" cases
    ("Scene 1(Trailer).mp4", "TRAILER"),
    ("Scene_1-Trailer.mp4", "TRAILER"),
    ("Full_trl_Dec20.mp4", "TRAILER"),
    ("Pre-Scene 1.mp4", "TRAILER"),
    ("Clip_FYP_Vertical.mp4", "FYP"),
    ("TikTok-123.mp4", "FYP"),
    
    # Grouping checks
    ("November 14th 2025 clip 2.mp4", "FYP"),
    ("November 21st 2025 - Scene 1 (alex & Chloe).mp4", "PPV")
]

print(f"{'FILENAME':<60} | {'EXPECTED TYPE':<15} | {'ACTUAL TYPE':<15} | {'NUM':<4} | {'STATUS'}")
print("-" * 110)

failed = 0
for filename, expected_type in test_cases:
    meta = parse_filename(filename)
    actual_type = meta["type"]
    actual_num = meta["number"]
    
    # Simple check: if filename has S1/Scene 1, number should be 1
    type_ok = actual_type == expected_type
    # (Note: Most tests here expect number 1 or default)
    
    status = "PASS" if type_ok else "FAIL"
    if status == "FAIL": failed += 1
    print(f"{filename:<60} | {expected_type:<15} | {actual_type:<15} | {actual_num:<4} | {status}")

print("-" * 100)
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"{failed} TESTS FAILED.")
