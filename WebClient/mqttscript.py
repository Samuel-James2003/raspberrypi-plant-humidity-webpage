from flask import Flask, render_template
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

def clean_log():
    try:
        # Load the JSON data from the file
        with open("log.json", "r") as file:
            data = json.load(file)
        
        # Define the cutoff time
        cutoff_time = datetime.now() - timedelta(days=3)
        
        # Convert the timestamps and filter out older entries
        for key, entries in data.items():
            data[key] = [
                entry for entry in entries 
                if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") > cutoff_time
            ]
        
        # Write the cleaned data back to the file
        with open("log.json", "w") as file:
            json.dump(data, file, indent=4)
    
    except Exception as e:
        print(f"An error occurred: {e}")


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

@app.route("/detail/<mac_address>")
def detail(mac_address):
    with open(log_file, "r") as file:
        log_data = json.load(file)   
    # Get data for the specified MAC address
    data = log_data.get(mac_address, [])
    return render_template("detail.html", mac_address=mac_address, data=data)


if __name__ == "__main__":
    app.run(host=os.getenv("LocalIP"), port=5000)
