from src.database import init_db, Content, Asset, db
from src.scanner import scan_directory
import os

def verify_phase10():
    print("--- VERIFYING PHASE 10: MASTER-ASSET RELATIONSHIP ---")
    
    # 1. Clear DB for clean test
    db.connect(reuse_if_open=True)
    Asset.delete().execute()
    Content.delete().execute()
    
    # 2. Run Scan on test_factory
    test_dir = os.path.abspath("test_factory")
    print(f"Scanning test directory: {test_dir}")
    scan_directory(test_dir)
    
    # 3. Verify Master Entry
    masters = Content.select()
    print(f"Masters Found: {masters.count()}")
    for m in masters:
        print(f"Master: {m.source_path} ({m.content_type})")
        
        # 4. Verify Linked Assets
        linked = Asset.select().where(Asset.content == m)
        print(f"  Linked Assets: {linked.count()}")
        for a in linked:
            print(f"    - [{a.asset_type}] {a.local_path}")

    if masters.count() == 1 and Asset.select().count() == 2:
        print("\nSUCCESS: Master-Asset Relationship Verified!")
    else:
        print("\nFAILURE: Grouping Logic Mismatch.")

if __name__ == "__main__":
    init_db()
    verify_phase10()
