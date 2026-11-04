/**
 * @file multi_sensor_compensated.ino
 * @author Sina Mozaffari Rad
 * @brief Combined sensor sketch for BME680, BME280, ENS160, AHT21, and MQ-135.
 * @version 2.0
 * @date 2024-07-25
 *
 * @details This sketch reads data from multiple environmental sensors and uses the
 * BME280's readings to provide external temperature and humidity compensation
 * to the BME680's BSEC algorithm and the ENS160 sensor. This improves the
 * accuracy of the IAQ, eCO2, and TVOC calculations by accounting for the
* BME680's self-heating.
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

// --- Sensor Objects ---
Adafruit_AHTX0 aht;                     // AHT21 at 0x38
DFRobot_ENS160_I2C ENS160(&Wire, 0x53);  // ENS160 at 0x53
Bsec iaqSensor;                         // BSEC for BME680 at 0x77
Adafruit_BME280 bme280;                 // BME280 at 0x76 (our reference sensor)

// --- Constants ---
#define SEALEVELPRESSURE_HPA (1013.25) // Standard sea level pressure
#define GREEN_LED 12  // D6 (GPIO12)
#define YELLOW_LED 13 // D7 (GPIO13)
#define RED_LED 15    // D8 (GPIO15)
#define BUZZER_PIN 14 // D5 (GPIO14)
#define MQ135_PIN A0  // MQ-135 analog pin

// --- Helper function to check BSEC status ---
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

void setup() {
  Serial.begin(9600);
  Serial.println(F("Multi-Sensor Test with BME680 External Compensation"));

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

  // --- Initialize Sensors ---
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
  // We no longer need the BSEC's internal heat-compensated temp/hum,
  // as we provide our own more accurate values.
  bsec_virtual_sensor_t sensorList[7] = {
    BSEC_OUTPUT_IAQ,
    BSEC_OUTPUT_STATIC_IAQ,
    BSEC_OUTPUT_CO2_EQUIVALENT,
    BSEC_OUTPUT_BREATH_VOC_EQUIVALENT,
    BSEC_OUTPUT_RAW_TEMPERATURE, // We can still read its raw temp
    BSEC_OUTPUT_RAW_PRESSURE,
    BSEC_OUTPUT_RAW_GAS
  };

  iaqSensor.updateSubscription(sensorList, 7, BSEC_SAMPLE_RATE_LP);
  checkIaqSensorStatus();
  
  Serial.println(F("\n--- Sensor Setup Complete, Starting Loop ---"));
}

void loop() {
  // --- STEP 1: Read from our reference sensor (BME280) first ---
  float ambient_temp = bme280.readTemperature();
  float ambient_hum = bme280.readHumidity();

  // Check for valid readings from BME280 to avoid feeding bad data
  if (isnan(ambient_temp) || isnan(ambient_hum)) {
    Serial.println(F("Failed to read from BME280, skipping loop."));
    delay(1000);
    return;
  }

  // --- STEP 2: Provide the reference data to other sensors ---
  
  // Update ENS160 with the accurate ambient temperature and humidity
  ENS160.setTempAndHum(ambient_temp, ambient_hum);

  // --- STEP 3: Run the BME680 BSEC algorithm with compensation ---
  // The BSEC library's .run() function automatically uses the temperature
  // and humidity values from the BME680's own sensor for its calculations.
  // To compensate for self-heating, we can provide an offset.
  // We calculate the offset based on the difference between the BME680's last
  // reading and the BME280's current (more accurate) reading.
  // Note: iaqSensor.temperature holds the BME680's temperature from the *previous* loop.
  if (iaqSensor.temperature != 0) { // Avoid calculating offset on the first run
      float temp_offset = iaqSensor.temperature - ambient_temp;
      iaqSensor.setTemperatureOffset(temp_offset);
  }

  // Now, run the BSEC processing. It will internally apply the offset.
  if (iaqSensor.run()) {
    // --- Print BME680 Data ---
    Serial.print(F("BME680 IAQ: "));
    Serial.print(iaqSensor.iaq);
    Serial.print(F(" (Acc: ")); Serial.print(iaqSensor.iaqAccuracy); Serial.print(F(") - "));
    if (iaqSensor.iaq <= 50) Serial.println(F("Excellent"));
    else if (iaqSensor.iaq <= 100) Serial.println(F("Good"));
    else if (iaqSensor.iaq <= 150) Serial.println(F("Lightly polluted"));
    else if (iaqSensor.iaq <= 200) Serial.println(F("Moderately polluted"));
    else if (iaqSensor.iaq <= 250) Serial.println(F("Heavily polluted"));
    else if (iaqSensor.iaq <= 350) Serial.println(F("Severely polluted"));
    else Serial.println(F("Extremely polluted"));

    Serial.print(F("BME680 Static IAQ: ")); Serial.println(iaqSensor.staticIaq);
    Serial.print(F("BME680 eCO2: ")); Serial.print(iaqSensor.co2Equivalent); Serial.println(F(" ppm"));
    Serial.print(F("BME680 bVOC: ")); Serial.print(iaqSensor.breathVocEquivalent); Serial.println(F(" ppm"));
    Serial.print(F("BME680 Raw Temp: ")); Serial.print(iaqSensor.rawTemperature); Serial.println(F(" C (internal)"));
    Serial.print(F("BME680 Gas: ")); Serial.print(iaqSensor.gasResistance / 1000.0); Serial.println(F(" kOhms"));
    Serial.print(F("BME680 Pres: ")); Serial.print(iaqSensor.pressure / 100.0); Serial.println(F(" hPa"));
    Serial.print(F("BME680 Alt: ")); Serial.print(bme280.readAltitude(SEALEVELPRESSURE_HPA)); Serial.println(F(" m")); // Use BME280 for altitude
  } else {
    checkIaqSensorStatus();
  }

  // --- Print Data from Other Sensors for Comparison ---
  Serial.print(F("BME280 Temp: ")); Serial.print(ambient_temp); Serial.println(F(" C (Reference)"));
  Serial.print(F("BME280 Hum: ")); Serial.print(ambient_hum); Serial.println(F(" % (Reference)"));
  
  sensors_event_t humidity_event, temp_event;
  aht.getEvent(&humidity_event, &temp_event);
  Serial.print(F("AHT Temp: ")); Serial.print(temp_event.temperature); Serial.println(F(" C"));
  Serial.print(F("AHT Hum: ")); Serial.print(humidity_event.relative_humidity); Serial.println(F(" %"));

  // Read from ENS160 (now that it's compensated)
  Serial.print(F("ENS AQI: ")); Serial.println(ENS160.getAQI());
  Serial.print(F("ENS TVOC: ")); Serial.print(ENS160.getTVOC()); Serial.println(F(" ppb"));
  Serial.print(F("ENS eCO2: ")); Serial.print(ENS160.getECO2()); Serial.println(F(" ppm"));

  // MQ-135 raw value
  int mq_value = analogRead(MQ135_PIN);
  Serial.print(F("MQ-135: ")); Serial.println(mq_value);

  // --- LED and Buzzer Logic ---
  // Using ENS160's AQI for general air quality indication
  uint8_t aqi = ENS160.getAQI();
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER_PIN, HIGH); // Off

  if (aqi <= 2) { // Good or Excellent
    digitalWrite(GREEN_LED, HIGH);
  } else if (aqi <= 3) { // Moderate
    digitalWrite(YELLOW_LED, HIGH);
  } else { // Poor or Unhealthy
    digitalWrite(RED_LED, HIGH);
    // Optional: Sound buzzer for very poor air quality
    // if (aqi >= 5) {
    //   digitalWrite(BUZZER_PIN, LOW); // On
    // }
  }

  Serial.println(F("-----"));
  // BSEC LP (Low Power) mode requires a 3-second delay
  delay(3000);
}
