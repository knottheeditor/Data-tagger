"""Database migration for v2.0 schema changes."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import db, Content

def migrate_v2():
    """Add new v2.0 columns to Content table."""
    print("=== DATA FORAGER v2.0 MIGRATION ===")
    
    # New columns to add
    new_columns = [
        ("content_category", "VARCHAR(255) DEFAULT 'HQ PPV'"),
        ("video_aspect_ratio", "VARCHAR(50)"),
        ("trailer_path", "VARCHAR(255)"),
        ("trailer_aspect_ratio", "VARCHAR(50)"),
        ("thumbnail_path", "VARCHAR(255)"),
        ("thumbnail_aspect_ratio", "VARCHAR(50)"),
        ("duration_seconds", "INTEGER"),
        ("price", "INTEGER DEFAULT 50"),
        ("ai_description", "TEXT"),
        ("ai_tags", "TEXT"),
    ]
    
    db.connect(reuse_if_open=True)
    
    for col_name, col_type in new_columns:
        try:
            db.execute_sql(f"ALTER TABLE content ADD COLUMN {col_name} {col_type}")
            print(f"  ✓ Added column: {col_name}")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print(f"  - Column exists: {col_name}")
            else:
                print(f"  ✗ Error adding {col_name}: {e}")
    
    print("\n=== MIGRATION COMPLETE ===")

if __name__ == "__main__":
    migrate_v2()
