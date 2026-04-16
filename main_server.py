from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import time
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyberpunk_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- STATE, THRESHOLDS & TIMERS ---
session_state = "stopped"
appliances = {"ac": False, "fan": False, "lamp_brightness": 50,"airPurifier":False}

THRESHOLDS = {
    "temp_high": 30.0, 
    "aqi_high": 150.0, 
    "distance_max": 100.0,
    "light_low": 300.0,
    "light_high": 700.0,
    "posture":5
}

condition_start_times = {"temp": None, "aqi": None}
LIMITS = {"temp": 300, "aqi": 120}

# --- SESSION LOGGING LOGIC ---
SESSION_FILE = 'sessions.json'
current_session_start = None

def load_sessions():
    if not os.path.exists(SESSION_FILE):
        return []
    with open(SESSION_FILE, 'r') as f:
        return json.load(f)

def save_session(start_dt, end_dt):
    sessions = load_sessions()
    duration_secs = (end_dt - start_dt).total_seconds()
    
    # Only save sessions that lasted longer than 1 minute to avoid clutter
    if duration_secs > 60:
        sessions.append({
            "date": start_dt.strftime("%b %d, %Y"),
            "start": start_dt.strftime("%I:%M %p"),
            "end": end_dt.strftime("%I:%M %p"),
            "duration_mins": round(duration_secs / 60)
        })
        with open(SESSION_FILE, 'w') as f:
            json.dump(sessions, f)

# --- ROUTES ---

@app.route('/')
def dashboard():
    return render_template('main_dashboard.html')

@app.route('/history')
def history():
    """Renders the History page and calculates a suggested timetable"""
    sessions = load_sessions()
    
    # Simple Timetable Suggestion Algorithm
    suggestion_title = "Awaiting Data"
    suggestion_text = "Complete a study session lasting more than 1 minute to generate a personalized timetable."
    
    if sessions:
        total_mins = sum(s['duration_mins'] for s in sessions)
        avg_duration = total_mins / len(sessions)
        
        # Find the most common time they start studying (AM/PM context)
        # We look at the first two characters of the start time (e.g., "10" from "10:30 AM")
        start_hours = [s['start'][:2] + s['start'][-2:] for s in sessions]
        best_hour = max(set(start_hours), key=start_hours.count)
        
        suggestion_title = f"Optimal Start Time: ~{best_hour}"
        
        if avg_duration < 45:
            suggestion_text = f"You prefer shorter study bursts (averaging {int(avg_duration)} mins). <strong>Recommendation:</strong> Use the Pomodoro technique. Study for 25 minutes, take a 5-minute break. Repeat 4 times before a long break."
        elif avg_duration < 90:
            suggestion_text = f"You have solid focus (averaging {int(avg_duration)} mins). <strong>Recommendation:</strong> The 50/10 Rule. Dive into deep work for 50 minutes, then physically step away from the desk for 10 minutes."
        else:
            suggestion_text = f"You run marathon sessions (averaging {int(avg_duration)} mins). <strong>Recommendation:</strong> Ultradian Rhythms. Work in intense 90-minute blocks, followed by mandatory 30-minute recovery breaks to prevent burnout."

    # Reverse the list to show the newest sessions at the top
    return render_template('history.html', sessions=reversed(sessions), suggestion_title=suggestion_title, suggestion_text=suggestion_text)

# --- INGESTION APIs (Same as before) ---

