#include <MQ135.h>

MQ135 mq135(A0); // Analog pin A0 on NodeMCU

void setup() {
  Serial.begin(9600);
  Serial.println("MQ-135 RZero Calibration");
}

void loop() {
  float rzero = mq135.getRZero();
  Serial.print("RZero: ");
  Serial.println(rzero);
  delay(1000); // Read every second
}