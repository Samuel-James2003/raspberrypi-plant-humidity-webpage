from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import os

app = Flask(__name__)
# MQTT status
mqtt_status = {"topic": "Unknown", "status": "Unknown", "timestamp": "Unknown"}
log_file = "log.csv"

if not os.path.exists(log_file):
    with open(log_file, "w") as file:
        file.write("MAC,Message,Timestamp\n")  # Add headers for clarity

# Callback for MQTT messages
def on_message(client, userdata, message):
    global mqtt_status
    mqtt_status["topic"] = message.topic  # Store the topic
    mqtt_status["status"] = message.payload.decode()  # Store the payload
    mqtt_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store the timestamp

    # Extract MAC address from the topic
    mac_address = message.topic.split("/")[-1]

    # Append message to log file
    with open(log_file, "a") as file:
        file.write(f"{mac_address},{mqtt_status['status']},{mqtt_status['timestamp']}\n")

    # Clean up log file for entries older than 72 hours
    clean_log_file()
# Callback for MQTT messages
def on_message(client, userdata, message):
    global mqtt_status
    mqtt_status["topic"] = message.topic  # Store the topic
    mqtt_status["status"] = message.payload.decode()  # Store the payload
    mqtt_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store the timestamp
    
def clean_log_file():
    cutoff_time = datetime.now() - timedelta(hours=72)
    lines_to_keep = []

    with open(log_file, "r") as file:
        lines = file.readlines()

    # Keep header and recent entries
    lines_to_keep.append(lines[0])  # Header
    for line in lines[1:]:
        try:
            mac, message, timestamp = line.strip().split(",")
            entry_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            if entry_time >= cutoff_time:
                lines_to_keep.append(line)
        except ValueError:
            continue  # Ignore malformed lines

    with open(log_file, "w") as file:
        file.writelines(lines_to_keep)

# MQTT client setup
client = mqtt.Client()
client.username_pw_set(os.getenv("MQTTCREDENTIALS"), os.getenv("MQTTCREDENTIALS"))
client.on_message = on_message
client.connect(os.getenv("IPAddress"), 1883, 60)
client.subscribe("home/ESP32/Humidity/#")
client.loop_start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def get_status():
    return jsonify(mqtt_status)

if __name__ == "__main__":
    app.run(host=os.getenv("IPAddress"), port=5000)