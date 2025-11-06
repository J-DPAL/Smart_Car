# Smart Mobile Robot — IoT Term Project (Track 2)
**Course:** 420-N55 IoT: Design & Prototyping of Connected Devices — Fall 2025  
**Author(s):** <YOUR NAME(s)>  
**Instructor:** Prof. Haikel Hichri

## What this deliverable contains
This repository provides a complete, runnable **smart mobile robot** project scaffold you can run on a Raspberry Pi (real-hardware) or in **simulation** on your workstation. It includes:
- Drivers for sensors/actuators (ADC, Ultrasonic, Infrared, Motor, Servo, LED, Buzzer) with **hardware** and **simulation** fallback.
- `main.py` state machine supporting **modes**: Line Follow (infrared), Ultrasonic obstacle avoidance, Manual, and Calibration.
- MQTT client module to publish telemetry and receive remote commands (designed for Adafruit IO; **no hard-coded keys**).
- Daily JSONL logging with rotation and an uploader script placeholder (cron friendly).
- `systemd` unit file example to auto-start the service.
- A `zip` file containing the entire codebase (this archive).

**Important — no hard-coded secrets:**  
Set the following environment variables before running:
- `ADA_USERNAME` — Adafruit IO username (or generic MQTT username)
- `ADA_KEY` — Adafruit IO key (or generic MQTT password)
- `CLOUD_UPLOAD_URL` — optional HTTP endpoint for automatic uploads
- `CLOUD_UPLOAD_TOKEN` — optional token for upload endpoint

## How to run (simulation mode, on any machine)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Run in simulation (no hardware required)
python src/main.py --mode simulate
```

## How to run on Raspberry Pi (hardware)
- Install Raspberry Pi OS (64-bit recommended), enable I2C and GPIO.
- Install requirements and run without `--mode simulate`. Ensure wiring is correct and batteries/regulators used.
- Configure MQTT/Adafruit IO credentials as environment variables before launching.

## Files of interest
- `src/main.py` — entrypoint and main loop
- `src/car/car.py` — Car high-level class (modes and motor commands)
- `src/mqtt_client.py` — MQTT wrapper (publishes telemetry and reacts to commands)
- `logs/` — daily JSONL logs (created at runtime)
- `upload_daily.sh` — example script to upload logs to a cloud endpoint

## What you must still provide / do
- Physical wiring and safety checks (fuses, separate motor power).
- Adafruit IO dashboard creation (feeds) and the credentials as environment variables.
- Optional: replace `CLOUD_UPLOAD_URL`/token with your chosen cloud storage (S3, Google Drive via rclone, etc.)

---
See the code in `src/` for implementation details and comments.
