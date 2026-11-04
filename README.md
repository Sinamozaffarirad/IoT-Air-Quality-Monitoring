# Multi-Sensor Indoor Air Quality Monitoring System (ESP8266 · MQTT · Node-RED · Streamlit)

**Internet of Things — Final Course Project, University of Kashan**
Author: **Sina Mozaffari Rad** (Student ID 40021160214)

An end-to-end IoT system covering the full hardware/software stack: an ESP8266 sensor node fusing five
environmental sensors over a shared I²C bus, an MQTT transport layer, a Node-RED backend for persistence,
alerting and cloud integration, and a Python analytics dashboard with short-term forecasting.

---

## System Architecture

```
┌──────────────────────── Sensor Node (NodeMCU ESP8266) ────────────────────────┐
│  BME680 (BSEC IAQ) ─┐                                                          │
│  BME280 (reference)─┤  I²C @100 kHz     sensor fusion &      change-detection  │
│  ENS160 (AQI/TVOC) ─┼───────────────►  cross-compensation ─► + JSON encoding ──┼──► MQTT publish
│  AHT21  (T/RH)     ─┘                                                          │   ESP8266/airquality/data
│  MQ-135 (analog A0) ───────────────►  ADC                                      │
│  Local actuation: Green/Yellow/Red LEDs + buzzer driven by AQI level           │
└────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────── Node-RED backend ─────────────────────────────────┐
│  mqtt-in ─► JSON parse ─► SQLite (sensor_data table)                           │
│                        ─► threshold rules ─► e-mail alerts (SMTP)              │
│                        ─► Blynk Cloud HTTP API (mobile dashboard + events)     │
└────────────────────────────────────────────────────────────────────────────────┘
                                         │ SQLite
                                         ▼
┌─────────────────────────── Streamlit analytics app ───────────────────────────┐
│  live gauges · historical trends · data explorer · regression forecasting ·    │
│  CSV / Excel export                                                            │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Hardware

| Component | Interface | Address / Pin | Role |
|-----------|-----------|---------------|------|
| NodeMCU ESP8266 | — | — | MCU + Wi-Fi |
| Bosch BME680 | I²C | 0x77 | Gas sensor; IAQ, static IAQ, CO₂-eq, breath-VOC via Bosch BSEC |
| Bosch BME280 | I²C | 0x76 | Reference temperature / humidity / pressure |
| ScioSense ENS160 | I²C | 0x53 | AQI (1–5), TVOC, eCO₂ |
| AHT21 | I²C | 0x38 | Secondary temperature / humidity |
| MQ-135 | Analog | A0 | Raw gas concentration |
| LEDs (G / Y / R) | GPIO | D6 / D7 / D8 | Air-quality level indicator |
| Active-low buzzer | GPIO | D5 | Audible alarm on poor air quality |

I²C bus: SDA = D2 (GPIO4), SCL = D1 (GPIO5).

## Engineering Highlights

- **Cross-sensor compensation.** The BME680 heater raises its own temperature reading; the firmware uses the
  BME280 as an ambient reference to compute a live temperature offset for the BSEC algorithm, and feeds the
  same reference T/RH into the ENS160 for its internal compensation — improving IAQ, eCO₂ and TVOC accuracy.
- **Bandwidth-aware telemetry.** Readings are published only when at least one quantity changes beyond a
  per-sensor threshold (e.g. ΔT ≥ 0.1 °C, ΔRH ≥ 1 %, ΔeCO₂ ≥ 5 ppm), with a 6 s minimum interval aligned to
  the BSEC low-power sampling period.
- **Robust data path.** NaN/Inf sanitisation of BSEC outputs before JSON serialisation, enlarged MQTT buffer,
  bounded reconnect with decoded PubSubClient error states.
- **Non-blocking actuation.** Buzzer timing is `millis()`-based and edge-triggered (fires once on entering the
  poor-AQI state) so the alarm never stalls the sensing loop.
- **Incremental bring-up.** Each sensor was validated in isolation before integration (see `sensor-tests/`),
  including MQ-135 R₀ calibration and ppm conversion.
- **Analytics.** The dashboard provides live gauges with health classifications, multi-tab trend charts,
  filtered data tables, scikit-learn regression forecasts of future readings, and data export.

## Repository Structure

```
firmware/AirQualityNode/   Final ESP8266 firmware (Arduino)
sensor-tests/              Per-sensor and integration bring-up sketches
  ├─ bme280test/           BME280 standalone test
  ├─ Rzero/                MQ-135 R0 calibration
  ├─ ppm/                  MQ-135 ppm conversion
  ├─ test3HW/              Three-sensor integration test
  └─ fulltest/             Full hardware integration test
node-red/flow.json         Node-RED flow (MQTT → SQLite, alerts, Blynk)
dashboard/app.py           Streamlit analytics & forecasting dashboard
data/sample_24h_readings.json   24 h of real recorded measurements (Sept 2025)
docs/                      Project report (PDF)
```

## Getting Started

### 1. Firmware
Arduino IDE with the ESP8266 core and libraries: `Adafruit AHTX0`, `Adafruit BME280`, `Adafruit Unified Sensor`,
`DFRobot_ENS160`, `BSEC Software Library` (Bosch), `PubSubClient`, `ArduinoJson`.
Set `ssid` / `password` in `firmware/AirQualityNode/AirQualityNode.ino`, then flash.

### 2. Node-RED
Install `node-red-node-sqlite` and `node-red-node-email`, import `node-red/flow.json`, and set your
Blynk auth token and alert e-mail address in the function nodes. The flow creates `sensor_data.db` automatically.

### 3. Dashboard
```bash
cd dashboard
pip install -r requirements.txt
SENSOR_DB_PATH=/path/to/sensor_data.db streamlit run app.py
```

## MQTT Payload

```json
{
  "temperature": 32.3, "humidity": 41.9, "pressure": 863.8,
  "mq135_value": 447,
  "iaq": 72.95, "static_iaq": 74.26, "co2_equivalent": 742.61, "breath_voc": 0.87,
  "temp_aht": 33.1, "hum_aht": 44.8,
  "aqi_ens": 2, "tvoc_ens": 126, "eco2_ens": 591
}
```

## Tech Stack
C++ / Arduino · ESP8266 · I²C · ADC · MQTT · Node-RED · SQLite · Blynk Cloud · SMTP · Python · Streamlit ·
Pandas · Plotly · scikit-learn
