"""Fix stale trailer records in the database."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Content
from src.utils import parse_filename

print("=== FIXING STALE TRAILER RECORDS ===")
fixed = 0
for c in Content.select().where(Content.source_path ** '%Trailer%'):
    filename = os.path.basename(c.source_path)
    meta = parse_filename(filename)
    if c.content_type != meta["type"]:
        old_type = c.content_type
        c.content_type = meta["type"]
        c.scene_number = meta["number"]
        c.save()
        print(f"Fixed: {filename}")
        print(f"  Old: {old_type} -> New: {c.content_type}")
        fixed += 1

print(f"\n=== DONE: {fixed} records updated ===")
