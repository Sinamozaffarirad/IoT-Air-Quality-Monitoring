/**
 * @file AirQualityNode.ino
 * @author Sina Mozaffari Rad
 * @brief Combined sensors sketch for BME680, BME280, ENS160, AHT21, and MQ-135.
 * @version 3.0
 * @date 2025-09-07
 *
 * @details This sketch reads data from multiple environmental sensors and uses the
 * BME280's readings to provide external temperature and humidity compensation
 * to the BME680's BSEC algorithm and the ENS160 sensor. This improves the
 * accuracy of the IAQ, eCO2, and TVOC calculations by accounting for the
 * BME680's self-heating. Data is published via MQTT to Node-RED.
 *
 * Connections (NodeMCU ESP8266):
 * - I2C SDA: D2 (GPIO4)
 * - I2C SCL: D1 (GPIO5)
 * - BME680: I2C Address 0x77
 * - BME280: I2C Address 0x76
 * - ENS160: I2C Address 0x53
 * - AHT21:  I2C Address 0x38
 * - MQ135:  Analog Pin A0
 * - Green LED:  D6 (GPIO12)
 * - Yellow LED: D7 (GPIO13)
 * - Red LED:    D8 (GPIO15)
 * - Buzzer:     D5 (GPIO14)
 */

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_AHTX0.h>
#include <DFRobot_ENS160.h>
#include <bsec.h>              // Bosch BSEC library for BME680
#include <Adafruit_BME280.h>   // For BME280
#include <ESP8266WiFi.h>
#define MQTT_MAX_PACKET_SIZE 1024  // Increase MQTT buffer size
#include <PubSubClient.h>
#include <ArduinoJson.h>


// WiFi and MQTT Configuration 
const char* ssid = "YOUR_WIFI_SSID";          
const char* password = "YOUR_WIFI_PASSWORD";  
const char* mqtt_server = "test.mosquitto.org";  // More reliable broker
const char* mqtt_topic = "ESP8266/airquality/data";
const char* client_id = "ESP8266_AirQuality";

WiFiClient espClient;
PubSubClient client(espClient);

// Sensor Objects 
Adafruit_AHTX0 aht;                     // AHT21 at 0x38
DFRobot_ENS160_I2C ENS160(&Wire, 0x53);  // ENS160 at 0x53
Bsec iaqSensor;                         // BSEC for BME680 at 0x77
Adafruit_BME280 bme280;                 // BME280 at 0x76 

// Constants 
#define SEALEVELPRESSURE_HPA (1013.25) // Standard sea level pressure
#define GREEN_LED 12  // D6 (GPIO12)
#define YELLOW_LED 13 // D7 (GPIO13)
#define RED_LED 15    // D8 (GPIO15)
#define BUZZER_PIN 14 // D5 (GPIO14)
#define MQ135_PIN A0  // MQ-135 analog pin
int Buzzercounter = 0;
int mqttCounter = 0;  // Counter for MQTT timing (send every 6 seconds)
unsigned long buzzerStartTime = 0;  // Buzzer timing for non-blocking control
bool buzzerActive = false;  // Track if buzzer is currently active
unsigned long messageId = 0;  // Unique message ID for tracking

// Variables for change detection
struct SensorData {
  float temperature = -999;
  float humidity = -999;
  float pressure = -999;
  int mq135_value = -999;
  float iaq = -999;
  float static_iaq = -999;
  float co2_equivalent = -999;
  float breath_voc = -999;
  float temp_aht = -999;
  float hum_aht = -999;
  uint8_t aqi_ens = 255;
  uint16_t tvoc_ens = 65535;
  uint16_t eco2_ens = 65535;
};

SensorData previousValues;
SensorData currentValues;

// Thresholds for change detection (adjust as needed)
const float TEMP_THRESHOLD = 0.1;      // 0.1°C
const float HUM_THRESHOLD = 1.0;       // 1% RH
const float PRESSURE_THRESHOLD = 2.0;  // 2 hPa
const int MQ135_THRESHOLD = 10;        // 10 units
const float IAQ_THRESHOLD = 5.0;       // 5 IAQ units
const float CO2_THRESHOLD = 5.0;      // 5 ppm
const float VOC_THRESHOLD = 0.1;       // 0.1 ppm
const uint8_t AQI_THRESHOLD = 1;       // 1 AQI unit
const uint16_t TVOC_THRESHOLD = 10;    // 10 ppb
const uint16_t ECO2_THRESHOLD = 5;    // 5 ppm

