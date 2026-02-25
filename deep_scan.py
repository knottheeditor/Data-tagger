from PySide6.QtGui import QImage, QColor
import os
import sys
from PySide6.QtWidgets import QApplication

def deep_scan():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    img = QImage(sheet_path).convertToFormat(QImage.Format_Grayscale8)
    if img.isNull(): return

    print("Row 1 (y around 25) X-Scan:")
    for x in range(100):
        c = QColor(img.pixel(x, 25)).lightness()
        if c < 200: print(f"X{x}", end=' ')
    print("\n\nRow 8 (y around 145) X-Scan:")
    for x in range(100):
        c = QColor(img.pixel(x, 145)).lightness()
        if c < 200: print(f"X{x}", end=' ')
    
    print("\n\nColumn 2 Y-Scan:")
    for y in range(img.height()):
        c = QColor(img.pixel(2, y)).lightness()
        if c < 200: print(f"Y{y}", end=' ')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    deep_scan()
