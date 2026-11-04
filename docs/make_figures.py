"""Generate the README figures from the project design and the recorded sample data.

Usage:  python docs/make_figures.py
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
C = {"node": "#2f81f7", "mqtt": "#a371f7", "nr": "#f85149", "db": "#3fb950",
     "app": "#d29922", "cloud": "#39c5cf", "sensor": "#58a6ff"}

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": FG,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": "#30363d",
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})


def box(ax, x, y, w, h, title, lines=(), color="#2f81f7", fs=12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc=color + "22", ec=color, lw=2))
    ax.text(x + w / 2, y + h - 0.32, title, ha="center", va="top", fontsize=fs, weight="bold", color=color)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.85 - i * 0.38, ln, ha="center", va="top", fontsize=fs - 3, color=FG)


def arrow(ax, p, q, color=MUTED, label=None, rad=0.0, lw=2):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=18, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.18, label, ha="center", fontsize=9,
                color=color, weight="bold")


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w * 1.5)
    ax.set_ylim(0, h * 1.5)
    ax.axis("off")
    return fig, ax


def architecture():
    fig, ax = canvas(14, 6.5)
    ax.text(10.5, 9.4, "End-to-End System Architecture", ha="center", fontsize=18, weight="bold")
    # sensors
    sensors = ["BME680  ·  IAQ / VOC", "BME280  ·  reference T/RH/P", "ENS160  ·  AQI / TVOC / eCO₂",
               "AHT21  ·  T / RH", "MQ-135  ·  analog gas"]
    for i, s in enumerate(sensors):
        y = 7.6 - i * 1.25
        ax.add_patch(FancyBboxPatch((0.3, y), 3.6, 0.85, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=C["sensor"] + "22", ec=C["sensor"], lw=1.5))
        ax.text(2.1, y + 0.42, s, ha="center", va="center", fontsize=9.5)
        arrow(ax, (3.95, y + 0.42), (5.2, 4.9), color=C["sensor"], lw=1.2)
    ax.text(4.55, 8.9, "I²C 100 kHz  +  ADC", ha="center", fontsize=9, color=C["sensor"])
    box(ax, 5.2, 2.9, 4.0, 4.0, "ESP8266 Node",
        ["sensor fusion", "BSEC temp. offset", "ENS160 T/RH comp.", "change detection", "JSON encoding",
         "LED + buzzer alarm"], C["node"])
    box(ax, 10.3, 3.9, 2.6, 2.2, "MQTT Broker", ["topic:", "ESP8266/", "airquality/data"], C["mqtt"], fs=11)
    arrow(ax, (9.25, 5.0), (10.25, 5.0), C["mqtt"])
    ax.text(9.75, 4.55, "publish", ha="center", fontsize=9, color=C["mqtt"], weight="bold")
    box(ax, 14.0, 3.3, 3.4, 3.4, "Node-RED", ["mqtt-in → parse", "threshold rules", "SQL insert",
                                                "HTTP requests", "SMTP alerts"], C["nr"])
    arrow(ax, (12.95, 5.0), (13.95, 5.0), C["mqtt"])
    ax.text(13.45, 4.55, "subscribe", ha="center", fontsize=9, color=C["mqtt"], weight="bold")
    box(ax, 18.3, 6.7, 2.6, 1.7, "Blynk Cloud", ["mobile app", "+ event log"], C["cloud"], fs=11)
    box(ax, 18.3, 4.15, 2.6, 1.7, "E-mail", ["air-quality", "alerts"], C["nr"], fs=11)
    box(ax, 18.3, 1.6, 2.6, 1.7, "SQLite", ["sensor_data", "table"], C["db"], fs=11)
    arrow(ax, (17.45, 6.2), (18.25, 7.4), C["cloud"])
    arrow(ax, (17.45, 5.0), (18.25, 5.0), C["nr"])
    arrow(ax, (17.45, 3.8), (18.25, 2.5), C["db"])
    box(ax, 12.2, 0.4, 4.6, 1.9, "Streamlit Dashboard", ["gauges · trends · tables", "regression forecast · export"],
        C["app"], fs=11)
    arrow(ax, (18.25, 2.1), (16.85, 1.4), C["db"])
    ax.text(17.6, 1.25, "query", ha="center", fontsize=9, color=C["db"], weight="bold")
    fig.savefig(OUT / "architecture.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def wiring():
    fig, ax = canvas(12, 6.5)
    ax.text(9, 9.4, "Hardware Wiring (NodeMCU ESP8266)", ha="center", fontsize=18, weight="bold")
    box(ax, 7.0, 1.2, 4.0, 7.2, "NodeMCU", [], C["node"], fs=14)
    pins = [("D1  GPIO5  SCL", 7.3), ("D2  GPIO4  SDA", 6.6), ("A0", 5.4), ("D5  GPIO14", 4.3),
            ("D6  GPIO12", 3.5), ("D7  GPIO13", 2.7), ("D8  GPIO15", 1.9)]
    for name, y in pins:
        ax.text(9.0, y, name, ha="center", va="center", fontsize=10, family="monospace")
    i2c = [("BME680", "0x77"), ("BME280", "0x76"), ("ENS160", "0x53"), ("AHT21", "0x38")]
    for i, (n, a) in enumerate(i2c):
        y = 8.0 - i * 1.15
        box(ax, 0.5, y - 0.45, 3.2, 0.95, f"{n}  @ {a}", [], C["sensor"], fs=10)
        ax.plot([3.7, 5.2], [y, y], color=C["sensor"], lw=1.5)
    ax.plot([5.2, 5.2], [8.0, 8.0 - 3 * 1.15], color=C["sensor"], lw=3)
    ax.plot([5.2, 7.0], [7.3, 7.3], color="#ffa657", lw=2.5)
    ax.plot([5.2, 7.0], [6.6, 6.6], color="#7ee787", lw=2.5)
    ax.text(5.6, 7.45, "SCL", fontsize=9, color="#ffa657")
    ax.text(5.6, 6.75, "SDA", fontsize=9, color="#7ee787")
    ax.text(2.1, 3.1, "shared I²C bus", ha="center", fontsize=10, color=MUTED, style="italic")
    box(ax, 0.5, 1.4, 3.2, 1.2, "MQ-135", ["analog out"], "#ffa657", fs=10)
    ax.plot([3.7, 5.8, 5.8, 7.0], [2.0, 2.0, 5.4, 5.4], color="#ffa657", lw=1.5, ls="--")
    outs = [("Buzzer (active-low)", 4.3, "#d2a8ff"), ("Green LED", 3.5, "#3fb950"),
            ("Yellow LED", 2.7, "#d29922"), ("Red LED", 1.9, "#f85149")]
    for n, y, col in outs:
        ax.plot([11.0, 13.6], [y, y], color=col, lw=2)
        ax.add_patch(Circle((13.9, y), 0.25, color=col))
        ax.text(14.35, y, n, va="center", fontsize=10)
    fig.savefig(OUT / "wiring.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def firmware_flow():
    fig, ax = canvas(10, 9)
    ax.text(7.5, 13.2, "Firmware Main Loop (3 s BSEC LP cycle)", ha="center", fontsize=17, weight="bold")
    steps = [("MQTT connected?  → else bounded reconnect (3 tries)", C["mqtt"]),
             ("Read BME280 reference  T / RH / P", C["sensor"]),
             ("ENS160.setTempAndHum(T, RH)", C["sensor"]),
             ("BME680 offset = T_bme680 − T_ref  →  BSEC run()", C["node"]),
             ("Every 2nd cycle: read AHT21, MQ-135, ENS160", C["sensor"]),
             ("NaN / Inf sanitisation  +  rounding", C["node"]),
             ("Δ value ≥ threshold on any channel?", C["app"]),
             ("Serialize JSON  →  publish to MQTT", C["mqtt"]),
             ("AQI → LED colour, edge-triggered 2 s buzzer", C["nr"])]
    for i, (t, col) in enumerate(steps):
        y = 11.6 - i * 1.3
        ax.add_patch(FancyBboxPatch((2.0, y), 11.0, 0.85, boxstyle="round,pad=0.02,rounding_size=0.15",
                                    fc=col + "22", ec=col, lw=2))
        ax.text(7.5, y + 0.42, t, ha="center", va="center", fontsize=11)
        if i:
            arrow(ax, (7.5, y + 1.3 - 0.02), (7.5, y + 0.88), MUTED)
    ax.text(13.3, 11.6 - 6 * 1.3 + 0.42, "no → skip publish", fontsize=9, color=C["app"], va="center")
    arrow(ax, (2.0, 0.6 + 0.42), (2.0, 11.6 + 0.42), MUTED, rad=-0.25)
    ax.text(0.2, 6.5, "loop", fontsize=10, color=MUTED, rotation=90)
    fig.savefig(OUT / "firmware_flow.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def load_sample():
    rows = json.loads((ROOT / "data" / "sample_24h_readings.json").read_text())
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    # insert a blank row at recording gaps (> 10 min) so plots don't bridge them with a line
    gaps = df.index[df["timestamp"].diff() > pd.Timedelta(minutes=10)]
    blanks = pd.DataFrame({"timestamp": df.loc[gaps, "timestamp"] - pd.Timedelta(seconds=1)})
    return pd.concat([df, blanks]).sort_values("timestamp").reset_index(drop=True)


def timeseries(df):
    panels = [("temperature", "Temperature (°C)", "#f85149"), ("humidity", "Humidity (%)", "#58a6ff"),
              ("eco2_ens", "eCO₂ ENS160 (ppm)", "#3fb950"), ("tvoc_ens", "TVOC ENS160 (ppb)", "#d29922"),
              ("iaq", "IAQ BME680 / BSEC", "#a371f7"), ("mq135_value", "MQ-135 raw ADC", "#ffa657")]
    fig, axes = plt.subplots(3, 2, figsize=(14, 9), sharex=True)
    for ax, (col, title, colr) in zip(axes.flat, panels):
        ax.plot(df["timestamp"], df[col], color=colr, lw=1.1)
        ax.fill_between(df["timestamp"], df[col], df[col].min(), where=df[col].notna(), color=colr, alpha=0.12)
        ax.set_title(title, fontsize=11, loc="left", color=FG)
        ax.grid(alpha=0.15)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.suptitle(f"Recorded Measurements, 5–6 Sept 2025  ({df['iaq'].notna().sum():,} change-triggered samples)",
                 fontsize=16, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "sample_24h.png", dpi=150)
    plt.close(fig)


def compensation(df):
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(df["timestamp"], df["temperature"], color="#f85149", lw=1.3, label="BME280 (reference)")
    ax.plot(df["timestamp"], df["temp_aht"], color="#58a6ff", lw=1.3, label="AHT21")
    ax.set_ylabel("°C")
    ax.grid(alpha=0.15)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(facecolor=BG, edgecolor="#30363d", labelcolor=FG)
    diff = (df["temp_aht"] - df["temperature"]).mean()
    ax.set_title(f"Cross-sensor temperature agreement  (mean offset AHT21 − BME280 = {diff:+.2f} °C)",
                 fontsize=13, loc="left", color=FG)
    fig.tight_layout()
    fig.savefig(OUT / "sensor_agreement.png", dpi=150)
    plt.close(fig)


def aqi_distribution(df):
    labels = {1: "Excellent", 2: "Good", 3: "Moderate", 4: "Poor", 5: "Unhealthy"}
    cols = {1: "#3fb950", 2: "#7ee787", 3: "#d29922", 4: "#f85149", 5: "#a40e26"}
    counts = df["aqi_ens"].value_counts().reindex(range(1, 6), fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.bar([f"{k}\n{labels[k]}" for k in counts.index], counts.values / counts.sum() * 100,
                  color=[cols[k] for k in counts.index])
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8, f"{b.get_height():.1f}%",
                ha="center", color=FG, fontsize=10)
    ax.set_ylabel("share of samples (%)")
    ax.set_title("ENS160 AQI distribution  →  drives Green / Yellow / Red LEDs + buzzer",
                 fontsize=13, loc="left", color=FG)
    ax.grid(axis="y", alpha=0.15)
    fig.tight_layout()
    fig.savefig(OUT / "aqi_distribution.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    wiring()
    firmware_flow()
    data = load_sample()
    timeseries(data)
    compensation(data)
    aqi_distribution(data)
    print("figures written to", OUT)
