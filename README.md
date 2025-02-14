# Raspberry Pi Plant Humidity Monitor Webpage

This project is a web-based application designed to monitor the humidity levels of plants using a Raspberry Pi and MQTT. It consists of a Flask web server that displays real-time humidity data from multiple devices.

## Features

- Real-time humidity monitoring for multiple devices.
- Detailed view of humidity data with charts.
- Automatic cleanup of old data entries.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Samuel-James2003/raspberrypi-plant-humidity-webpage.git
   cd raspberrypi-plant-humidity-webpage
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environmental variables:**
   Create a `.env` file with the following variables:
   ```env
   MQTTCREDENTIALS=your_mqtt_credentials
   MQTTServer=your_mqtt_server
   LocalIP=your_local_ip
   ```

## Usage

1. **Run the Flask application:**
   ```bash
   python mqttscript.py
   ```

2. **Access the web interface:**
   Open your browser and navigate to `http://<LocalIP>:5000`.

## Endpoints

- `/` - Main page displaying real-time humidity status.
- `/status` - Endpoint to fetch the latest humidity data.
- `/detail/<mac_address>` - Detailed view of humidity data for a specific device.

## Author

Samuel-James2003
