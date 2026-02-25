from src.database import Content

def list_valid():
    # Find videos in kinks folder (usually healthy .webm files)
    valid = Content.select().where(
        Content.source_path.contains("kinks")
    ).order_by(Content.file_size.desc())
    
    print("Top 5 Valid Videos:")
    for c in valid[:5]:
        print(f"ID={c.id} | Size={c.file_size/1e6:.1f}MB | Path={c.source_path}")

if __name__ == "__main__":
    list_valid()
