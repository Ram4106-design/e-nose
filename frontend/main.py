"""
E-NOSE Dashboard - Main Application
Simplified 3-file structure with modern dark UI
"""

import sys
import asyncio
import socket
import json
import csv
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QTextEdit, QLineEdit,
    QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import qasync
import pyqtgraph as pg

from config import BACKEND_HOST, BACKEND_PORT, RECONNECT_DELAY, MAX_DATA_POINTS, SENSORS, STATES

# Try to import Edge Impulse (optional)
try:
    from utils import EdgeImpulseHandler
    EDGE_IMPULSE_AVAILABLE = True
except ImportError:
    print("⚠️ Edge Impulse not available (missing dependencies)")
    EdgeImpulseHandler = None
    EDGE_IMPULSE_AVAILABLE = False


# ==================== SIGNAL EMITTER ====================
class DataSignal(QObject):
    """Signal emitter untuk komunikasi thread-safe antara async loop dan GUI"""
    data_received = pyqtSignal(dict)
    sampling_complete = pyqtSignal()
    classification_result = pyqtSignal(dict)


signal_emitter = DataSignal()


# ==================== MAIN GUI ====================
class ENoseGUI(QMainWindow):
    """Main GUI window untuk E-NOSE Dashboard"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 E-NOSE Dashboard")
        self.resize(1300, 650)
        self.setMinimumSize(1100, 550)

        self._sock: Optional[socket.socket] = None
        self.connected = False
        self.current_sample_data = []
        self.is_sampling = False
        
        # Initialize Edge Impulse (if available)
        if EDGE_IMPULSE_AVAILABLE:
            self.ei_handler = EdgeImpulseHandler()
        else:
            self.ei_handler = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup semua UI components dengan tema gelap modern"""
        # Central widget dengan background gelap
        wrapper = QWidget()
        wrapper.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }
        """)
        self.setCentralWidget(wrapper)
        root = QVBoxLayout(wrapper)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(10)
        
        # Title dengan gradient modern
        title = QLabel("🔬 E-NOSE REALTIME MONITORING")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: white; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #e94560, stop:0.5 #00d9ff, stop:1 #e94560);
            padding: 10px; 
            border-radius: 12px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        root.addWidget(title)

        # Main Content
        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)
        root.addLayout(main_layout, stretch=1)

        # Left: Graph
        self._setup_graph(main_layout)
        
        # Right: Controls
        self._setup_controls(main_layout)

        # Timer untuk update graph
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(100)

    def _setup_graph(self, parent_layout):
        """Setup graph area dengan tema gelap"""
        graph_frame = QFrame()
        graph_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0e27;
                border-radius: 12px;
                border: 2px solid #00d9ff;
                padding: 12px;
            }
        """)
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.setContentsMargins(8, 8, 8, 8)
        graph_layout.setSpacing(5)

        graph_title = QLabel("📊 Real-Time Sensor Data")
        graph_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        graph_title.setStyleSheet("color: #00d9ff; padding: 5px;")
        graph_layout.addWidget(graph_title)

        # Setup pyqtgraph dengan tema gelap
        self.graph = pg.PlotWidget()
        self.graph.setLabel('left', 'Value (ppm)', color='#ffffff', size='11pt')
        self.graph.setLabel('bottom', 'Samples', color='#ffffff', size='11pt')
        self.graph.showGrid(x=True, y=True, alpha=0.1)
        self.graph.setBackground('#0a0e27')
        
        legend = self.graph.addLegend(offset=(10, 10), labelTextColor='#ffffff')

        # Setup plot lines dengan warna neon
        self.lines = {}
        self.data_buffers = {}
        
        neon_colors = {
            "NO2": "#ff006e",    # Neon pink
            "ETH": "#00f5ff",    # Neon cyan
            "VOC": "#39ff14",    # Neon green
            "CO": "#ffbe0b",     # Neon yellow
            "COM": "#fb5607",    # Neon orange
            "ETHM": "#8338ec",   # Neon purple
            "VOCM": "#3a86ff"    # Neon blue
        }
        
        for sensor in SENSORS.keys():
            color = neon_colors.get(sensor, "#ffffff")
            self.lines[sensor] = self.graph.plot(
                [], [], 
                pen=pg.mkPen(color, width=3), 
                name=sensor,
                symbol='o', 
                symbolSize=3,
                symbolBrush=color
            )
            self.data_buffers[sensor] = []

        graph_layout.addWidget(self.graph, stretch=1)
        parent_layout.addWidget(graph_frame, stretch=3)

    def _setup_controls(self, parent_layout):
        """Setup control panel dengan tema gelap"""
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        # Top row: Status + Controls side by side
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # Status panel (left side of top row)
        self._setup_status_panel(top_row)
        
        # Control buttons (right side of top row)
        self._setup_control_buttons(top_row)
        
        right_panel.addLayout(top_row)
        
        # Bottom row: CSV + Log side by side
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        
        # CSV Export & Model (left side of bottom row)
        self._setup_csv_panel(bottom_row)
        
        # Log (right side of bottom row)
        self._setup_log_panel(bottom_row)
        
        right_panel.addLayout(bottom_row, stretch=1)

        parent_layout.addLayout(right_panel, stretch=2)

    def _setup_status_panel(self, parent_layout):
        """Setup status panel"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 10px;
                border: 2px solid #00d9ff;
                padding: 12px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(6)

        self.status = QLabel("🔴 Disconnected")
        self.status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status.setStyleSheet("""
            color: #e94560; 
            padding: 10px; 
            background: rgba(233, 69, 96, 0.15); 
            border-radius: 8px;
        """)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status)

        # State & Level
        info_layout = QHBoxLayout()
        info_layout.setSpacing(6)
        
        self.state_label = QLabel("STATE: —")
        self.state_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.state_label.setStyleSheet("""
            color: #00d9ff; 
            background: rgba(0, 217, 255, 0.15); 
            padding: 6px; 
            border-radius: 6px;
        """)
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.state_label)

        self.level_label = QLabel("LVL: —")
        self.level_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.level_label.setStyleSheet("""
            color: #ffbe0b; 
            background: rgba(255, 190, 11, 0.15); 
            padding: 6px; 
            border-radius: 6px;
        """)
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.level_label)
        
        status_layout.addLayout(info_layout)

        # Progress Bar for Levels 1-5
        progress_container = QFrame()
        progress_container.setStyleSheet("""
            QFrame {
                background: rgba(0, 217, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(8, 8, 8, 8)
        progress_layout.setSpacing(4)

        # Progress title
        progress_title = QLabel("LEVEL PROGRESS")
        progress_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        progress_title.setStyleSheet("color: #00d9ff; padding: 2px;")
        progress_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(progress_title)

        # Progress bar with level indicators
        level_bar_layout = QHBoxLayout()
        level_bar_layout.setSpacing(4)
        
        self.level_indicators = []
        for i in range(1, 6):
            level_box = QLabel(str(i))
            level_box.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            level_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            level_box.setMinimumSize(35, 35)
            level_box.setMaximumSize(35, 35)
            level_box.setStyleSheet("""
                QLabel {
                    background: rgba(255, 255, 255, 0.1);
                    color: #666;
                    border: 2px solid #444;
                    border-radius: 6px;
                    font-weight: bold;
                }
            """)
            self.level_indicators.append(level_box)
            level_bar_layout.addWidget(level_box)
        
        progress_layout.addLayout(level_bar_layout)
        status_layout.addWidget(progress_container)

        # Prediction Label
        self.pred_label = QLabel("PREDICTION: —")
        self.pred_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.pred_label.setStyleSheet("""
            color: white; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #8338ec, stop:1 #3a86ff);
            padding: 10px; 
            border-radius: 8px;
        """)
        self.pred_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.pred_label)

        parent_layout.addWidget(status_frame)

    def _setup_control_buttons(self, parent_layout):
        """Setup control buttons dengan hover effect"""
        btn_frame = QFrame()
        btn_frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 10px;
                border: 2px solid #e94560;
                padding: 12px;
            }
        """)
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(8, 8, 8, 8)

        self.btn_start = QPushButton("▶ START SAMPLING")
        self.btn_start.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_start.setMinimumHeight(28)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00d9ff, stop:1 #0096c7);
                color: white;
                padding: 8px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00f5ff, stop:1 #00b4d8);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: #0077b6;
            }
        """)
        self.btn_start.clicked.connect(self.start_sampling_clicked)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏹ STOP SAMPLING")
        self.btn_stop.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_stop.setMinimumHeight(28)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e94560, stop:1 #c1121f);
                color: white;
                padding: 8px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff4d6d, stop:1 #d62828);
            }
            QPushButton:pressed {
                background: #9d0208;
            }
        """)
        self.btn_stop.clicked.connect(lambda: asyncio.create_task(self.send_cmd("STOP_SAMPLING")))
        btn_layout.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("🗑 CLEAR GRAPH")
        self.btn_clear.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_clear.setMinimumHeight(28)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8338ec, stop:1 #5a189a);
                color: white;
                padding: 8px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9d4edd, stop:1 #7209b7);
            }
            QPushButton:pressed {
                background: #3c096c;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_graph)
        btn_layout.addWidget(self.btn_clear)

        parent_layout.addWidget(btn_frame)

    def _setup_csv_panel(self, parent_layout):
        """Setup CSV export and model loading panel"""
        csv_frame = QFrame()
        csv_frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 10px;
                border: 2px solid #ffbe0b;
                padding: 12px;
            }
        """)
        csv_layout = QVBoxLayout(csv_frame)
        csv_layout.setSpacing(3)
        csv_layout.setContentsMargins(6, 6, 6, 6)

        csv_title = QLabel("💾 Export & Model")
        csv_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        csv_title.setStyleSheet("color: #ffbe0b; padding: 2px;")
        csv_layout.addWidget(csv_title)

        self.sample_name_input = QLineEdit()
        self.sample_name_input.setPlaceholderText("Sample name...")
        self.sample_name_input.setMinimumHeight(22)
        self.sample_name_input.setMaximumHeight(22)
        self.sample_name_input.setFont(QFont("Segoe UI", 8))
        self.sample_name_input.setStyleSheet("""
            QLineEdit {
                background: #0a0e27;
                color: white;
                border: 2px solid #444;
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid #00d9ff;
            }
        """)
        csv_layout.addWidget(self.sample_name_input)

        # Edge Impulse API Key Input
        self.ei_api_key_input = QLineEdit()
        self.ei_api_key_input.setPlaceholderText("API Key...")
        self.ei_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ei_api_key_input.setMinimumHeight(22)
        self.ei_api_key_input.setMaximumHeight(22)
        self.ei_api_key_input.setFont(QFont("Segoe UI", 8))
        self.ei_api_key_input.setStyleSheet("""
            QLineEdit {
                background: #0a0e27;
                color: white;
                border: 2px solid #444;
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid #8338ec;
            }
        """)
        csv_layout.addWidget(self.ei_api_key_input)

        # Edge Impulse Project ID Input
        self.ei_project_id_input = QLineEdit()
        self.ei_project_id_input.setPlaceholderText("Project ID...")
        self.ei_project_id_input.setMinimumHeight(22)
        self.ei_project_id_input.setMaximumHeight(22)
        self.ei_project_id_input.setFont(QFont("Segoe UI", 8))
        self.ei_project_id_input.setStyleSheet("""
            QLineEdit {
                background: #0a0e27;
                color: white;
                border: 2px solid #444;
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid #8338ec;
            }
        """)
        csv_layout.addWidget(self.ei_project_id_input)

        # Edge Impulse Label Input
        self.ei_label_input = QLineEdit()
        self.ei_label_input.setPlaceholderText("Label (coffee, tea...)")
        self.ei_label_input.setMinimumHeight(22)
        self.ei_label_input.setMaximumHeight(22)
        self.ei_label_input.setFont(QFont("Segoe UI", 8))
        self.ei_label_input.setStyleSheet("""
            QLineEdit {
                background: #0a0e27;
                color: white;
                border: 2px solid #444;
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid #8338ec;
            }
        """)
        csv_layout.addWidget(self.ei_label_input)

        self.btn_save_csv = QPushButton("💾 SAVE CSV")
        self.btn_save_csv.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_save_csv.setMinimumHeight(22)
        self.btn_save_csv.setMaximumHeight(22)
        self.btn_save_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_csv.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffbe0b, stop:1 #fb8500);
                color: #1a1a2e;
                padding: 4px;
                border-radius: 4px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffd60a, stop:1 #ffb703);
            }
        """)
        self.btn_save_csv.clicked.connect(self.save_to_csv)
        csv_layout.addWidget(self.btn_save_csv)

        # Model Control
        # Upload to Edge Impulse Button
        self.btn_upload_ei = QPushButton("📤 UPLOAD TO EI")
        self.btn_upload_ei.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_upload_ei.setMinimumHeight(22)
        self.btn_upload_ei.setMaximumHeight(22)
        self.btn_upload_ei.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload_ei.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8338ec, stop:1 #5a189a);
                color: white;
                padding: 4px;
                border-radius: 4px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9d4edd, stop:1 #7209b7);
            }
            QPushButton:pressed {
                background: #3c096c;
            }
        """)
        self.btn_upload_ei.clicked.connect(self.upload_to_edge_impulse_clicked)
        csv_layout.addWidget(self.btn_upload_ei)

        model_btn = QPushButton("📂 LOAD MODEL")
        model_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        model_btn.setMinimumHeight(22)
        model_btn.setMaximumHeight(22)
        model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        model_btn.setStyleSheet("""
            QPushButton {
                background: #8338ec;
                color: white;
                padding: 4px;
                border-radius: 4px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #9d4edd;
            }
        """)
        model_btn.clicked.connect(self.load_model_clicked)
        csv_layout.addWidget(model_btn)

        parent_layout.addWidget(csv_frame)

    def _setup_log_panel(self, parent_layout):
        """Setup log panel"""
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 10px;
                border: 2px solid #39ff14;
                padding: 12px;
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setSpacing(5)
        log_layout.setContentsMargins(8, 8, 8, 8)

        log_title = QLabel("📋 System Log")
        log_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        log_title.setStyleSheet("color: #39ff14; padding: 5px;")
        log_layout.addWidget(log_title)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("""
            QTextEdit {
                background: #0a0e27;
                color: #00ff00;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-family: Consolas;
                font-size: 9pt;
                line-height: 1.5;
            }
        """)
        log_layout.addWidget(self.log)

        parent_layout.addWidget(log_frame, stretch=1)

    def _connect_signals(self):
        """Connect all signals"""
        signal_emitter.data_received.connect(self.on_data_received)
        signal_emitter.sampling_complete.connect(self.on_sampling_complete)
        signal_emitter.classification_result.connect(self.update_prediction)

    # Event handlers
    def start_sampling_clicked(self):
        """Reset data dan mulai sampling baru"""
        self.current_sample_data = []
        self.is_sampling = True
        self.log.append("🔄 Starting sampling...")
        self.log.append("⏱ Hold: 2m | Purge: 4m")
        asyncio.create_task(self.send_cmd("START_SAMPLING"))

    def clear_graph(self):
        """Clear all graph data and reset for new sample"""
        # Clear all data buffers
        for sensor in self.data_buffers.keys():
            self.data_buffers[sensor] = []
        
        # Clear current sample data
        self.current_sample_data = []
        
        # Reset level indicators to default state
        for indicator in self.level_indicators:
            indicator.setStyleSheet("""
                QLabel {
                    background: rgba(255, 255, 255, 0.1);
                    color: #666;
                    border: 2px solid #444;
                    border-radius: 6px;
                    font-weight: bold;
                }
            """)
        
        # Reset prediction label
        self.pred_label.setText("PREDICTION: —")
        
        # Log the action
        self.log.append("🗑 Graph cleared - Ready for new sample")
        
        QMessageBox.information(
            self,
            "Graph Cleared",
            "All graph data has been cleared.\nReady for new sample collection."
        )

    def on_sampling_complete(self):
        """Handle ketika sampling selesai"""
        self.is_sampling = False
        self.log.append("🎉 COMPLETE! 5 levels done")
        self.log.append(f"📊 Total: {len(self.current_sample_data)} samples")
        
        # Auto-upload to Edge Impulse if credentials are provided
        api_key = self.ei_api_key_input.text().strip()
        project_id = self.ei_project_id_input.text().strip()
        label = self.ei_label_input.text().strip()
        
        if api_key and project_id and label and self.current_sample_data:
            self.log.append("📤 Auto-uploading to Edge Impulse...")
            try:
                # Prepare data directly from current_sample_data
                if EDGE_IMPULSE_AVAILABLE and self.ei_handler:
                    result = self.ei_handler.upload_data_to_edge_impulse(
                        data=self.current_sample_data,
                        api_key=api_key,
                        project_id=project_id,
                        label=label
                    )
                else:
                    from utils import EdgeImpulseHandler
                    result = EdgeImpulseHandler.upload_data_to_edge_impulse(
                        data=self.current_sample_data,
                        api_key=api_key,
                        project_id=project_id,
                        label=label
                    )
                
                if result['success']:
                    self.log.append(f"✅ {result['message']}")
                    QMessageBox.information(
                        self,
                        "Complete",
                        f"Sampling finished!\n\nSamples: {len(self.current_sample_data)}\n\n✅ Auto-uploaded to Edge Impulse!\nLabel: {label}"
                    )
                else:
                    self.log.append(f"⚠️ Upload warning: {result['message']}")
                    QMessageBox.information(
                        self,
                        "Complete",
                        f"Sampling finished!\n\nSamples: {len(self.current_sample_data)}\n\n⚠️ Upload failed: {result['message']}"
                    )
            except Exception as e:
                self.log.append(f"⚠️ Upload error: {str(e)}")
                QMessageBox.information(
                    self,
                    "Complete",
                    f"Sampling finished!\n\nSamples: {len(self.current_sample_data)}\n\n⚠️ Upload error: {str(e)}"
                )
        else:
            # No auto-upload, just show completion
            QMessageBox.information(
                self,
                "Complete",
                f"Sampling finished!\n\nSamples: {len(self.current_sample_data)}\nReady to save CSV."
            )

    def on_data_received(self, data: dict):
        """Handle data dari async loop"""
        # Normalize field names to uppercase
        normalized_data = {k.upper(): v for k, v in data.items()}
        
        if self.is_sampling:
            data_row = {'timestamp': datetime.now().isoformat()}
            
            for k, v in normalized_data.items():
                key = k.upper()
                if key in self.data_buffers:
                    try:
                        value = float(v)
                        self.data_buffers[key].append(value)
                        data_row[key] = value
                        
                        if len(self.data_buffers[key]) > MAX_DATA_POINTS:
                            self.data_buffers[key].pop(0)
                    except:
                        pass
            
            if any(k in data_row for k in SENSORS.keys()):
                self.current_sample_data.append(data_row)

        # Update state display with color coding
        if 'STATE_NAME' in normalized_data:
            state_name = normalized_data['STATE_NAME']
            state_config = STATES.get(state_name, {"color": "#ffffff", "desc": state_name})
            self.state_label.setText(f"STATE: {state_name}")
            self.state_label.setStyleSheet(f"""
                color: {state_config['color']}; 
                background: rgba({int(state_config['color'][1:3], 16)}, {int(state_config['color'][3:5], 16)}, {int(state_config['color'][5:7], 16)}, 0.15); 
                padding: 6px; 
                border-radius: 6px;
                font-weight: bold;
            """)
        elif 'STATE' in normalized_data:
            # Fallback if state_name not available
            self.state_label.setText(f"STATE: {normalized_data['STATE']}")
        
        # Update level display and progress bar
        if 'LEVEL' in normalized_data:
            try:
                current_level = int(normalized_data['LEVEL'])
                self.level_label.setText(f"LVL: {current_level}")
                self.update_level_progress(current_level)
            except (ValueError, TypeError):
                self.level_label.setText(f"LVL: {normalized_data['LEVEL']}")

        # Compact log
        if any(k.upper() in SENSORS for k in data.keys()):
            sensor_str = ", ".join([f"{k}:{v:.1f}" for k,v in data.items() if k.upper() in SENSORS])
            self.log.append(f"✅ {sensor_str}")
            
            # Run classification (if Edge Impulse available)
            if self.ei_handler:
                res = self.ei_handler.classify(normalized_data)
                if res:
                    signal_emitter.classification_result.emit(res)

    def update_prediction(self, result: dict):
        """Update prediction label"""
        if "classification" in result:
            best_label = max(result["classification"], key=result["classification"].get)
            confidence = result["classification"][best_label]
            self.pred_label.setText(f"PRED: {best_label} ({confidence:.2f})")

    def update_level_progress(self, current_level: int):
        """Update visual progress bar for levels 1-5"""
        for i, indicator in enumerate(self.level_indicators, start=1):
            if i < current_level:
                # Completed levels - green gradient
                indicator.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #39ff14, stop:1 #00ff00);
                        color: #0a0e27;
                        border: 2px solid #39ff14;
                        border-radius: 6px;
                        font-weight: bold;
                    }
                """)
            elif i == current_level:
                # Current level - cyan gradient with glow
                indicator.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #00d9ff, stop:1 #00f5ff);
                        color: #0a0e27;
                        border: 3px solid #00d9ff;
                        border-radius: 6px;
                        font-weight: bold;
                    }
                """)
            else:
                # Pending levels - dark/inactive
                indicator.setStyleSheet("""
                    QLabel {
                        background: rgba(255, 255, 255, 0.1);
                        color: #666;
                        border: 2px solid #444;
                        border-radius: 6px;
                        font-weight: bold;
                    }
                """)


    def update_graph(self):
        """Update semua line di graph"""
        for sensor, line in self.lines.items():
            buf = self.data_buffers[sensor]
            if buf:
                line.setData(list(range(len(buf))), buf)

    def save_to_csv(self):
        """Save current sample data to CSV"""
        sample_name = self.sample_name_input.text().strip()
        
        if not sample_name:
            QMessageBox.warning(self, "Warning", "Enter sample name!")
            return
        
        if not self.current_sample_data:
            QMessageBox.warning(self, "Warning", "No data! Start sampling first.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{sample_name}_{timestamp}.csv"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", default_filename, "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            collection_date = self.current_sample_data[0]['timestamp']
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['sample_name', 'collection_date', 'timestamp'] + list(SENSORS.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in self.current_sample_data:
                    csv_row = {
                        'sample_name': sample_name,
                        'collection_date': collection_date,
                        'timestamp': row['timestamp']
                    }
                    for sensor in SENSORS.keys():
                        csv_row[sensor] = row.get(sensor, '')
                    writer.writerow(csv_row)
            
            self.log.append(f"💾 Saved: {filename}")
            self.log.append(f"📊 {len(self.current_sample_data)} samples")
            
        except Exception as e:
            self.log.append(f"❌ Error saving CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save CSV:\n{e}")

    def upload_to_edge_impulse_clicked(self):
        """Upload saved CSV file to Edge Impulse"""
        # Get API credentials
        api_key = self.ei_api_key_input.text().strip()
        project_id = self.ei_project_id_input.text().strip()
        label = self.ei_label_input.text().strip()
        
        # Validate inputs
        if not api_key:
            QMessageBox.warning(self, "Missing API Key", "Please enter your Edge Impulse API Key.")
            return
        
        if not project_id:
            QMessageBox.warning(self, "Missing Project ID", "Please enter your Edge Impulse Project ID.")
            return
        
        if not label:
            QMessageBox.warning(self, "Missing Label", "Please enter a label for the data (e.g., coffee, tea).")
            return
        
        # Select CSV file to upload
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File to Upload", "", "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        # Upload to Edge Impulse
        self.log.append(f"📤 Uploading {filename} to Edge Impulse...")
        
        try:
            if EDGE_IMPULSE_AVAILABLE and self.ei_handler:
                result = self.ei_handler.upload_csv_to_edge_impulse(
                    csv_file_path=filename,
                    api_key=api_key,
                    project_id=project_id,
                    label=label
                )
            else:
                # Use static method if handler not available
                from utils import EdgeImpulseHandler
                result = EdgeImpulseHandler.upload_csv_to_edge_impulse(
                    csv_file_path=filename,
                    api_key=api_key,
                    project_id=project_id,
                    label=label
                )
            
            if result['success']:
                self.log.append(f"✅ {result['message']}")
                QMessageBox.information(
                    self, 
                    "Upload Successful", 
                    f"{result['message']}\n\nLabel: {label}"
                )
            else:
                self.log.append(f"❌ {result['message']}")
                QMessageBox.warning(
                    self, 
                    "Upload Failed", 
                    result['message']
                )
        except Exception as e:
            error_msg = f"Error during upload: {str(e)}"
            self.log.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Upload Error", error_msg)

    def load_model_clicked(self):
        """Open file dialog to load Edge Impulse model"""
        if not EDGE_IMPULSE_AVAILABLE:
            QMessageBox.warning(
                self, 
                "Edge Impulse Not Available", 
                "Edge Impulse library is not installed.\nModel loading is disabled."
            )
            return
            
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Edge Impulse Model", "", "EIM Files (*.eim);;All Files (*)"
        )
        
        if filename:
            if self.ei_handler.load_model(filename):
                self.log.append(f"🧠 Model loaded: {filename}")
                QMessageBox.information(self, "Success", "Model loaded successfully!")
            else:
                self.log.append("❌ Failed to load model")
                QMessageBox.warning(self, "Error", "Failed to load model.")

    # Async methods
    async def connect_backend(self):
        """Connect to backend server"""
        while True:
            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.setblocking(False)
                await asyncio.get_event_loop().sock_connect(self._sock, (BACKEND_HOST, BACKEND_PORT))

                self.connected = True
                self.status.setText("🟢 Connected")
                self.status.setStyleSheet("""
                    color: #39ff14; 
                    padding: 8px; 
                    background: rgba(57, 255, 20, 0.15); 
                    border-radius: 8px;
                """)
                self.log.append("🟢 Connected to backend!")
                await self.recv_loop()

            except Exception as e:
                self.connected = False
                self.status.setText("🔴 Disconnected")
                self.status.setStyleSheet("""
                    color: #e94560; 
                    padding: 8px; 
                    background: rgba(233, 69, 96, 0.15); 
                    border-radius: 8px;
                """)
                self.log.append(f"⚠️ Reconnect in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)

    async def recv_loop(self):
        """Receive data forever until disconnected"""
        loop = asyncio.get_event_loop()

        while True:
            try:
                data = await loop.sock_recv(self._sock, 4096)
                if not data:
                    raise ConnectionError("Backend closed")

                for line in data.decode(errors="ignore").splitlines():
                    line = line.strip()
                    if line:
                        if line == "SAMPLING_COMPLETE":
                            signal_emitter.sampling_complete.emit()
                            continue
                        elif line == "SAMPLING_STOPPED":
                            self.is_sampling = False
                            self.log.append("⏹ Stopped")
                            continue
                        
                        try:
                            obj = json.loads(line)
                            signal_emitter.data_received.emit(obj)
                        except:
                            self.log.append(f"📝 {line}")

            except Exception as e:
                self.log.append(f"⚠️ Disconnected")
                break

    async def send_cmd(self, cmd: str):
        """Send command ke backend"""
        if not self.connected:
            self.log.append("❌ Not connected!")
            return
        try:
            await asyncio.get_event_loop().sock_sendall(self._sock, (cmd + "\n").encode())
            self.log.append(f"➡️ {cmd}")
            
            if cmd == "STOP_SAMPLING":
                self.is_sampling = False
        except Exception as e:
            self.log.append(f"❌ Send error")


# ==================== MAIN ENTRY POINT ====================
def main():
    """Main entry point untuk E-NOSE Dashboard"""
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    gui = ENoseGUI()
    gui.show()

    loop.call_soon(asyncio.create_task, gui.connect_backend())

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
