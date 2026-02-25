from PySide6.QtGui import QImage, QColor
import os
import sys
from PySide6.QtWidgets import QApplication

def find_grid():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    img = QImage(sheet_path).convertToFormat(QImage.Format_Grayscale8)
    if img.isNull(): return

    print("Checking Row 6 area (Y=115):")
    for y in range(112, 135):
        line = ""
        for x in range(32):
            c = QColor(img.pixel(x, y)).lightness()
            line += "#" if c < 200 else "."
        print(f"{y:03d}: {line}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    find_grid()
