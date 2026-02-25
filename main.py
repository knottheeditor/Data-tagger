import sys
import argparse
import json
import os
from src.database import init_db
from src.engine import TaskScheduler

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        # Use template if real config missing
        config_path = os.path.join(os.path.dirname(__file__), "config.json.template")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def run_gui():
    from PySide6.QtWidgets import QApplication
    from src.gui_v2 import DataForagerV2
    
    app = QApplication(sys.argv)
    gui = DataForagerV2()
    gui.show()
    
    # Run the GUI event loop
    ret = app.exec()
    
    # Teardown the background SQLite Queue Thread to prevent zombie hangs
    from src.database import db
    if hasattr(db, 'stop'):
        print("Stopping database queue thread...")
        db.stop()
        
    sys.exit(ret)

def run_worker(dry_run=False):
    config = load_config()
    scheduler = TaskScheduler(config)
    print(f"Cloud Worker Started {'(DRY RUN)' if dry_run else ''}. Watching for tasks...")
    scheduler.run_batch(dry_run=dry_run)

def main():
    parser = argparse.ArgumentParser(description="Content Factory Organizer")
    parser.add_argument("--mode", choices=["gui", "worker"], default="gui", help="Mode to run in")
    parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode (no moves)")
    args = parser.parse_args()
    
    # Ensure DB is initialized
    init_db()
    
    if args.mode == "gui":
        run_gui()
    else:
        run_worker(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
