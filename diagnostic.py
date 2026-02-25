from PySide6.QtGui import QImage, QColor
import os
import sys
from PySide6.QtWidgets import QApplication

def diagnostic_crop():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    img = QImage(sheet_path)
    if img.isNull(): return

    # Crop the whole row 8 (Y=143 area)
    row_strip = img.copy(0, 140, img.width(), 20)
    row_strip.save(r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\debug_row_8.png")
    print("Saved debug_row_8.png")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    diagnostic_crop()
