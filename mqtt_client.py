# mqtt_client.py
import os
import json
import time
import threading
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Callable
from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_KEY, MQTT_TELEMETRY_FEED, MQTT_COMMAND_FEED

class MQTTClient:
    def __init__(self, on_command: Callable[[str, dict], None] = None, use_tls=True):
        """
        MQTT client wrapper for smart car with Adafruit IO support.
        on_command: callback for incoming commands
        use_tls: enable TLS/SSL connection
        """
        self.on_command = on_command
        self.use_tls = use_tls
        self._already_connected = False
        self._connected = threading.Event()

        # Use unique client_id per run
        self.client = mqtt.Client(client_id=f"smartcar-{int(time.time())}")

        # Enable debug logging
        self.client.enable_logger()

        # Username/password authentication
        if MQTT_USERNAME and MQTT_KEY:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_KEY)

        # TLS/SSL setup
        if self.use_tls:
            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED,
                                tls_version=ssl.PROTOCOL_TLS_CLIENT)
            self.client.tls_insecure_set(False)

        # Event callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            if not self._already_connected:
                print("[MQTT] Connected successfully!")
                self._already_connected = True
            # Subscribe to command feed
            client.subscribe(MQTT_COMMAND_FEED)
            self._connected.set()
        else:
            print(f"[MQTT] Connect failed, return code={rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] Disconnected with return code={rc}")
        # Auto-reconnect if disconnected unexpectedly
        if rc != 0:
            print("[MQTT] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
            try:
                client.reconnect()
            except Exception as e:
                print("[MQTT] Reconnect failed:", e)

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload) if payload.strip().startswith("{") else {"value": payload}
            print(f"[MQTT] Message received on {msg.topic}: {payload}")
            if self.on_command:
                self.on_command(msg.topic, data)
        except Exception as e:
            print("[MQTT] Message handling error:", e)

    def connect(self):
        try:
            print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT} as {MQTT_USERNAME}")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print("[MQTT] Connection error:", e)
            return

        # Start loop in background thread
        thread = threading.Thread(target=self.client.loop_forever, daemon=True)
        thread.start()

        # Wait for connection with timeout
        if not self._connected.wait(timeout=10):
            print("[MQTT] Warning: Could not establish connection in 10 seconds")

    def publish(self, topic, payload):
        try:
            self.client.publish(topic, payload, qos=1)
        except Exception as e:
            print("[MQTT] Publish failed:", e)

    def disconnect(self):
        try:
            self.client.disconnect()
            print("[MQTT] Disconnected cleanly")
        except Exception as e:
            print("[MQTT] Disconnect failed:", e)


