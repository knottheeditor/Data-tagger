import sys
sys.path.insert(0, '/workspace')
from src.scanner import extract_random_thumbnail
import traceback

try:
    r = extract_random_thumbnail('do:chloe-storage/content-for-sale/STREAMVOD/April 3rd Stream pt1.mp4')
    print("SUCCESS:" + str(r))
except Exception as e:
    print("FAILED EXCEPTION:")
    traceback.print_exc()
