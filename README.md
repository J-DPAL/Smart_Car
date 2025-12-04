# 🚗 Smart Car Project

> An IoT-powered autonomous robotic car with real-time telemetry monitoring, line tracking, obstacle avoidance, and cloud integration.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-smart--car--y6gs.onrender.com-blue?style=for-the-badge)](https://smart-car-y6gs.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4%2F5-red?style=flat-square&logo=raspberry-pi)](https://www.raspberrypi.org/)

---

## 👥 Team Members

- **Jean-David** - Full-Stack Developer
- **Jose** - Full-Stack Developer

**Institution:** Champlain College Saint-Lambert  
**Course:** IoT: Design and Prototyping of Connected Devices (420-N55)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Hardware Components](#-hardware-components)
- [Software Stack](#-software-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Usage](#-usage)
- [Live Links](#-live-links)
- [Reflection](#-reflection)
- [Future Improvements](#-future-improvements)
- [License](#-license)

---

## 🔍 Overview

This project implements a comprehensive **IoT Smart Car system** featuring advanced autonomous capabilities including line tracking, obstacle avoidance, real-time telemetry monitoring, and cloud-based data synchronization. Built with modern web technologies and IoT protocols, the system provides a complete solution for robotic car control and analytics.

The smart car operates on a **Raspberry Pi 4/5**, communicating with a cloud-based Flask web application via **MQTT (Adafruit IO)** for real-time command and telemetry exchange. All sensor data is synchronized to a **PostgreSQL cloud database** for historical analysis and visualization.

**Live Website:** [https://smart-car-y6gs.onrender.com/](https://smart-car-y6gs.onrender.com/)

---

## ✨ Features

### 🤖 Autonomous Modes
- **Line Tracking Algorithm** - Autonomous line following using 3 IR sensors with real-time path correction
- **Obstacle Avoidance System** - Ultrasonic-based collision detection with intelligent navigation responses (<20cm threshold)

### 🎮 Manual Control
- Full directional control (forward, backward, left, right, stop)
- Buzzer control (ON/OFF)
- LED control (all LEDs, individual LED1/LED2)
- Camera capture with image gallery

### 📊 Real-Time Monitoring
- Live sensor dashboard with auto-refresh (1.5s intervals)
- IR sensor readings (3 channels)
- Ultrasonic distance measurements (cm)
- Motor speed tracking
- Connection status indicators

### 📈 Historical Analytics
- Interactive Chart.js visualizations
- Date-based sensor data queries
- Telemetry trend analysis over time

### ☁️ Cloud Integration
- **Adafruit IO MQTT** - Real-time bidirectional communication
- **PostgreSQL (Neon.tech)** - Cloud database for persistent storage
- **Local SQLite** - Offline buffering with automatic cloud sync
- **Image Gallery** - Captured photos stored and served via Flask

### 🌐 Web Interface
- Responsive design with dark mode support
- 7 pages: Home, Sensors, Control, Line Tracking, Obstacle Avoidance, Gallery, About
- Real-time WebSocket-like updates via MQTT polling
- Mobile-friendly UI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLOUD LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Flask Web   │  │  PostgreSQL  │  │ Adafruit IO  │     │
│  │  (Render)    │  │  (Neon.tech) │  │    (MQTT)    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
          │ HTTP/REST        │ psycopg         │ MQTT
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────┐
│               RASPBERRY PI (Backend)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  main.py (Python)                                    │  │
│  │  - MQTT Client                                       │  │
│  │  - Sensor Reading Loop                               │  │
│  │  - Autonomous Algorithms                             │  │
│  │  - Local SQLite + Cloud Sync                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│         ┌─────────────────┴─────────────────┐              │
│         ▼                 ▼                 ▼               │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │ Sensors  │     │  Motors  │     │ Camera   │           │
│  │ IR×3     │     │  PCA9685 │     │ Picamera2│           │
│  │ Ultrasonic│    │  4-wheel │     │          │           │
│  │ ADC      │     │  Drive   │     │          │           │
│  └──────────┘     └──────────┘     └──────────┘           │
│                                                             │
│  ┌──────────┐     ┌──────────┐                             │
│  │ Buzzer   │     │ LEDs     │                             │
│  │          │     │ WS281x/  │                             │
│  │          │     │ SPI      │                             │
│  └──────────┘     └──────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Hardware Components

### Main Board
- **Raspberry Pi 4/5** - Main controller running Python backend
- **Freenove 4WD Smart Car Kit** - Chassis and motor system

### Sensors
- **3× IR Line Sensors** (GPIO pins 14, 15, 23) - Line detection
- **HC-SR04 Ultrasonic** (Trigger: GPIO 5, Echo: GPIO 6) - Distance measurement
- **ADC Module** - Battery voltage monitoring

### Actuators
- **PCA9685 PWM Driver** (I2C bus 1, address 0x40) - Motor control
- **4× DC Motors** - 4-wheel drive system
- **Active Buzzer** - Audio feedback
- **WS281x/SPI LED Strip** - Visual indicators (4-60 LEDs)

### Peripherals
- **Picamera2 Module** - Image/video capture
- **Servo Motor** (optional) - Camera pan/tilt

---

## 💻 Software Stack

### Backend (Raspberry Pi)
```
Python 3.11
├── paho-mqtt           # MQTT client for Adafruit IO
├── gpiozero            # GPIO control (sensors, buzzer)
├── picamera2           # Camera interface
├── psycopg2-binary     # PostgreSQL adapter
├── sqlalchemy          # ORM for local/cloud DB
├── adafruit-pca9685    # PWM motor driver
├── rpi_ws281x          # LED strip control
├── python-dotenv       # Environment variables
└── requests            # HTTP client
```

### Frontend (Flask Web App)
```
Python 3.13
├── Flask 3.0.0         # Web framework
├── gunicorn 21.2.0     # WSGI server
├── psycopg 3.2.3       # PostgreSQL driver (v3)
├── requests 2.31.0     # HTTP client
└── python-dotenv 1.0.0 # Environment variables

Frontend Assets
├── Chart.js 4.4.0      # Data visualization
├── Vanilla JavaScript  # Dynamic UI updates
└── Custom CSS          # Responsive design + dark mode
```

### Cloud Services
- **Render.com** - Flask app hosting (free tier)
- **Neon.tech** - PostgreSQL database (serverless)
- **Adafruit IO** - MQTT broker for IoT messaging
- **GitHub** - Version control and CI/CD

---

## 📁 Project Structure

```
SmartCarApp/
├── frontend/                    # Flask web application
│   ├── app.py                  # Main Flask server
│   ├── requirements.txt        # Python dependencies
│   ├── database/
│   │   ├── db.py              # Database connection
│   │   └── create_tables.py   # Schema definitions
│   ├── static/
│   │   ├── styles.css         # Global styles
│   │   ├── script.js          # Main JS functions
│   │   ├── chart.js           # Chart rendering
│   │   ├── control.js         # Control page logic
│   │   └── images/
│   │       └── smart_car.png  # Project photo
│   └── templates/
│       ├── base.html          # Base template with nav
│       ├── index.html         # Home page
│       ├── sensors.html       # Live dashboard
│       ├── control.html       # Manual control
│       ├── line_tracking.html # Line tracking UI
│       ├── obstacle.html      # Obstacle avoidance UI
│       ├── gallery.html       # Image gallery
│       ├── about.html         # About page
│       └── error.html         # Error page
│
├── backend/                     # Raspberry Pi Python code
│   ├── main.py                 # Main control loop
│   ├── config.py               # Configuration (not tracked)
│   ├── requirements.txt        # Python dependencies
│   ├── car.py                  # Car class (high-level)
│   ├── motor.py                # PCA9685 motor driver
│   ├── infrared.py             # IR sensor module
│   ├── ultrasonic.py           # Ultrasonic sensor
│   ├── camera.py               # Picamera2 interface
│   ├── buzzer.py               # Buzzer control
│   ├── leds.py                 # LED strip manager
│   ├── adc.py                  # ADC voltage reader
│   ├── mqtt_client.py          # Adafruit IO MQTT
│   ├── localdb.py              # SQLite local DB
│   ├── sync_to_cloud.py        # Cloud sync worker
│   ├── logger.py               # JSONL logging
│   ├── parameter.py            # Hardware detection
│   ├── rpi_ledpixel.py         # WS281x LED driver
│   ├── spi_ledpixel.py         # SPI LED driver
│   ├── smartcar.service        # systemd service
│   └── upload_daily.sh         # Daily log upload script
│
├── .env                        # Environment variables (not tracked)
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Raspberry Pi 4/5** with Raspbian OS
- **Python 3.11+** on Raspberry Pi
- **Python 3.13+** for local frontend development
- **Git** installed
- **Adafruit IO account** (free tier)
- **Neon.tech PostgreSQL database** (free tier)

### 1. Clone the Repository
```bash
git clone https://github.com/J-DPAL/Smart_Car.git
cd Smart_Car
```

### 2. Backend Setup (Raspberry Pi)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create config.py from template
cat > config.py << EOF
import os
from dotenv import load_dotenv

load_dotenv()

# MQTT Configuration
MQTT_BROKER = "io.adafruit.com"
MQTT_PORT = 1883
MQTT_USERNAME = os.getenv("AIO_USERNAME")
MQTT_KEY = os.getenv("AIO_KEY")
MQTT_TELEMETRY_FEED = f"{MQTT_USERNAME}/feeds/smartcar-telemetry"
MQTT_COMMAND_FEED = f"{MQTT_USERNAME}/feeds/smartcar-commands"

# Database Configuration
CLOUD_DB_URL = os.getenv("DB_URL")
LOCAL_DB_FILE = "local_data.db"

# Logging
LOG_DIR = "logs"
CAPTURE_DIR = "captures"
EOF

# Create .env file
nano .env
# Add:
# AIO_USERNAME=your_username
# AIO_KEY=your_key
# DB_URL=your_postgresql_url

# Run the backend
python main.py --mode hardware
```

### 3. Frontend Setup (Local Development)

```bash
cd frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Add:
# AIO_USERNAME=your_username
# AIO_KEY=your_key
# DATABASE_URL=your_postgresql_url

# Run Flask development server
python app.py
```

### 4. Deploy Frontend to Render.com

1. Push code to GitHub
2. Create new Web Service on Render.com
3. Configure:
   - **Root Directory:** `frontend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
   - **Environment Variables:** Add `AIO_USERNAME`, `AIO_KEY`, `DATABASE_URL`

### 5. Auto-Start Backend on Raspberry Pi

```bash
# Copy service file
sudo cp smartcar.service /etc/systemd/system/

# Enable and start
sudo systemctl enable smartcar.service
sudo systemctl start smartcar.service

# Check status
sudo systemctl status smartcar.service
```

---

## 📖 Usage

### Web Interface

1. **Home Page** - Overview and project information
2. **Sensors Dashboard** - Real-time sensor monitoring with live charts
3. **Control Panel** - Manual car control (motors, buzzer, LEDs, camera)
4. **Line Tracking** - Start/stop autonomous line following mode
5. **Obstacle Avoidance** - Enable/disable obstacle detection and avoidance
6. **Gallery** - View captured images from the car's camera
7. **About** - Team information and project details

### API Endpoints

```
GET  /                        # Home page
GET  /sensors                 # Sensors dashboard
GET  /control                 # Control panel
GET  /line                    # Line tracking page
GET  /obstacle                # Obstacle avoidance page
GET  /gallery                 # Image gallery
GET  /about                   # About page

GET  /api/live                # Get latest telemetry (JSON)
POST /api/control             # Send control command (JSON)
GET  /api/history?date=YYYY-MM-DD  # Get historical data (JSON)
GET  /api/images              # List all captured images (JSON)
GET  /api/images/latest       # Get latest captured image info (JSON)
GET  /images/<filename>       # Serve image file
```

### MQTT Topics

**Publish (Backend → Cloud):**
- `AIO_USERNAME/feeds/smartcar-telemetry` - Sensor data (JSON)

**Subscribe (Cloud → Backend):**
- `AIO_USERNAME/feeds/smartcar-commands` - Control commands (JSON)

**Command Format:**
```json
{
  "device": "motor|buzzer|led|camera",
  "value": "forward|backward|left|right|stop|buzzer_on|buzzer_off|led_on|led_off|led1_on|led1_off|led2_on|led2_off|take_photo",
  "mode": "manual|line_tracking|obstacle_avoidance"
}
```

---

## 🔗 Live Links

### 🌐 Live Website
**URL:** [https://smart-car-y6gs.onrender.com/](https://smart-car-y6gs.onrender.com/)

The live website features:
- Real-time sensor monitoring
- Manual car control interface
- Historical data charts
- Captured image gallery
- Responsive design with dark mode

### 📡 Adafruit IO Dashboard
<img width="1688" height="758" alt="image" src="https://github.com/user-attachments/assets/2eb13dd9-67b9-437e-a7df-6ffc2b9ffb54" />


### ☁️ Cloud Database
**Provider:** Neon.tech (PostgreSQL serverless)  
**Tables:**
- `telemetry` - Historical sensor readings (timestamp, ir_value, ultrasonic_value, speed_value)
- `car_logs` - Operational logs
- `images` - Captured image metadata
- `commands` - Command history

### 📂 GitHub Repository
**URL:** [https://github.com/J-DPAL/Smart_Car](https://github.com/J-DPAL/Smart_Car)

---

## 💭 Reflection

### What Worked Well
The smart car project successfully integrated multiple IoT technologies into a cohesive autonomous system. The **infrared sensors** and **ultrasonic sensor** performed reliably for line tracking and obstacle detection. The **Adafruit IO MQTT** integration provided seamless real-time communication between the Raspberry Pi and the cloud-based Flask web application, enabling live monitoring and remote control. The **PostgreSQL cloud database** (Neon.tech) worked well for persistent storage and historical data analysis. The **Flask web interface** with Chart.js visualizations provided an intuitive and professional dashboard for interacting with the car. The **local SQLite database** with automatic cloud synchronization ensured data wasn't lost during network interruptions.

### Biggest Challenges
The **assembly process** was the most challenging aspect, as we encountered issues with missing hardware components and time management constraints. **Hardware debugging** on the Raspberry Pi required careful GPIO pin mapping and troubleshooting of sensor connections. Implementing **thread-safe camera captures** during obstacle avoidance mode required careful synchronization to prevent blocking the main control loop. Migrating from **psycopg2 to psycopg v3** during deployment to Render.com (Python 3.13 compatibility) required code adjustments. **Fine-tuning the line tracking algorithm** for different lighting conditions and line widths took significant testing and iteration.

### Future Improvements
We would add a **servo-controlled camera pan/tilt system** with live video streaming to the web dashboard for real-time remote viewing. Implementing **computer vision** using OpenCV for advanced line detection and object recognition would enhance autonomous capabilities. Adding **PWM speed control** for smoother acceleration and deceleration curves would improve driving performance. Creating a **mobile app** (React Native or Flutter) for on-the-go control would enhance accessibility. Expanding the **LED system** to display status information (e.g., mode indicators, battery level) through color-coded patterns would improve user feedback. Finally, implementing **automated testing** with pytest for both backend hardware modules and frontend API endpoints would improve code reliability and maintainability.

---

## 🔮 Future Improvements

### Planned Enhancements
- [ ] **Live Video Streaming** - WebRTC or MJPEG stream from Picamera2
- [ ] **Servo Camera Control** - Remote pan/tilt via web interface
- [ ] **Computer Vision** - OpenCV integration for advanced line detection
- [ ] **Mobile App** - React Native/Flutter app for iOS/Android
- [ ] **Voice Control** - Integration with Google Assistant/Alexa
- [ ] **Battery Monitoring** - Real-time voltage display with alerts
- [ ] **Speed Control** - PWM-based variable speed control
- [ ] **Path Recording** - Save and replay autonomous paths
- [ ] **Multi-Car Fleet** - Control multiple cars from one dashboard
- [ ] **Automated Testing** - Pytest unit tests for backend modules

---

## 📄 License

© 2025 Smart Car Project. All rights reserved.

Developed as part of **IoT: Design and Prototyping of Connected Devices (420-N55)**  
**Champlain College Saint-Lambert**

---

## 🙏 Acknowledgments

- **Freenove** - For the 4WD Smart Car Kit and hardware drivers
- **Adafruit** - For the excellent IoT cloud platform (Adafruit IO)
- **Neon.tech** - For the serverless PostgreSQL database
- **Render.com** - For free web hosting
- **Chart.js** - For beautiful data visualizations
- **Flask Team** - For the elegant Python web framework
- **Raspberry Pi Foundation** - For the amazing single-board computer


