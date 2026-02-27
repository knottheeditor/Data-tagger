"""
DATA FORAGER v2.0 - Simplified Content Pipeline
All-in-one: Scan → Select → AI Tag → Categorize → Thumbnail → Export
"""
import sys
import os
import subprocess
import json
import re
import time
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QListWidget,
                               QLineEdit, QTextEdit, QComboBox, QSpinBox,
                               QSplitter, QFrame, QFileDialog, QScrollArea,
                               QGridLayout, QGroupBox, QMessageBox, QProgressBar,
                               QCheckBox, QListWidgetItem, QSizePolicy, QTabWidget)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QPointF
from PySide6.QtGui import QFont, QPixmap, QColor, QLinearGradient, QIcon, QPainter, QRadialGradient, QBrush

try:
    from src.worker import RemoteScanWorker, ScanWorker
except ImportError:
    from worker import RemoteScanWorker, ScanWorker

import shutil
import tempfile
import traceback
import hashlib
from src.video_utils import VideoUtils
from src.vlm import VLMClient
from src.database import db, Content, Asset
from src.utils import resolve_ssh_details, RemotePaths, StandardNaming, ConfigManager

class SystemStatusWorker(QThread):
    status_updated = Signal(str, str) # text, color (hex)

    def __init__(self, check_url):
        super().__init__()
        self.check_url = check_url

    def run(self):
        try:
            # We use a short timeout so the GUI isn't hung if the droplet is off
            res = requests.get(self.check_url, timeout=3)
            if res.status_code == 200:
                self.status_updated.emit("🟢 DROPLET ONLINE | VLM READY", "#00FF00")
            else:
                self.status_updated.emit(f"🟡 DROPLET ONLINE | VLM ERR: {res.status_code}", "#FFFF00")
        except Exception:
            self.status_updated.emit("🔴 DROPLET OFFLINE | VLM UNREACHABLE", "#FF0000")

# ==================== CYBER-INDUSTRIAL "MISSION CONTROL" THEME ====================
COLOR_ORANGE = "#FF5F1F"    # NASA/Industrial Orange
COLOR_BLUE = "#00D9FF"      # Cyan Data Blue
COLOR_DEEP_BLUE = "#0B0E14" # Charcoal Navy
COLOR_GREY = "#2E2E2E"      # Signal Grey
COLOR_BG_DARK = "#050510"   # Almost Black Blue
COLOR_PANEL = "rgba(15, 20, 30, 0.95)" # Solid-ish Industrial
TEXT_HIGH_VIZ = "#FFFFFF"   # Pure White
TEXT_ORANGE = "#FF8000"     # Readable Orange

MISSION_CONTROL_QSS = f"""
QMainWindow {{
    background: transparent;
}}
QWidget {{
    color: {TEXT_HIGH_VIZ};
    font-family: 'Segoe UI', 'Consolas', sans-serif;
    font-size: 13px;
}}
QLabel#Header {{
    font-size: 26px;
    font-weight: 900;
    color: {COLOR_ORANGE};
    letter-spacing: 5px;
    border-bottom: 4px solid {COLOR_ORANGE};
    padding-bottom: 10px;
    margin-bottom: 25px;
    text-transform: uppercase;
    background: rgba(255, 95, 31, 0.1);
    qproperty-alignment: 'AlignCenter';
    font-family: 'Consolas';
}}
QListWidget {{
    background-color: {COLOR_DEEP_BLUE};
    border: 2px solid {COLOR_GREY};
    border-radius: 0px;
    padding: 0px;
}}
QListWidget::item {{
    padding: 18px;
    border-bottom: 1px solid {COLOR_GREY};
    color: {COLOR_BLUE};
}}
QListWidget::item:selected {{
    background-color: {COLOR_ORANGE};
    color: {COLOR_DEEP_BLUE};
    font-weight: bold;
    border-left: 4px solid {TEXT_HIGH_VIZ};
}}
QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: #000;
    border: 1px solid {COLOR_GREY};
    border-left: 4px solid {COLOR_BLUE};
    padding: 10px;
    color: #FFF;
    min-height: 40px;
}}
QComboBox {{
    background-color: #1A1A1A;
    border: 1px solid {COLOR_GREY};
    border-left: 4px solid {COLOR_ORANGE};
}}
QComboBox QAbstractItemView {{
    background-color: #1A1A1A;
    selection-background-color: {COLOR_ORANGE};
    color: white;
    border: 1px solid {COLOR_GREY};
}}
QSpinBox {{
    background-color: #1A1A1A;
    border: 1px solid {COLOR_GREY};
    border-left: 4px solid {COLOR_BLUE};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {COLOR_ORANGE};
    subcontrol-origin: border;
    width: 30px;
    border: 1px solid white;
}}
QSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 14px;
    height: 14px;
    background-color: {COLOR_DEEP_BLUE};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLOR_ORANGE};
    border-left: 4px solid {COLOR_ORANGE};
}}
QPushButton {{
    background-color: {COLOR_GREY};
    border: 1px solid #444;
    border-bottom: 3px solid #000;
    padding: 12px;
    min-height: 45px;
    font-weight: 800;
    text-transform: uppercase;
    color: #CCC;
    text-align: center;
}}
QPushButton:hover {{
    background-color: #444;
    color: #FFF;
    border-bottom: 3px solid {COLOR_BLUE};
}}
QPushButton#Primary {{
    background-color: {COLOR_ORANGE};
    border: none;
    border-bottom: 4px solid #803000;
    color: #FFF;
    letter-spacing: 2px;
    min-height: 55px;
}}
QPushButton#Primary:hover {{
    background-color: #FF7F50;
    border-bottom: 4px solid #A04000;
}}
QPushButton#Danger {{
    background-color: #330000;
    border: 1px solid #660000;
    color: #FF5555;
    min-height: 45px;
}}
QPushButton#Danger:hover {{
    background-color: #660000;
    color: #FFF;
}}
QGroupBox {{
    border: 2px solid {COLOR_GREY};
    margin-top: 35px;
    padding-top: 45px;
    padding-bottom: 20px;
    font-weight: bold;
    color: {COLOR_ORANGE};
    background-color: rgba(0, 0, 0, 0.4);
}}
QGroupBox::title {{
    subcontrol-origin: border;
    subcontrol-position: top center;
    top: -12px;
    padding: 4px 25px;
    background-color: {COLOR_ORANGE};
    color: {COLOR_DEEP_BLUE};
    text-transform: uppercase;
    font-weight: 900;
    font-size: 11px;
}}
QProgressBar {{
    border: 1px solid {COLOR_BLUE};
    text-align: center;
    background: #000;
    height: 30px;
}}
QProgressBar::chunk {{
    background-color: {COLOR_BLUE};
}}
QToolTip {{
    background-color: {COLOR_ORANGE};
    color: {COLOR_DEEP_BLUE};
    border: 3px solid {COLOR_DEEP_BLUE};
    padding: 10px;
    font-weight: bold;
}}
"""

# ==================== MAIN GUI ====================

