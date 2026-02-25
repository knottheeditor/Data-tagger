from PySide6.QtGui import QImage
import os

def slice_icons():
    sheet_path = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons\sprite_sheet.png"
    output_dir = r"d:\AI_Shit\08_Utlity_Datatagger_Organizer\src\assets\icons"
    
    if not os.path.exists(sheet_path):
        print(f"Error: {sheet_path} not found.")
        return

    full_image = QImage(sheet_path)
    if full_image.isNull():
        print("Error: Could not load image.")
        return

    tile_size = 16 # Full standard tile size to prevent "cutting off"
    
    # Absolute Coordinates (x, y) gathered via deep_scan
    # (Avoids grid math issues on non-uniform sheets)
    icons = {
        "deploy": (2, 21),   # Green Up Arrow
        "scan": (51, 141),   # Industrial Gear
        "ai": (68, 141),     # Circuit Board
        "save": (86, 38),    # Blue Medal 
        "purge": (51, 105),  # Big Red Button
        "refresh": (2, 73),  # Blue Curve Arrow
        "folder": (187, 21), # Briefcase
        "video": (170, 73)   # Industrial Monitor
    }

    from PySide6.QtCore import Qt

    for name, (x, y) in icons.items():
        cropped = full_image.copy(x, y, tile_size, tile_size)
        save_path = os.path.join(output_dir, f"{name}.png")
        
        # Scale with FastTransformation to keep the pixel-art crisp
        scaled = cropped.scaled(48, 48, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        scaled.save(save_path)
        print(f"Saved: {save_path} from absolute px({x},{y})")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    slice_icons()
