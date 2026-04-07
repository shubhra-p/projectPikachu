from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Address of the Main Brain
MAIN_SERVER_URL = "http://127.0.0.1:5000/ingest"

@app.route('/')
def simulator():
    return render_template('simulator.html')

@app.route('/transmit', methods=['POST'])
def transmit():
    """Receives data from the Simulator UI and pushes it to the Main Server"""
    sensor_data = request.json
    try:
        # PUSH data to the main server
        response = requests.post(MAIN_SERVER_URL, json=sensor_data, timeout=2)
        if response.status_code == 200:
            return jsonify({"status": "Transmission Successful"}), 200
    except requests.exceptions.RequestException as e:
        print("MAIN SERVER UNREACHABLE. Check connection.")
        return jsonify({"error": "Transmission Failed"}), 503

if __name__ == '__main__':
    print("EDGE NODE (Sensor Simulator) ONLINE on Port 5001")
    app.run(port=5001, debug=True)