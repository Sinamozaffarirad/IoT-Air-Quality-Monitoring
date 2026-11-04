#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MQ135.h>

Adafruit_BME280 bme; // Create BME280 object using I2C
MQ135 mq135(A0, 20.0, 10.0); // RLOAD 10.0 kΩ
#define SEALEVELPRESSURE_HPA (1013.25) // Standard sea level pressure for altitude calculation (optional)
#define BUZZER_PIN 14 // D5 on ESP8266 is GPIO14
#define GREEN_LED 12 // D6 on ESP8266 is GPIO12
#define YELLOW_LED 13 // D7 on ESP8266 is GPIO13
#define RED_LED 15 // D8 on ESP8266 is GPIO15
#define GOOD_AIR_THRESHOLD 1000 // Threshold for good air quality (green LED)
#define MODERATE_AIR_THRESHOLD 2000 // Threshold for moderate (yellow) to poor (red) air quality

void setup() {
  Serial.begin(9600);
  Serial.println("BME280 Sensor Test + MQ-135 Sensor Test + Buzzer Alert + LED Indicators");

  // Initialize buzzer, LEDs, and DO pin
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  
  digitalWrite(BUZZER_PIN, LOW); // Ensure buzzer is off initially
  digitalWrite(GREEN_LED, LOW); // Ensure LEDs are off initially
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);

  // Initialize I2C with custom pins: SDA on D2 (GPIO4), SCL on D1 (GPIO5)
  Wire.begin(4, 5); // SDA pin first, then SCL pin

  // Attempt to initialize the sensor (try 0x76 or 0x77)
  if (!bme.begin(0x76)) {  // Change to 0x77 if this fails
    Serial.println("Could not find a valid BME280 sensor, check wiring and I2C address!");
    // Instead of halting, just delay and retry in loop if needed
  } else {
    Serial.println("Sensor initialized successfully.");
  }
}

void loop() {
  if (bme.begin(0x76)) {  // Re-check in loop if initial fail
    float temperature = bme.readTemperature();
    float humidity = bme.readHumidity();
    int sensorValue = analogRead(A0);
    Serial.print("Raw Value: ");
    Serial.println(sensorValue);
    float ppm = mq135.getCorrectedPPM(temperature, humidity);
    Serial.print("CO2 PPM: ");
    Serial.println(ppm);
    Serial.print("RZero value: ");
    Serial.println(mq135.getRZero());

    // Turn off all LEDs and buzzer initially
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(RED_LED, LOW);
    digitalWrite(BUZZER_PIN, HIGH);
    
    // Activate LEDs and buzzer based on air quality reading
    if (ppm < GOOD_AIR_THRESHOLD) {
      digitalWrite(GREEN_LED, HIGH);
      Serial.println("Air Quality: Good (Green LED ON)");
    } else if (ppm < MODERATE_AIR_THRESHOLD) {
      digitalWrite(YELLOW_LED, HIGH);
      Serial.println("Air Quality: Moderate (Yellow LED ON)");
    } else {
      digitalWrite(RED_LED, HIGH);
      digitalWrite(BUZZER_PIN, LOW);
      Serial.println("Air Quality: Poor (Red LED ON, Buzzer ON)");
    }
    
    // Read and print temperature
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" °C");

    // Read and print humidity
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");

    // Read and print pressure
    Serial.print("Pressure: ");
    Serial.print(bme.readPressure() / 100.0F);
    Serial.println(" hPa");

    // Optional: Approximate altitude based on pressure
    Serial.print("Approx. Altitude: ");
    Serial.print(bme.readAltitude(SEALEVELPRESSURE_HPA));
    Serial.println(" m");

    Serial.println("---------------------");
  } else {
    Serial.println("Sensor not detected - retrying...");
    digitalWrite(BUZZER_PIN, HIGH); // Ensure buzzer is off if sensor not detected
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(RED_LED, LOW);
  }

  delay(2000); // Wait 2 seconds before next attempt
}