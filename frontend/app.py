import os
import json
import requests
import psycopg2
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# -------------------------
# CONFIG
# -------------------------
AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

HEADERS = {
    "X-AIO-Key": AIO_KEY,
    "Content-Type": "application/json"
}

# Telemetry feed
FEED_TELEMETRY = os.getenv("AIO_FEED_TELEMETRY", "smartcar-telemetry")

# Command feed
FEED_COMMANDS = os.getenv("AIO_CMD_COMMANDS", "smartcar-commands")

# Database credentials
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Image storage directory (for local development/testing)
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "static", "captures")
os.makedirs(CAPTURE_DIR, exist_ok=True)


# -------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


# -------------------------------------------
# ADAFRUIT IO HELPERS
# -------------------------------------------
def aio_get(feed, key=None):
    """Get last value from Adafruit IO feed. Parse JSON if necessary."""
    url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed}/data/last"
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
        data = r.json().get("value")
        if data is None:
            return "N/A"
        # Parse JSON if feed value is JSON string
        if isinstance(data, str):
            data = json.loads(data)
        return data[key] if key else data
    except Exception as e:
        print("AIO GET ERROR:", e)
        return "N/A"


def aio_send(feed, value):
    """Send command to Adafruit IO."""
    url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed}/data"
    # Always send {"value": ...} for Adafruit IO feeds
    data = {"value": value}
    try:
        requests.post(url, headers=HEADERS, json=data, timeout=4)
        return True
    except Exception as e:
        print("AIO SEND ERROR:", e)
        return False



# -------------------------------------------
# ROUTES
# -------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/sensors")
def sensors():
    return render_template("sensors.html")


@app.route("/control")
def control():
    return render_template("control.html")


@app.route("/line")
def line_tracking():
    return render_template("line_tracking.html")


@app.route("/obstacle")
def obstacle_avoid():
    return render_template("obstacle.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/api/live")
def api_live():
    """Return latest telemetry data for dashboard."""
    telemetry = aio_get(FEED_TELEMETRY)
    if telemetry == "N/A":
        return {"ir": "N/A", "ultrasonic": "N/A", "speed": "N/A"}

    return {
        "ir": telemetry.get("ir", "N/A"),
        "ultrasonic": telemetry.get("distance", "N/A"),
        "speed": telemetry.get("motor", [0])[0],  # first motor as example
        "mode": telemetry.get("mode", "N/A"),
        "battery": telemetry.get("battery", "N/A"),
        "car_active": telemetry.get("car_active", False)
    }


@app.route("/api/control", methods=["POST"])
def api_control():
    """Send control command to backend."""
    data = request.json
    device = data.get("device")
    value = data.get("value")

    # Map all device types to the command feed
    mapping = {
        "motor": FEED_COMMANDS,
        "mode": FEED_COMMANDS,
        "buzzer": FEED_COMMANDS,
        "led": FEED_COMMANDS,      # LED control
        "camera": FEED_COMMANDS     # Camera control
    }

    feed = mapping.get(device)
    if feed is None:
        return jsonify({"status": "error", "msg": "unknown device"}), 400

    # Send the command value to Adafruit IO
    # Backend will receive and process: take_photo, led_on, led_off, etc.
    ok = aio_send(feed, value)
    return jsonify({"status": "ok" if ok else "error"})


