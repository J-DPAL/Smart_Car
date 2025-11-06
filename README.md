# Smart Car

Project title: JDJV Car

Team members:
- Jean-David Pallares
- Jose Villegas Morilla

Overview
--------
This repository contains the code for the Smart Car project. The system collects sensor data, logs it locally with date-stamped filenames, publishes telemetry to Adafruit IO, and allows remote control and mode switching via the Adafruit IO dashboard. The project is implemented primarily in Python and is designed to run on a Raspberry Pi.

Adafruit IO dashboard
---------------------
<img width="1919" height="1037" alt="image" src="https://github.com/user-attachments/assets/595892fa-54ec-4407-8e63-9ca8e4e473fc" />


YouTube demo 
---------------------------
Link to a short video demonstrating the system and items below: https://youtube.com/shorts/RbXNCYkUxqU?si=R_-PdSzn4XZXOnhV

Repo structure 
-----------------------------------------------------------------------
- main.py — main loop, orchestrates sensors, actuators, MQTT client, and logger.
- sensors.py — sensor readers (e.g., distance sensor, line sensors, IMU).
- actuators.py — motor and servo control.
- mqtt_client.py — Adafruit IO / MQTT client wrapper (connect, publish, subscribe, reconnect logic).
- uploader.py — uploads daily files to cloud (e.g., to Google Drive / S3 / Dropbox).
- logger.py — local file logging, date-stamped filenames and format.
- systemd/smart_car.service — optional systemd unit for running at boot.
- requirements.txt — Python dependencies.

How to run 
---------------------
Command-line (development):
- Activate venv and run:
  python3 main.py

Logging and date-stamped filenames
----------------------------------
Local logging is implemented to create one file per day (example format):
- logs/YYYY-MM-DD.csv
- Each line is a timestamped record, for example:
  2025-11-06T23:26:23Z, sensor1_value, sensor2_value, ...

Uploader behavior
-----------------
- Uploader script runs periodically (e.g., cron or periodic thread) to upload the daily file to the cloud folder:
  - Local filename: logs/YYYY-MM-DD.csv
  - Uploaded path example: CloudFolder/Smart_Car/YYYY-MM-DD.csv

MQTT / Adafruit IO
------------------
- Adafruit IO is used for live telemetry and remote control.
- Ensure your Adafruit IO key is stored securely (e.g., environment variable or config file ignored by git).
- Typical topics:
  - feeds/smart-car/telemetry (publish sensor data)
  - feeds/smart-car/controls (subscribe for actuator commands)

Security & config
-----------------
- Keep secrets out of the repo. Use environment variables or a local config (config.example.json in repo).
- Example .gitignore entries:
```
config.json
secrets.env
logs/
```

Short reflection 
---------------------------------
This smart car project worked with the 2 sensors included: the infared and the ultrasonic. We also got the adafruit feeds to work correctly project some data from the car. The line tracking functionned well with some bugs in the sensors. What was the hardest was the assembly of the car as we had issues with missing screws and time management. What we would improve in this project is add a servio remote tracking to the dashboard and also a remote control to be able to drive around the car without the need of lines.
