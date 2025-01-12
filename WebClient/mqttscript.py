from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
from datetime import datetime  
import os

app = Flask(__name__)

# MQTT status
mqtt_status = {"topic": "Unknown", "status": "Unknown", "timestamp": "Unknown"}

# Callback for MQTT messages
def on_message(client, userdata, message):
    global mqtt_status
    mqtt_status["topic"] = message.topic  # Store the topic
    mqtt_status["status"] = message.payload.decode()  # Store the payload
    mqtt_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store the timestamp

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
    app.run(host="192.168.1.20", port=5000)