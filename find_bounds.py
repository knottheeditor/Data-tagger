from PySide6.QtGui import QImage, QColor
import os
import sys
from PySide6.QtWidgets import QApplication

def find_precise_bounds():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    img = QImage(sheet_path)
    if img.isNull(): return

    # Scan Row 8 (Gear, Circuit)
    # The Gear is roughly around x=50, y=142
    print("Row 8 (Gear/Circuit) X-Scan:")
    for x in range(40, 100):
        # Look at y=150 (middle of row 8)
        c = QColor(img.pixel(x, 150))
        if c.alpha() > 0 and (c.red() < 240 or c.green() < 240 or c.blue() < 240): # Not white/transparent
            print(f"px {x}: {c.name()} (Y=150)")
    
    # Scan Row 1 (Green Arrow)
    print("\nRow 1 (Green Arrow) X-Scan:")
    for x in range(0, 32):
        c = QColor(img.pixel(x, 28)) # Roughly middle of row 1
        if c.alpha() > 0 and (c.red() < 240 or c.green() < 240 or c.blue() < 240):
            print(f"px {x}: {c.name()} (Y=28)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    find_precise_bounds()
