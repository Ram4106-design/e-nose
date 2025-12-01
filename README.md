# 🔬 E-NOSE Real-Time Monitoring System

Electronic Nose (E-Nose) system dengan monitoring real-time dan integrasi Edge Impulse untuk machine learning.

## 📋 Features

### Backend (Rust)
- ⚡ High-performance TCP server
- 📊 Real-time sensor data streaming
- 🔄 Finite State Machine (FSM) untuk sampling control
- 🎯 5-level sampling protocol (PRE_COND → RAMP_UP → HOLD → PURGE → RECOVERY)
- 📡 Serial communication dengan Arduino

### Frontend (Python/PyQt6)
- 🎨 Modern dark-themed UI dengan neon accents
- 📈 Real-time graph visualization (7 sensors)
- 🔴 Live status monitoring dengan level progress bar
- 💾 CSV export untuk data analysis
- 📤 **Real-time auto-upload ke Edge Impulse**
- 🧠 Edge Impulse model loading untuk klasifikasi

### Edge Impulse Integration
- ✅ Automatic data upload setelah sampling selesai
- 🔐 Secure API authentication
- 🏷️ Automatic data labeling
- 📊 Seamless training data collection

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Rust 1.70+
- Edge Impulse account (optional, untuk ML features)

### Installation

1. **Clone repository**
```bash
git clone https://github.com/YOUR_USERNAME/enose.git
cd enose
```

2. **Setup Backend (Rust)**
```bash
cd backend
cargo build --release
cargo run --release
```

3. **Setup Frontend (Python)**
```bash
cd frontend
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python main.py
```

## 📊 Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| NO2 | Nitrogen Dioxide | ppm |
| ETH | Ethanol | ppm |
| VOC | Volatile Organic Compounds | ppm |
| CO | Carbon Monoxide | ppm |
| COM | Compensated value | - |
| ETHM | Ethanol Modified | ppm |
| VOCM | VOC Modified | ppm |

## 🎯 Usage

### Real-Time Edge Impulse Integration

1. **Fill credentials** di panel "💾 Export & Model":
   - API Key: Your Edge Impulse API key
   - Project ID: Your Edge Impulse project ID
   - Label: Data label (e.g., `coffee`, `tea`, `ethanol`)

2. **Start sampling**:
   - Click "▶ START SAMPLING"
   - Wait for 5 levels to complete (~6 minutes)

3. **Automatic upload**:
   - Data otomatis ter-upload ke Edge Impulse
   - Check Edge Impulse dashboard untuk verify

### Manual Workflow

1. Start sampling → Wait for completion
2. Save CSV dengan "💾 SAVE CSV"
3. Upload manual dengan "📤 UPLOAD TO EI" (optional)

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Arduino   │ Serial  │ Rust Backend │  TCP    │ Python Frontend │
│  (Sensors)  │────────▶│   (Server)   │────────▶│   (Dashboard)   │
└─────────────┘         └──────────────┘         └─────────────────┘
                                                          │
                                                          │ HTTPS
                                                          ▼
                                                  ┌───────────────┐
                                                  │ Edge Impulse  │
                                                  │      API      │
                                                  └───────────────┘
```

## 📁 Project Structure

```
enose/
├── backend/           # Rust TCP server
│   ├── src/
│   │   ├── main.rs
│   │   ├── filtering.rs
│   │   └── ...
│   └── Cargo.toml
├── frontend/          # Python PyQt6 GUI
│   ├── main.py        # Main application
│   ├── config.py      # Configuration
│   ├── utils.py       # Edge Impulse handler
│   └── requirements.txt
└── csv/              # Saved CSV files
```

## 🔧 Configuration

### Backend (`backend/src/main.rs`)
- TCP Port: `8082`
- Serial Port: Auto-detect Arduino
- Baud Rate: `115200`

### Frontend (`frontend/config.py`)
- Backend Host: `127.0.0.1`
- Backend Port: `8082`
- Max Data Points: `300`
- Edge Impulse API: `https://ingestion.edgeimpulse.com/api/training/data`

## 📝 CSV Format

```csv
sample_name,collection_date,timestamp,NO2,ETH,VOC,CO,COM,ETHM,VOCM
coffee,2025-12-01T17:00:00,2025-12-01T17:00:01,1.2,3.4,5.6,7.8,9.0,1.1,2.2
...
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Edge Impulse for ML platform
- PyQt6 for GUI framework
- Rust community for excellent tools
