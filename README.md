<div align="center">

# Multi-Sensor Indoor Air Quality Monitoring System

**ESP8266 · Sensor Fusion · MQTT · Node-RED · SQLite · Streamlit**

*Internet of Things — Final Course Project, University of Kashan*
**Sina Mozaffari Rad** · Student ID 40021160214

![ESP8266](https://img.shields.io/badge/MCU-ESP8266-2f81f7?style=flat-square&logo=espressif&logoColor=white)
![Arduino](https://img.shields.io/badge/Firmware-C%2B%2B%20%2F%20Arduino-00979D?style=flat-square&logo=arduino&logoColor=white)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-660066?style=flat-square&logo=mqtt&logoColor=white)
![Node-RED](https://img.shields.io/badge/Backend-Node--RED-8F0000?style=flat-square&logo=nodered&logoColor=white)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Python](https://img.shields.io/badge/Dashboard-Python%20%2F%20Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

</div>

---

## Overview

A complete hardware/software co-designed IoT system for indoor air-quality monitoring. Five heterogeneous
environmental sensors share one I²C bus and one ADC on a resource-constrained ESP8266. The firmware
cross-compensates the sensors against a reference, filters redundant data at the edge, and acts on the result
locally with LEDs and a buzzer. Telemetry travels over MQTT to a Node-RED backend that stores it, raises alerts
and mirrors it to a mobile cloud dashboard. A Python analytics application then visualises and forecasts the data.

The project covers every layer of an embedded IoT product: **sensor interfacing → embedded firmware → network
protocol → server-side data flow → storage → analytics UI.**

<p align="center"><img src="docs/figures/architecture.png" width="100%" alt="System architecture"></p>

---

## 1 · Hardware Layer

<p align="center"><img src="docs/figures/wiring.png" width="85%" alt="Wiring diagram"></p>

| Component | Interface | Address / Pin | Measured quantities |
|-----------|-----------|---------------|---------------------|
| **NodeMCU ESP8266** | — | — | 80 MHz MCU, 802.11 b/g/n Wi-Fi |
| **Bosch BME680** | I²C | `0x77` | Gas resistance → IAQ, static IAQ, CO₂-equivalent, breath-VOC (Bosch BSEC) |
| **Bosch BME280** | I²C | `0x76` | Reference temperature, humidity, pressure |
| **ScioSense ENS160** | I²C | `0x53` | Metal-oxide AQI (1–5), TVOC, eCO₂ |
| **AHT21** | I²C | `0x38` | Secondary temperature / humidity |
| **MQ-135** | Analog | `A0` | Raw gas concentration (10-bit ADC) |
| **Green / Yellow / Red LED** | GPIO | `D6 / D7 / D8` | Local air-quality indicator |
| **Active-low buzzer** | GPIO | `D5` | Audible alarm |

Four sensors are multiplexed by address on a single I²C bus (SDA `D2`, SCL `D1`) clocked at 100 kHz for
signal integrity over jumper wiring. The MQ-135 was characterised separately: its sensing resistance R₀ was
calibrated in clean air (`sensor-tests/Rzero`) and a ppm conversion curve was applied (`sensor-tests/ppm`).

---

## 2 · Embedded Firmware Layer

<p align="center"><img src="docs/figures/firmware_flow.png" width="70%" alt="Firmware main loop"></p>

**Cross-sensor compensation.** The BME680 heats its gas plate, which biases its own temperature reading and
therefore the humidity compensation inside BSEC. On every cycle the firmware computes the offset
`T_BME680 − T_BME280` and feeds it to BSEC through `setTemperatureOffset()`. The same BME280 reference
T/RH is written into the ENS160 with `setTempAndHum()`, so both gas sensors work from a common, unbiased
ambient reference.

**Edge-side data reduction.** Each of the 13 channels has its own change threshold:

| Channel | Threshold | Channel | Threshold |
|---------|-----------|---------|-----------|
| Temperature | 0.1 °C | IAQ / static IAQ | 5 |
| Humidity | 1 % RH | CO₂-equivalent | 5 ppm |
| Pressure | 2 hPa | ENS160 eCO₂ | 5 ppm |
| MQ-135 | 10 ADC counts | ENS160 TVOC | 10 ppb |
| ENS160 AQI | 1 level | Breath-VOC | 0.1 ppm |

A packet is published only when at least one channel crosses its threshold. The sampling interval is at least
6 s, set by the BSEC low-power (LP) sampling period. This keeps the network quiet when the room is stable and
still catches events at full resolution.

**Reliability.** BSEC outputs are checked for NaN/Inf before JSON serialisation so a bad value cannot produce
an invalid payload. The MQTT buffer is enlarged to 1 KB for the 13-field message. Reconnection is limited to
three attempts, and every `PubSubClient` error state is decoded to readable text on the serial console.

**Non-blocking local actuation.** The ENS160 AQI selects the LED colour. The buzzer is triggered on the rising
edge into the *poor* state and timed with `millis()`, so the 2 s alarm never stalls the sensing loop.

---

## 3 · Communication Layer — MQTT

The node publishes compact JSON to the topic `ESP8266/airquality/data` (QoS 0) through a public broker:

```json
{
  "temperature": 32.3, "humidity": 41.9, "pressure": 863.8,
  "mq135_value": 447,
  "iaq": 72.95, "static_iaq": 74.26, "co2_equivalent": 742.61, "breath_voc": 0.87,
  "temp_aht": 33.1, "hum_aht": 44.8,
  "aqi_ens": 2, "tvoc_ens": 126, "eco2_ens": 591
}
```

The publish/subscribe model decouples the sensor node from its consumers. Storage, alerting and the cloud
dashboard each subscribe on their own, with no change to the firmware.

---

## 4 · Backend Layer — Node-RED

The flow in [`node-red/flow.json`](node-red/flow.json) does four jobs:

1. **Ingest:** `mqtt-in` subscribes to the topic and parses the JSON.
2. **Persist:** each message is inserted into an SQLite `sensor_data` table with a local timestamp.
3. **Alert:** rules (ENS160 AQI ≥ 4, eCO₂ ≥ 1000 ppm, MQ-135 ≥ 990) send e-mail notifications over SMTP/TLS.
4. **Mirror to cloud:** values go to 10 Blynk virtual pins over the HTTP API, and alert events are logged for
   the mobile app.

---

## 5 · Analytics Layer — Streamlit Dashboard

[`dashboard/app.py`](dashboard/app.py) reads the SQLite database and provides:

- live gauges with health classifications for AQI, eCO₂, IAQ and VOC
- tabbed trend charts (climate, air quality, BME680, auxiliary sensors)
- a filterable data table with date/time range selection
- **forecasting:** a scikit-learn regression pipeline (standardisation + linear regression on cyclic hour encoding, lags and rolling means)
  that projects readings up to 24 h ahead
- CSV / JSON export

---

## 6 · Results — Real Recorded Data

Measurements from a recording session on 5–6 Sept 2025 (raw data in
[`data/sample_24h_readings.json`](data/sample_24h_readings.json)). Gaps are periods when the node was powered off.

<p align="center"><img src="docs/figures/sample_24h.png" width="100%" alt="Recorded measurements"></p>

Around 12:00 the gas-sensing channels (ENS160 eCO₂/TVOC, BME680 IAQ, MQ-135) all spike at the same moment.
Three independent sensing technologies detecting the same pollution event confirm that the multi-sensor setup
is consistent.

<p align="center"><img src="docs/figures/sensor_agreement.png" width="90%" alt="Temperature agreement"></p>

<p align="center"><img src="docs/figures/aqi_distribution.png" width="80%" alt="AQI distribution"></p>

---

## Repository Structure

```
firmware/AirQualityNode/      Final ESP8266 firmware
sensor-tests/                 Incremental hardware bring-up
  ├─ bme280test/              BME280 standalone validation
  ├─ Rzero/                   MQ-135 R0 calibration
  ├─ ppm/                     MQ-135 ppm conversion
  ├─ test3HW/                 Three-sensor integration
  └─ fulltest/                Full system integration
node-red/flow.json            Node-RED flow (ingest, storage, alerts, cloud)
dashboard/                    Streamlit analytics & forecasting app
data/                         Recorded sensor data
docs/
  ├─ IOT_FinalProject_40021160214.pdf   Project report
  ├─ make_figures.py          Script that generates all README figures
  └─ figures/
```

---

## Build & Run

**Firmware:** Arduino IDE with the ESP8266 core and the libraries
`Adafruit AHTX0`, `Adafruit BME280`, `Adafruit Unified Sensor`, `DFRobot_ENS160`,
`BSEC Software Library`, `PubSubClient` and `ArduinoJson`. Set `ssid` / `password` in
`firmware/AirQualityNode/AirQualityNode.ino`, then flash.

**Node-RED:** install `node-red-node-sqlite` and `node-red-node-email`, import `node-red/flow.json`, and fill in
the Blynk auth token and alert e-mail address.

**Dashboard:**
```bash
cd dashboard
pip install -r requirements.txt
SENSOR_DB_PATH=/path/to/sensor_data.db streamlit run app.py
```

**Figures:**
```bash
pip install matplotlib pandas
python docs/make_figures.py
```
