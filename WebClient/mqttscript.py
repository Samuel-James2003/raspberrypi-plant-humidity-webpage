from flask import Flask, jsonify, render_template, send_file
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)

# MQTT status
mqtt_status = {"topic": "Unknown", "status": "Unknown", "timestamp": "Unknown"}
log_file = "log.json"

# Ensure log file exists
def initialize_log_file():
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            json.dump({}, f)

initialize_log_file()

# Clean up old entries from the log
def clean_log():
    with open(log_file, "r") as f:
        log_data = json.load(f)

    cutoff_time = datetime.now() - timedelta(hours=72)
    
    for mac, entries in list(log_data.items()):
        log_data[mac] = [entry for entry in entries if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") > cutoff_time]

        # Remove MAC if no entries remain
        if not log_data[mac]:
            del log_data[mac]

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=4)

# Callback for MQTT messages
def on_message(client, userdata, message):
    global mqtt_status
    mqtt_status["topic"] = message.topic  
    mqtt_status["status"] = message.payload.decode()
    mqtt_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 

    # Extract MAC address from topic
    mac_address = message.topic.split("/")[-1]

    # Update log
    with open(log_file, "r") as f:
        log_data = json.load(f)

    if mac_address not in log_data:
        log_data[mac_address] = []

    log_data[mac_address].append({
        "payload": message.payload.decode(),
        "timestamp": mqtt_status["timestamp"]
    })

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=4)

    # Clean up old entries
    clean_log()

# MQTT client setup
client = mqtt.Client()
client.username_pw_set(os.getenv("MQTTCREDENTIALS"), os.getenv("MQTTCREDENTIALS"))
client.on_message = on_message
client.connect(os.getenv("MQTTServer"), 1883, 60)
client.subscribe("home/ESP32/Humidity/#")
client.loop_start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def get_status():
    with open(log_file, 'r') as file:
        file_contents = file.read()
    return file_contents

if __name__ == "__main__":
    app.run(host=os.getenv("LocalIP"), port=5000)
