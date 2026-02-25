from PySide6.QtGui import QImage, QColor
import os
import sys
from PySide6.QtWidgets import QApplication

def scan_row_8():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    img = QImage(sheet_path).convertToFormat(QImage.Format_Grayscale8)
    if img.isNull(): return

    print("Row 8 X-Transitions (Y=150):")
    was_dark = False
    for x in range(img.width()):
        c = QColor(img.pixel(x, 150)).lightness()
        is_dark = c < 200
        if is_dark != was_dark:
            print(f"X={x} -> {'DARK' if is_dark else 'LIGHT'}")
            was_dark = is_dark

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scan_row_8()
