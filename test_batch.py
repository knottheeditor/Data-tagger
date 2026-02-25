import json
import os
from src.engine import TaskScheduler

def run_test():
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return
        
    with open(config_path) as f:
        config = json.load(f)
        
    scheduler = TaskScheduler(config)
    print("Starting test batch for ID=23 (kinks/webm)...")
    # Target specific ID
    from src.database import Content
    c = Content.get_by_id(23)
    c.status = "pending" # Reset to pending
    c.save()
    scheduler.process_item(c)

if __name__ == "__main__":
    run_test()