@app.route("/api/history")
def history():
    """Return historical telemetry from database."""
    date = request.args.get("date")
    if not date:
        return {"error": "missing date"}, 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First, check if telemetry table exists and get its columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'telemetry'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
        
        # If table doesn't exist or is empty, return empty data
        if not columns:
            cur.close()
            conn.close()
            return {
                "timestamps": [],
                "ir": [],
                "ultrasonic": [],
                "speed": []
            }
        
        # Build query based on available columns
        timestamp_col = next((col for col in columns if 'time' in col.lower()), 'id')
        ir_col = next((col for col in columns if 'ir' in col.lower()), None)
        ultrasonic_col = next((col for col in columns if 'ultrasonic' in col.lower() or 'distance' in col.lower()), None)
        speed_col = next((col for col in columns if 'speed' in col.lower() or 'motor' in col.lower()), None)
        
        # Execute query with dynamic column names
        if timestamp_col != 'id':
            cur.execute(f"""
                SELECT {timestamp_col}, {ir_col or 'NULL'}, {ultrasonic_col or 'NULL'}, {speed_col or 'NULL'}
                FROM telemetry
                WHERE DATE({timestamp_col}) = %s
                ORDER BY {timestamp_col} ASC
            """, (date,))
        else:
            # If no timestamp column, just get recent records
            cur.execute(f"""
                SELECT {timestamp_col}, {ir_col or 'NULL'}, {ultrasonic_col or 'NULL'}, {speed_col or 'NULL'}
                FROM telemetry
                ORDER BY {timestamp_col} DESC
                LIMIT 100
            """)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Return empty arrays if no data found
        if not rows:
            return {
                "timestamps": [],
                "ir": [],
                "ultrasonic": [],
                "speed": []
            }
        
        return {
            "timestamps": [str(r[0]) for r in rows],
            "ir": [r[1] if r[1] is not None else 0 for r in rows],
            "ultrasonic": [r[2] if r[2] is not None else 0 for r in rows],
            "speed": [r[3] if r[3] is not None else 0 for r in rows]
        }
    except Exception as e:
        print("DB ERROR:", e)
        # Return empty data instead of error to prevent frontend issues
        return {
            "timestamps": [],
            "ir": [],
            "ultrasonic": [],
            "speed": [],
            "error": str(e)
        }


@app.route("/images/<filename>")
def serve_image(filename):
    """Serve captured images from the captures directory."""
    try:
        return send_from_directory(CAPTURE_DIR, filename)
    except Exception as e:
        print("IMAGE SERVE ERROR:", e)
        return jsonify({"status": "error", "msg": "Image not found"}), 404


@app.route("/api/images")
def api_images():
    """Get list of all captured images."""
    try:
        # Get images from local directory
        if os.path.exists(CAPTURE_DIR):
            files = [f for f in os.listdir(CAPTURE_DIR) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            # Sort by modification time, newest first
            files.sort(key=lambda x: os.path.getmtime(os.path.join(CAPTURE_DIR, x)), reverse=True)
            
            images = []
            for f in files:
                file_path = os.path.join(CAPTURE_DIR, f)
                images.append({
                    "filename": f,
                    "url": f"/images/{f}",
                    "timestamp": os.path.getmtime(file_path),
                    "size": os.path.getsize(file_path)
                })
            
            return jsonify({"status": "ok", "images": images, "count": len(images)})
        else:
            return jsonify({"status": "ok", "images": [], "count": 0})
    except Exception as e:
        print("IMAGE LIST ERROR:", e)
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route("/api/images/latest")
def api_latest_image():
    """Get info about the most recently captured image."""
    try:
        # Check local directory first
        if os.path.exists(CAPTURE_DIR):
            files = [f for f in os.listdir(CAPTURE_DIR) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if files:
                # Get most recent file
                latest = max(files, key=lambda x: os.path.getmtime(os.path.join(CAPTURE_DIR, x)))
                file_path = os.path.join(CAPTURE_DIR, latest)
                return jsonify({
                    "status": "ok",
                    "image": {
                        "filename": latest,
                        "url": f"/images/{latest}",
                        "timestamp": os.path.getmtime(file_path)
                    }
                })
        
        # Fall back to Adafruit IO if no local images
        image_data = aio_get("smartcar-images")
        if image_data != "N/A":
            return jsonify({"status": "ok", "image": image_data})
        else:
            return jsonify({"status": "ok", "image": None, "msg": "No images available"})
    except Exception as e:
        print("IMAGE API ERROR:", e)
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
