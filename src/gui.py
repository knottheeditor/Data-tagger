import sys
import os
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTreeView, 
                               QProgressBar, QTextEdit, QFrame, QSplitter, QCheckBox,
                               QMenu, QInputDialog, QStackedWidget, QLineEdit)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QPoint
from PySide6.QtGui import QColor, QPalette, QFont, QStandardItemModel, QStandardItem, QAction, QPainter, QPen
import json
import requests

# Import backend logic
from src.database import Content, Asset, db, DB_PATH
from src.scanner import scan_directory

# Astropunk Theme Colors
BG_DARK = "#0D0D1A"
BG_CARD = "#16213E"
BG_PANEL = "#0F3460"
ACCENT_PURPLE = "#7B2CBF"
ACCENT_TEAL = "#00D9FF"
ACCENT_RED = "#E94560"
TEXT_PRIMARY = "#E0E0E0"
TEXT_SECONDARY = "#A0A0C0"

# --- WIZARD COMPONENTS ---

class WizardStepper(QWidget):
    def __init__(self, steps=["MASTER", "NAMING", "ASSETS", "AI", "DEPLOY"]):
        super().__init__()
        self.steps = steps
        self.current_step = 1
        self.setMinimumHeight(60)
        
    def set_step(self, step):
        self.current_step = step
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        margin = 40
        step_width = (width - 2*margin) / (len(self.steps) - 1) if len(self.steps) > 1 else width
        
        # Draw Line
        pen = QPen(QColor(40, 40, 60), 3)
        painter.setPen(pen)
        painter.drawLine(margin, 30, width - margin, 30)
        
        # Draw Progress Line
        progress_end = margin + (self.current_step - 1) * step_width
        pen.setColor(QColor(ACCENT_TEAL))
        painter.setPen(pen)
        painter.drawLine(margin, 30, progress_end, 30)
        
        # Draw Nodes
        for i, name in enumerate(self.steps):
            x = margin + i * step_width
            is_active = (i + 1) == self.current_step
            is_done = (i + 1) < self.current_step
            
            # Node Circle
            color = QColor(ACCENT_TEAL) if (is_active or is_done) else QColor(40, 40, 60)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            size = 7 if is_active else 5
            painter.drawEllipse(QPoint(int(x), 30), size, size)
            
            # Label
            font = QFont("JetBrains Mono", 8, QFont.Bold if is_active else QFont.Normal)
            painter.setFont(font)
            painter.setPen(color)
            painter.drawText(int(x - 40), 45, 80, 20, Qt.AlignCenter, name)

ASTROPUNK_QSS = f"""
QMainWindow {{
    background-color: {BG_DARK};
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: 'Outfit', 'Inter', 'SF Pro Display', sans-serif;
    font-size: 13px;
}}

QLabel#Header {{
    font-size: 16px;
    font-weight: 900;
    color: {ACCENT_TEAL};
    letter-spacing: 2px;
    margin-bottom: 10px;
    text-transform: uppercase;
}}

QFrame#Panel {{
    background-color: {BG_CARD};
    border-radius: 12px;
    border: 1px solid rgba(0, 217, 255, 0.15);
}}

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT_PURPLE}, stop:1 #480CA8);
    border-radius: 8px;
    padding: 12px;
    font-weight: 800;
    border: 1px solid rgba(255,255,255,0.1);
    color: white;
    text-transform: uppercase;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #9D4EDD, stop:1 {ACCENT_PURPLE});
    border: 1px solid {ACCENT_TEAL};
}}

QPushButton#Secondary {{
    background: transparent;
    border: 1px solid {ACCENT_PURPLE};
    color: {ACCENT_PURPLE};
}}

QPushButton#Danger {{
    background: transparent;
    border: 1px solid {ACCENT_RED};
    color: {ACCENT_RED};
}}

QPushButton#Danger:hover {{
    background: {ACCENT_RED};
    color: white;
}}

QPushButton#Special {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00D9FF, stop:1 #0077B6);
    color: black;
    border: none;
}}

QPushButton#DiscoveryBrand {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00D9FF, stop:0.5 #7B2CBF, stop:1 {ACCENT_RED});
    color: white;
    font-size: 15px;
    font-weight: 900;
    padding: 20px;
    border: 2px solid white;
    letter-spacing: 2px;
}}

QProgressBar {{
    background-color: #050510;
    border-radius: 6px;
    text-align: center;
    border: 1px solid rgba(0, 217, 255, 0.1);
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_PURPLE}, stop:1 {ACCENT_TEAL});
    border-radius: 6px;
}}

QTreeView {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QTreeView::item:selected {{
    background-color: rgba(0, 217, 255, 0.05);
    border-left: 2px solid {ACCENT_TEAL};
    color: {ACCENT_TEAL};
}}

QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: rgba(0, 217, 255, 0.2);
    border-radius: 3px;
    min-height: 20px;
}}

QTextEdit {{
    background-color: {BG_PANEL};
    border: 1px solid #2A2A4A;
    border-radius: 8px;
    padding: 10px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.5;
}}
"""