@app.route('/ingest', methods=['POST'])
def ingest_data():
    global session_state, appliances, condition_start_times
    sensor_data = request.json
    current_time = time.time()
    alerts = []
    time_remaining = {"temp": None, "aqi": None}

    if session_state == "running":
        # 1. TEMPERATURE LOGIC
        if sensor_data['temperature'] > THRESHOLDS['temp_high']:
            appliances['ac'], appliances['fan'] = True, True
            if condition_start_times['temp'] is None: condition_start_times['temp'] = current_time
            elapsed = current_time - condition_start_times['temp']
            remaining = max(0, LIMITS['temp'] - elapsed)
            time_remaining['temp'] = remaining
            
            if remaining > 0: alerts.append("TEMP HIGH: COOLING IN PROGRESS...")
            else:
                session_state = "paused"
                alerts.append("CRITICAL TEMP: SESSION AUTO-PAUSED.")
                condition_start_times['temp'] = None
        else:
            appliances['ac'], appliances['fan'] = False, False
            condition_start_times['temp'] = None

        # 2. AIR QUALITY LOGIC
        if sensor_data['aqi'] > THRESHOLDS['aqi_high']:
            appliances['airPurifier'] = True
            if condition_start_times['aqi'] is None: condition_start_times['aqi'] = current_time
            elapsed = current_time - condition_start_times['aqi']
            remaining = max(0, LIMITS['aqi'] - elapsed)
            time_remaining['aqi'] = remaining
            
            if remaining > 0: alerts.append("AQI WARNING: AIR QUALITY DEGRADING.")
            else:
                session_state = "paused"
                alerts.append("CRITICAL AQI: SESSION AUTO-PAUSED.")
                condition_start_times['aqi'] = None
        else:
            appliances['airPurifier'] = False
            condition_start_times['aqi'] = None

        # 3. DISTANCE LOGIC
        if sensor_data['distance'] > THRESHOLDS['distance_max']:
            session_state = "paused"
            alerts.append("USER ABSENT: SESSION AUTO-PAUSED.")
            
        # 4. LIGHT INTENSITY LOGIC
        if sensor_data['light'] >= THRESHOLDS['light_high']:
            # Highly lit environment -> Turn lamp completely off
            appliances['lamp_brightness'] = 0
        elif sensor_data['light'] < THRESHOLDS['light_low']:
            # Dim environment -> Max brightness
            appliances['lamp_brightness'] = 100
        else:
            # Moderate lighting (between 300 and 700) -> 50% brightness
            appliances['lamp_brightness'] = 50

    elif session_state == "paused" and sensor_data['distance'] <= THRESHOLDS['distance_max']:
        if sensor_data['temperature'] <= THRESHOLDS['temp_high'] and sensor_data['aqi'] <= THRESHOLDS['aqi_high']:
            session_state = "running"
            alerts.append("USER DETECTED & CONDITIONS SAFE: SESSION RESUMED.")
    # Force all hardware off if the session is not actively running
    if session_state != "running":
        appliances['ac'] = False
        appliances['fan'] = False
        appliances['airPurifier'] = False
        appliances['lamp_brightness'] = 0

    payload = {"sensors": sensor_data, "state": session_state, "appliances": appliances, "alerts": alerts, "timers": time_remaining}
    socketio.emit('system_update', payload)
    return jsonify({"status": "Data ingested"}), 200

# --- POSTURE API ---
posture_data = { "neck_angle": 0, "torso_angle": 0, "status": "STANDBY", "bad_time": 0.0 }
posture_alert_triggered = False

@app.route('/posture', methods=['POST'])
def receive_posture():
    global session_state, posture_data, posture_alert_triggered
    incoming_data = request.json
    posture_data.update(incoming_data)
    alerts = []
    
    if session_state == "running":
        if posture_data['bad_time'] > THRESHOLDS['posture']:
            alerts.append("POSTURE WARNING: Please correct your posture!")
            posture_alert_triggered = True
        else:
            posture_alert_triggered = False

    socketio.emit('posture_update', {"posture": posture_data, "alerts": alerts, "is_triggered": posture_alert_triggered})
    return jsonify({"status": "Posture tracked"}), 200

# --- SESSION CONTROLS ---

@socketio.on('command')
def handle_command(cmd):
    global session_state, condition_start_times, current_session_start
    action = cmd['action']
    
    if action == 'start':
        session_state = "running"
        # Start the clock if we haven't already
        if current_session_start is None:
            current_session_start = datetime.now()
            
    elif action == 'stop':
        session_state = "stopped"
        # Stop the clock and save the session
        if current_session_start is not None:
            save_session(current_session_start, datetime.now())
            current_session_start = None # Reset
            
        condition_start_times = {"temp": None, "aqi": None}
        
    elif action == 'pause':
        session_state = "paused"
        
    print(f"SYSTEM OVERRIDE: Session {session_state.upper()}")

if __name__ == '__main__':
    print("MAIN SERVER ONLINE on Port 5000")
    socketio.run(app, port=5000, debug=True)