import os
from src.database import Content

def find_first_real_video():
    # Find the first pending video that is at least 5MB
    content = Content.select().where(
        (Content.status == "pending") & 
        (Content.file_size > 5 * 1024 * 1024)
    ).first()
    
    if content:
        print(f"FOUND VIDEO: ID={content.id} Path={content.source_path} Size={content.file_size}")
    else:
        print("No valid pending videos found.")

if __name__ == "__main__":
    find_first_real_video()