class ScanWorker(QThread):
    finished = Signal(int)
    log = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        self.log.emit(f"Starting scan of {self.path}...")
        count = scan_directory(self.path)
        self.finished.emit(count)

class ProcessWorker(QThread):
    finished = Signal()
    log = Signal(str)
    progress = Signal(int)

    def __init__(self, content_list, dry_run=False):
        super().__init__()
        self.content_list = content_list
        self.dry_run = dry_run

    def run(self):
        from src.engine import TaskScheduler
        # Load config again in thread to be safe
        config_path = "config_remote.json" if os.path.exists("config_remote.json") else "config.json"
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        scheduler = TaskScheduler(config)
        total = len(self.content_list)
        for i, content in enumerate(self.content_list):
            self.log.emit(f"Processing Scene: {content.scene_name}...")
            scheduler.process_item(content, dry_run=self.dry_run)
            self.progress.emit(int((i + 1) / total * 100))
            
        self.finished.emit()

class DataForagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DATA FORAGER // Astropunk Content Engine")
        self.resize(1280, 800)
        
        # Load Config
        self.config = self.load_config()
        
        # Initialize Database
        db.connect(reuse_if_open=True)
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Splitter for adjustable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # 1. Left Panel: Control Center
        left_panel = QFrame()
        left_panel.setObjectName("Panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        
        # --- DISCOVERY MODULE ---
        discovery_group = QFrame()
        discovery_group.setStyleSheet("background-color: rgba(0, 217, 255, 0.03); border-radius: 10px; border: 1px solid rgba(0, 217, 255, 0.1);")
        discovery_layout = QVBoxLayout(discovery_group)
        
        lbl_ingesta = QLabel("DISCOVERY HUB")
        lbl_ingesta.setObjectName("Header")
        discovery_layout.addWidget(lbl_ingesta)
        
        self.tree = QTreeView()
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["File", "Type", "Status"])
        self.tree.setModel(self.model)
        discovery_layout.addWidget(self.tree)
        
        self.scan_btn = QPushButton("LOCAL SCAN (BACKBONE)")
        self.scan_btn.setObjectName("Secondary")
        self.scan_btn.clicked.connect(self.start_scan)
        discovery_layout.addWidget(self.scan_btn)
        
        discovery_layout.addSpacing(10)
        discovery_layout.addWidget(QLabel("TARGETED PATH:"))
        self.remote_folder_input = QTextEdit()
        self.remote_folder_input.setPlaceholderText("e.g. Content-Archive")
        self.remote_folder_input.setMaximumHeight(35)
        self.remote_folder_input.setStyleSheet("background-color: #050510; border: 1px solid rgba(0,217,255,0.2); font-family: 'JetBrains Mono';")
        discovery_layout.addWidget(self.remote_folder_input)
        
        self.cloud_scan_btn = QPushButton("LAUNCH DISCOVERY HUB")
        self.cloud_scan_btn.setObjectName("DiscoveryBrand")
        self.cloud_scan_btn.clicked.connect(self.start_cloud_scan)
        discovery_layout.addWidget(self.cloud_scan_btn)
        
        self.purge_btn = QPushButton("PURGE HUB")
        self.purge_btn.setObjectName("Danger")
        self.purge_btn.clicked.connect(self.purge_hub)
        discovery_layout.addWidget(self.purge_btn)
        
        left_layout.addWidget(discovery_group)

        # --- OPERATION COMMANDS ---
        ops_group = QFrame()
        ops_group.setObjectName("Panel")
        ops_layout = QVBoxLayout(ops_group)
        
        lbl_ops = QLabel("OPERATIONS CONTROL")
        lbl_ops.setObjectName("Header")
        ops_layout.addWidget(lbl_ops)
        
        # Dry Run Toggle
        self.dry_run_check = QCheckBox("SIMULATION MODE (DRY RUN)")
        self.dry_run_check.setStyleSheet(f"color: {ACCENT_TEAL}; font-weight: bold;")
        ops_layout.addWidget(self.dry_run_check)
        
        self.process_btn = QPushButton("EXECUTE WORKER BATCH")
        self.process_btn.clicked.connect(self.start_processing)
        ops_layout.addWidget(self.process_btn)
        
        self.sync_db_btn = QPushButton("SYNC CLOUD DATA")
        self.sync_db_btn.setObjectName("Secondary")
        self.sync_db_btn.clicked.connect(self.sync_db_from_pod)
        ops_layout.addWidget(self.sync_db_btn)
        
        h_danger = QHBoxLayout()
        self.stop_scan_btn = QPushButton("STOP SCAN")
        self.stop_scan_btn.setObjectName("Danger")
        self.stop_scan_btn.clicked.connect(self.stop_remote_scan)
        h_danger.addWidget(self.stop_scan_btn)
        
        self.abort_btn = QPushButton("ABORT ALL")
        self.abort_btn.setObjectName("Danger")
        self.abort_btn.clicked.connect(self.abort_batch)
        h_danger.addWidget(self.abort_btn)
        
        ops_layout.addLayout(h_danger)
        left_layout.addWidget(ops_group)
        
        # 2. Middle Panel: Engine Intelligence
        middle_panel = QFrame()
        middle_panel.setObjectName("Panel")
        mid_layout = QVBoxLayout(middle_panel)
        mid_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_logs = QLabel("ENGINE INTELLIGENCE")
        lbl_logs.setObjectName("Header")
        mid_layout.addWidget(lbl_logs)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: rgba(5, 5, 16, 0.5); border: 1px solid rgba(0, 217, 255, 0.1); border-radius: 8px; font-family: 'JetBrains Mono'; color: #00D9FF;")
        mid_layout.addWidget(self.log_view)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        mid_layout.addWidget(self.progress_bar)
        
        # 3. Right Panel: Guided Scene Composer (Wizard)
        right_panel = QFrame()
        right_panel.setObjectName("Panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_wizard = QLabel("SCENE COMPOSER")
        lbl_wizard.setObjectName("Header")
        right_layout.addWidget(lbl_wizard)
        
        # Stepper
        self.stepper = WizardStepper()
        right_layout.addWidget(self.stepper)
        
        # Step Container
        self.step_stack = QStackedWidget()
        
        # --- PAGE 1: MASTER ---
        self.page_master = QWidget()
        l1 = QVBoxLayout(self.page_master)
        self.thumb_preview = QLabel("NO PREVIEW")
        self.thumb_preview.setAlignment(Qt.AlignCenter)
        self.thumb_preview.setMinimumHeight(200)
        self.thumb_preview.setStyleSheet("background-color: #050510; border: 1px solid rgba(123, 44, 191, 0.3); border-radius: 12px;")
        l1.addWidget(self.thumb_preview)
        self.lbl_master_info = QLabel("Select a scene to begin.")
        self.lbl_master_info.setWordWrap(True)
        l1.addWidget(self.lbl_master_info)
        self.btn_confirm_master = QPushButton("STEP 1: CONFIRM AS MASTER")
        self.btn_confirm_master.clicked.connect(lambda: self.next_wizard_step(2))
        l1.addWidget(self.btn_confirm_master)
        self.step_stack.addWidget(self.page_master)
        
        # --- PAGE 2: NAMING ---
        self.page_naming = QWidget()
        l2 = QVBoxLayout(self.page_naming)
        l2.addWidget(QLabel("STANDARDIZE SCENE NAME:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Scene Name")
        l2.addWidget(self.name_input)
        self.lbl_naming_preview = QLabel("PREVIEW: TYPE_##_YYYY-MM-DD_Name.mp4")
        self.lbl_naming_preview.setStyleSheet(f"color: {ACCENT_TEAL}; font-size: 10px;")
        l2.addWidget(self.lbl_naming_preview)
        self.name_input.textChanged.connect(self.update_live_previews)
        self.btn_confirm_name = QPushButton("STEP 2: LOCK NAME")
        self.btn_confirm_name.clicked.connect(self.lock_name)
        l2.addWidget(self.btn_confirm_name)
        self.step_stack.addWidget(self.page_naming)
        
        # --- PAGE 3: ASSETS ---
        self.page_assets = QWidget()
        l3 = QVBoxLayout(self.page_assets)
        l3.addWidget(QLabel("LINKED ADDITIONS (FYPs/TRAILERS):"))
        self.asset_list_view = QTextEdit()
        self.asset_list_view.setReadOnly(True)
        l3.addWidget(self.asset_list_view)
        self.btn_add_asset = QPushButton("+ MANUALLY ATTACH FILE")
        self.btn_add_asset.clicked.connect(self.attach_asset_manually)
        l3.addWidget(self.btn_add_asset)
        self.btn_confirm_assets = QPushButton("STEP 3: ASSETS READY")
        self.btn_confirm_assets.clicked.connect(lambda: self.next_wizard_step(4))
        l3.addWidget(self.btn_confirm_assets)
        self.step_stack.addWidget(self.page_assets)

        # --- PAGE 4: AI ---
        self.page_ai = QWidget()
        l4 = QVBoxLayout(self.page_ai)
        l4.addWidget(QLabel("AI INTELLIGENCE PIPELINE"))
        self.btn_run_vlm = QPushButton("RUN VLM ANALYSIS & THUMBS")
        self.btn_run_vlm.clicked.connect(self.run_analysis_targeted)
        l4.addWidget(self.btn_run_vlm)
        self.btn_confirm_ai = QPushButton("STEP 4: ANALYSIS COMPLETE")
        self.btn_confirm_ai.clicked.connect(lambda: self.next_wizard_step(5))
        l4.addWidget(self.btn_confirm_ai)
        self.step_stack.addWidget(self.page_ai)

        # --- PAGE 5: DEPLOY ---
        self.page_deploy = QWidget()
        l5 = QVBoxLayout(self.page_deploy)
        l5.addWidget(QLabel("FINAL COMMIT: CLOUD DEPLOY"))
        self.lbl_deploy_summary = QLabel("Ready to move files to organized/Scene folder.")
        l5.addWidget(self.lbl_deploy_summary)
        self.btn_finalize = QPushButton("STEP 5: ATOMIC DEPLOY TO S3")
        self.btn_finalize.setObjectName("DiscoveryBrand")
        self.btn_finalize.clicked.connect(self.deploy_to_s3_atomic)
        l5.addWidget(self.btn_finalize)
        self.step_stack.addWidget(self.page_deploy)
        
        right_layout.addWidget(self.step_stack)
        
        self.meta_details = QTextEdit()
        self.meta_details.setPlaceholderText("Analysis data stream pending...")
        self.meta_details.setStyleSheet("background-color: transparent; border: none; font-size: 11px;")
        right_layout.addWidget(self.meta_details)
        
        # Add to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Apply Theme
        self.setStyleSheet(ASTROPUNK_QSS)
        
        # Connect Selection
        self.tree.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Discovery Hub starts empty (User must scan to populate)
        # self.refresh_data() 

    def refresh_data(self, filter_path=None):
        """Reloads master content tree from SQLite. Supports optional path filtering."""
        self.model.removeRows(0, self.model.rowCount())
        # Only show Masters (Content table) that are still PENDING
        query = Content.select().where(Content.status == "pending")
        if filter_path:
            # Case-insensitive robust filtering
            clean_filter = filter_path.replace("\\", "/").lower()
            clean_filter = clean_filter.replace("do:chloe-storage/", "").replace("do:", "").strip("/")
            query = query.where(Content.source_path ** f"%{clean_filter}%")

        for content in query:
            name_item = QStandardItem(os.path.basename(content.source_path))
            c_type = content.content_type if content.content_type else "unknown"
            type_item = QStandardItem(c_type)
            
            # Asset Count info
            asset_count = Asset.select().where(Asset.content == content).count()
            status_text = f"{content.status} (+{asset_count} assets)" if asset_count > 0 else content.status
            status_item = QStandardItem(status_text)
            
            self.model.appendRow([name_item, type_item, status_item])

    def purge_hub(self):
        """Clears all discovery data from database."""
        self.update_log("PURGING DISCOVERY HUB: Clearing all pending records...")
        try:
            # Delete references first (Asset) then Content
            Asset.delete().execute()
            Content.delete().execute()
            self.refresh_data()
            self.update_log("Hub purged successfully. Ready for fresh scan.")
        except Exception as e:
            self.update_log(f"Purge failed: {e}")

    def update_log(self, message):
        self.log_view.append(message)

    def on_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            file_name = self.model.item(row, 0).text()
            # Find in DB
            content = Content.select().where(Content.source_path.contains(file_name)).first()
            if content:
                self.selected_content = content
                self.stepper.set_step(content.wizard_step)
                self.step_stack.setCurrentIndex(content.wizard_step - 1)
                self.show_details(content)

    def next_wizard_step(self, step):
        if not hasattr(self, "selected_content") or not self.selected_content:
            return
            
        # Update DB
        self.selected_content.wizard_step = step
        self.selected_content.save()
        
        # Update UI
        self.stepper.set_step(step)
        self.step_stack.setCurrentIndex(step - 1)
        self.update_log(f"Scene progressed to Step {step}: {self.stepper.steps[step-1]}")
        self.show_details(self.selected_content)

    def lock_name(self):
        if not hasattr(self, "selected_content"): return
        new_name = self.name_input.text().strip()
        if new_name:
            self.selected_content.scene_name = new_name
            self.selected_content.save()
            self.update_log(f"Name locked: {new_name}")
            self.next_wizard_step(3)

    def attach_asset_manually(self):
        if not hasattr(self, "selected_content"): return
        from PySide6.QtWidgets import QFileDialog
        from src.utils import parse_filename
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Asset to Attach")
        if file_path:
            meta = parse_filename(os.path.basename(file_path))
            Asset.create(
                content=self.selected_content,
                asset_type=meta["type"].lower(),
                local_path=file_path,
                status="pending"
            )
            self.update_log(f"Manually attached: {os.path.basename(file_path)}")
            # Refresh scavenging in case this manual add triggers new links
            self.show_details(self.selected_content)

    def show_details(self, content):
        """Displays metadata and thumbnail in the wizard panels."""
        from src.utils import generate_standard_name, parse_filename
        
        # 0. Intelligent Date Check (If date in title, prioritize it)
        meta = parse_filename(os.path.basename(content.source_path))
        if meta["date"] and (not content.content_date or content.content_date == "None"):
            content.content_date = meta["date"]
            content.save()
            self.update_log(f"Auto-detected date from title: {meta['date']}")

        # 0.5. Smart Scavenging (Link related assets by Date/Number)
        self.scavenge_assets(content)

        # 1. Update MASTER Page (Step 1)
        self.lbl_master_info.setText(
            f"<b>MASTER SELECTED:</b> {os.path.basename(content.source_path)}<br>"
            f"Original Size: {content.file_size / (1024*1024):.1f} MB<br>"
            f"Original Date: {content.content_date}"
        )
        
        # 2. Update NAMING Page (Step 2)
        self.name_input.blockSignals(True)
        self.name_input.setText(content.scene_name)
        self.name_input.blockSignals(False)
        self.update_live_previews()
        
        # 3. Update ASSETS Page (Step 3)
        linked_assets = Asset.select().where(Asset.content == content)
        asset_count = linked_assets.count()
        asset_text = "\n".join([f"• {a.asset_type.upper()}: {os.path.basename(a.local_path)}" for a in linked_assets])
        self.asset_list_view.setText(asset_text if asset_text else "No assets detected yet.")

        # 4. Update DEPLOY Page (Step 5)
        # Note: Summary is handled by update_live_previews() called in Step 2 section above

        # 5. Global Insights (Bottom Panel)
        rel_info = "MASTER (Solo)" if asset_count == 0 else f"MASTER (+{asset_count} assets)"
        details = (
            f"<b style='color:{ACCENT_TEAL}; font-size: 14px;'>INDEXING INSIGHTS:</b><br>"
            f"<hr style='border: 1px solid rgba(0,217,255,0.1);'>"
            f"<b>Stage:</b> {self.stepper.steps[content.wizard_step-1]}<br>"
            f"<b>Relationship:</b> {rel_info}<br>"
            f"<b>Base Name:</b> {content.scene_name}<br>"
            f"<i style='color:{TEXT_SECONDARY}; font-size: 10px;'>Path: {content.source_path}</i>"
        )
        self.meta_details.setHtml(details)

    def scavenge_assets(self, content):
        """Finds unlinked records with matching date/scene and links them as assets."""
        if not content.content_date or str(content.content_date) == "None": 
            return
            
        # 1. Broad Query: Match by Date, must NOT be the same record, 
        # and MUST NOT be another PPV (only link trailers/clips as assets)
        query = (Content.content_date == content.content_date) & \
                (Content.id != content.id) & \
                (Content.content_type != "PPV")
        
        # 2. Refine by Scene Number if available
        if content.scene_number:
            query &= (Content.scene_number == content.scene_number)
            
        potentials = Content.select().where(query)
        
        links_made = 0
        for p in potentials:
            # Check if p is already an asset for ANY content
            if not Asset.select().where(Asset.local_path == p.source_path).exists():
                Asset.create(
                    content=content,
                    asset_type=p.content_type.lower(),
                    local_path=p.source_path,
                    status="pending"
                )
                links_made += 1
                self.update_log(f"Smart Linked: {os.path.basename(p.source_path)} (Match: {content.content_date}/#{content.scene_number})")
                
                # Mark the potential record as 'linked' so it doesn't show up in Hub as a separate scene
                p.status = "linked"
                p.save()
        
        if links_made > 0:
            self.update_log(f"Found {links_made} related assets for this scene.")
        
        # Update Preview (Shared)
        # (Assuming VLM logic will eventually populate this)

    def update_live_previews(self):
        """Updates all name-dependent labels in real-time."""
        if not hasattr(self, "selected_content") or not self.selected_content: return
        from src.utils import generate_standard_name
        
        current_name = self.name_input.text().strip()
        proj_name = generate_standard_name(
            self.selected_content.content_type, 
            str(self.selected_content.content_date), 
            current_name if current_name else "Unknown", 
            self.selected_content.scene_number
        )
        
        # Update Step 2 Label
        self.lbl_naming_preview.setText(f"PROJECTED FILENAME: {proj_name}")
        
        # Update Step 5 Summary
        linked_assets = Asset.select().where(Asset.content == self.selected_content)
        asset_count = linked_assets.count()
        self.lbl_deploy_summary.setText(
            f"<b>READY FOR DEPLOYMENT:</b><br>"
            f"• 1 Master File<br>"
            f"• {asset_count} Attached Assets<br><br>"
            f"Target: organized/{proj_name.replace('.mp4', '')}"
        )

    def start_scan(self):
        path = "Z:/" if os.path.exists("Z:/") else "."
        self.worker = ScanWorker(path)
        self.worker.log.connect(self.update_log)
        self.worker.finished.connect(self.on_scan_finished)
        self.scan_btn.setEnabled(False)
        self.worker.start()

    def on_scan_finished(self, count):
        self.update_log(f"Scan complete. Found {count} new files.")
        self.refresh_data()
        self.scan_btn.setEnabled(True)
        self.cloud_scan_btn.setEnabled(True)

    def show_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid(): return
        
        item = self.model.itemFromIndex(index)
        content_id = item.data(Qt.UserRole)
        if not content_id: return
        
        menu = QMenu()
        anchor_action = menu.addAction("⚓ Anchor to Scene...")
        anchor_action.triggered.connect(lambda: self.anchor_to_scene(content_id))
        
        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def anchor_to_scene(self, content_id):
        # 1. Get current record
        current = Content.get_by_id(content_id)
        
        # 2. Find Candidate Masters (recent 50)
        masters = Content.select().where(Content.id != content_id).order_by(Content.id.desc()).limit(50)
        choices = [f"ID:{m.id} | {m.content_date} | {m.scene_name}" for m in masters]
        
        if not choices:
            self.update_log("No other scenes found to anchor to.")
            return
            
        choice, ok = QInputDialog.getItem(self, "Manual Anchor", "Select the MASTER scene to sink into:", choices, 0, False)
        
        if ok and choice:
            master_id = int(choice.split(" | ")[0].replace("ID:", ""))
            master = Content.get_by_id(master_id)
            
            # Transfer to asset
            Asset.create(
                content=master,
                asset_type=current.content_type.lower(),
                local_path=current.source_path,
                status="pending"
            )
            
            # Delete orphaned master record
            current.delete_instance()
            
            self.update_log(f"SUCCESS: Anchored '{current.scene_name}' to Master ID {master_id}.")
            self.refresh_data()

    def run_analysis_targeted(self):
        if not hasattr(self, "selected_content"): return
        self.update_log(f"Triggering VLM targeted analysis for: {self.selected_content.scene_name}")
        # Reuse Engine logic for a single item batch
        from src.engine import process_batch
        self.process_worker = ProcessWorker([self.selected_content], dry_run=self.dry_run_check.isChecked())
        self.process_worker.log.connect(self.update_log)
        self.process_worker.progress.connect(self.progress_bar.setValue)
        self.process_worker.finished.connect(lambda: self.update_log("Analysis complete. Review Step 4."))
        self.process_worker.start()

    def load_config(self):
        config_path = "config_remote.json" if os.path.exists("config_remote.json") else "config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def deploy_to_s3_atomic(self):
        if not hasattr(self, "selected_content"): return
        from src.engine import TaskScheduler
        
        # Lock name again just in case
        new_name = self.name_input.text().strip()
        if new_name:
            self.selected_content.scene_name = new_name
            self.selected_content.save()

        self.update_log(f"ATOMIC DEPLOYMENT INITIATED: {self.selected_content.scene_name}")
        
        # We'll use the TaskScheduler for the real move
        # We need to make sure process_item handles the specific path logic we defined in wizard
        scheduler = TaskScheduler(self.config)
        
        # In this context, we've already done most steps manually, 
        # so we trigger the engine's move-to-s3 part.
        # For simplicity, we can just call process_item which handles the full pipeline
        # but since we already named it, the engine will use our DB values.
        
        self.process_worker = ProcessWorker([self.selected_content], dry_run=self.dry_run_check.isChecked())
        self.process_worker.log.connect(self.update_log)
        self.process_worker.finished.connect(self.on_deploy_finished)
        self.process_worker.start()

    def on_deploy_finished(self):
        self.update_log("Deployment SUCCESSFUL. Scene archived.")
        self.refresh_data()
        self.step_stack.setCurrentIndex(0) # Back to master select
        self.stepper.set_step(1)
        self.selected_content = None

    def start_cloud_scan(self):
        raw_target = self.remote_folder_input.toPlainText().strip()
        if not raw_target:
            self.update_log("ERROR: Enter a folder name (e.g. Content-Archive)")
            return
            
        # 1. Normalize slashes first
        target = raw_target.replace("\\", "/")
        
        # 2. Extract the core path if they included the bucket prefix
        bucket_prefix = "do:chloe-storage/"
        if target.lower().startswith(bucket_prefix.lower()):
            target = target[len(bucket_prefix):]
        elif target.lower().startswith("do:"):
            # If they used a different 'do:' prefix, strip it too
            target = re.sub(r"^do:[^/]+/", "", target)
            
        # 3. Strip any local drive letter (e.g. Z:/ or C:/)
        target = re.sub(r"^[a-zA-Z]:/?", "", target)
        
        # 4. Final cleaning: remove leading/trailing slashes and re-attach fixed prefix
        target = target.strip("/")
        final_target = f"{bucket_prefix}{target}"
            
        self.update_log(f"Command Sent: Targeted Remote Scan -> {final_target}")
        self.cloud_scan_btn.setEnabled(False)
        
        # We need a new Worker type for remote scans via SSH
        self.remote_scan_worker = RemoteScanWorker(final_target, self.config)
        self.remote_scan_worker.log.connect(self.update_log)
        self.remote_scan_worker.request_db_unlock.connect(lambda: db.close())
        self.remote_scan_worker.finished.connect(self.on_remote_scan_finished)
        self.remote_scan_worker.start()

    def on_remote_scan_finished(self, count):
        self.cloud_scan_btn.setEnabled(True)
        
        # Re-establish connection in main thread
        from src.database import db
        db.connect(reuse_if_open=True)
        
        # Determine filter: if we used a targeted path, show ONLY that folder
        raw_target = self.remote_folder_input.toPlainText().strip()
        
        # USE SAME SANITIZATION AS START SCAN
        target = raw_target.replace("\\", "/")
        bucket_prefix = "do:chloe-storage/"
        if target.lower().startswith(bucket_prefix.lower()):
            target = target[len(bucket_prefix):]
        elif target.lower().startswith("do:"):
            target = re.sub(r"^do:[^/]+/", "", target)
        target = re.sub(r"^[a-zA-Z]:/?", "", target).strip("/")
        final_filter = f"{bucket_prefix}{target}"

        # Only filter if target doesn't look like a bug/log message
        if target and len(target) < 200 and "PURGING" not in target:
            self.refresh_data(filter_path=final_filter)
            display_path = final_filter
        else:
            self.refresh_data()
            display_path = "All"
            
        self.update_log(f"Remote Discovery complete. Hub filtered by: {display_path}")

    def sync_db_with_pod(self, direction="download"):
        """Resilient DB sync using temp files and absolute paths."""
        try:
            from src.database import db, DB_PATH
            abs_local_path = os.path.abspath(DB_PATH)
            temp_local_path = abs_local_path + ".tmp"
            remote_path = "root@209.170.80.132:/root/src/content_factory.db"
            
            import subprocess
            
            if direction == "download":
                self.update_log("Initiating resilient DOWNLOAD from Pod...")
                # 1. SCP to temp file first to avoid lock
                cmd = [
                    "scp", "-o", "StrictHostKeyChecking=no", 
                    "-i", "C:/Users/nicho/.ssh/id_runpod", 
                    "-P", "11246", 
                    remote_path, temp_local_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"SCP failed: {result.stderr}")
                
                # 2. Atomic swap (Close DB -> Move -> Reopen)
                db.close()
                if os.path.exists(abs_local_path):
                    os.remove(abs_local_path)
                os.rename(temp_local_path, abs_local_path)
                db.connect(reuse_if_open=True)
                
            else:
                self.update_log("Initiating resilient UPLOAD to Pod...")
                db.close()
                cmd = [
                    "scp", "-o", "StrictHostKeyChecking=no", 
                    "-i", "C:/Users/nicho/.ssh/id_runpod", 
                    "-P", "11246", 
                    abs_local_path, remote_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                db.connect(reuse_if_open=True)
                if result.returncode != 0:
                    raise Exception(f"SCP failed: {result.stderr}")
            
            self.update_log(f"Resilient {direction} successful.")
            return True
        except Exception as e:
            self.update_log(f"Resilient sync failed: {e}")
            try: db.connect(reuse_if_open=True)
            except: pass
            return False

    def sync_db_from_pod(self):
        if self.sync_db_with_pod(direction="download"):
            self.refresh_data()

    def start_processing(self):
        self.update_log("Preparing Cloud Worker batch...")
        dry_run = self.dry_run_check.isChecked()
        mode_str = " (DRY RUN)" if dry_run else ""
        
        # 1. Upload DB
        if not self.sync_db_with_pod(direction="upload"):
            return

        # 2. Start Worker
        self.update_log(f"Command Sent: Starting Cloud Worker batch{mode_str}...")
        try:
            worker_cmd = "python3 /root/main.py --mode worker"
            if dry_run:
                worker_cmd += " --dry-run"
                
            cmd_start = [
                "ssh", "-o", "StrictHostKeyChecking=no", 
                "-i", "C:/Users/nicho/.ssh/id_runpod", 
                "-p", "11246", "root@209.170.80.132",
                f"export PYTHONPATH=/root && {worker_cmd}"
            ]
            subprocess.Popen(cmd_start) 
            self.update_log(f"Remote worker is now running in background{mode_str}.")
        except Exception as e:
            self.update_log(f"Failed to start remote worker: {e}")

    def stop_remote_scan(self):
        self.update_log("EMERGENCY STOP: Killing remote rclone scan...")
        try:
            import subprocess
            cmd = [
                "ssh", "-o", "StrictHostKeyChecking=no", 
                "-i", "C:/Users/nicho/.ssh/id_runpod", 
                "-p", "11246", "root@209.170.80.132",
                "pkill -f rclone"
            ]
            subprocess.run(cmd, check=False)
            self.update_log("Stop signal sent to Pod.")
        except Exception as e:
            self.update_log(f"Failed to send stop signal: {e}")

    def abort_batch(self):
        self.update_log("EMERGENCY ABORT: Killing worker processes...")
        try:
            import subprocess
            cmd = [
                "ssh", "-o", "StrictHostKeyChecking=no", 
                "-i", "C:/Users/nicho/.ssh/id_runpod", 
                "-p", "11246", "root@209.170.80.132",
                "pkill -f python3"
            ]
            subprocess.run(cmd, check=False)
            self.update_log("Abort signal sent to Pod.")
        except Exception as e:
            self.update_log(f"Failed to send abort signal: {e}")

class RemoteScanWorker(QThread):
    finished = Signal(int)
    log = Signal(str)
    request_db_unlock = Signal() # New signal to request main thread to close DB

    def __init__(self, remote_path, config):
        super().__init__()
        self.remote_path = remote_path
        self.config = config

    def resolve_ssh_details(self):
        """Fetches current Pod IP and Port from RunPod API if not in config or connection fails."""
        api_key = self.config.get("runpod_api_key")
        pod_id = self.config.get("runpod_pod_id")
        
        # 1. Use config values if they exist
        host = self.config.get("ssh_host")
        port = self.config.get("ssh_port")
        
        # 2. If missing or we want to be fresh, query the API
        if not api_key or not pod_id:
            return host, port

        try:
            self.log.emit("Resolving RunPod SSH details via API...")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            query = """
            query Pod($podId: String!) {
              pod(input: {podId: $podId}) {
                runtime {
                  ports {
                    ip
                    publicPort
                    privatePort
                  }
                }
              }
            }
            """
            response = requests.post(
                "https://api.runpod.io/graphql",
                json={"query": query, "variables": {"podId": pod_id}},
                headers=headers,
                timeout=10
            )
            data = response.json()
            pod_data = data.get("data", {}).get("pod")
            if pod_data:
                ports = pod_data.get("runtime", {}).get("ports", [])
                for p in ports:
                    if p["privatePort"] == 22:
                        host = p["ip"]
                        port = p["publicPort"]
                        self.log.emit(f"Resolved: {host}:{port}")
                        return host, port
        except Exception as e:
            self.log.emit(f"Warning: API resolution failed ({e}). Using config defaults.")
            
        return host, port

    def run(self):
        # Resolve details
        host, port = self.resolve_ssh_details()
        if not host or not port:
            self.log.emit("Error: Could not determine SSH host or port. Check config.")
            self.finished.emit(0)
            return

        ssh_key = self.config.get("ssh_key", "C:/Users/nicho/.ssh/id_runpod")
        ssh_key = ssh_key.replace("\\", "/") # Ensure forward slashes for cross-plat compatibility in path strings

        # remote_path is already sanitized by the GUI caller
        self.log.emit(f"Initiating REMOTE SCAN on POD for: {self.remote_path}")
        
        try:
            import subprocess
            # 1. Execute Scan on Pod - wrap path in quotes for spaces
            scan_cmd = [
                "ssh", "-o", "StrictHostKeyChecking=no", 
                "-i", ssh_key, 
                "-p", str(port), f"root@{host}",
                f"export PYTHONPATH=/workspace && python3 /workspace/src/scanner.py '{self.remote_path}'"
            ]
            self.log.emit(f"Connecting to {host}:{port}...")
            subprocess.run(scan_cmd, check=True)
            
            # 2. Sync DB back to Local
            self.log.emit("Scan complete. Pulling results to local hub...")
            
            # CRITICAL: Signal main thread to release lock
            self.request_db_unlock.emit()
            import time
            time.sleep(1) # Give main thread a moment to close
            
            from src.database import DB_PATH
            abs_local_path = os.path.abspath(DB_PATH)
            temp_local_path = abs_local_path + ".tmp"
            
            sync_cmd = [
                "scp", "-o", "StrictHostKeyChecking=no", 
                "-i", ssh_key, 
                "-P", str(port), 
                f"root@{host}:/workspace/src/content_factory.db", 
                temp_local_path
            ]
            result = subprocess.run(sync_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Atomic swap handled by main thread via reopening
                # For simplicity here, we just move it if we can
                try:
                    if os.path.exists(abs_local_path):
                        os.remove(abs_local_path)
                    os.rename(temp_local_path, abs_local_path)
                except Exception as e:
                    self.log.emit(f"Swap failed: {e}")
            else:
                self.log.emit(f"Sync failed: {result.stderr}")

            # Notify finished (Main thread will re-connect)
            self.finished.emit(-1) # Use -1 to indicate refresh needed
        except Exception as e:
            self.log.emit(f"Remote Scan Failed: {e}")
            self.finished.emit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DataForagerGUI()
    gui.show()
    sys.exit(app.exec())