// Function to check if sensor data has changed significantly
bool hasDataChanged() {
  bool changed = false;
  
  if (abs(currentValues.temperature - previousValues.temperature) >= TEMP_THRESHOLD) {
    Serial.println(F("Temperature changed"));
    changed = true;
  }
  if (abs(currentValues.humidity - previousValues.humidity) >= HUM_THRESHOLD) {
    Serial.println(F("Humidity changed"));
    changed = true;
  }
  if (abs(currentValues.pressure - previousValues.pressure) >= PRESSURE_THRESHOLD) {
    Serial.println(F("Pressure changed"));
    changed = true;
  }
  if (abs(currentValues.mq135_value - previousValues.mq135_value) >= MQ135_THRESHOLD) {
    Serial.println(F("MQ135 changed"));
    changed = true;
  }
  if (abs(currentValues.iaq - previousValues.iaq) >= IAQ_THRESHOLD) {
    Serial.println(F("IAQ changed"));
    changed = true;
  }
  if (abs(currentValues.static_iaq - previousValues.static_iaq) >= IAQ_THRESHOLD) {
    Serial.println(F("Static IAQ changed"));
    changed = true;
  }
  if (abs(currentValues.co2_equivalent - previousValues.co2_equivalent) >= CO2_THRESHOLD) {
    Serial.println(F("CO2 changed"));
    changed = true;
  }
  if (abs(currentValues.breath_voc - previousValues.breath_voc) >= VOC_THRESHOLD) {
    Serial.println(F("VOC changed"));
    changed = true;
  }
  if (abs(currentValues.temp_aht - previousValues.temp_aht) >= TEMP_THRESHOLD) {
    Serial.println(F("AHT Temperature changed"));
    changed = true;
  }
  if (abs(currentValues.hum_aht - previousValues.hum_aht) >= HUM_THRESHOLD) {
    Serial.println(F("AHT Humidity changed"));
    changed = true;
  }
  if (abs(currentValues.aqi_ens - previousValues.aqi_ens) >= AQI_THRESHOLD) {
    Serial.println(F("AQI changed"));
    changed = true;
  }
  if (abs(currentValues.tvoc_ens - previousValues.tvoc_ens) >= TVOC_THRESHOLD) {
    Serial.println(F("TVOC changed"));
    changed = true;
  }
  if (abs(currentValues.eco2_ens - previousValues.eco2_ens) >= ECO2_THRESHOLD) {
    Serial.println(F("eCO2 changed"));
    changed = true;
  }
  
  return changed;
}

// Function to copy current values to previous values
void updatePreviousValues() {
  previousValues = currentValues;
}

// Helper function to check BSEC status 
void checkIaqSensorStatus(void) {
  if (iaqSensor.bme68xStatus < BME68X_OK) {
    Serial.print(F("BME68x error: "));
    Serial.println(iaqSensor.bme68xStatus);
  } else if (iaqSensor.bme68xStatus > BME68X_OK) {
    Serial.print(F("BME68x warning: "));
    Serial.println(iaqSensor.bme68xStatus);
  }

  if (iaqSensor.bsecStatus < BSEC_OK) {
    Serial.print(F("BSEC error: "));
    Serial.println(iaqSensor.bsecStatus);
  } else if (iaqSensor.bsecStatus > BSEC_OK) {
    Serial.print(F("BSEC warning: "));
    Serial.println(iaqSensor.bsecStatus);
  }
}

