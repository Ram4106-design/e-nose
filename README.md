# 🔬 E-NOSE Real-Time Monitoring System

An advanced Electronic Nose (E-Nose) system designed for real-time air quality monitoring, featuring seamless integration with Edge Impulse for machine learning applications. This project leverages the high-performance capabilities of **Rust** for the backend and the versatility of **Python (PyQt6)** for a modern, responsive user interface.

---

## 📋 Key Features

### Backend (Rust)
- **⚡ High-Performance TCP Server**: Efficiently handles high-frequency sensor data streams with minimal latency.
- **🔄 Finite State Machine (FSM)**: Precisely controls the 5-stage sampling cycle (PRE_COND → RAMP_UP → HOLD → PURGE → RECOVERY) for consistent data acquisition.
- **📡 Robust Serial Communication**: Ensures stable and reliable data transmission from the Arduino microcontroller.

### Frontend (Python/PyQt6)
- **🎨 Modern Aesthetic**: A sleek, dark-themed user interface with neon accents for a premium look and feel.
- **📈 Real-Time Visualization**: Live plotting of data from 7 different sensors simultaneously.
- **☁️ Edge Impulse Integration**: Automatic and secure data uploading to Edge Impulse for training machine learning models.
- **💾 Data Management**: Easy export of sensor data to CSV format for offline analysis.

---

## 🛠️ Prerequisites

Before you begin, ensure your system meets the following requirements:

