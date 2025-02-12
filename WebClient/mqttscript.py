from flask import Flask, render_template , redirect, redirect, url_for, request
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)

# MQTT status
mqtt_status = {"topic": "Unknown", "status": "Unknown", "timestamp": "Unknown", "batterylevel": "Unknown"}
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
    response = next((response_entry for response_entry in log_data["responses"] if response_entry["MACAddress"].lower() == mac_address), None)
    data = response["messages"] if response else []
    familiar_name = response["FamiliarName"] if response else ""
    return data, familiar_name

# Callback for MQTT messages
def on_message(client, userdata, message):
    try:
        # Decode the MQTT message payload
        payload = message.payload.decode()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mac_address = message.topic.split("/")[-1]

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

        # Add the new message to the response's messages list
        response["messages"].append({
            "payload": payload,
            "timestamp": timestamp,
            "batterylevel": ""
        })

        # Save the updated log data
        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=4)
    
    except Exception as e:
        print(f"An error occurred on message: {e}")
        
    finally:
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
