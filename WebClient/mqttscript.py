from flask import Flask, render_template , redirect, redirect, url_for, request
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import os
import json
from debug import log_event
import telegramAlert

app = Flask(__name__)

log_file = "log.json"

# Ensure log file exists
def initialize_log_file():
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            json.dump({"responses": []}, f)

initialize_log_file()

# Function to clean old entries from the log
def clean_log():
    try:
        # Load the JSON data from the file
        with open(log_file, "r") as file:
            data = json.load(file)

        # Define the cutoff time
        cutoff_time = datetime.now() - timedelta(days=3)

        # Filter out old entries from each response
        for response in data["responses"]:
            response["messages"] = [
                message for message in response["messages"]
                if datetime.strptime(message["timestamp"], "%Y-%m-%d %H:%M:%S") > cutoff_time
            ]

        # Write the cleaned data back to the file
        with open(log_file, "w") as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        print(f"An error occurred during log cleaning: {e}")
  
def get_device_details(mac_address):
    with open(log_file, "r") as file:
        log_data = json.load(file)

    # Find the response entry for the specified MAC address
    response = next((response_entry for response_entry in log_data["responses"] if response_entry["MACAddress"] == mac_address), None)
    data = response["messages"] if response else []
    familiar_name = response["FamiliarName"] if response else ""
    return data, familiar_name

# Callback for MQTT messages
def on_message(client, userdata, message):
    try:
        # Decode the MQTT message payload
        payload_str = message.payload.decode()
        log_event(f"Decoded payload: {payload_str}")
        mac_address = message.topic.split("/")[-1]
        log_event(f"Extracted MAC address: {mac_address}")

        try:
            # Attempt to parse the payload as JSON
            data = json.loads(payload_str)
            log_event("JSON payload parsed successfully")
            # If successful, extract details from the JSON
            temperature = data.get("temperature")
            air_humidity = data.get("air_humidity")
            soil_humidity = data.get("soil_humidity")
            message_timestamp = data.get("timestamp")
            heat_index = data.get("heat_index")
            # Use the provided timestamp, or fallback to current time if absent
            timestamp = message_timestamp if message_timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare the log entry using the JSON data
            log_message = {
                "payload": str(soil_humidity),  # storing the soil humidity
                "timestamp": timestamp,
                "temperature": str(temperature), 
                "air_humidity": str(air_humidity),
                "heat_index": str(heat_index),
                "batterylevel": "0"
            }
        except (json.JSONDecodeError, AttributeError) as e:
            log_event(f"JSON decoding failed: {e}", level="ERROR", exc_info=True)
            # If JSON decoding fails, assume it's the plain integer payload
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = {
                "payload": payload_str,
                "timestamp": timestamp,
                "temperature": "0", 
                "air_humidity": "0",
                "heat_index": "0",
                "batterylevel": "0"
            }
        if int(log_message.get("payload", 0)) > 900:
            log_event(f"Alert: High soil humidity detected for MAC address: {mac_address}")
            telegramAlert.send_update(mac_address, os.getenv('BOT_TOKEN'))
        # Load the current log data
        with open(log_file, "r") as f:
            log_data = json.load(f)

        # Find or create the response entry for the MAC address
        response = next((r for r in log_data["responses"] if r["MACAddress"] == mac_address), None)
        if not response:
            response = {
                "MACAddress": mac_address,
                "FamiliarName": "",
                "messages": []
            }
            log_data["responses"].append(response)
            log_event(f"create a new response entry for MAC address: {mac_address}")
        
        # Add the new message to the response's messages list
        response["messages"].append(log_message)
        log_event(f"add a {log_message} to the response entry for MAC address: {mac_address}")
        # Save the updated log data
        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=4)

    except Exception as e:
        print(e)
        # Log the error and continue processing the next message
        log_event(f"An error occurred: {e}", level="ERROR", exc_info=True)
        
    finally:
        # Clean up old entries
        clean_log()

        
# MQTT client setup
client = mqtt.Client()
client.username_pw_set(os.getenv("MQTTCREDENTIALS"), os.getenv("MQTTCREDENTIALS"))
client.on_message = on_message
client.connect(os.getenv("MQTTServer"), 1883, 60)
client.subscribe("home/ESP32/Humidity/#")
client.subscribe("home/ESP32/Sensor/#")
client.loop_start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/change-name/<mac_address>", methods=["POST"])
def new_name(mac_address):
    if request.get_json()["new_name"]:
        name = request.get_json()["new_name"]
    else:
        name = ""

    with open(log_file, "r") as file:
        log_data = json.load(file)

    for response in log_data["responses"]:
        if response["MACAddress"] == mac_address:
            response["FamiliarName"] = name
            break
    else:
        return "MAC address not found", 404

    with open(log_file, "w") as file:
        json.dump(log_data, file, indent=4)
    return "Success", 200

@app.route("/status")
def get_status():
    with open(log_file, 'r') as file:
        log_data = json.load(file)

    # Extract the last message for each MAC address
    status_data = {
        response["MACAddress"]: response["messages"][-1] if response["messages"] else None
        for response in log_data["responses"]
    }

    return json.dumps(status_data, indent=4)


@app.route("/detail/<mac_address>")
def detail(mac_address):
    data, familiar_name = get_device_details(mac_address)
    return render_template("detail.html", mac_address=mac_address, data=data, familiar_name=familiar_name)

@app.route("/delete/<mac_address>")
def delete(mac_address):
    with open(log_file, "r") as file:
        log_data = json.load(file)

    # Remove the response entry for the specified MAC address
    log_data["responses"] = [
        response for response in log_data["responses"] if response["MACAddress"] != mac_address
    ]

    with open(log_file, "w") as file:
        json.dump(log_data, file, indent=4)

    return redirect(url_for("index"))

# Custom 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Run the Flask app
    print("Flask app is running...")
    app.run(host=os.getenv("LocalIP"), port=5000)
