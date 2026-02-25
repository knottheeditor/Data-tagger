"""Check what the scanner stored in the database."""
import sys, os
sys.path.insert(0, "/workspace")
os.chdir("/workspace")

from src.database import db, Content
db.connect(reuse_if_open=True)
for c in Content.select():
    dur = str(c.duration_seconds) if c.duration_seconds else "0"
    thumb = c.thumbnail_path or "NONE"
    print(f"  {c.scene_name[:40]:40s} | dur={dur:>5s} | status={c.status:12s} | thumb={thumb}")
db.close()