1.  **Rust Toolchain**: Required to compile and run the backend server.
    - [Download & Install Rust](https://rustup.rs/)
2.  **Python 3.8+**: Required to run the graphical user interface (GUI).
    - [Download & Install Python](https://www.python.org/downloads/)
3.  **Arduino IDE**: Required to upload the firmware to your microcontroller.
    - [Download Arduino IDE](https://www.arduino.cc/en/software)
4.  **Git**: Required to clone the project repository.
    - [Download Git](https://git-scm.com/downloads)
5.  **Edge Impulse Account** (Optional): Required if you plan to use the machine learning features.

---

## 📥 Installation Guide

Follow these steps to set up the project on your local machine:

### 1. Clone the Repository
Open your terminal (Command Prompt, PowerShell, or Terminal) and run:

```bash
git clone https://github.com/Ram4106-design/e-nose.git
cd e-nose
```

### 2. Setup the Backend (Rust)
Navigate to the backend directory and build the project in release mode for optimal performance:

```bash
cd backend
cargo build --release
```
*Note: The first build may take a few minutes as it downloads and compiles dependencies.*

### 3. Setup the Frontend (Python)
Open a **new** terminal window, navigate to the frontend directory, and install the required Python libraries:

```bash
cd frontend
pip install -r requirements.txt
```

---

## 🚀 How to Run the System

To operate the E-Nose system, you must start the components in the specific order outlined below.

### Step 1: Flash the Arduino Firmware
1.  Connect your Arduino board to your computer via USB.
2.  Open the file `arduino_enose_persistent.ino` in the **Arduino IDE**.
3.  Select your specific board model and the correct COM port under **Tools > Board** and **Tools > Port**.
4.  Click the **Upload** button (➡️ arrow icon).
5.  Wait for the "Done uploading" message.
6.  **Important**: Close the Serial Monitor in Arduino IDE if it is open, as it will block the backend from connecting.

### Step 2: Start the Backend Server
The backend acts as a bridge between the Arduino and the Frontend.

1.  Open a terminal in the `backend` directory.
2.  Run the server:
    ```bash
    cargo run --release
    ```
3.  You should see a message indicating the server is listening (e.g., `Server listening on 127.0.0.1:8082`).
4.  **Keep this terminal window open.** Closing it will stop the server.

### Step 3: Launch the Frontend Application
1.  Open a **new** terminal in the `frontend` directory.
2.  Launch the application:
    ```bash
    python main.py
    ```
3.  The E-Nose Dashboard window should appear on your screen.

---

## 📖 Detailed User Guide

### A. Verifying Connection
- Look at the status indicator in the bottom-left corner of the application window.
- It should display a green **"Connected"** status.
- If it says "Disconnected" (Red), ensure the Backend server (Step 2) is running and no other application is using the Arduino's serial port.

### B. Performing a Sampling Cycle
The system uses a standardized 5-stage sampling process to ensure data consistency.

1.  **Prepare Sample**: Place the substance you wish to analyze near the sensor array.
2.  **Start**: Click the large **▶ START SAMPLING** button.
3.  **Monitor Progress**: Watch the progress bar and status text. The system will automatically cycle through:
    - **PRE_COND**: Sensor pre-heating to baseline temperature.
    - **RAMP_UP**: Increasing sensor voltage/sensitivity.
    - **HOLD**: The critical data collection phase where the sensor is most stable.
    - **PURGE**: Cleaning the sensor chamber with fresh air.
    - **RECOVERY**: Allowing sensors to return to baseline resistance.
4.  **Completion**: Wait until the cycle finishes and the status returns to "IDLE".

### C. Uploading Data to Edge Impulse
This feature allows you to build a dataset for machine learning classification.

1.  **Configure Credentials**:
    - Locate the "💾 Export & Model" panel on the right side.
    - **API Key**: Paste your Edge Impulse project's API Key (found in Dashboard > Keys).
    - **Project ID**: Enter your Project ID (found in Dashboard).
    - **Label**: Enter a label for the current sample (e.g., `coffee`, `spoiled_milk`, `ambient`).
2.  **Automatic Upload**:
    - If the API Key is provided, the system is designed to automatically upload data at the end of a sampling cycle.
3.  **Manual Upload**:
    - If you want to re-upload the last collected sample, click the **📤 UPLOAD TO EI** button.
    - Check the application logs (terminal) or your Edge Impulse dashboard to confirm success.

### D. Exporting Data Locally
1.  After a sampling cycle is complete, click the **💾 SAVE CSV** button.
2.  The data will be saved as a `.csv` file in the `csv/` directory within your project folder.
3.  The filename will include the current timestamp for easy organization.

### E. 📊 Data Visualization
The system comes bundled with **Gnuplot** for advanced 3D visualization of sensor data.

1.  Navigate to the `csv/` directory:
    ```bash
    cd csv
    ```
2.  Run the visualization script:
    ```powershell
    .\plot_all.ps1
    ```
3.  This will automatically:
    - Detect all `.csv` files in the directory.
    - Launch Gnuplot for each file.
    - Display a 3D interactive plot of the sensor data.
    - Press **Enter** in the command window to proceed to the next file.

---

## 🔧 Troubleshooting

### Common Issues

**1. "Serial port not found" (Backend)**
- **Cause**: Arduino is not connected or the port is in use.
- **Fix**: Reconnect the USB cable. Ensure Arduino IDE Serial Monitor is closed. Restart the backend.

**2. "Connection Refused" (Frontend)**
- **Cause**: The Rust backend server is not running.
- **Fix**: Open the backend terminal and ensure `cargo run --release` is executing and shows "Listening".

**3. "Upload Failed" (Edge Impulse)**
- **Cause**: Incorrect API Key or Project ID.
- **Fix**: Double-check your credentials in the "Export & Model" panel. Ensure you have an active internet connection.

---
## Presentation 
You can see a presentation in this link :
https://www.canva.com/design/DAG6WvuOCFE/WUbyx3I3FtInJN7jPv_UEg/edit?utm_content=DAG6WvuOCFE&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton

## Report UAS 
You can see a report in this link :
https://drive.google.com/file/d/1iQDORXXXcKGlINf4yj-QDosfoPlXGISc/view?usp=sharing

## Documentation
You can see full documentation on graphic and UI in this link :
https://drive.google.com/drive/folders/1JMfnT8XOA5uCpr5_LnS0CNYw-blEBz39?usp=sharing

## Video Youtube
You can see full documentation video in this link :
[https://drive.google.com/drive/folders/1JMfnT8XOA5uCpr5_LnS0CNYw-blEBz39?usp=sharing](https://youtu.be/aB62kY_1prM?feature=shared)

## 👥 Authors
- **Sadrakh Ram Loudan Saputra** - Institut Teknologi Sepuluh Nopember
- **Hakan Maulana Yazid Zidane** - Institut Teknologi Sepuluh Nopember
- **Melodya Sembiring** - Institut Teknologi Sepuluh Nopember

---

## 📄 License
This project is open-source and available under the MIT License.
