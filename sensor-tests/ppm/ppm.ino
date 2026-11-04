#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MQ135.h>

#undef ATMOCO2
#define ATMOCO2 427.0

Adafruit_BME280 bme;
MQ135 mq135(A0, 17.0);  // RLOAD 17.0 kΩ

#define SEALEVELPRESSURE_HPA (1013.25)

void setup() {
  Serial.begin(9600);
  Wire.begin(4, 5);
  if (!bme.begin(0x76)) Serial.println("BME280 not found!");
  else Serial.println("Sensors initialized.");
}

void loop() {
  int raw = analogRead(A0);
  float temperature = bme.readTemperature();
  float humidity = bme.readHumidity();
  float ppm = mq135.getCorrectedPPM(temperature, humidity);

  Serial.print("Raw Value: ");
  Serial.print(raw);
  Serial.print(" | CO2 PPM: ");
  Serial.println(ppm);
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" °C");
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");
  Serial.println("---------------------");
  delay(1000); // Log every second for real-time tracking
}