# ==================== MAIN GUI ====================
class DataForagerV2(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DATA FORAGER // Mission Dispatch Hub")
        self.resize(1400, 900)
        
        # Load Config
        self.config = ConfigManager.get_config()
        self.selected_content = None
        
        self.init_ui()
        self.setStyleSheet(MISSION_CONTROL_QSS)

    def paintEvent(self, event):
        """High-Fidelity Industrial Background with Grid Overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Base Radial Gradient
        rect = self.rect()
        gradient = QRadialGradient(rect.center(), max(rect.width(), rect.height()))
        gradient.setColorAt(0, QColor("#121826")) # Deep Slate
        gradient.setColorAt(1, QColor("#05070a")) # Midnight
        painter.fillRect(rect, QBrush(gradient))
        
        # 2. Subtle Grid Overlay
        painter.setPen(QColor(0, 217, 255, 15)) # Ultra-faint Cyan
        grid_size = 40
        for x in range(0, rect.width(), grid_size):
            painter.drawLine(x, 0, x, rect.height())
        for y in range(0, rect.height(), grid_size):
            painter.drawLine(0, y, rect.width(), y)
            
        # 3. Vignette
        vignette = QRadialGradient(rect.center(), rect.width() * 0.7)
        vignette.setColorAt(0, Qt.transparent)
        vignette.setColorAt(1, QColor(0, 0, 0, 150))
        painter.fillRect(rect, QBrush(vignette))

    def load_config(self):
        return ConfigManager.get_config()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== LEFT PANEL: Discovery ==========
        left_panel = QFrame()
        left_panel.setMinimumWidth(380)
        left_panel.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 1px solid #444;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        header = QLabel("[ SCAN_CONFIG ]")
        header.setObjectName("Header")
        left_layout.addWidget(header)
        
        self.status_lbl = QLabel("🟡 SYSTEM_STATUS: INITIALIZING...")
        self.status_lbl.setStyleSheet(f"color: {COLOR_BLUE}; font-size: 11px; font-weight: bold; background: #000; padding: 5px;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_lbl)
        
        # Remote Scan Box
        scan_group = QGroupBox("Target Reconnaissance")
        scan_inner = QVBoxLayout(scan_group)
        
        self.scan_path_input = QLineEdit()
        self.scan_path_input.setPlaceholderText("SECTOR: RAW_ARCHIVE/2026/...")
        scan_inner.addWidget(self.scan_path_input)
        
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons")
        
        self.scan_btn = QPushButton(" INITIATE SECTOR SCAN")
        self.scan_btn.setIcon(QIcon(os.path.join(icon_path, "scan.png")))
        self.scan_btn.setIconSize(QSize(24, 24))
        self.scan_btn.setToolTip("Broadcast scanning signal to remote RunPod cluster.")
        self.scan_btn.setObjectName("Primary")
        self.scan_btn.clicked.connect(self.start_scan)
        scan_inner.addWidget(self.scan_btn)
        
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        scan_inner.addWidget(self.scan_progress)
        
        left_layout.addWidget(scan_group)
        
        # Video List
        list_header = QLabel("[ INCOMING_CLIPS ]")
        list_header.setStyleSheet(f"color: {COLOR_BLUE}; font-weight: bold; margin-top: 15px; text-transform: uppercase;")
        left_layout.addWidget(list_header)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search clips...")
        self.search_bar.setStyleSheet(f"background-color: {COLOR_BG_DARK}; color: {TEXT_HIGH_VIZ}; border: 1px solid {COLOR_GREY}; padding: 5px;")
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        left_layout.addWidget(self.search_bar)
        
        # Tabs for Pending vs Completed
        self.list_tabs = QTabWidget()
        self.list_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLOR_GREY}; background: {COLOR_BG_DARK}; }}
            QTabBar::tab {{ background: {COLOR_DEEP_BLUE}; color: {COLOR_GREY}; padding: 8px 15px; border: 1px solid {COLOR_GREY}; }}
            QTabBar::tab:selected {{ background: {COLOR_ORANGE}; color: {TEXT_HIGH_VIZ}; font-weight: bold; border-bottom: none; }}
        """)
        
        self.video_list = QListWidget() # Pending Tab
        self.video_list.itemClicked.connect(self.on_video_selected)
        
        self.completed_list = QListWidget() # Completed Tab
        self.completed_list.itemClicked.connect(self.on_video_selected)
        
        self.list_tabs.addTab(self.video_list, "Inbox")
        self.list_tabs.addTab(self.completed_list, "Archive")
        self.list_tabs.currentChanged.connect(lambda idx: self._on_search_text_changed(self.search_bar.text()))
        left_layout.addWidget(self.list_tabs)
        
        # Show All Toggle
        self.show_all_cb = QCheckBox("Show All Pending (Disable Filter)")
        self.show_all_cb.setStyleSheet(f"color: {COLOR_BLUE}; font-size: 10px;")
        self.show_all_cb.stateChanged.connect(self._on_show_all_toggled)
        left_layout.addWidget(self.show_all_cb)
        
        # Footer Buttons
        footer_layout = QHBoxLayout()
        refresh_btn = QPushButton(" RE-SYNC")
        refresh_btn.setIcon(QIcon(os.path.join(icon_path, "refresh.png")))
        refresh_btn.setIconSize(QSize(20, 20))
        refresh_btn.setMinimumWidth(150)
        refresh_btn.setToolTip("Refresh local hub with database actuals.")
        refresh_btn.clicked.connect(self.refresh_video_list)
        footer_layout.addWidget(refresh_btn)
        
        purge_btn = QPushButton(" PURGE_HUB")
        purge_btn.setMinimumWidth(150)
        purge_btn.setIcon(QIcon(os.path.join(icon_path, "purge.png")))
        purge_btn.setIconSize(QSize(20, 20))
        purge_btn.setToolTip("WARNING: Critical Data Disposal. Wipes local pending queue.")
        purge_btn.setObjectName("Danger")
        purge_btn.clicked.connect(self.purge_hub)
        footer_layout.addWidget(purge_btn)
        
        remove_btn = QPushButton(" REMOVE")
        remove_btn.setMinimumWidth(120)
        remove_btn.setIcon(QIcon(os.path.join(icon_path, "minus.png")))
        remove_btn.setIconSize(QSize(20, 20))
        remove_btn.setToolTip("Remove selected item from inbox.")
        remove_btn.clicked.connect(self.remove_selected_item)
        footer_layout.addWidget(remove_btn)
        
        left_layout.addLayout(footer_layout)
        
        main_layout.addWidget(left_panel)

        # ========== MIDDLE PANEL: Editor ==========
        middle_panel = QFrame()
        middle_panel.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 2px solid {COLOR_GREY};")
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(20, 20, 20, 20)
        
        mid_header = QLabel("[ CLIP_EDITOR ]")
        mid_header.setObjectName("Header")
        middle_layout.addWidget(mid_header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(25)
        form_layout.setVerticalSpacing(30)
        form_layout.setContentsMargins(10, 20, 10, 20)
        
        r = 0
        # Title
        title_lbl = QLabel("MASTER_MANIFEST_TITLE:")
        title_lbl.setStyleSheet(f"color: {COLOR_ORANGE}; font-weight: bold; text-transform: uppercase;")
        title_lbl.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(title_lbl, r, 0)
        self.title_input = QLineEdit()
        form_layout.addWidget(self.title_input, r, 1)
        r += 1
        
        # Scene ID Control (own row for visibility)
        id_lbl = QLabel("SCENE_ID:")
        id_lbl.setStyleSheet(f"color: {COLOR_ORANGE}; font-weight: bold;")
        form_layout.addWidget(id_lbl, r, 0)
        self.scene_id_input = QLineEdit("1")
        self.scene_id_input.setFixedWidth(120)
        self.scene_id_input.setPlaceholderText("Scene # (default 1)")
        self.scene_id_input.setToolTip("Manual Scene ID — controls the number in the filename (e.g. PPV_01_...)")
        form_layout.addWidget(self.scene_id_input, r, 1)
        r += 1
        
        # Type/Category Row
        form_layout.addWidget(QLabel("PIPELINE_ROUTE:"), r, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItems(["HQ PPV", "SEMIPPV", "STREAMVOD"])
        form_layout.addWidget(self.category_combo, r, 1)
        r += 1
        
        # Price/Duration Row
        form_layout.addWidget(QLabel("VALUE_UNIT ($):"), r, 0)
        
        stats_layout = QHBoxLayout()
        # Custom Price Controls
        self.price_val = QLineEdit("50")
        self.price_val.setReadOnly(True)
        self.price_val.setFixedWidth(60)
        self.price_val.setAlignment(Qt.AlignCenter)
        self.price_val.setStyleSheet(f"background: #000; color: {COLOR_ORANGE}; font-weight: bold; border: 1px solid {COLOR_GREY};")
        
        btn_style = f"background: {COLOR_GREY}; border: 1px solid #444; min-height: 40px; width: 40px;"
        self.minus_btn = QPushButton()
        self.minus_btn.setIcon(QIcon(os.path.join(icon_path, "minus.png")))
        self.minus_btn.setIconSize(QSize(20, 20))
        self.minus_btn.setStyleSheet(btn_style)
        self.minus_btn.clicked.connect(lambda: self.adjust_price(-5))
        
        self.plus_btn = QPushButton()
        self.plus_btn.setIcon(QIcon(os.path.join(icon_path, "plus.png")))
        self.plus_btn.setIconSize(QSize(20, 20))
        self.plus_btn.setStyleSheet(btn_style)
        self.plus_btn.clicked.connect(lambda: self.adjust_price(5))
        
        stats_layout.addWidget(self.minus_btn)
        stats_layout.addWidget(self.price_val)
        stats_layout.addWidget(self.plus_btn)
        
        stats_layout.addStretch()
        stats_layout.addWidget(QLabel("TIME_SIG:"))
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet(f"color: {COLOR_BLUE}; font-weight: 800;")
        stats_layout.addWidget(self.duration_label)
        
        form_layout.addLayout(stats_layout, r, 1)
        
        # Add Refresh Duration Button
        self.refresh_dur_btn = QPushButton()
        self.refresh_dur_btn.setIcon(QIcon(os.path.join(icon_path, "refresh.png")))
        self.refresh_dur_btn.setFixedWidth(40)
        self.refresh_dur_btn.setToolTip("Force re-scan video duration.")
        self.refresh_dur_btn.clicked.connect(self.force_refresh_duration)
        stats_layout.addWidget(self.refresh_dur_btn)
        r += 1
        
        # Content Date Row
        form_layout.addWidget(QLabel("CONTENT_DATE:"), r, 0)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYY-MM-DD (from original clip)")
        form_layout.addWidget(self.date_input, r, 1)
        r += 1
        
        # Aspect Ratio
        form_layout.addWidget(QLabel("FRAME_RATIO:"), r, 0)
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9", "9:16", "1:1"])
        form_layout.addWidget(self.aspect_combo, r, 1)
        r += 1

        # Live Name Preview
        preview_group = QGroupBox("Export Path Preview")
        preview_inner = QVBoxLayout(preview_group)
        self.path_preview_lbl = QLabel("Awaiting input...")
        self.path_preview_lbl.setStyleSheet(f"color: {COLOR_BLUE}; font-family: 'Consolas'; font-size: 11px;")
        self.path_preview_lbl.setWordWrap(True)
        preview_inner.addWidget(self.path_preview_lbl)
        form_layout.addWidget(preview_group, r, 0, 1, 2)
        r += 1
        
        # AI Logic
        form_layout.addWidget(QLabel("AI_LOG_ANALYSIS:"), r, 0)
        r += 1
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Awaiting VLM input...")
        self.description_input.setMinimumHeight(150)
        form_layout.addWidget(self.description_input, r, 0, 1, 2)
        r += 1
        
        form_layout.addWidget(QLabel("AI_TAG_VECTOR:"), r, 0)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Manual override enabled...")
        form_layout.addWidget(self.tags_input, r, 1)
        r += 1
        
        # Manual Toy Selector
        toy_group = QGroupBox("Quick Toy Selector")
        toy_layout = QGridLayout(toy_group)
        #toy_layout.setSpacing(5)
        
        TOY_TAGS = [
            "dildo", "vibrator", "wand", "drilldo", "estim", "fucking-machine", "butt-plug",
            "strap-on", "cage", "restraints", "collar", "leash", "gag", "clamps",
            "one-bar-prison", "grinder", "suction-toy", "anal-beads", "blindfold", "whip", "massage gun"
        ]
        
        row, col = 0, 0
        for tag in TOY_TAGS:
            btn = QPushButton(tag)
            #btn.setFlat(True)
            btn.setStyleSheet(f"background: #1A1A1A; color: #BBB; border: 1px solid #333; padding: 2px; min-height: 25px;")
            btn.setCursor(Qt.PointingHandCursor)
            # Use default param to capture loop variable
            btn.clicked.connect(lambda checked=False, t=tag: self.add_toy_tag(t))
            toy_layout.addWidget(btn, row, col)
            col += 1
            if col > 3: # 4 columns
                col = 0
                row += 1
        
        form_layout.addWidget(toy_group, r, 0, 1, 2)
        r += 1
        
        # Quick Performer Selector
        performer_group = QGroupBox("Quick Performer Selector")
        performer_layout = QGridLayout(performer_group)
        
        PERFORMER_TAGS = ["dumlovebun", "victoriana", "kurainu", "solarcat"]
        
        for pi, ptag in enumerate(PERFORMER_TAGS):
            btn = QPushButton(ptag)
            btn.setStyleSheet(f"background: #0B0E14; color: {COLOR_ORANGE}; border: 1px solid {COLOR_ORANGE}; padding: 4px; min-height: 28px; font-weight: bold;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, t=ptag: self.add_toy_tag(t))
            performer_layout.addWidget(btn, 0, pi)
        
        form_layout.addWidget(performer_group, r, 0, 1, 2)
        r += 1
        
        # Connect signals for Live Preview
        self.title_input.textChanged.connect(self.update_path_preview)
        self.scene_id_input.textChanged.connect(self.update_path_preview)
        self.date_input.textChanged.connect(self.update_path_preview)
        self.category_combo.currentTextChanged.connect(self.update_path_preview)
        self.price_val.textChanged.connect(self.update_path_preview)
        
        scroll.setWidget(form_widget)
        middle_layout.addWidget(scroll)
        
        h_ai = QHBoxLayout()
        self.ai_btn = QPushButton(" 🧠 TRIGGER AI VLM ANALYSIS")
        self.ai_btn.setIcon(QIcon(os.path.join(icon_path, "ai.png")))
        self.ai_btn.setIconSize(QSize(28, 28))
        self.ai_btn.setToolTip("Upload visual buffer to Gemma-3 node for deep scene parsing.")
        self.ai_btn.setObjectName("Primary")
        self.ai_btn.clicked.connect(self.run_ai_tagger)
        h_ai.addWidget(self.ai_btn)
        
        self.re_judge_btn = QPushButton(" ⚖️ RE-JUDGE")
        self.re_judge_btn.setIcon(QIcon(os.path.join(icon_path, "refresh.png")))
        self.re_judge_btn.setIconSize(QSize(24, 24))
        self.re_judge_btn.setToolTip("Skip frame sampling and re-run logic on existing sensor log.")
        self.re_judge_btn.clicked.connect(self.run_re_judge_tagger)
        self.re_judge_btn.setVisible(False) # Hidden until we have a sensor log
        h_ai.addWidget(self.re_judge_btn)
        
        middle_layout.addLayout(h_ai)
        
        main_layout.addWidget(middle_panel)

        # ========== RIGHT PANEL: Asset Pipeline ==========
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setMinimumWidth(420)
        right_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        right_panel = QFrame()
        right_panel.setMinimumWidth(380)
        right_panel.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 1px solid {COLOR_GREY};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)
        
        right_header = QLabel("[ FILES_&_PREVIEW ]")
        right_header.setObjectName("Header")
        right_layout.addWidget(right_header)
        
        # Visual Preview
        preview_group = QGroupBox("Optical Interface")
        preview_inner = QVBoxLayout(preview_group)
        preview_inner.setSpacing(10)

        # Image container
        self.thumbnail_preview = QLabel("NO_SIGNAL")
        self.thumbnail_preview.setMinimumHeight(200)
        self.thumbnail_preview.setAlignment(Qt.AlignCenter)
        self.thumbnail_preview.setStyleSheet(f"background-color: #000; border: 2px solid {COLOR_GREY};")
        preview_inner.addWidget(self.thumbnail_preview)
        
        # Wrapping buttons in a strict fixed-height widget blocks the image from overlapping
        btn_widget = QWidget(preview_group)
        btn_widget.setFixedHeight(65)
        btn_widget.setStyleSheet("background: transparent;")
        btn_row = QHBoxLayout(btn_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(10)
        
        self.extract_btn = QPushButton(" RE-CAPTURE")
        self.extract_btn.setMinimumWidth(120)
        self.extract_btn.setToolTip("Extract primary frame buffer.")
        self.extract_btn.clicked.connect(self.extract_thumbnail)
        btn_row.addWidget(self.extract_btn)

        self.random_btn = QPushButton(" 🎲 RANDOMIZE")
        self.random_btn.setMinimumWidth(120)
        self.random_btn.setToolTip("Extract a random high-quality frame.")
        self.random_btn.clicked.connect(self.randomize_thumbnail)
        btn_row.addWidget(self.random_btn)
        
        self.browse_btn = QPushButton(" BROWSE")
        self.browse_btn.setIcon(QIcon(os.path.join(icon_path, "folder.png")))
        self.browse_btn.setIconSize(QSize(20, 20))
        self.browse_btn.setMinimumWidth(140)
        self.browse_btn.setToolTip("Select manual visual asset.")
        self.browse_btn.clicked.connect(self.browse_thumbnail)
        btn_row.addWidget(self.browse_btn)
        
        preview_inner.addWidget(btn_widget)
        right_layout.addWidget(preview_group)
        
        # Trailer
        trailer_group = QGroupBox("Teaser Subsystem")
        trailer_inner = QVBoxLayout(trailer_group)
        self.trailer_label = QLabel("DISCONNECTED")
        self.trailer_label.setStyleSheet(f"color: {COLOR_BLUE}; font-weight: bold;")
        trailer_inner.addWidget(self.trailer_label)
        
        trailer_btn_row = QHBoxLayout()
        self.trailer_btn = QPushButton(" LINK TRAILER")
        self.trailer_btn.setIcon(QIcon(os.path.join(icon_path, "video.png")))
        self.trailer_btn.setIconSize(QSize(20, 20))
        self.trailer_btn.setToolTip("Associate promotional teaser.")
        self.trailer_btn.clicked.connect(self.attach_trailer)
        trailer_btn_row.addWidget(self.trailer_btn)
        
        self.clear_trailer_btn = QPushButton("❌ CLEAR")
        self.clear_trailer_btn.setStyleSheet("background: #330000; color: #FF5555; border: 1px solid #660000; min-height: 40px;")
        self.clear_trailer_btn.setToolTip("Unlink trailer so auto-trailer can regenerate.")
        self.clear_trailer_btn.clicked.connect(self.clear_trailer)
        trailer_btn_row.addWidget(self.clear_trailer_btn)
        
        trailer_inner.addLayout(trailer_btn_row)
        right_layout.addWidget(trailer_group)
        
        # Addons Subsystem
        addons_group = QGroupBox("Custom Addons / Extras")
        addons_inner = QVBoxLayout(addons_group)
        self.addons_list = QListWidget()
        self.addons_list.setMinimumHeight(100)
        self.addons_list.setStyleSheet(f"background: #000; color: {COLOR_ORANGE}; border: 1px solid {COLOR_GREY};")
        addons_inner.addWidget(self.addons_list)
        
        addon_btn_row = QHBoxLayout()
        self.add_addon_btn = QPushButton(" + ADD")
        self.add_addon_btn.setToolTip("Attach extra VODs, Twitter clips, or documents.")
        self.add_addon_btn.clicked.connect(self.attach_addon)
        addon_btn_row.addWidget(self.add_addon_btn)
        
        self.remove_addon_btn = QPushButton(" - REMOVE")
        self.remove_addon_btn.setToolTip("Detach selected extra file.")
        self.remove_addon_btn.clicked.connect(self.remove_addon)
        addon_btn_row.addWidget(self.remove_addon_btn)
        addons_inner.addLayout(addon_btn_row)
        right_layout.addWidget(addons_group)

        right_layout.addStretch()
        
        right_layout.addStretch()
        
        # Deploy
        self.save_btn = QPushButton(" LOCAL_SYNC")
        self.save_btn.setIcon(QIcon(os.path.join(icon_path, "save.png")))
        self.save_btn.setIconSize(QSize(24, 24))
        self.save_btn.setToolTip("Commit staging buffers to local hub.")
        self.save_btn.clicked.connect(self.save_metadata)
        right_layout.addWidget(self.save_btn)
        
        # Export Root Configuration
        export_root_group = QGroupBox("Deployment Configuration")
        export_root_layout = QHBoxLayout(export_root_group)
        self.export_root_input = QLineEdit()
        self.export_root_input.setText(self.config.get("export_root", ""))
        self.export_root_input.setPlaceholderText("Set base deployment folder...")
        export_root_layout.addWidget(self.export_root_input)
        
        self.browse_export_btn = QPushButton("...")
        self.browse_export_btn.setFixedWidth(30)
        self.browse_export_btn.clicked.connect(self.browse_export_root)
        export_root_layout.addWidget(self.browse_export_btn)
        
        right_layout.addWidget(export_root_group)

        self.export_btn = QPushButton(" INITIATE DEPLOYMENT")
        self.export_btn.setIcon(QIcon(os.path.join(icon_path, "deploy.png")))
        self.export_btn.setIconSize(QSize(32, 32))
        self.export_btn.setToolTip("🚨 WARNING: Destructive Pipeline Execution.")
        self.export_btn.setObjectName("Primary")
        self.export_btn.setMinimumHeight(60)
        self.export_btn.clicked.connect(self.deploy_content)
        right_layout.addWidget(self.export_btn)
        
        right_scroll.setWidget(right_panel)
        main_layout.addWidget(right_scroll)

        # Stretching
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 2)
        main_layout.setStretch(2, 1)

    # ==================== ACTIONS ====================
    
    def start_scan(self):
        raw_target = self.scan_path_input.text().strip()
        if not raw_target:
            QMessageBox.warning(self, "Invalid Path", "Please enter a directory or cloud folder.")
            return

        # 1. Cloud routing shortcut: Offload Z: drive (TntDrive) to the heavy-duty RunPod worker
        normalized_target = raw_target.replace("\\\\", "/").replace("\\", "/")
        if normalized_target.lower().startswith("z:/"):
            print("GUI: Z: drive detected. Automatically offloading scan to high-speed cloud pod worker...")
            # Convert to rclone syntax for the pod
            raw_target = "do:chloe-storage/" + normalized_target[3:]
            
        # 2. Check for Local Path
        if (os.path.exists(raw_target) or re.match(r'^[a-zA-Z]:', raw_target) or raw_target.startswith("//")) and not raw_target.lower().startswith("do:"):
            # LOCAL SCAN
            self.scan_btn.setEnabled(False)
            self.scan_btn.setText("📁 SCANNING LOCAL...")
            self.scan_progress.setVisible(True)
            self.scan_progress.setRange(0, 0) # Indeterminate
            
            try:
                from src.worker import ScanWorker # Ensure imported
                # Store worker as instance var to prevent garbage collection
                self.scan_worker = ScanWorker(raw_target)
                self.scan_worker.log.connect(print)
                self.scan_worker.finished.connect(self.on_local_scan_finished)
                self.scan_worker.start()
            except ImportError:
                QMessageBox.critical(self, "Error", "ScanWorker not found (check imports).")
                self.scan_btn.setEnabled(True)
                self.scan_progress.setVisible(False)
            return

        # 3. Assume Remote/Cloud Scan
        # Normalize slashes
        target = raw_target.replace("\\\\", "/").replace("\\", "/")
        
        # Extract core path (strip bucket and drive letters)
        bucket_prefix = "do:chloe-storage/"
        if target.lower().startswith(bucket_prefix.lower()):
            target = target[len(bucket_prefix):]
        elif target.lower().startswith("do:"):
            target = re.sub(r"^do:[^/]+/", "", target)
        
        target = re.sub(r"^[a-zA-Z]:/?", "", target).strip("/")
        final_target = f"{bucket_prefix}{target}"
        
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("📡 SCANNING CLOUD...")
        self.scan_progress.setVisible(True)
        self.scan_progress.setRange(0, 0) # Indeterminate
        
        self.scan_worker = RemoteScanWorker(final_target, self.config)
        self.scan_worker.log.connect(print) # Console log
        
        def _unlock_db():
            print("GUI: Stopping database thread for cloud sync...")
            if hasattr(db, 'stop'):
                db.stop()
            db.close()
            
        self.scan_worker.request_db_unlock.connect(_unlock_db)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.start()

    def on_local_scan_finished(self, count):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🚀 START DISCOVERY")
        self.scan_progress.setVisible(False)
        
        # Don't show all - filter to what we just scanned
        self.show_all_cb.setChecked(False)
        self.refresh_video_list(filter_path=self.scan_path_input.text().strip())
        
        QMessageBox.information(self, "Local Scan Complete", f"Found {count} new files in local folder.")

    def on_scan_finished(self, success):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🚀 START REMOTE DISCOVERY")
        self.scan_progress.setVisible(False)
        
        # Reopen DB
        print("GUI: Restarting database thread...")
        if hasattr(db, 'start'):
            db.start()
        db.connect(reuse_if_open=True)
        
        # Cloud scan: show ALL results (scan path is Z:\ but DB has do: paths)
        self.show_all_cb.setChecked(True)
        self.refresh_video_list(filter_path=None)
        
        if success:
            count = self.video_list.count()
            QMessageBox.information(self, "Scan Complete", f"Cloud synchronization successful.\n{count} pending clip(s) in hub.")
        else:
            QMessageBox.warning(self, "Scan Issue", "Scan finished with errors. Check console for details.")

    def _on_show_all_toggled(self):
        """Toggle between showing all pending clips or only the last-scanned path."""
        if self.show_all_cb.isChecked():
            self.refresh_video_list(filter_path=None)
        else:
            scan_text = self.scan_path_input.text().strip()
            self.refresh_video_list(filter_path=scan_text if scan_text else None)

    def refresh_video_list(self, filter_path=None):
        self.video_list.clear()
        self.completed_list.clear()
        try:
            # Query constraints based on status
            query_pending = Content.select().where(Content.status.in_(["pending", "pending_meta"]))
            query_completed = Content.select().where(Content.status == "completed")
            
            if filter_path and filter_path.strip():
                clean = filter_path.replace("\\", "/").rstrip("/")
                if clean:
                    query_pending = query_pending.where(Content.source_path.startswith(clean))
                    query_completed = query_completed.where(Content.source_path.startswith(clean))
            
            # Populate Pending
            for content in query_pending.order_by(Content.created_at.desc()):
                prefix = "☁️ " if content.source_path.startswith("do:") else "📁 "
                item = QListWidgetItem(prefix + os.path.basename(content.source_path))
                item.setData(Qt.UserRole, content.id)
                self.video_list.addItem(item)
                
            # Populate Completed
            for content in query_completed.order_by(Content.created_at.desc()):
                prefix = "✅ " if content.source_path.startswith("do:") else "✅📁 "
                item = QListWidgetItem(prefix + os.path.basename(content.source_path))
                item.setData(Qt.UserRole, content.id)
                item.setForeground(QColor(COLOR_GREY))
                self.completed_list.addItem(item)

        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh list: {e}")
            
        # Re-apply any active search filter after refresh
        if hasattr(self, 'search_bar') and self.search_bar.text():
            self._on_search_text_changed(self.search_bar.text())

    def _on_search_text_changed(self, text):
        """Filters the video list based on the search input for both active tabs."""
        query = text.lower()
        active_list = self.video_list if self.list_tabs.currentIndex() == 0 else self.completed_list
        for i in range(active_list.count()):
            item = active_list.item(i)
            item.setHidden(query not in item.text().lower())

    def purge_hub(self):
        reply = QMessageBox.question(self, "Confirm Purge", "Clear ALL pending records from the local hub?\n\nThis will remove all pending clips and their linked assets.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Explicitly delete assets first (SQLite cascade needs PRAGMA)
                pending_ids = [c.id for c in Content.select(Content.id).where(Content.status.in_(["pending", "pending_meta"]))]
                if pending_ids:
                    Asset.delete().where(Asset.content.in_(pending_ids)).execute()
                    Content.delete().where(Content.id.in_(pending_ids)).execute()
                
                self.selected_content = None
                self.title_input.clear()
                self.scene_id_input.setText("1")
                self.date_input.clear()
                self.description_input.clear()
                self.tags_input.clear()
                self.thumbnail_preview.setText("NO_SIGNAL")
                self.thumbnail_preview.setPixmap(QPixmap())
                self.refresh_video_list()
                QMessageBox.information(self, "Purged", f"Cleared {len(pending_ids)} pending record(s).")
            except Exception as e:
                QMessageBox.critical(self, "Purge Error", f"Failed to purge: {e}")

    def remove_selected_item(self):
        if not self.selected_content: return
        name = self.selected_content.scene_name or os.path.basename(self.selected_content.source_path or "Unknown")
        reply = QMessageBox.question(self, "Confirm Remove", f"Remove '{name}' from the inbox?\nThis deletes the database record only — source files are untouched.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                Asset.delete().where(Asset.content == self.selected_content.id).execute()
                self.selected_content.delete_instance()
                self.selected_content = None
                self.title_input.clear()
                self.description_input.clear()
                self.tags_input.clear()
                self.thumbnail_preview.setText("NO_SIGNAL")
                self.thumbnail_preview.setPixmap(QPixmap())
                self.refresh_video_list()
            except Exception as e:
                QMessageBox.critical(self, "Remove Error", f"Failed: {e}")

    def on_video_selected(self, item):
        content_id = item.data(Qt.UserRole)
        content = Content.get_or_none(Content.id == content_id)
        if content:
            self.selected_content = content
            self.load_content_to_form(content)

    def load_content_to_form(self, content):
        self.title_input.setText(content.scene_name or "")
        self.scene_id_input.setText(str(content.scene_number or 1))
        self.date_input.setText(str(content.content_date or ""))
        
        cat = content.content_category or "HQ PPV"
        idx = self.category_combo.findText(cat)
        if idx >= 0: self.category_combo.setCurrentIndex(idx)
        
        self.price_val.setText(str(content.price or 50))
        
        # Lazy Duration Extraction
        if not content.duration_seconds:
            if content.source_path.startswith("do:"):
                # Remote lazy extraction - warning: might block UI temporarily on massive files if not cached
                from src.scanner import extract_metadata_remote
                dur, _ = extract_metadata_remote(content.source_path)
                if dur:
                    content.duration_seconds = dur
                    if content.status == "pending_meta": content.status = "pending"
                    content.save()
            else:
                from src.video_utils import VideoUtils
                dur = VideoUtils.get_duration(content.source_path)
                if dur > 0:
                    content.duration_seconds = int(dur)
                    if content.status == "pending_meta": content.status = "pending"
                    content.save()
        
        if content.duration_seconds:
            h = content.duration_seconds // 3600
            m = (content.duration_seconds % 3600) // 60
            s = content.duration_seconds % 60
            self.duration_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        else:
            self.duration_label.setText("??:??:??")
        
        # Lazy Aspect Ratio Probing
        ar = content.video_aspect_ratio
        if not ar:
            if not content.source_path.startswith("do:"):
                from src.video_utils import VideoUtils
                ar = VideoUtils.get_aspect_ratio(content.source_path)
                content.video_aspect_ratio = ar
                content.save()
            else:
                ar = "16:9" # Fallback for remote files to save time, or we could probe if needed
        
        ar = ar or "16:9"
        idx = self.aspect_combo.findText(ar)
        if idx >= 0: self.aspect_combo.setCurrentIndex(idx)
        
        # Trailer Aspect Ratio
        if content.trailer_path and not content.trailer_aspect_ratio and os.path.exists(content.trailer_path):
            from src.video_utils import VideoUtils
            content.trailer_aspect_ratio = VideoUtils.get_aspect_ratio(content.trailer_path)
            content.save()
            
        # Thumbnail Aspect Ratio
        if content.thumbnail_path and not content.thumbnail_aspect_ratio and os.path.exists(content.thumbnail_path):
            from src.video_utils import VideoUtils
            content.thumbnail_aspect_ratio = VideoUtils.get_aspect_ratio(content.thumbnail_path)
            content.save()
        
        self.description_input.setText(content.ai_description or "")
        self.tags_input.setText(content.ai_tags or "")
        
        # Enable/Show Re-Judge if sensor log exists
        if content.sensor_log_raw:
            self.re_judge_btn.setVisible(True)
        else:
            self.re_judge_btn.setVisible(False)
            
        self.update_path_preview()
        
        # Trailer
        self.trailer_label.setText(os.path.basename(content.trailer_path) if content.trailer_path else "Not Linked")
        
        # Addons
        self.addons_list.clear()
        from src.database import Asset
        linked_addons = Asset.select().where((Asset.content == content) & (Asset.asset_type == "addon"))
        for addon in linked_addons:
            self.addons_list.addItem(os.path.basename(addon.local_path))
        
        # Thumbnail
        thumb_path = content.thumbnail_path
        # Re-map if it's still using the remote path prefix but exists locally
        if thumb_path and thumb_path.startswith("/workspace"):
            fname = os.path.basename(thumb_path)
            local_alt = os.path.normpath(os.path.join(os.path.dirname(__file__), ".thumbnails", fname))
            if os.path.exists(local_alt):
                thumb_path = local_alt
        
        if thumb_path and os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            self.thumbnail_preview.setPixmap(pixmap.scaled(350, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.thumbnail_preview.setText(f"SIGNAL_LOST\n({os.path.basename(thumb_path) if thumb_path else 'EMPTY'})")
            self.thumbnail_preview.setPixmap(QPixmap()) # Clear previous

    def update_path_preview(self):
        if not self.selected_content:
            self.path_preview_lbl.setText("NO_CLIP_SELECTED")
            return
        
        category = self.category_combo.currentText()
        title = self.title_input.text() or "UNKNOWN_TITLE"
        # Sanitize title for filename
        ext = os.path.splitext(self.selected_content.source_path)[1] or ".mp4"
        
        # Standardized naming using unified utility
        date_str = self.date_input.text() or None
        scene_id = self.scene_id_input.text() or "1"
        file_base = StandardNaming.get_file_name(scene_id, date_str, title, ext="")
        meta_base = StandardNaming.get_meta_name(scene_id, date_str)
            
        preview = f"DEPLOY_TARGET:\n/{category}/{title}/\n├── {file_base}{ext}\n└── {meta_base}"
        self.path_preview_lbl.setText(preview)

    def force_refresh_duration(self):
        if not self.selected_content: return
        source = self.selected_content.source_path
        dur = 0
        
        if source.startswith("do:"):
            # REMOTE REFRESH for Cloud Clips
            QMessageBox.information(self, "Cloud Request", "Sending duration probe command via remote tunnel...")
            QApplication.processEvents()
            from src.scanner import extract_metadata_remote
            dur, _ = extract_metadata_remote(source)
        else:
            from src.video_utils import VideoUtils
            dur = VideoUtils.get_duration(source)
            
        if dur and dur > 0:
            self.selected_content.duration_seconds = int(dur)
            self.selected_content.save()
            self.load_content_to_form(self.selected_content)
            QMessageBox.information(self, "Success", f"Duration updated: {int(dur)}s")
        else:
            QMessageBox.warning(self, "Failed", "Duration extraction returned 0. Verify file is valid or check network connection.")

    def save_metadata(self, silent=False):
        if not self.selected_content: return
        
        self.selected_content.scene_name = self.title_input.text()
        try:
            self.selected_content.scene_number = int(self.scene_id_input.text() or 1)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Scene ID must be a number.")
            return
        
        # Parse Date
        date_val = self.date_input.text().strip()
        if date_val:
            try:
                # Basic check for YYYY-MM-DD
                if not re.match(r"\d{4}-\d{2}-\d{2}", date_val):
                    raise ValueError
                self.selected_content.content_date = date_val
            except:
                QMessageBox.warning(self, "Invalid Date", "Format: YYYY-MM-DD")
                return
        
        self.selected_content.content_category = self.category_combo.currentText()
        try:
            self.selected_content.price = int(self.price_val.text())
        except:
            self.selected_content.price = 50
        self.selected_content.video_aspect_ratio = self.aspect_combo.currentText()
        self.selected_content.ai_description = self.description_input.toPlainText()
        self.selected_content.ai_tags = self.tags_input.text()
        self.selected_content.tags = self.tags_input.text()
        self.selected_content.save()
        if not silent:
            QMessageBox.information(self, "Staging Saved", "Metadata buffers committed to local hub.")

    def adjust_price(self, delta):
        try:
            val = int(self.price_val.text())
            new_val = max(0, min(995, val + delta))
            self.price_val.setText(str(new_val))
        except:
            self.price_val.setText("50")

    def run_ai_tagger(self):
        if not self.selected_content: return
        
        thumb_path = self.selected_content.thumbnail_path
        
        # Auto-extract a thumbnail if one doesn't exist
        if not thumb_path or not os.path.exists(thumb_path):
            source = self.selected_content.source_path
            if source and not source.startswith("do:") and os.path.exists(source):
                from src.video_utils import VideoUtils
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="forager_vlm_")
                candidate = VideoUtils.random_thumbnail_candidate(source, temp_dir)
                if candidate:
                    thumb_path = candidate
                    self.selected_content.thumbnail_path = candidate
                    self.selected_content.save()
                    self.load_content_to_form(self.selected_content)
                else:
                    QMessageBox.warning(self, "Need Image", "Could not auto-extract a thumbnail. Please extract one manually first.")
                    return
            else:
                QMessageBox.warning(self, "Need Image", "Please extract or randomize a thumbnail frame first for AI analysis.")
                return
        
        # Save any user-inputted text fields BEFORE blocking, so they don't revert
        self.save_metadata(silent=True)
        
        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("🧬 ANALYZING WITH VLM...")
        QApplication.processEvents()
        
        try:
            # Extract 10 frames from the clip for the VLM to see
            temp_frames = []
            source = self.selected_content.source_path
            duration = self.selected_content.duration_seconds
            
            burst_points = []
            if duration:
                # Action Burst Overhaul v3: 10 clusters evenly spaced (High-Res Forensic Scan)
                burst_points = [
                    duration * 0.1, duration * 0.2, duration * 0.3, 
                    duration * 0.4, duration * 0.5, duration * 0.6,
                    duration * 0.7, duration * 0.8, duration * 0.9, 
                    (duration * 0.5) + 2.0
                ]
            
            if source and not source.startswith("do:") and os.path.exists(source) and duration:
                from src.video_utils import VideoUtils
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="vlm_batch_")
                frame_idx = 1
                for base_ts in burst_points:
                    for offset in [0, 0.5, 1.0, 1.5]:
                        ts = min(duration - 0.05, base_ts + offset)
                        fmeta = os.path.join(temp_dir, f"frame_{frame_idx}.png")
                        # High-Res Forensic Scan: 1280px + Brightening
                        if VideoUtils.extract_frame(source, ts, fmeta, width=1280, brighten=True):
                            temp_frames.append(fmeta)
                        frame_idx += 1
            elif source and source.startswith("do:") and duration:
                # CLOUD CLIPS: Extract frames remotely on the pod (it has rclone+ffmpeg)
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="vlm_batch_")
                
                self.ai_btn.setText("🧬 EXTRACTING FRAMES ON POD...")
                QApplication.processEvents()
                
                from src.utils import resolve_ssh_details
                host, port = resolve_ssh_details(self.config)
                ssh_key = self.config.get("ssh_key", "~/.ssh/id_ed25519").replace("\\", "/")
                ssh_key = os.path.expanduser(ssh_key)
                
                # Build timestamp list: 10 burst points × 4 offsets = 40 frames
                timestamps = []
                for base_ts in burst_points:
                    for offset in [0, 0.5, 1.0, 1.5]:
                        timestamps.append(min(duration - 0.05, base_ts + offset))
                
                ts_list_str = ",".join([f"{t:.2f}" for t in timestamps])
                remote_dir = "/workspace/vlm_frames"
                
                # Download clip from cloud via rclone on pod, then extract frames with ffmpeg
                extract_script = (
                    f'set -e; '
                    f'TMPVID="/workspace/vlm_temp_video.mp4"; '
                    f'mkdir -p {remote_dir}; rm -f {remote_dir}/*.png; '
                    f'echo "Downloading clip from cloud..."; '
                    f'rclone copyto "{source}" "$TMPVID" 2>&1 | tail -1; '
                    f'echo "Extracting frames..."; '
                    f'IDX=1; for TS in {ts_list_str.replace(",", " ")}; do '
                    f'  ffmpeg -y -ss $TS -i "$TMPVID" '
                    f'  -frames:v 1 -q:v 2 -vf "scale=1280:-1,eq=brightness=0.3:contrast=1.4:saturation=1.2" '
                    f'  {remote_dir}/frame_$IDX.png 2>/dev/null; '
                    f'  IDX=$((IDX+1)); '
                    f'done; '
                    f'TOTAL=$(ls {remote_dir}/*.png 2>/dev/null | wc -l); '
                    f'echo "FRAMES_READY:$TOTAL"; '
                    f'rm -f "$TMPVID"'
                )
                
                ssh_cmd = [
                    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                    "-i", ssh_key, "-p", str(port), f"root@{host}",
                    f"bash -c '{extract_script}'"
                ]
                
                print(f"REMOTE FRAME EXTRACT: Extracting {len(timestamps)} frames on pod...")
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
                print(f"POD OUTPUT: {result.stdout}")
                if result.stderr:
                    print(f"POD STDERR: {result.stderr[-200:]}")
                
                # Parse frame count
                frame_count = 0
                for line in result.stdout.strip().split("\n"):
                    if "FRAMES_READY:" in line:
                        frame_count = int(line.split(":")[1].strip())
                
                if frame_count > 0:
                    # SCP all frames back
                    self.ai_btn.setText(f"🧬 DOWNLOADING {frame_count} FRAMES...")
                    QApplication.processEvents()
                    
                    scp_cmd = [
                        "scp", "-o", "StrictHostKeyChecking=no",
                        "-P", str(port), "-i", ssh_key,
                        f"root@{host}:{remote_dir}/*.png", temp_dir
                    ]
                    scp_res = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=120)
                    
                    if scp_res.returncode == 0:
                        # Collect downloaded frames in order
                        for i in range(1, len(timestamps) + 1):
                            fpath = os.path.join(temp_dir, f"frame_{i}.png")
                            if os.path.exists(fpath):
                                temp_frames.append(fpath)
                        print(f"REMOTE EXTRACT SUCCESS: {len(temp_frames)} frames downloaded.")
                    else:
                        print(f"SCP failed: {scp_res.stderr}")
                
                if not temp_frames:
                    print("Remote extraction failed — falling back to thumbnail.")
                    temp_frames = [thumb_path]
            else:
                # Fallback to single thumbnail if video not local/probed
                temp_frames = [thumb_path]

            api_url = self.config.get("vlm_endpoint", self.config.get("vlm_api_url", "http://localhost:11434/v1"))
            model = self.config.get("vlm_model", "gemma3-heretic:12b")
            audit_model = self.config.get("vlm_audit_model")
            
            # Pack SSH details for direct pod access (bypass proxy)
            ssh_config = {
                "host": self.config.get("ssh_host"),
                "port": self.config.get("ssh_port", 22),
                "ssh_key": self.config.get("ssh_key")
            }
            
            from src.vlm import VLMClient
            vlm = VLMClient(api_url, model_name=model, audit_model=audit_model, ssh_config=ssh_config)
            result = vlm.get_metadata_from_video(temp_frames)
            
            if result:
                self.description_input.setText(result.get("description", ""))
                self.tags_input.setText(", ".join(result.get("tags", [])))
                self.selected_content.sensor_log_raw = result.get("sensor_log_raw")
                self.save_metadata(silent=True)
                
                # --- AUTO TRAILER GENERATION ---
                best_burst_index = result.get("best_burst_index", 0)
                max_intensity = result.get("max_intensity", -1)
                
                if not self.selected_content.trailer_path and burst_points:
                    import time
                    best_ts = burst_points[0]
                    if best_burst_index < len(burst_points):
                        best_ts = burst_points[best_burst_index]
                    
                    print(f"AUTO-TRAILER: trailer_path is empty, generating...")
                    print(f"AUTO-TRAILER: best_burst_index={best_burst_index}, best_ts={best_ts:.1f}s, max_intensity={max_intensity}/10")
                    
                    if max_intensity > -1:
                        self.ai_btn.setText(f"🎬 GENERATING TRAILER (ACTION: {max_intensity}/10)...")
                        QApplication.processEvents()
                        
                        start_time = max(0, min(best_ts, duration - 15))
                        import tempfile
                        trailer_dir = os.path.dirname(source) if source and not source.startswith("do:") else os.path.join(tempfile.gettempdir(), "data_forager")
                        os.makedirs(trailer_dir, exist_ok=True)
                        trailer_path = os.path.join(trailer_dir, f"auto_trailer_{int(time.time())}.mp4").replace("\\", "/")
                        
                        if source and source.startswith("do:"):
                            # Remote cloud extraction over HTTP via rclone on pod
                            try:
                                from src.utils import resolve_ssh_details
                                host, port = resolve_ssh_details(self.config)
                                ssh_key = os.path.expanduser(self.config.get("ssh_key", "~/.ssh/id_ed25519").replace("\\", "/"))
                                
                                remote_trailer_dir = "/workspace/vlm_trailers"
                                remote_trailer_file = f"{remote_trailer_dir}/auto_trailer.mp4"
                                trailer_script = (
                                    f'set -e; '
                                    f'TMPVID="/workspace/vlm_temp_video.mp4"; '
                                    f'mkdir -p {remote_trailer_dir}; rm -f {remote_trailer_file}; '
                                    f'rclone copyto "{source}" "$TMPVID" 2>&1 | tail -1; '
                                    f'ffmpeg -y -ss {start_time} -t 15 -i "$TMPVID" -vf "crop=min(ih\\,iw):min(ih\\,iw):(iw-min(ih\\,iw))/2:(ih-min(ih\\,iw))/2" -c:v libx264 -preset fast -crf 22 -c:a aac {remote_trailer_file} 2>/dev/null; '
                                    f'rm -f "$TMPVID"'
                                )
                                ssh_cmd = [
                                    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                                    "-i", ssh_key, "-p", str(port), f"root@{host}",
                                    f"bash -c '{trailer_script}'"
                                ]
                                subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
                                
                                # SCP the finished trailer back to local Temp
                                scp_cmd = [
                                    "scp", "-o", "StrictHostKeyChecking=no",
                                    "-P", str(port), "-i", ssh_key,
                                    f"root@{host}:{remote_trailer_file}", trailer_path
                                ]
                                scp_res = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=120)
                                if scp_res.returncode == 0 and os.path.exists(trailer_path):
                                    self.selected_content.trailer_path = trailer_path
                            except Exception as e:
                                print(f"Remote trailer generation failed: {e}")
                        else:
                            # Local file generation
                            from src.video_utils import VideoUtils
                            success = VideoUtils.generate_clip(source, start_time, 15, trailer_path, ratio_1_1=True)
                            if success and os.path.exists(trailer_path):
                                self.selected_content.trailer_path = trailer_path
                                
                        self.selected_content.save()
                        self.load_content_to_form(self.selected_content)
                self.re_judge_btn.setVisible(True)
                QMessageBox.information(self, "AI Success", "VLM Scene Analysis synchronized.")
            else:
                QMessageBox.warning(self, "Fail", "VLM returned empty results.")
        except Exception as e:
            QMessageBox.critical(self, "AI Failure", f"VLM Engine Error: {e}")
        finally:
            self.ai_btn.setEnabled(True)
            self.ai_btn.setText("🧠 TRIGGER AI VLM ANALYSIS")

    def run_re_judge_tagger(self):
        if not self.selected_content or not self.selected_content.sensor_log_raw:
            return
            
        self.save_metadata(silent=True)
        self.re_judge_btn.setEnabled(False)
        self.re_judge_btn.setText("⚖️ AUDITING...")
        QApplication.processEvents()
        
        try:
            api_url = self.config.get("vlm_endpoint", self.config.get("vlm_api_url", "http://localhost:11434/v1"))
            model = self.config.get("vlm_model", "gemma3-heretic:12b")
            audit_model = self.config.get("vlm_audit_model")
            
            # Pack SSH details for direct pod access (bypass proxy)
            ssh_config = {
                "host": self.config.get("ssh_host"),
                "port": self.config.get("ssh_port", 22),
                "ssh_key": self.config.get("ssh_key")
            }
            
            from src.vlm import VLMClient
            vlm = VLMClient(api_url, model_name=model, audit_model=audit_model, ssh_config=ssh_config)
            
            result = vlm.re_judge_metadata(self.selected_content.sensor_log_raw)
            
            if result:
                self.description_input.setText(result.get("description", ""))
                self.tags_input.setText(", ".join(result.get("tags", [])))
                self.save_metadata()
                QMessageBox.information(self, "Re-Judge Success", "Forensic Audit re-executed successfully.")
            else:
                QMessageBox.warning(self, "Fail", "Re-Judge returned empty results.")
        except Exception as e:
            QMessageBox.critical(self, "Re-Judge Failure", f"VLM Engine Error: {e}")
        finally:
            self.re_judge_btn.setEnabled(True)
            self.re_judge_btn.setText(" ⚖️ RE-JUDGE")
            
    def save_config(self):
        """Save the current self.config dictionary to config.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def extract_thumbnail(self):
        if not self.selected_content: return
        
        source = self.selected_content.source_path
        if source.startswith("do:"):
            # Check if we already have a synced thumb
            if self.selected_content.thumbnail_path and os.path.exists(self.selected_content.thumbnail_path):
                QMessageBox.information(self, "Cloud Clip", "Remote thumbnail already synchronized from pod cluster.")
                return
            QMessageBox.information(self, "Cloud Clip", "Direct extraction from cloud requires sector re-sync.")
            return
        
        if not os.path.exists(source):
            QMessageBox.warning(self, "Error", f"File not found: {source}")
            return

        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("🎬 ...")
        QApplication.processEvents()
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="forager_")
            candidates = VideoUtils.extract_thumbnail_candidates(source, temp_dir, num_frames=1)
            if candidates:
                target_dir = os.path.join(os.path.dirname(source), ".thumbnails")
                os.makedirs(target_dir, exist_ok=True)
                target = os.path.join(target_dir, f"THUMB_{self.selected_content.id}.png")
                shutil.move(candidates[0], target)
                self.selected_content.thumbnail_path = target
                self.selected_content.save()
                self.load_content_to_form(self.selected_content)
                QMessageBox.information(self, "Success", "Master Thumbnail synchronized.")
            else:
                QMessageBox.warning(self, "Extraction Failed", "FFmpeg could not extract a frame. Check if video is corrupted or duration is 0.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed: {e}")
        finally:
            self.extract_btn.setEnabled(True)
            self.extract_btn.setText("🎬 EXTRACT")

    def randomize_thumbnail(self):
        if not self.selected_content: return
        
        from src.video_utils import VideoUtils
        import tempfile, shutil
        
        source = self.selected_content.source_path
        if source.startswith("do:"):
            # CLOUD CLIPS: SSH to pod, extract there (pod has rclone+ffmpeg), scp thumbnail back
            self.random_btn.setEnabled(False)
            self.random_btn.setText("🎲 REMOTE EXTRACT...")
            QApplication.processEvents()
            
            try:
                host, port = resolve_ssh_details(self.config)
                if not host or not port:
                    raise Exception("Could not resolve SSH details for remote pod.")
                
                ssh_key = self.config.get("ssh_key", "~/.ssh/id_ed25519").replace("\\", "/")
                ssh_key = os.path.expanduser(ssh_key)
                
                # Generate a unique thumbnail name
                import hashlib
                fname = os.path.basename(source)
                fhash = hashlib.md5(fname.encode()).hexdigest()[:8]
                remote_thumb = f"/workspace/src/.thumbnails/THUMB_{fhash}.png"
                
                # SSH: run python one-liner to extract random thumbnail on the pod
                extract_cmd = (
                    f'python3 -c "'
                    f'import sys; sys.path.insert(0, \\\"/workspace\\\"); '
                    f'from src.scanner import extract_random_thumbnail; '
                    f'r = extract_random_thumbnail(\\\"{source}\\\"); '
                    f'print(\\\"SUCCESS:\\\" + r if r else \\\"FAILED\\\")'
                    f'"'
                )
                
                ssh_cmd = [
                    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                    "-i", ssh_key, "-p", str(port), f"root@{host}",
                    extract_cmd
                ]
                
                self.random_btn.setText("🎲 POD EXTRACTING...")
                QApplication.processEvents()
                
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=90)
                out = result.stdout.strip()
                
                if "SUCCESS:" in out:
                    remote_path = out.split("SUCCESS:")[1].strip()
                    
                    # SCP just this one thumbnail back
                    thumb_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".thumbnails"))
                    os.makedirs(thumb_dir, exist_ok=True)
                    local_target = os.path.join(thumb_dir, f"THUMB_{self.selected_content.id}.png")
                    
                    scp_cmd = [
                        "scp", "-o", "StrictHostKeyChecking=no",
                        "-P", str(port), "-i", ssh_key,
                        f"root@{host}:{remote_path}", local_target
                    ]
                    
                    self.random_btn.setText("🎲 DOWNLOADING...")
                    QApplication.processEvents()
                    
                    scp_res = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
                    
                    if scp_res.returncode == 0 and os.path.exists(local_target):
                        self.selected_content.thumbnail_path = local_target
                        self.selected_content.save()
                        self.load_content_to_form(self.selected_content)
                        QMessageBox.information(self, "Cloud Success", "Thumbnail extracted from cloud clip!")
                    else:
                        raise Exception(f"SCP failed: {scp_res.stderr[:200]}")
                else:
                    err = result.stderr.strip()[:200] if result.stderr else out[:200]
                    raise Exception(f"Pod extraction failed: {err}")
                    
            except subprocess.TimeoutExpired:
                QMessageBox.warning(self, "Timeout", "Remote extraction timed out (90s). The pod may be busy.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Cloud Randomization Failed: {e}")
            finally:
                self.random_btn.setEnabled(True)
                self.random_btn.setText("🎲 RANDOMIZE")
            return
        
        if not os.path.exists(source):
            QMessageBox.warning(self, "Error", f"File not found: {source}")
            return

        self.random_btn.setEnabled(False)
        self.random_btn.setText("🎲 ...")
        QApplication.processEvents()
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="forager_")
            candidate = VideoUtils.random_thumbnail_candidate(source, temp_dir)
            if candidate:
                target_dir = os.path.join(os.path.dirname(source), ".thumbnails")
                os.makedirs(target_dir, exist_ok=True)
                target = os.path.join(target_dir, f"THUMB_{self.selected_content.id}.png")
                shutil.move(candidate, target)
                self.selected_content.thumbnail_path = target
                self.selected_content.save()
                self.load_content_to_form(self.selected_content)
            else:
                QMessageBox.warning(self, "Extraction Failed", "FFmpeg could not extract a random frame.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed: {e}")
        finally:
            self.random_btn.setEnabled(True)
            self.random_btn.setText("🎲 RANDOMIZE")

    def browse_thumbnail(self):
        if not self.selected_content: return
        path, _ = QFileDialog.getOpenFileName(self, "Link Visual Asset", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_content.thumbnail_path = path
            self.selected_content.save(); self.load_content_to_form(self.selected_content)

    def attach_trailer(self):
        if not self.selected_content: return
        path, _ = QFileDialog.getOpenFileName(self, "Link Trailer Asset", "", "Videos (*.mp4 *.mov)")
        if path:
            self.selected_content.trailer_path = path
            self.selected_content.save(); self.trailer_label.setText(os.path.basename(path))

    def clear_trailer(self):
        if not self.selected_content: return
        self.selected_content.trailer_path = None
        self.selected_content.trailer_aspect_ratio = None
        self.selected_content.save()
        self.trailer_label.setText("DISCONNECTED")

    def browse_export_root(self):
        path = QFileDialog.getExistingDirectory(self, "Select Deployment Root")
        if path:
            self.export_root_input.setText(path)
            self.config["export_root"] = path
            self.save_config()

    def add_toy_tag(self, tag):
        """Appends a manual tag to the tags list if not already present."""
        current_text = self.tags_input.text()
        current_tags = [t.strip() for t in current_text.split(',') if t.strip()]
        
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags_input.setText(", ".join(current_tags))
            self.save_metadata(silent=True) # Auto-persists to buffer without annoying popup

    def attach_addon(self):
        if not self.selected_content: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Addon File")
        if file_path:
            from src.database import Asset
            Asset.create(content=self.selected_content, asset_type="addon", local_path=file_path, status="pending")
            self.addons_list.addItem(os.path.basename(file_path))
            
    def remove_addon(self):
        item = self.addons_list.currentItem()
        if not item or not self.selected_content: return
        
        from src.database import Asset
        filename = item.text()
        Asset.delete().where((Asset.content == self.selected_content) & (Asset.local_path.contains(filename))).execute()
        self.addons_list.takeItem(self.addons_list.row(item))

    def deploy_content(self):
        # 1. Force save current GUI state to DB object
        self.save_metadata()
        
        if not self.selected_content or not self.selected_content.scene_name:
            QMessageBox.warning(self, "Invalid", "Set Title before deployment.")
            return
        
        root = self.export_root_input.text().strip()
        if not root:
            root = QFileDialog.getExistingDirectory(self, "Select Deployment Root")
            if not root: return
            self.export_root_input.setText(root)
            self.config["export_root"] = root
            self.save_config()
        
        import shutil
        c = self.selected_content
        
        # Deploy directly into the export root — no category subfolder nesting
        deploy_base = root.replace("\\", "/").rstrip("/")
            
        # Sanitize folder name
        clean_title = re.sub(r'[\\/*?:"<>|]', "", c.scene_name).strip()
        folder = os.path.join(deploy_base, clean_title).replace("\\", "/")
        os.makedirs(folder, exist_ok=True)
        
        date_str = c.content_date or datetime.date.today().strftime("%Y-%m-%d")
        safe_date = str(date_str).replace("_", "-") # Standardize on dashes for legacy compatibility
        
        # Standardized naming: [TYPE]_[ID]_[DATE]
        cat_type = "PPV"
        if "SEMI" in c.content_category.upper(): cat_type = "SEMI"
        elif "STREAM" in c.content_category.upper(): cat_type = "STREAM"
        
        # Use user-defined scene number, fallback to ID if 0/None
        sid = c.scene_number if c.scene_number else c.id
        file_base = f"{cat_type}_{sid}_{safe_date}"

        # Duration HH:MM:SS
        seconds = c.duration_seconds or 0
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        duration_hms = f"{h:02d}:{m:02d}:{s:02d}"

        # 1. Move/Copy Video
        if c.source_path.startswith("do:"):
            # Remote file -> Rclone Download
            ext = os.path.splitext(c.source_path)[1]
            dest_video = os.path.join(folder, f"{file_base}{ext}").replace("\\", "/")
            print(f"DEPLOY: Downloading remote master: {c.source_path} -> {dest_video}")
            
            try:
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                # Fetch DO credentials to use as environment variables
                do_access = self.config.get("do_access_key", "")
                do_secret = self.config.get("do_secret_key", "")
                do_endpoint = self.config.get("do_endpoint", "nyc3.digitaloceanspaces.com")
                
                # Use environment variables instead of temporary files for better security
                env = os.environ.copy()
                env["RCLONE_CONFIG_DO_TYPE"] = "s3"
                env["RCLONE_CONFIG_DO_PROVIDER"] = "DigitalOcean"
                env["RCLONE_CONFIG_DO_ACCESS_KEY_ID"] = do_access
                env["RCLONE_CONFIG_DO_SECRET_ACCESS_KEY"] = do_secret
                env["RCLONE_CONFIG_DO_ENDPOINT"] = do_endpoint
                env["RCLONE_CONFIG_DO_ACL"] = "private"
                
                # Look for rclone.exe using ConfigManager
                rclone_exe = ConfigManager.get_rclone_exe()
                
                if not os.path.exists(rclone_exe) and not shutil.which("rclone"):
                    QMessageBox.critical(self, "Rclone Missing",
                        "rclone.exe not found!\n\n"
                        "Install with: winget install Rclone.Rclone\n"
                        "Or set 'rclone_path' in config.json to the full path.")
                    return
                
                # Execute copyto using the 'do:' remote prefix which rclone will now find in environment
                subprocess.run([rclone_exe, "copyto", c.source_path, dest_video], 
                               check=True, startupinfo=startupinfo, env=env)
                
            except Exception as e:
                QMessageBox.critical(self, "Download Failed", f"Rclone error: {e}")
                return

        elif os.path.exists(c.source_path):
            ext = os.path.splitext(c.source_path)[1]
            dest_video = os.path.join(folder, f"{file_base}{ext}").replace("\\", "/")
            shutil.copy2(c.source_path, dest_video)
        else:
            QMessageBox.warning(self, "Missing Source", f"Source file not found:\n{c.source_path}")
            return
        
        # 2. Move/Copy Trailer
        trailer_filename = "N/A"
        dest_trailer_full = "N/A"
        trailer_ar = "N/A"
        if c.trailer_path and os.path.exists(c.trailer_path):
            from src.video_utils import VideoUtils
            trailer_ar = VideoUtils.get_aspect_ratio(c.trailer_path)
            c.trailer_aspect_ratio = trailer_ar
            
            t_ext = os.path.splitext(c.trailer_path)[1]
            trailer_filename = f"TRAILER_{sid}_{safe_date}{t_ext}" 
            dest_trailer_full = os.path.join(folder, trailer_filename)
            shutil.copy2(c.trailer_path, dest_trailer_full)

        # 3. Move Thumbnail
        thumb_filename = "N/A"
        dest_thumb_full = "N/A"
        thumb_ar = "N/A"
        if c.thumbnail_path and os.path.exists(c.thumbnail_path):
            from src.video_utils import VideoUtils
            thumb_ar = VideoUtils.get_aspect_ratio(c.thumbnail_path)
            c.thumbnail_aspect_ratio = thumb_ar
            
            t_ext = os.path.splitext(c.thumbnail_path)[1]
            thumb_filename = f"THUMBNAIL_{sid}_{safe_date}{t_ext}"
            dest_thumb_full = os.path.join(folder, thumb_filename)
            shutil.copy2(c.thumbnail_path, dest_thumb_full)

        # 4. Create Standardized METADATA_[id]_[date].txt (EXACT user format)
        meta_path = os.path.join(folder, f"METADATA_{sid}_{safe_date}.txt")
        video_ext = os.path.splitext(c.source_path)[1]
        with open(meta_path, "w") as f:
            f.write(f"Title: {c.scene_name}\n\n")
            f.write(f"Video File Name: {file_base}{video_ext}\n")
            f.write(f"Video File Aspect Ratio: {c.video_aspect_ratio or '16:9'}\n\n")
            f.write(f"Trailer File Name: {trailer_filename}\n")
            f.write(f"Trailer File Aspect Ratio: {trailer_ar}\n\n")
            f.write(f"Thumbnail File Name: {thumb_filename}\n")
            f.write(f"Thumbnail File Aspect Ratio: {thumb_ar}\n\n")
            f.write(f"Duration: {duration_hms}\n\n")
            f.write(f"Price: {c.price}$\n\n")
            f.write(f"Description: {c.ai_description or ''}\n\n")
            f.write(f"Tags: {c.tags or ''}\n")
        # 5. Move/Copy Custom Addons
        from src.database import Asset
        addons = Asset.select().where((Asset.content == c) & (Asset.asset_type == "addon"))
        for i, addon in enumerate(addons):
            if os.path.exists(addon.local_path):
                a_name = os.path.basename(addon.local_path)
                a_ext = os.path.splitext(a_name)[1]
                # Standardized Addon Naming: ADDON_[ID]_[DATE]_[Index]_[OrigName]
                addon_filename = f"ADDON_{sid}_{safe_date}_{i+1}_{a_name}"
                shutil.copy2(addon.local_path, os.path.join(folder, addon_filename))
        
        c.status = "completed"
        c.save()
        self.refresh_video_list()
        QMessageBox.information(self, "DEPLOYED", f"Pipeline finalized at: {folder}")
        
    def update_system_status(self, text, color):
        if hasattr(self, 'status_lbl'):
            self.status_lbl.setText(text)
            self.status_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; background: #000; padding: 5px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DataForagerV2()
    gui.show()
    sys.exit(app.exec())
