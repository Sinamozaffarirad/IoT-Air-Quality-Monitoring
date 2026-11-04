#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

Adafruit_BME280 bme; // Create BME280 object using I2C

#define SEALEVELPRESSURE_HPA (1013.25) // Standard sea level pressure for altitude calculation (optional)

void setup() {
  Serial.begin(9600);
  Serial.println("BME280 Sensor Test + MQ-135 Sensor Test");

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

    int sensorValue = analogRead(A0);
    Serial.print("Air Quality Value: ");
    Serial.println(sensorValue);
    
    // Read and print temperature
    Serial.print("Temperature: ");
    Serial.print(bme.readTemperature());
    Serial.println(" °C");

    // Read and print humidity
    Serial.print("Humidity: ");
    Serial.print(bme.readHumidity());
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
  }

  delay(2000); // Wait 2 seconds before next attempt
}