// MQTT Reconnect Function 
void reconnect() {
  int attempts = 0;
  while (!client.connected() && attempts < 3) {
    Serial.print(F("Attempting MQTT connection... "));
    Serial.print(F("Attempt "));
    Serial.print(attempts + 1);
    Serial.print(F("/3"));
    
    if (client.connect(client_id)) {
      Serial.println(F(" - SUCCESS!"));
      Serial.print(F("[MQTT] Connected to broker: "));
      Serial.println(mqtt_server);
    } else {
      Serial.print(F(" - FAILED! Error code: "));
      Serial.print(client.state());
      Serial.print(F(" ("));
      
      // Decode MQTT error states
      switch(client.state()) {
        case -4: Serial.print(F("TIMEOUT")); break;
        case -3: Serial.print(F("CONNECTION_LOST")); break;
        case -2: Serial.print(F("CONNECT_FAILED")); break;
        case -1: Serial.print(F("DISCONNECTED")); break;
        case 1: Serial.print(F("BAD_PROTOCOL")); break;
        case 2: Serial.print(F("BAD_CLIENT_ID")); break;
        case 3: Serial.print(F("UNAVAILABLE")); break;
        case 4: Serial.print(F("BAD_CREDENTIALS")); break;
        case 5: Serial.print(F("UNAUTHORIZED")); break;
        default: Serial.print(F("UNKNOWN"));
      }
      Serial.println(F(")"));
      
      attempts++;
      if (attempts < 3) {
        Serial.println(F("Retrying in 2 seconds..."));
        delay(2000);
      }
    }
  }
  
  if (!client.connected()) {
    Serial.println(F("[ERROR] Failed to connect to MQTT after 3 attempts"));
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println(F("Multi-Sensor Code with BME680 External Compensation"));

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // MQTT Setup
  client.setServer(mqtt_server, 1883);

  // Initialize I2C with custom pins: SDA on D2 (GPIO4), SCL on D1 (GPIO5)
  Wire.begin(4, 5);
  Wire.setClock(100000); // 100kHz for stability

  // Initialize LEDs and Buzzer
  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER_PIN, HIGH); // Buzzer off (active low)

  // Initialize Sensors 
  // BME280 (our reference sensor)
  if (!bme280.begin(0x76)) {
    Serial.println(F("BME280 not found!"));
  } else {
    Serial.println(F("BME280 OK - Using for compensation"));
  }

  // AHT21
  if (!aht.begin()) {
    Serial.println(F("AHT21 not found!"));
  } else {
    Serial.println(F("AHT21 OK"));
  }
  
  // ENS160
  while (NO_ERR != ENS160.begin()) {
    Serial.println(F("ENS160 failed, retrying..."));
    delay(1000);
  }
  Serial.println(F("ENS160 OK"));
  ENS160.setPWRMode(ENS160_STANDARD_MODE);
  // We will provide real-time compensation in the loop

  // BME680 with BSEC
  iaqSensor.begin(BME68X_I2C_ADDR_HIGH, Wire);
  Serial.print(F("BSEC version "));
  Serial.print(iaqSensor.version.major); Serial.print(F("."));
  Serial.print(iaqSensor.version.minor); Serial.print(F("."));
  Serial.print(iaqSensor.version.major_bugfix); Serial.print(F("."));
  Serial.println(iaqSensor.version.minor_bugfix);
  checkIaqSensorStatus();

  // Subscribe to the BSEC outputs we want
  bsec_virtual_sensor_t sensorList[7] = {
    BSEC_OUTPUT_IAQ,
    BSEC_OUTPUT_STATIC_IAQ,
    BSEC_OUTPUT_CO2_EQUIVALENT,
    BSEC_OUTPUT_BREATH_VOC_EQUIVALENT,
    BSEC_OUTPUT_RAW_TEMPERATURE,
    BSEC_OUTPUT_RAW_PRESSURE,
    BSEC_OUTPUT_RAW_GAS
  };

  iaqSensor.updateSubscription(sensorList, 7, BSEC_SAMPLE_RATE_LP);
  checkIaqSensorStatus();
  
  Serial.println(F("\n--- Sensor Setup Complete, Starting Loop ---"));
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Handle non-blocking buzzer timing
  if (buzzerActive && (millis() - buzzerStartTime >= 2000)) {
    digitalWrite(BUZZER_PIN, HIGH); // Turn buzzer off after 2 seconds
    buzzerActive = false;
  }

  // STEP 1: Read from our reference sensor (BME280)
  float ambient_temp = bme280.readTemperature();
  float ambient_hum = bme280.readHumidity();
  float pressure = bme280.readPressure() / 100.0F; 

  // Check for valid readings from BME280
  if (isnan(ambient_temp) || isnan(ambient_hum)) {
    Serial.println(F("Failed to read from BME280, skipping loop."));
    delay(3000);
    return;
  }

  // STEP 2: Provide the reference data to other sensors 
  ENS160.setTempAndHum(ambient_temp, ambient_hum);

  // STEP 3: Run the BME680 BSEC algorithm with compensation 
  if (iaqSensor.temperature != 0) {
    float temp_offset = iaqSensor.temperature - ambient_temp;
    iaqSensor.setTemperatureOffset(temp_offset);
  }

  if (iaqSensor.run()) {
    
    // Increment MQTT counter
    mqttCounter++;
    
    // Only check for changes and potentially send MQTT every 6 seconds (every 2 cycles)
    if (mqttCounter >= 2) {
      mqttCounter = 0;  // Reset counter
      
      // Get fresh sensor data at transmission check time
      sensors_event_t humidity_event, temp_event;
      aht.getEvent(&humidity_event, &temp_event);
      int mq_value = analogRead(MQ135_PIN);
      
      // Get fresh ENS160 readings
      uint8_t fresh_aqi = ENS160.getAQI();
      uint16_t fresh_tvoc = ENS160.getTVOC();
      uint16_t fresh_eco2 = ENS160.getECO2();

      // Update current sensor values with sanitized data
      currentValues.temperature = round(ambient_temp * 10) / 10.0;
      currentValues.humidity = round(ambient_hum * 10) / 10.0;
      currentValues.pressure = round(pressure * 10) / 10.0;
      currentValues.mq135_value = mq_value;
      
      // Validate and sanitize BSEC values
      currentValues.iaq = (isnan(iaqSensor.iaq) || isinf(iaqSensor.iaq)) ? 50.0 : round(iaqSensor.iaq * 100) / 100.0;
      currentValues.static_iaq = (isnan(iaqSensor.staticIaq) || isinf(iaqSensor.staticIaq)) ? 50.0 : round(iaqSensor.staticIaq * 100) / 100.0;
      currentValues.co2_equivalent = (isnan(iaqSensor.co2Equivalent) || isinf(iaqSensor.co2Equivalent)) ? 600.0 : round(iaqSensor.co2Equivalent * 100) / 100.0;
      currentValues.breath_voc = (isnan(iaqSensor.breathVocEquivalent) || isinf(iaqSensor.breathVocEquivalent)) ? 0.5 : round(iaqSensor.breathVocEquivalent * 100) / 100.0;
      
      currentValues.temp_aht = round(temp_event.temperature * 10) / 10.0;
      currentValues.hum_aht = round(humidity_event.relative_humidity * 10) / 10.0;
      currentValues.aqi_ens = fresh_aqi;
      currentValues.tvoc_ens = fresh_tvoc;
      currentValues.eco2_ens = fresh_eco2;

      // Check if data has changed significantly or if this is the first run
      if (hasDataChanged() || previousValues.temperature == -999) {
        Serial.println(F("Data changed - sending MQTT"));
        
        // Create JSON document with current values
        StaticJsonDocument<768> doc;
        messageId++;  // Increment message ID
        
        doc["temperature"] = currentValues.temperature;
        doc["humidity"] = currentValues.humidity;
        doc["pressure"] = currentValues.pressure;
        doc["mq135_value"] = currentValues.mq135_value;
        doc["iaq"] = currentValues.iaq;
        doc["static_iaq"] = currentValues.static_iaq;
        doc["co2_equivalent"] = currentValues.co2_equivalent;
        doc["breath_voc"] = currentValues.breath_voc;
        doc["temp_aht"] = currentValues.temp_aht;
        doc["hum_aht"] = currentValues.hum_aht;
        doc["aqi_ens"] = currentValues.aqi_ens;
        doc["tvoc_ens"] = currentValues.tvoc_ens;
        doc["eco2_ens"] = currentValues.eco2_ens;

        // Serialize the document into a string
        String payload;
        size_t jsonSize = serializeJson(doc, payload);

        // Check if serialization was successful
        if (jsonSize == 0) {
          Serial.println(F("[ERROR] JSON serialization failed!"));
          return;
        }
        
        // Publish payload
        bool published = client.publish(mqtt_topic, payload.c_str(), false);
        
        // Status output
        Serial.print(F("MQTT: "));
        Serial.println(published ? F("SENT") : F("FAILED"));
        Serial.println(payload);
        
        // Update previous values after successful transmission
        updatePreviousValues();
      } else {
        Serial.println(F("No significant change - skipping MQTT"));
      }
    }
  } else {
    checkIaqSensorStatus();
  }

  // LED and Buzzer Logic 
  uint8_t aqi = ENS160.getAQI();
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);

  if (aqi <= 2) {
    Buzzercounter = 0;
    digitalWrite(GREEN_LED, HIGH);
    // Turn off buzzer if it was active
    if (buzzerActive) {
      digitalWrite(BUZZER_PIN, HIGH);
      buzzerActive = false;
    }
  } else if (aqi <= 3) {
    Buzzercounter = 0;
    digitalWrite(YELLOW_LED, HIGH);
    // Turn off buzzer if it was active
    if (buzzerActive) {
      digitalWrite(BUZZER_PIN, HIGH);
      buzzerActive = false;
    }
  } else {
    digitalWrite(RED_LED, HIGH);
    // Only activate buzzer on first entry into poor AQI condition
    if (Buzzercounter == 0) {
      digitalWrite(BUZZER_PIN, LOW); // Turn buzzer on
      buzzerStartTime = millis(); // Start timing
      buzzerActive = true;
    }
    Buzzercounter = 1; // Mark that we're in poor AQI state
  }

  Serial.println(F("-----"));
  // BSEC LP (Low Power) mode requires consistent 3-second delay for proper calibration
  delay(3000); 
}