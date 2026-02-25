"""Database migration for adding intensity_score."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import db

def migrate_intensity():
    print("=== MIGRATION: Adding intensity_score ===")
    
    db.connect(reuse_if_open=True)
    try:
        db.execute_sql("ALTER TABLE content ADD COLUMN intensity_score INTEGER")
        print("  ✓ Added column: intensity_score")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("  - Column already exists: intensity_score")
        else:
            print(f"  ✗ Error adding column: {e}")
            
    print("\n=== MIGRATION COMPLETE ===")

if __name__ == "__main__":
    migrate_intensity()
