from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Global dictionary to store the latest posture data
latest_posture_data = {
    "neck_angle": 0,
    "torso_angle": 0,
    "status": "Waiting for camera feed...",
    "good_time": 0.0,
    "bad_time": 0.0
}

# A simple, self-contained HTML dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Posture Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2f; color: #ffffff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background-color: #2a2a40; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; width: 400px; }
        h1 { margin-top: 0; color: #00d2ff; }
        .metric { margin: 20px 0; font-size: 1.2em; }
        .value { font-weight: bold; font-size: 1.5em; }
        .status-Good { color: #00ff88; font-weight: bold; font-size: 1.8em; margin: 20px 0; text-transform: uppercase;}
        .status-Bad { color: #ff3366; font-weight: bold; font-size: 1.8em; margin: 20px 0; text-transform: uppercase;}
        .alert { color: #ff3366; font-weight: bold; margin-top: 20px; animation: blinker 1s linear infinite; display: none; }
        @keyframes blinker { 50% { opacity: 0; } }
    </style>
</head>
<body>
    <div class="card">
        <h1>Posture Analysis</h1>
        <div id="status" class="status-Good">Waiting...</div>
        
        <div class="metric">Neck Angle: <span id="neck" class="value">0</span>&deg;</div>
        <div class="metric">Torso Angle: <span id="torso" class="value">0</span>&deg;</div>
        
        <hr style="border-color: #444; margin: 30px 0;">
        
        <div class="metric" style="color: #00ff88; font-size: 1em;">Good Time: <span id="good_time">0</span>s</div>
        <div class="metric" style="color: #ff3366; font-size: 1em;">Bad Time: <span id="bad_time">0</span>s</div>
        
        <div id="alert_box" class="alert">&#9888; CRITICAL: BAD POSTURE DETECTED FOR TOO LONG! &#9888;</div>
    </div>

    <script>
        // Fetch data from the server every 500ms
        setInterval(() => {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('neck').innerText = data.neck_angle;
                    document.getElementById('torso').innerText = data.torso_angle;
                    
                    const statusEl = document.getElementById('status');
                    statusEl.innerText = data.status;
                    statusEl.className = 'status-' + data.status;

                    document.getElementById('good_time').innerText = data.good_time;
                    document.getElementById('bad_time').innerText = data.bad_time;

                    // Trigger alert if bad posture exceeds 180 seconds
                    if (data.bad_time > 180) {
                        document.getElementById('alert_box').style.display = 'block';
                    } else {
                        document.getElementById('alert_box').style.display = 'none';
                    }
                })
                .catch(err => console.error("Error fetching data:", err));
        }, 500);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/update', methods=['POST'])
def update_data():
    global latest_posture_data
    latest_posture_data = request.json
    return jsonify({"message": "Data received"}), 200

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(latest_posture_data)

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(debug=True, port=5000, use_reloader=False)
