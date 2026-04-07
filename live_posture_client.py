import cv2
import time
import math as m
import mediapipe as mp
import requests
import threading

# Server URL
SERVER_URL = "http://127.0.0.1:5000/posture"

def findDistance(x1, y1, x2, y2):
    dist = m.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return dist

def findAngle(x1, y1, x2, y2):
    theta = m.acos((y2 - y1) * (-y1) / (m.sqrt(
        (x2 - x1) ** 2 + (y2 - y1) ** 2) * y1))
    degree = int(180 / m.pi) * theta
    return degree

# Function to send data to server without blocking the video feed
def send_to_server(payload):
    try:
        requests.post(SERVER_URL, json=payload, timeout=0.5)
    except requests.exceptions.RequestException:
        pass # Ignore errors if server is down so video doesn't freeze

good_frames = 0
bad_frames = 0

font = cv2.FONT_HERSHEY_SIMPLEX
blue = (255, 127, 0)
red = (50, 50, 255)
green = (127, 255, 0)
dark_blue = (127, 20, 0)
light_green = (127, 233, 100)
yellow = (0, 255, 255)
pink = (255, 0, 255)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

if __name__ == "__main__":
    # 0 accesses the default webcam. Change to 1 or 2 if using an external USB camera.
    cap = cv2.VideoCapture(0)

    # Set frame rate for calculations (since live feed doesn't have a static FPS property like a file)
    fps = 30 
    
    # Optional: Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Counter to limit API calls (send every 5 frames instead of every single frame)
    frame_counter = 0

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Failed to grab frame from camera.")
            break

        h, w = image.shape[:2]
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        keypoints = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if keypoints.pose_landmarks:
            lm = keypoints.pose_landmarks
            lmPose = mp_pose.PoseLandmark

            l_shldr_x = int(lm.landmark[lmPose.LEFT_SHOULDER].x * w)
            l_shldr_y = int(lm.landmark[lmPose.LEFT_SHOULDER].y * h)
            r_shldr_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
            r_shldr_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)
            l_ear_x = int(lm.landmark[lmPose.LEFT_EAR].x * w)
            l_ear_y = int(lm.landmark[lmPose.LEFT_EAR].y * h)
            l_hip_x = int(lm.landmark[lmPose.LEFT_HIP].x * w)
            l_hip_y = int(lm.landmark[lmPose.LEFT_HIP].y * h)

            offset = findDistance(l_shldr_x, l_shldr_y, r_shldr_x, r_shldr_y)

            if offset < 100:
                cv2.putText(image, str(int(offset)) + ' Aligned', (w - 150, 30), font, 0.9, green, 2)
            else:
                cv2.putText(image, str(int(offset)) + ' Not Aligned', (w - 150, 30), font, 0.9, red, 2)

            neck_inclination = findAngle(l_shldr_x, l_shldr_y, l_ear_x, l_ear_y)
            torso_inclination = findAngle(l_hip_x, l_hip_y, l_shldr_x, l_shldr_y)

            cv2.circle(image, (l_shldr_x, l_shldr_y), 7, yellow, -1)
            cv2.circle(image, (l_ear_x, l_ear_y), 7, yellow, -1)
            cv2.circle(image, (l_shldr_x, l_shldr_y - 100), 7, yellow, -1)
            cv2.circle(image, (r_shldr_x, r_shldr_y), 7, pink, -1)
            cv2.circle(image, (l_hip_x, l_hip_y), 7, yellow, -1)
            cv2.circle(image, (l_hip_x, l_hip_y - 100), 7, yellow, -1)

            angle_text_string = 'Neck : ' + str(int(neck_inclination)) + '  Torso : ' + str(int(torso_inclination))
            current_status = "Good"

            if neck_inclination < 40 and torso_inclination < 10:
                bad_frames = 0
                good_frames += 1
                current_status = "Good"
                color = light_green
                line_color = green
            else:
                good_frames = 0
                bad_frames += 1
                current_status = "Bad"
                color = red
                line_color = red

            cv2.putText(image, angle_text_string, (10, 30), font, 0.9, color, 2)
            cv2.putText(image, str(int(neck_inclination)), (l_shldr_x + 10, l_shldr_y), font, 0.9, color, 2)
            cv2.putText(image, str(int(torso_inclination)), (l_hip_x + 10, l_hip_y), font, 0.9, color, 2)

            cv2.line(image, (l_shldr_x, l_shldr_y), (l_ear_x, l_ear_y), line_color, 4)
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_shldr_x, l_shldr_y - 100), line_color, 4)
            cv2.line(image, (l_hip_x, l_hip_y), (l_shldr_x, l_shldr_y), line_color, 4)
            cv2.line(image, (l_hip_x, l_hip_y), (l_hip_x, l_hip_y - 100), line_color, 4)

            good_time = (1 / fps) * good_frames
            bad_time =  (1 / fps) * bad_frames

            if good_time > 0:
                cv2.putText(image, f'Good Posture Time: {round(good_time, 1)}s', (10, h - 20), font, 0.9, green, 2)
            else:
                cv2.putText(image, f'Bad Posture Time: {round(bad_time, 1)}s', (10, h - 20), font, 0.9, red, 2)

            # Send data to server every 5 frames to avoid network congestion
            frame_counter += 1
            if frame_counter % 5 == 0:
                payload = {
                    "neck_angle": int(neck_inclination),
                    "torso_angle": int(torso_inclination),
                    "status": current_status,
                    "good_time": round(good_time, 1),
                    "bad_time": round(bad_time, 1)
                }
                # Use threading so the network request doesn't drop the video framerate
                threading.Thread(target=send_to_server, args=(payload,), daemon=True).start()

        # Display the live feed
        cv2.imshow('MediaPipe Pose - Live Feed', image)
        
        # Press 'q' to quit
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()