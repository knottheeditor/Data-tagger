import os
import sys

# Ensure the project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.database import db, Content, Asset
from src.scanner import scan_directory

def run_test():
    print("Initializing Database...")
    db.connect(reuse_if_open=True)
    db.create_tables([Content, Asset], safe=True)
    
    test_dir = r"Z:\content-for-sale\STREAMVOD"
    print(f"Starting test scan of {test_dir}...")
    try:
        count = scan_directory(test_dir)
        print(f"\nSUCCESS: Added/Updated {count} records.")
    except Exception as e:
        print(f"\nCRASH CAUGHT: {e}")
        import traceback
        traceback.print_exc()
    
if __name__ == "__main__":
    run_test()
