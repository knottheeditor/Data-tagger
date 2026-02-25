import sqlite3
import os

db_path = "/root/src/content_factory.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- REMOTE CONTENT TABLE ---")
cursor.execute("SELECT id, source_path, status FROM content ORDER BY id DESC LIMIT 10")
for row in cursor.fetchall():
    print(row)

conn.close()
