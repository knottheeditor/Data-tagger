import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src.utils import parse_filename

# Exact strings from user's screenshot
failures_from_screenshot = [
    "Trailer & Twitter - December 31st 2025 - Scene 1.mp4",
    "Trailer & Twitter - December 31st 2025 - Scene 2.mp4",
    "Trailer & Twitter- November 21st 2025 - Scene 1 .mp4",
    "Trailer & Twitter- November 21st 2025 - Scene 2.mp4",
    "Trailer & Twitter- November 21st 2025 - Scene 3.mp4",
    "Trailer & Twitter- November 22nd 2025 - Scene 1 .mp4",
    "Trailer & Twitter- November 22nd 2025 - Scene 2.mp4",
    "Twitter & Trailer - December 20th 2025 - Scene 1.mp4",
    "Twitter & Trailer - December 20th 2025 - Scene 2.mp4",
    "Twitter & Trailer December 6th 2025 - Scene 1.mp4",
    "Twitter & Trailer December 6th 2025 - Scene 2.mp4"
]

successes_from_screenshot = [
    "Trailer & Twitter - November 28th 29th 2025 - S1.mp4",
    "Trailer & Twitter - November 28th 29th 2025 - S2.mp4",
    "Trailer & Twitter - November 28th 29th 2025 - S3.mp4",
    "Trailer & Twitter - November 28th 29th 2025 - S4.mp4",
    "Trailer & Twitter - November 28th 29th 2025 - S5.mp4",
    "Trailer & Twitter - November 28th 29th 2025 - S6.mp4"
]

def run_suite(name, cases, expected_type="TRAILER"):
    print(f"\n--- {name} ---")
    print(f"{'FILENAME':<60} | {'TYPE':<10} | {'NUM':<4} | {'STATUS'}")
    failed = 0
    for f in cases:
        meta = parse_filename(f)
        actual = meta["type"]
        status = "PASS" if actual == expected_type else "FAIL"
        if status == "FAIL": failed += 1
        print(f"{f:<60} | {actual:<10} | {meta['number']:<4} | {status}")
    return failed

f1 = run_suite("REPORTED FAILURES", failures_from_screenshot)
f2 = run_suite("REPORTED SUCCESSES", successes_from_screenshot)

if f1 + f2 == 0:
    print("\n[SUCCESS] Current logic passes all screenshot cases!")
else:
    print(f"\n[FAILURE] {f1 + f2} cases still failing.")
