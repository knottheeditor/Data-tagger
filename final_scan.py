from PySide6.QtGui import QImage, QColor
import os
import sys
from PySide6.QtWidgets import QApplication

def final_scan():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    img = QImage(sheet_path).convertToFormat(QImage.Format_Grayscale8)
    if img.isNull(): return

    # 1. Medal (Row 2, Col 4 area)
    print("Row 2 (Medal) X-Scan at Y=43:")
    for x in range(60, 100):
        if QColor(img.pixel(x, 43)).lightness() < 240: print(f"X{x}", end=' ')
    
    # 2. Button (Row 6, Col 3 area)
    print("\n\nRow 6 (Button) X-Scan at Y=113:")
    for x in range(40, 80):
        if QColor(img.pixel(x, 113)).lightness() < 240: print(f"X{x}", end=' ')

    # 3. Gear & AI (Row 8) X-Scan at Y=145
    print("\n\nRow 8 (Gear/AI) X-Scan at Y=145:")
    for x in range(50, 100):
        if QColor(img.pixel(x, 145)).lightness() < 240: print(f"X{x}", end=' ')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    final_scan()
