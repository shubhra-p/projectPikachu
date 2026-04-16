#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- NETWORK CONFIGURATION ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// CRITICAL: Change this to your computer's actual IPv4 address!
const char* serverName = "http://host.wokwi.internal:5000/ingest"; 

// --- PIN DEFINITIONS ---
const int TEMP_PIN = 34;   
const int HUM_PIN = 35;    
const int AQI_PIN = 32;    
const int LIGHT_PIN = 33;  

// Distance Sensor (Moved to safe pins!)
const int TRIG_PIN = 19; 
const int ECHO_PIN = 18;

unsigned long lastTime = 0;
unsigned long timerDelay = 500; 

void setup() {
  Serial.begin(115200);
  
  // Add a small delay to let power stabilize before booting
  delay(1000); 
  Serial.println("\n--- ESP32 Booting ---");

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[SUCCESS] Connected to WiFi!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());
}

float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // Added 30ms timeout to prevent hanging
  if (duration == 0) return 0; // Prevent math errors if sensor drops out
  
  float distanceCm = duration * 0.034 / 2;
  return distanceCm;
}

void loop() {
  if ((millis() - lastTime) > timerDelay) {
    
    int rawTemp = analogRead(TEMP_PIN);
    int rawHum = analogRead(HUM_PIN);
    int rawAqi = analogRead(AQI_PIN);
    int rawLight = analogRead(LIGHT_PIN);

    float tempValue = map(rawTemp, 0, 4095, 10, 45);   
    float humValue = map(rawHum, 0, 4095, 0, 100);     
    float aqiValue = map(rawAqi, 0, 4095, 0, 500);     
    float lightValue = map(rawLight, 0, 4095, 0, 1000);
    float distValue = readDistance();                  

    // Updated syntax for ArduinoJson v7
    JsonDocument doc;
    doc["temperature"] = tempValue;
    doc["humidity"] = humValue;
    doc["aqi"] = aqiValue;
    doc["distance"] = distValue;
    doc["light"] = lightValue;

    String jsonString;
    serializeJson(doc, jsonString);

    if(WiFi.status() == WL_CONNECTED){
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");
      
      int httpResponseCode = http.POST(jsonString);
      
      Serial.print("Transmitting Payload... Server Response: ");
      Serial.println(httpResponseCode);
      
      http.end();
    }
    else {
      Serial.println("[ERROR] WiFi Disconnected");
    }
    lastTime = millis();
  }
}