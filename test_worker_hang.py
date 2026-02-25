import sys
from PySide6.QtWidgets import QApplication
from src.worker import ScanWorker
import time

def run_gui_scan():
    app = QApplication(sys.argv)
    
    print("Initializing ScanWorker...")
    worker = ScanWorker(r"Z:\content-for-sale\STREAMVOD")
    
    def on_finished(count):
        print(f"\n[Worker Signal] Finished with {count} items!")
        app.quit()
        
    worker.finished.connect(on_finished)
    
    print("Starting worker thread...")
    worker.start()
    
    print("Entering QApplication.exec_()...")
    # Set a safety timeout just in case it deadlocks
    # Wait maximum 60 seconds
    start = time.time()
    def check_timeout():
        if time.time() - start > 60:
            print("TEST SCRIPT TIMEOUT: The worker thread is hanging.")
            app.quit()
    
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(check_timeout)
    timer.start(1000)
    
    app.exec_()
    print("Application successfully exited.")

if __name__ == "__main__":
    run_gui_scan()
