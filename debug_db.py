from src.database import Content, init_db

init_db()

search_term = "First Bare Masturbation"
print(f"SEARCHING DB FOR: {search_term}")

results = Content.select().where(Content.scene_name.contains(search_term))
count = results.count()
print(f"Found {count} records.")

for c in results:
    print(f"ID: {c.id} | Name: {c.scene_name} | Path: {c.source_path}")
