<p align="center">
<img width="100" height="150" alt="pikachu" src="https://github.com/user-attachments/assets/00093461-e0c2-4e6e-98df-003bce09a787" />
</p>

# Project Pikachu: Smart Study Desk IoT
Project Pikachu is a fully decoupled, real-time IoT smart environment monitor. It is designed to track a student's study conditions, automate room appliances (AC, Fan, Lamp) based on environmental thresholds, enforce healthy posture using computer vision, and intelligently log study sessions to recommend personalized timetables.

## ✨ Features
**Decoupled Microservice Architecture:** Separates the central command hub (Main Server) from the data ingestion endpoints (Edge Nodes).

**Real-Time Telemetry**: Live streaming and graphing of Temperature, Humidity, AQI, Distance (Presence), and Light (Lux) using WebSockets and Chart.js.

### Smart Appliance Automation:

  **3-Phase Lighting**: Lamp adjusts automatically (OFF, 50%, 100%) based on ambient room Lux levels.

  **Climate Control**: AC and Fan auto-engage when temperature thresholds are breached.

**Intelligent Safety Timers**: Auto-pauses study sessions if critical conditions (High Temp for 5 mins, Bad AQI for 2 mins, or user absence) persist.

**Computer Vision Posture Tracking**: Uses OpenCV and MediaPipe to track neck and torso angles. Alerts the user if bad posture is maintained for over 10 seconds.

**Session Analytics & AI Timetable**: Records session start/stop times to sessions.json and analyzes average study durations to recommend scientifically backed study patterns (e.g., Pomodoro, 50/10 Rule, Ultradian Rhythms).

**Immersive UI/UX**: Built with Tailwind CSS, featuring "Thunderbolt" screen-shake animations, neon edge-lighting, and custom audio alerts.

## 🛠️ Tech Stack
Backend: Python 3, Flask, Flask-SocketIO, Requests

Frontend: HTML5, Tailwind CSS, JavaScript, Chart.js

Computer Vision: OpenCV (cv2), Google MediaPipe

Communication: HTTP REST API (Data Ingestion), WebSockets (Live UI Updates)

## 📁 Directory Structure
```
smart_study_iot/
│
├── main_server.py             # Central Command Hub (Port 5000)
├── sensor_server.py           # Edge Node Simulator (Port 5001)
├── posture.py                 # Computer Vision Edge Node
├── sessions.json              # Auto-generated study log database
│
├── static/
│   ├── alert.mp3              # Standard warning audio
│   ├── thunderbolt.mp3        # Session termination audio
│   └── pikachu.png            # Dashboard logo
│
└── templates/
    ├── main_dashboard.html    # Central UI & Analytics Graph
    ├── history.html           # Session Logs & AI Timetable
    └── simulator.html         # Manual Telemetry Injector UI
```
## 🚀 Installation & Setup
### 1. Clone or set up the directory
Ensure your folder structure matches the layout above and you have all your audio/image assets in the static folder.

### 2. Install Dependencies
Open your terminal and install the required Python libraries:

```
pip install Flask Flask-SocketIO requests opencv-python mediapipe
```
### 🎮 How to Run the System
Because this is a decoupled IoT network, you will need to start the different "nodes" in separate terminal windows.

#### Terminal 1: Start the Central Brain
This server hosts the UI, manages the WebSockets, and evaluates all logic thresholds.

Bash
```
python main_server.py
```
Access: Open http://127.0.0.1:5000 in your browser.

Click "INITIALIZE" on the dashboard to start accepting data.

#### Terminal 2: Start the Environment Simulator (Edge Node 1)
This server acts as your physical room sensors. It provides a UI with sliders that continuously POST data to the main server every 1 second.

Bash
```
python sensor_server.py
```
Access: Open http://127.0.0.1:5001 in a second browser tab.

Move the sliders here to watch the Main Dashboard react in real-time.

#### Terminal 3: Start the Biometrics Camera (Edge Node 2)
This script activates your webcam, calculates your spinal alignment, and pushes alerts to the Main Server if you slouch.

```
python posture.py
```
A video window will open. Slouch for 10 seconds to trigger the dashboard alarm!

## ⚙️ Configuration
You can easily adjust the environment thresholds by modifying the THRESHOLDS dictionary at the top of main_server.py:

```
THRESHOLDS = {
    "temp_high": 30.0,    # Trigger AC/Fan
    "aqi_high": 150.0,    # Trigger Air Quality Warning
    "distance_max": 100.0,# Trigger Auto-Pause (User Absent)
    "light_low": 300.0,   # Trigger 100% Lamp Brightness & Edge Glow
    "light_high": 700.0   # Turn Lamp OFF
}
```
