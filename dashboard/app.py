import os
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import math
from io import BytesIO
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    layout="wide",
    page_title="Air Quality Monitor",
    page_icon="🌱",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Global Dark Theme */
    html, body, .stApp, .main {
        background: linear-gradient(135deg, #0a0e27 0%, #161b3d 100%) !important;
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    h1, p {
            color: #ffffff !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #f8fafc !important; /* Dark green text */
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        color: white !important; /* White text on hover */
    }

    /* Download Button Styling */
    .stDownloadButton > button,
    [data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #f8fafc !important; /* Dark green text */
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stDownloadButton > button:hover,
    [data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        color: white !important; /* White text on hover */
        background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%) !important;
    }

    /* Additional download button text styling */
    .stDownloadButton > button p,
    [data-testid="stDownloadButton"] > button p {
        color: inherit !important;
        margin: 0 !important;
    }
            
    /* Animated Background Pattern */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image:
            radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(255, 219, 120, 0.05) 0%, transparent 50%);
        z-index: -1;
        animation: gradientShift 20s ease infinite;
    }

    @keyframes gradientShift {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* Sidebar radio buttons styling */
    [data-testid="stSidebar"] .stRadio label p {
        color: #ffffff !important; /* This ensures the text is white */
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* IMPROVED TEXT VISIBILITY - Changed all gray text to white/light colors */
    .stMultiSelect > div > div {
        color: #ffffff !important;
    }
    
    .stMultiSelect > div > div > div {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #ffffff !important;
    }
    
    /* Multiselect dropdown */
    .stMultiSelect [data-baseweb="select"] {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #ffffff !important;
    }
    
    /* Multiselect options */
    .stMultiSelect [role="option"] {
        background-color: rgba(30, 41, 59, 0.9) !important;
        color: #ffffff !important;
    }
    
    .stMultiSelect [role="option"]:hover {
        background-color: rgba(102, 126, 234, 0.3) !important;
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #ffffff !important;
    }
    
    /* Radio button styling */
    .stRadio > div {
        color: #ffffff !important;
    }
    
    .stRadio label {
        color: #ffffff !important;
    }

    /* Info/warning/success messages */
    .stAlert {
        color: #1e293b !important;
    }

    /* --- Live Indicator --- */
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }

    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: rgba(34, 197, 94, 0.25); /* Brighter green background */
        border: 1px solid #22c55e; /* Brighter green border */
        border-radius: 20px;
        color: #22c55e !important; /* Brighter green text, !important to override global styles */
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background: #22c55e; /* Brighter green dot */
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    /* Hero Section */
    .hero-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px 30px;
        border-radius: 24px;
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }

    .hero-gradient::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: rotate 30s linear infinite;
    }

    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: white;
        margin-bottom: 12px;
        text-shadow: 0 4px 6px rgba(0,0,0,0.1);
        position: relative;
        z-index: 1;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.95);
        position: relative;
        z-index: 1;
    }

    /* Modern Card Design */
    .sensor-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        height: 100%;
    }

    .sensor-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--card-color), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .sensor-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .sensor-card:hover::before {
        opacity: 1;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        border-radius: 16px;
        padding: 20px;
        color: white;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 10px 0;
        font-family: 'Space Grotesk', sans-serif;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.95;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-icon {
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 3rem;
        opacity: 0.3;
    }

    /* Average Cards */
    .avg-card {
        background: linear-gradient(135deg, rgba(51, 65, 85, 0.9) 0%, rgba(30, 41, 59, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 18px;
        color: #f8fafc;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    .avg-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .avg-label {
        font-size: 0.85rem;
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    .avg-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc !important;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Charts Container */
    .chart-container {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    
    /* Footer */
    .footer {
        text-align: center !important;
        margin-top: 60px !important;
        padding: 30px !important;
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .footer-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        margin-bottom: 12px !important;
    }
    
    .footer-links {
        display: flex !important;
        gap: 25px !important;
        justify-content: center !important;
        flex-wrap: wrap !important;
        margin-bottom: 15px !important;
    }
    
    .footer-links a {
        color: #667eea !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        transition: color 0.3s ease !important;
    }
    
    .footer-links a:hover {
        color: #764ba2 !important;
    }
    
    .footer-copyright {
        color: #cbd5e1 !important;
        font-size: 0.9rem !important;
    }

    /* Section Headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        color: #ffffff !important;
        margin: 40px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Remove border for Current Key Metrics */
    .section-header.no-border {
        border-bottom: none !important;
        padding-bottom: 0 !important;
    }

    /* Improved text colors for better visibility */
    .sensor-card div {
        color: #ffffff !important;
    }
    
    /* Make all text in cards more visible */
    .sensor-card * {
        color: #ffffff !important;
    }
    
    /* Status text visibility */
    .sensor-card div[style*="color: #94a3b8"] {
        color: #cbd5e1 !important;
    }
    
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        # update this path to the location of database file
        conn = sqlite3.connect(os.environ.get('SENSOR_DB_PATH', 'sensor_data.db'), check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection failed: {e}")
        st.info("Please ensure the database file 'sensor_data.db' is accessible and the path is correct in the script.")
        st.stop()

def init_db(conn):
    """Initializes the database table if it doesn't exist."""
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    DATETIME DEFAULT (datetime('now', 'localtime')),
                temperature  REAL,
                humidity     REAL,
                pressure     REAL,
                mq135_value  REAL,
                iaq          REAL,
                static_iaq   REAL,
                co2_equivalent REAL,
                breath_voc   REAL,
                temp_aht     REAL,
                hum_aht      REAL,
                aqi_ens      INTEGER,
                tvoc_ens     INTEGER,
                eco2_ens     INTEGER
            );
        ''')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database initialization failed: {e}")
        st.stop()

conn = get_db_connection()
init_db(conn)

@st.cache_data(ttl=5)  # Refresh every 5 seconds
def load_data(start_datetime=None, end_datetime=None):
    """Loads sensor data from the database with datetime filtering."""
    query = "SELECT * FROM sensor_data WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC"
    try:
        start_dt_str = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        end_dt_str = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_sql_query(query, conn, params=(start_dt_str, end_dt_str))
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def get_latest_reading():
    """Get the most recent sensor reading."""
    query = "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1"
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.iloc[0]
        return None
    except Exception as e:
        st.error(f"Error fetching latest reading: {e}")
        return None

def get_aqi_status(aqi):
    """Returns AQI status and color based on value (1-5 scale)."""
    if aqi is None or not math.isfinite(aqi):
        return "Unknown", "#64748b"
    if aqi <= 1:
        return "Excellent", "#10b981"
    elif aqi <= 2:
        return "Good", "#84cc16"
    elif aqi <= 3:
        return "Moderate", "#fbbf24"
    elif aqi <= 4:
        return "Poor", "#fb923c"
    else:
        return "Very Poor", "#dc2626"

def get_co2_status(co2):
    """Returns CO2 status based on ppm value."""
    if co2 is None or not math.isfinite(co2):
        return "Unknown", "#64748b"
    if co2 <= 600:
        return "Excellent", "#10b981"
    elif co2 <= 1000:
        return "Good", "#84cc16"
    elif co2 <= 1500:
        return "Moderate", "#fbbf24"
    elif co2 <= 2000:
        return "Poor", "#fb923c"
    else:
        return "Very Poor", "#ef4444"

def get_iaq_status(iaq):
    """Returns IAQ status based on BSEC library ranges."""
    if iaq is None or not math.isfinite(iaq):
        return "Unknown", "#64748b"
    if iaq <= 50:
        return "Excellent", "#10b981"
    elif iaq <= 100:
        return "Good", "#84cc16"
    elif iaq <= 150:
        return "Lightly Polluted", "#fbbf24"
    elif iaq <= 200:
        return "Moderately Polluted", "#fb923c"
    elif iaq <= 250:
        return "Heavily Polluted", "#ef4444"
    else:
        return "Severely Polluted", "#dc2626"

def get_breath_voc_status(voc):
    """Returns Breath VOC status based on ppm value."""
    if voc is None or not math.isfinite(voc):
        return "Unknown", "#64748b"
    if voc <= 0.3:
        return "Excellent", "#10b981"
    elif voc <= 0.5:
        return "Good", "#84cc16"
    elif voc <= 1.0:
        return "Moderate", "#fbbf24"
    elif voc <= 2.0:
        return "Poor", "#fb923c"
    else:
        return "Very Poor", "#dc2626"

def create_modern_gauge(value, title, vmin, vmax, color, unit=""):
    """Creates a modern gauge chart."""
    if value is None or not math.isfinite(value):
        value = 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16, 'color': '#f8fafc', 'family': 'Inter'}},
        number = {'suffix': unit, 'font': {'size': 28, 'color': color, 'family': 'Space Grotesk'}},
        gauge = {
            'axis': {'range': [vmin, vmax], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "rgba(30, 41, 59, 0.3)",
            'borderwidth': 1,
            'bordercolor': "rgba(255, 255, 255, 0.1)",
        }
    ))
    
    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f8fafc', family='Inter')
    )
    
    return fig

def create_aqi_gauge(value, title, color):
    """Creates a specialized AQI gauge with range 0-5 but labels 1-5."""
    if value is None or not math.isfinite(value):
        value = 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16, 'color': '#f8fafc', 'family': 'Inter'}},
        number = {'suffix': "", 'font': {'size': 28, 'color': color, 'family': 'Space Grotesk'}},
        gauge = {
            'axis': {
                'range': [0, 5], 
                'tickwidth': 1, 
                'tickcolor': "#cbd5e1",
                'tickvals': [1, 2, 3, 4, 5],
                'ticktext': ['1', '2', '3', '4', '5']
            },
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "rgba(30, 41, 59, 0.3)",
            'borderwidth': 1,
            'bordercolor': "rgba(255, 255, 255, 0.1)",
        }
    ))
    
    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f8fafc', family='Inter')
    )
    
    return fig

def safe_get(data, key, default=0):
    """Safely get a value from data, returning default if None or NaN."""
    value = data.get(key, default)
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return default
    return value

def calculate_averages(df):
    """Calculate average values for the selected time period."""
    if df.empty:
        return {}
    
    averages = {
        'temperature': df['temperature'].mean() if 'temperature' in df else 0,
        'humidity': df['humidity'].mean() if 'humidity' in df else 0,
        'pressure': df['pressure'].mean() if 'pressure' in df else 0,
        'mq135_value': df['mq135_value'].mean() if 'mq135_value' in df else 0,
        'iaq': df['iaq'].mean() if 'iaq' in df else 0,
        'static_iaq': df['static_iaq'].mean() if 'static_iaq' in df else 0,
        'co2_equivalent': df['co2_equivalent'].mean() if 'co2_equivalent' in df else 0,
        'breath_voc': df['breath_voc'].mean() if 'breath_voc' in df else 0,
        'aqi_ens': df['aqi_ens'].mean() if 'aqi_ens' in df else 0,
        'eco2_ens': df['eco2_ens'].mean() if 'eco2_ens' in df else 0,
        'tvoc_ens': df['tvoc_ens'].mean() if 'tvoc_ens' in df else 0,
    }
    
    # Handle NaN values
    for key in averages:
        if pd.isna(averages[key]):
            averages[key] = 0
    
    return averages

def predict_future_readings(df, target_column, hours_ahead=24):
    """Improved ML prediction with better error handling."""
    try:
        if df.empty or target_column not in df.columns:
            return None, None, None
        
        df_clean = df.dropna(subset=[target_column]).copy()
        if len(df_clean) < 10:  # Reduced minimum requirement
            return None, None, None
        
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        df_clean = df_clean.sort_values('timestamp')
        
        df_clean['hour'] = df_clean['timestamp'].dt.hour
        df_clean['day_of_week'] = df_clean['timestamp'].dt.dayofweek
        df_clean['time_numeric'] = (df_clean['timestamp'] - df_clean['timestamp'].min()).dt.total_seconds() / 3600
        
        df_clean['rolling_3'] = df_clean[target_column].rolling(window=min(3, len(df_clean)), min_periods=1).mean()
        df_clean['rolling_6'] = df_clean[target_column].rolling(window=min(6, len(df_clean)), min_periods=1).mean()
        
        df_clean['trend'] = df_clean[target_column].diff().fillna(0)
        
        df_clean['hour_sin'] = np.sin(2 * np.pi * df_clean['hour'] / 24)
        df_clean['hour_cos'] = np.cos(2 * np.pi * df_clean['hour'] / 24)
        
        df_clean['lag_1'] = df_clean[target_column].shift(1).fillna(df_clean[target_column].iloc[0])
        
        features = ['time_numeric', 'hour', 'day_of_week', 'rolling_3', 'rolling_6', 'trend', 'hour_sin', 'hour_cos', 'lag_1']
        
        # Use only available features
        available_features = [f for f in features if f in df_clean.columns]
        if not available_features:
            return None, None, None
        
        X = df_clean[available_features].fillna(0)
        y = df_clean[target_column]
        
        best_model = None
        best_score = -1
        
        from sklearn.linear_model import Ridge
        
        models_to_try = [
            ('linear', Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', LinearRegression())
            ])),
            ('ridge', Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', Ridge(alpha=1.0))
            ]))
        ]
        
        # Try RandomForest only if we have enough data
        if len(df_clean) > 20:
            from sklearn.ensemble import RandomForestRegressor
            models_to_try.append(
                ('rf', Pipeline([
                    ('scaler', StandardScaler()),
                    ('regressor', RandomForestRegressor(n_estimators=20, random_state=42, max_depth=5))
                ]))
            )
        
        for name, model in models_to_try:
            try:
                model.fit(X, y)
                score = model.score(X, y)
                if score > best_score:
                    best_model = model
                    best_score = score
            except Exception as model_error:
                continue
        
        if best_model is None or best_score < 0:
            return None, None, None
        
        last_time = df_clean['timestamp'].max()
        future_times = [last_time + timedelta(hours=i) for i in range(1, hours_ahead + 1)]
        
        future_features = []
        last_values = df_clean[target_column].tail(12).values
        
        for i, future_time in enumerate(future_times):
            time_numeric = (future_time - df_clean['timestamp'].min()).total_seconds() / 3600
            hour = future_time.hour
            day_of_week = future_time.dayofweek
            
            # Use recent values for rolling averages
            if i == 0:
                rolling_3 = df_clean[target_column].tail(3).mean()
                rolling_6 = df_clean[target_column].tail(6).mean()
                trend = df_clean[target_column].diff().tail(1).iloc[0] if not df_clean[target_column].diff().tail(1).isna().iloc[0] else 0
                lag_1 = df_clean[target_column].iloc[-1]
            else:
                # Use simple trend continuation with previous predictions
                prev_predictions = [pred[-1] if isinstance(pred, list) else pred for pred in future_features[:i]]
                combined_values = list(last_values[-max(1, 6-i):]) + prev_predictions
                rolling_3 = np.mean(combined_values[-3:]) if len(combined_values) >= 3 else rolling_3
                rolling_6 = np.mean(combined_values[-6:]) if len(combined_values) >= 6 else rolling_6
                trend = trend * 0.9  # Decay trend
                lag_1 = prev_predictions[-1] if prev_predictions else lag_1
            
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)
            
            feature_dict = {
                'time_numeric': time_numeric,
                'hour': hour,
                'day_of_week': day_of_week,
                'rolling_3': rolling_3,
                'rolling_6': rolling_6,
                'trend': trend,
                'hour_sin': hour_sin,
                'hour_cos': hour_cos,
                'lag_1': lag_1
            }
            
            # Only use features that were available during training
            feature_vector = [feature_dict.get(f, 0) for f in available_features]
            future_features.append(feature_vector)
        
        future_X = pd.DataFrame(future_features, columns=available_features)
        predictions = best_model.predict(future_X)
        
        # Post-process predictions
        if 'aqi' in target_column.lower():
            # For AQI, ensure 1-5 range with some variation
            base_aqi = df_clean[target_column].iloc[-1]  # Start from current
            for i in range(len(predictions)):
                # Add small random variation based on trend
                variation = np.random.normal(0, 0.3)
                predictions[i] = max(1, min(5, round(base_aqi + variation + (predictions[i] - base_aqi) * 0.5)))
                base_aqi = predictions[i]  # Update base for next prediction
            predictions = predictions.astype(int)
        else:
            # For CO2, ensure reasonable bounds
            predictions = np.clip(predictions, 300, 3000)
        
        return future_times, predictions, max(0, best_score)
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return None, None, None

def create_prediction_chart(historical_data, future_times, predictions, target_column, title, color):
    """Create a prediction chart with complete historical and predicted data."""
    fig = go.Figure()
    
    # Get MORE historical data for better context
    if not historical_data.empty and target_column in historical_data.columns:
        # Use ALL available historical data instead of just last 48 points
        historical_clean = historical_data.dropna(subset=[target_column])
        
        # If we have a lot of data, use last 7 days for better visibility
        if len(historical_clean) > 168:  # More than 7 days of hourly data
            historical_clean = historical_clean.tail(168)  # Last 7 days
        
        if not historical_clean.empty:
            fig.add_trace(go.Scatter(
                x=historical_clean['timestamp'],
                y=historical_clean[target_column],
                mode='lines+markers',
                name='Historical Data',
                line=dict(color=color, width=2.5),
                marker=dict(size=3, opacity=0.7),
                opacity=0.8
            ))
    
    # Predicted data with better visualization
    if future_times and predictions is not None:
        # Connect last historical point with first prediction
        if not historical_data.empty and target_column in historical_data.columns:
            last_historical = historical_data.dropna(subset=[target_column])
            if not last_historical.empty:
                last_point_time = last_historical['timestamp'].iloc[-1]
                last_point_value = last_historical[target_column].iloc[-1]
                
                # Add connection line
                connection_times = [last_point_time] + future_times
                connection_values = [last_point_value] + list(predictions)
                
                fig.add_trace(go.Scatter(
                    x=connection_times,
                    y=connection_values,
                    mode='lines+markers',
                    name='AI Predictions',
                    line=dict(color=color, width=3, dash='dash'),
                    marker=dict(size=6, symbol='diamond'),
                    fill='tonexty' if len(fig.data) > 0 else None,
                    fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)'
                ))
            else:
                # No historical data, just show predictions
                fig.add_trace(go.Scatter(
                    x=future_times,
                    y=predictions,
                    mode='lines+markers',
                    name='AI Predictions',
                    line=dict(color=color, width=3, dash='dash'),
                    marker=dict(size=6, symbol='diamond')
                ))
        else:
            # No historical data, just show predictions
            fig.add_trace(go.Scatter(
                x=future_times,
                y=predictions,
                mode='lines+markers',
                name='AI Predictions',
                line=dict(color=color, width=3, dash='dash'),
                marker=dict(size=6, symbol='diamond')
            ))
    
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center'},
        xaxis_title="Time",
        yaxis_title="Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Inter'),
        title_font=dict(size=16, family='Space Grotesk'),
        margin=dict(l=10, r=10, t=50, b=10),
        height=350,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        hovermode='x unified'
    )
    
    return fig

st.sidebar.title("🎛️ Controls")

page = st.sidebar.radio("Navigation", ["🏠 Home", "📊 Dashboard", "🧠 AI Predictions", "📋 Data Table", "📥 Export"])

st.sidebar.markdown("---")
st.sidebar.title("🔄 Data Control")

if st.sidebar.button("🔄 Refresh Data", key="refresh_data", use_container_width=True):
    # Clear the cached data functions only - session state should persist
    load_data.clear()
    get_latest_reading.clear()
    
    # Force a rerun to refresh the page with new data
    st.rerun()

st.sidebar.title("📅 Date & Time Filters")

# Initialize session state for filters if they don't exist to prevent resets
if 'start_date' not in st.session_state:
    today = datetime.now()
    default_start_datetime = today - timedelta(days=1)
    st.session_state.start_date = default_start_datetime.date()
    st.session_state.start_time = default_start_datetime.time()
    st.session_state.end_date = today.date()
    st.session_state.end_time = today.time()

# Use st.session_state to make the widgets' values persistent
start_date = st.sidebar.date_input("Start Date", key='start_date')
start_time = st.sidebar.time_input("Start Time", key='start_time')
end_date = st.sidebar.date_input("End Date", key='end_date')
end_time = st.sidebar.time_input("End Time", key='end_time')

# Combine the persistent date and time values
start_datetime = datetime.combine(st.session_state.start_date, st.session_state.start_time)
end_datetime = datetime.combine(st.session_state.end_date, st.session_state.end_time)


if start_datetime > end_datetime:
    st.sidebar.error("Error: Start datetime must be before end datetime.")
    st.stop()

df = load_data(start_datetime, end_datetime)

st.sidebar.markdown("---")
st.sidebar.title("🧠 AI Predictions")

prediction_end = datetime.now()
prediction_start = prediction_end - timedelta(days=7)
prediction_df = load_data(prediction_start, prediction_end)


if not prediction_df.empty and len(prediction_df) >= 10:
    aqi_future_times, aqi_predictions, aqi_accuracy = predict_future_readings(
        prediction_df, 'aqi_ens', hours_ahead=24
    )
    
    co2_future_times, co2_predictions, co2_accuracy = predict_future_readings(
        prediction_df, 'eco2_ens', hours_ahead=24
    )
    
    if aqi_predictions is not None:
        st.sidebar.markdown("### 🌬️ AQI Forecast")
        
        # Current vs Next prediction - Use REAL-TIME latest reading
        latest_reading = get_latest_reading()
        current_aqi = safe_get(latest_reading, 'aqi_ens', 3) if latest_reading is not None else 3
        next_aqi = aqi_predictions[0] if len(aqi_predictions) > 0 else current_aqi
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ec4899, #be185d); padding: 10px; border-radius: 8px; text-align: center;">
                <div style="color: white; font-size: 0.8rem;">Current</div>
                <div style="color: white; font-size: 1.4rem; font-weight: bold;">{int(current_aqi)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            trend_arrow = "📈" if next_aqi > current_aqi else "📉" if next_aqi < current_aqi else "➡️"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 10px; border-radius: 8px; text-align: center;">
                <div style="color: white; font-size: 0.8rem;">Next Hour</div>
                <div style="color: white; font-size: 1.4rem; font-weight: bold;">{int(next_aqi)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if aqi_accuracy:
            accuracy_pct = min(max(aqi_accuracy * 100, 0), 100)
            st.sidebar.markdown(f"**Model Accuracy:** {accuracy_pct:.1f}%")
    
    if co2_predictions is not None:
        st.sidebar.markdown("### 🏭 CO₂ Forecast")
        
        # Use REAL-TIME latest reading for CO2 as well
        current_co2 = safe_get(latest_reading, 'eco2_ens', 800) if latest_reading is not None else 800
        next_co2 = co2_predictions[0] if len(co2_predictions) > 0 else current_co2
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #10b981, #047857); padding: 10px; border-radius: 8px; text-align: center;">
                <div style="color: white; font-size: 0.8rem;">Current</div>
                <div style="color: white; font-size: 1.2rem; font-weight: bold;">{int(current_co2)} ppm</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            trend_arrow = "📈" if next_co2 > current_co2 else "📉" if next_co2 < current_co2 else "➡️"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #3b82f6, #1e40af); padding: 10px; border-radius: 8px; text-align: center;">
                <div style="color: white; font-size: 0.8rem;">Next Hour</div>
                <div style="color: white; font-size: 1.2rem; font-weight: bold;">{int(next_co2)} ppm</div>
            </div>
            """, unsafe_allow_html=True)
        
        if co2_accuracy:
            accuracy_pct = min(max(co2_accuracy * 100, 0), 100)
            st.sidebar.markdown(f"**Model Accuracy:** {accuracy_pct:.1f}%")
    
    st.sidebar.markdown("### 🧠 AI Insights")
    if aqi_predictions is not None and co2_predictions is not None:
        aqi_trend = np.mean(np.diff(aqi_predictions[:6]))  # First 6 hours trend
        co2_trend = np.mean(np.diff(co2_predictions[:6]))
        
        insights = []
        if aqi_trend > 0.1:
            insights.append("🔴 Air quality may worsen")
        elif aqi_trend < -0.1:
            insights.append("🟢 Air quality improving")
        
        if co2_trend > 50:
            insights.append("⬆️ CO₂ levels rising")
        elif co2_trend < -50:
            insights.append("⬇️ CO₂ levels declining")
        
        if not insights:
            insights.append("📊 Stable conditions expected")
        
        for insight in insights:
            st.sidebar.markdown(f"• {insight}")
        
else:
    st.sidebar.markdown("### 🤖 AI Predictions")
    st.sidebar.info("Need more data for predictions (minimum 10 readings)")

def render_home_page():
    """Enhanced home page with modern design."""
    hero_html = """
    <div class="hero-gradient">
        <h1 class="hero-title">🌱 Air Quality Monitoring System</h1>
        <p class="hero-subtitle">Real-time environmental monitoring with advanced IoT sensors for a healthier living space.</p>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)
    
    latest = get_latest_reading()
    if latest is not None:
        st.markdown('<h2 class="section-header no-border">⭐ Current Key Metrics</h2>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = safe_get(latest, 'temperature', 0)
            st.markdown(f"""
            <div class="metric-card" style="--gradient-start: #667eea; --gradient-end: #764ba2;">
                <div class="metric-label">Temperature</div>
                <div class="metric-value">{temp:.1f}°C</div>
                <div class="metric-icon">🌡️</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            humidity = safe_get(latest, 'humidity', 0)
            st.markdown(f"""
            <div class="metric-card" style="--gradient-start: #3b82f6; --gradient-end: #1e40af;">
                <div class="metric-label">Humidity</div>
                <div class="metric-value">{humidity:.1f}%</div>
                <div class="metric-icon">💧</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            aqi = safe_get(latest, 'aqi_ens', 1)
            aqi_status, aqi_color = get_aqi_status(aqi)
            st.markdown(f"""
            <div class="metric-card" style="--gradient-start: {aqi_color}; --gradient-end: {aqi_color};">
                <div class="metric-label">Air Quality ({aqi_status})</div>
                <div class="metric-value">{aqi:.0f}</div>
                <div class="metric-icon">🌬️</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            co2 = safe_get(latest, 'eco2_ens', 400)
            co2_status, co2_color = get_co2_status(co2)
            st.markdown(f"""
            <div class="metric-card" style="--gradient-start: {co2_color}; --gradient-end: {co2_color};">
                <div class="metric-label">CO₂ Level ({co2_status})</div>
                <div class="metric-value">{int(co2)}</div>
                <div class="metric-icon">🏭</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No recent data available. Waiting for sensor readings...")

def render_dashboard_page(data):
    """Renders the main dashboard with all metrics and charts."""
    st.markdown('<h1 style="font-family: Space Grotesk; color: #ffffff;">📊 Air Quality Dashboard</h1>', unsafe_allow_html=True)
    
    if data.empty:
        st.warning("No data available for the selected date range.")
        return
    
    latest = get_latest_reading()
    if latest is None:
        st.warning("Could not fetch the latest sensor reading.")
        return

    # Live indicator with last update time
    time_diff = datetime.now() - latest['timestamp']
    if time_diff.total_seconds() < 300:  # Less than 5 minutes
        st.markdown(f"""
        <div class="live-indicator">
            <div class="live-dot"></div>
            LIVE - Last update: {latest['timestamp'].strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-header">🎯 Current Readings</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    primary_metrics = [
        (col1, "Temperature", safe_get(latest, 'temperature'), "°C", "🌡️", "#667eea", ""),
        (col2, "Humidity", safe_get(latest, 'humidity'), "%", "💧", "#3b82f6", ""),
        (col3, "Pressure", safe_get(latest, 'pressure'), " hPa", "📊", "#8b5cf6", ""),
        (col4, "MQ-135 Gas", safe_get(latest, 'mq135_value'), "", "🔥", "#ec4899", ""),
        (col5, "AQI", safe_get(latest, 'aqi_ens', 1), "", "🌬️", get_aqi_status(safe_get(latest, 'aqi_ens', 1))[1], get_aqi_status(safe_get(latest, 'aqi_ens', 1))[0]),
        (col6, "TVOC", safe_get(latest, 'tvoc_ens'), " ppb", "☁️", "#f59e0b", ""),
        (col7, "CO₂", safe_get(latest, 'eco2_ens', 400), " ppm", "🏭", get_co2_status(safe_get(latest, 'eco2_ens', 400))[1], get_co2_status(safe_get(latest, 'eco2_ens', 400))[0])
    ]
    
    for col, label, value, unit, icon, color, status in primary_metrics:
        with col:
            val_str = f"{value:.1f}" if isinstance(value, float) else str(int(value))
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: {color};">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
                    <div style="font-size: 1.7rem; font-weight: 700; color: {color}; margin: 8px 0;">
                        {val_str}{unit}
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.75rem; height: 1.2em;">{status}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<h2 class="section-header">🔬 BME680 Environmental Sensor</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    # Get Breath VOC value and status for dynamic coloring
    breath_voc_val = safe_get(latest, 'breath_voc', 0.5)
    breath_voc_status, breath_voc_color = get_breath_voc_status(breath_voc_val)
    
    bme680_metrics = [
        (col1, "IAQ", safe_get(latest, 'iaq', 50), "", "🌬️", get_iaq_status(safe_get(latest, 'iaq', 50))[1], get_iaq_status(safe_get(latest, 'iaq', 50))[0]),
        (col2, "Static IAQ", safe_get(latest, 'static_iaq', 50), "", "📊", get_iaq_status(safe_get(latest, 'static_iaq', 50))[1], get_iaq_status(safe_get(latest, 'static_iaq', 50))[0]),
        (col3, "CO₂ Equivalent", safe_get(latest, 'co2_equivalent', 600), " ppm", "💨", get_co2_status(safe_get(latest, 'co2_equivalent', 600))[1], get_co2_status(safe_get(latest, 'co2_equivalent', 600))[0]),
        (col4, "Breath VOC", breath_voc_val, " ppm", "🫁", breath_voc_color, breath_voc_status) 
    ]
    
    for col, label, value, unit, icon, color, status in bme680_metrics:
        with col:
            val_str = f"{value:.2f}" if isinstance(value, float) else str(int(value))
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: {color};">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
                    <div style="font-size: 1.7rem; font-weight: 700; color: {color}; margin: 8px 0;">
                        {val_str}{unit}
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.75rem; height: 1.2em;">{status}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<h2 class="section-header">🎛️ Detailed Gauges</h2>', unsafe_allow_html=True)
    
    gauge_col1, gauge_col2 = st.columns(2)
    with gauge_col1:
        st.plotly_chart(create_modern_gauge(safe_get(latest, 'temperature'), "Temperature", -10, 50, "#667eea", "°C"), use_container_width=True)
    with gauge_col2:
        st.plotly_chart(create_modern_gauge(safe_get(latest, 'humidity'), "Humidity", 0, 100, "#3b82f6", "%"), use_container_width=True)
    
    gauge_col3, gauge_col4 = st.columns(2)
    with gauge_col3:
        aqi_color = get_aqi_status(safe_get(latest, 'aqi_ens', 1))[1]
        st.plotly_chart(create_aqi_gauge(safe_get(latest, 'aqi_ens', 1), "Air Quality Index", aqi_color), use_container_width=True)
    with gauge_col4:
        co2_color = get_co2_status(safe_get(latest, 'eco2_ens', 400))[1]
        st.plotly_chart(create_modern_gauge(safe_get(latest, 'eco2_ens', 400), "CO₂ Level", 400, 3000, co2_color, " ppm"), use_container_width=True)

    st.markdown('<h3 style="color: #ffffff; margin-top: 30px;">🔬 BME680 Detailed Gauges</h3>', unsafe_allow_html=True)
    
    bme680_gauge_col1, bme680_gauge_col2 = st.columns(2)
    with bme680_gauge_col1:
        iaq_color = get_iaq_status(safe_get(latest, 'iaq', 50))[1]
        st.plotly_chart(create_modern_gauge(safe_get(latest, 'iaq'), "BME680 IAQ", 0, 500, iaq_color), use_container_width=True)
    with bme680_gauge_col2:
        static_iaq_color = get_iaq_status(safe_get(latest, 'static_iaq', 50))[1]
        st.plotly_chart(create_modern_gauge(safe_get(latest, 'static_iaq'), "BME680 Static IAQ", 0, 500, static_iaq_color), use_container_width=True)
    
    bme680_gauge_col3, bme680_gauge_col4 = st.columns(2)
    with bme680_gauge_col3:
        bme680_co2_color = get_co2_status(safe_get(latest, 'co2_equivalent', 600))[1]
        st.plotly_chart(create_modern_gauge(safe_get(latest, 'co2_equivalent'), "BME680 CO₂ Equivalent", 400, 2000, bme680_co2_color, " ppm"), use_container_width=True)
    with bme680_gauge_col4:
        # Use dynamic color and better range for Breath VOC gauge
        st.plotly_chart(create_modern_gauge(breath_voc_val, "BME680 Breath VOC", 0, 3, breath_voc_color, " ppm"), use_container_width=True)

    st.markdown('<h2 class="section-header">📊 Average Values (Selected Period)</h2>', unsafe_allow_html=True)
    
    averages = calculate_averages(data)
    avg_col1, avg_col2, avg_col3, avg_col4, avg_col5, avg_col6, avg_col7 = st.columns(7)
    
    avg_metrics = [
        (avg_col1, "Avg Temperature", averages.get('temperature', 0), "°C"),
        (avg_col2, "Avg Humidity", averages.get('humidity', 0), "%"),
        (avg_col3, "Avg Pressure", averages.get('pressure', 0), " hPa"),
        (avg_col4, "Avg MQ-135 Gas", averages.get('mq135_value', 0), ""),
        (avg_col5, "Avg AQI", averages.get('aqi_ens', 0), ""),
        (avg_col6, "Avg CO₂", averages.get('eco2_ens', 0), " ppm"),
        (avg_col7, "Avg TVOC", averages.get('tvoc_ens', 0), " ppb"),
    ]
    
    for col, label, value, unit in avg_metrics:
        with col:
            val_str = f"{value:.1f}" if value != 0 else "N/A"
            st.markdown(f"""
            <div class="avg-card">
                <div class="avg-label">{label}</div>
                <div class="avg-value">{val_str}{unit if val_str != "N/A" else ""}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<h3 class="section-header">🔬 BME680 Average Values (Selected Period)</h3>', unsafe_allow_html=True)
    
    bme680_avg_col1, bme680_avg_col2, bme680_avg_col3, bme680_avg_col4 = st.columns(4)
    
    bme680_avg_metrics = [
        (bme680_avg_col1, "Avg IAQ", averages.get('iaq', 0), ""),
        (bme680_avg_col2, "Avg Static IAQ", averages.get('static_iaq', 0), ""),
        (bme680_avg_col3, "Avg CO₂ Equivalent", averages.get('co2_equivalent', 0), " ppm"),
        (bme680_avg_col4, "Avg Breath VOC", averages.get('breath_voc', 0), " ppm"),
    ]
    
    for col, label, value, unit in bme680_avg_metrics:
        with col:
            val_str = f"{value:.2f}" if value != 0 else "N/A"
            st.markdown(f"""
            <div class="avg-card">
                <div class="avg-label">{label}</div>
                <div class="avg-value">{val_str}{unit if val_str != "N/A" else ""}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<h3 class="section-header">📊 Average Gauges</h3>', unsafe_allow_html=True)
    
    # Create gauge rows for averages (2 per row)
    avg_gauge_row1_col1, avg_gauge_row1_col2 = st.columns(2)
    with avg_gauge_row1_col1:
        avg_temp = averages.get('temperature', 0)
        st.plotly_chart(create_modern_gauge(avg_temp, "Average Temperature", -10, 50, "#667eea", "°C"), use_container_width=True)
    with avg_gauge_row1_col2:
        avg_humidity = averages.get('humidity', 0)
        st.plotly_chart(create_modern_gauge(avg_humidity, "Average Humidity", 0, 100, "#3b82f6", "%"), use_container_width=True)
    
    avg_gauge_row2_col1, avg_gauge_row2_col2 = st.columns(2)
    with avg_gauge_row2_col1:
        avg_aqi = averages.get('aqi_ens', 1)
        avg_aqi_color = get_aqi_status(avg_aqi)[1]
        st.plotly_chart(create_aqi_gauge(avg_aqi, "Average Air Quality Index", avg_aqi_color), use_container_width=True)
    with avg_gauge_row2_col2:
        avg_co2 = averages.get('eco2_ens', 400)
        avg_co2_color = get_co2_status(avg_co2)[1]
        st.plotly_chart(create_modern_gauge(avg_co2, "Average CO₂ Level", 400, 3000, avg_co2_color, " ppm"), use_container_width=True)
    
    st.markdown('<h4 style="color: #ffffff; margin-top: 30px;">BME680 Average Gauges</h4>', unsafe_allow_html=True)
    bme680_gauge_row1_col1, bme680_gauge_row1_col2 = st.columns(2)
    with bme680_gauge_row1_col1:
        avg_iaq = averages.get('iaq', 50)
        avg_iaq_color = get_iaq_status(avg_iaq)[1]
        st.plotly_chart(create_modern_gauge(avg_iaq, "Average BME680 IAQ", 0, 500, avg_iaq_color), use_container_width=True)
    with bme680_gauge_row1_col2:
        avg_static_iaq = averages.get('static_iaq', 50)
        avg_static_iaq_color = get_iaq_status(avg_static_iaq)[1]
        st.plotly_chart(create_modern_gauge(avg_static_iaq, "Average Static IAQ", 0, 500, avg_static_iaq_color), use_container_width=True)

    # New row for remaining BME680 average gauges
    bme680_gauge_row2_col1, bme680_gauge_row2_col2 = st.columns(2)
    with bme680_gauge_row2_col1:
        avg_bme680_co2 = averages.get('co2_equivalent', 600)
        avg_bme680_co2_color = get_co2_status(avg_bme680_co2)[1]
        st.plotly_chart(create_modern_gauge(avg_bme680_co2, "Average BME680 CO₂", 400, 2000, avg_bme680_co2_color, " ppm"), use_container_width=True)
    with bme680_gauge_row2_col2:
        avg_breath_voc = averages.get('breath_voc', 0.5)
        avg_breath_voc_color = get_breath_voc_status(avg_breath_voc)[1]
        st.plotly_chart(create_modern_gauge(avg_breath_voc, "Average Breath VOC", 0, 3, avg_breath_voc_color, " ppm"), use_container_width=True)


    st.markdown('<h2 class="section-header">📉 Historical Trends</h2>', unsafe_allow_html=True)
    
    def create_trend_chart(df, y_col, title, color, unit=""):
        if y_col not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text=f"Column '{y_col}' not found", 
                                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                                font=dict(color="#cbd5e1", size=14))
        elif df[y_col].isna().all():
            fig = go.Figure()
            fig.add_annotation(text=f"No data for {title}", 
                                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                                font=dict(color="#cbd5e1", size=14))
        else:
            # Clean the data and check if we have any valid data points
            clean_df = df.dropna(subset=[y_col, 'timestamp'])
            if clean_df.empty:
                fig = go.Figure()
                fig.add_annotation(text=f"No valid data for {title}", 
                                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                                    font=dict(color="#cbd5e1", size=14))
            else:
                fig = px.line(clean_df, x='timestamp', y=y_col)
                fig.update_traces(
                    line=dict(color=color, width=2.5),
                    mode='lines',
                    fill='tozeroy',
                    fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)'
                )
        
        fig.update_layout(
            title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
            xaxis_title="", yaxis_title=unit, hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff', family='Inter'), title_font=dict(size=18, family='Space Grotesk'),
            margin=dict(l=40, r=40, t=50, b=40), height=350, width=500,
            xaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)'),
            yaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)'),
            showlegend=False
        )
        return fig
    
    # Tab-based organization for better performance and readability
    tab1, tab2, tab3, tab4 = st.tabs(["🌡️💧 Climate", "🏭🌬️ Air Quality", "🔬 BME680 Sensors", "🔥☁️ Additional"])
    
    with tab1:
        climate_col1, climate_col2 = st.columns(2)
        with climate_col1:
            if not data.empty and 'temperature' in data.columns:
                clean_temp = data.dropna(subset=['temperature', 'timestamp'])
                if not clean_temp.empty:
                    temp_fig = go.Figure()
                    temp_fig.add_trace(go.Scatter(
                        x=clean_temp['timestamp'],
                        y=clean_temp['temperature'],
                        mode='lines',
                        name='Temperature',
                        line=dict(color='#667eea', width=2.5),
                        fill='tozeroy',
                        fillcolor='rgba(102, 126, 234, 0.1)'
                    ))
                    temp_fig.update_layout(
                        title={'text': '🌡️ Temperature', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
                        xaxis_title="", yaxis_title="°C", hovermode="x unified",
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#ffffff', family='Inter'), 
                        title_font=dict(size=18, family='Space Grotesk'),
                        margin=dict(l=40, r=40, t=50, b=40), height=350, width=500,
                        xaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)'),
                        yaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)'),
                        showlegend=False
                    )
                    st.plotly_chart(temp_fig, use_container_width=True, key="temp_tab")
        
        with climate_col2:
            if not data.empty and 'humidity' in data.columns:
                clean_hum = data.dropna(subset=['humidity', 'timestamp'])
                if not clean_hum.empty:
                    hum_fig = go.Figure()
                    hum_fig.add_trace(go.Scatter(
                        x=clean_hum['timestamp'],
                        y=clean_hum['humidity'],
                        mode='lines',
                        name='Humidity',
                        line=dict(color='#3b82f6', width=2.5),
                        fill='tozeroy',
                        fillcolor='rgba(59, 130, 246, 0.1)'
                    ))
                    hum_fig.update_layout(
                        title={'text': '💧 Humidity', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
                        xaxis_title="", yaxis_title="%", hovermode="x unified",
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#ffffff', family='Inter'), 
                        title_font=dict(size=18, family='Space Grotesk'),
                        margin=dict(l=40, r=40, t=50, b=40), height=350, width=500,
                        xaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)'),
                        yaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)'),
                        showlegend=False
                    )
                    st.plotly_chart(hum_fig, use_container_width=True, key="humidity_tab")
    
    with tab2:
        air_col1, air_col2 = st.columns(2)
        with air_col1:
            st.plotly_chart(create_trend_chart(data, 'eco2_ens', '🏭 CO₂ Trend', '#10b981', 'ppm'), 
                            use_container_width=True, key="co2_tab")
        with air_col2:
            st.plotly_chart(create_trend_chart(data, 'aqi_ens', '🌬️ AQI Trend', '#ec4899', 'AQI'), 
                            use_container_width=True, key="aqi_tab")
    
    with tab3:
        bme_col1, bme_col2 = st.columns(2)
        with bme_col1:
            st.plotly_chart(create_trend_chart(data, 'iaq', '🔬 BME680 IAQ Trend', '#667eea', 'IAQ'), 
                            use_container_width=True, key="bme680_iaq_tab")
            st.plotly_chart(create_trend_chart(data, 'static_iaq', '📊 BME680 Static IAQ Trend', '#8b5cf6', 'Static IAQ'), 
                            use_container_width=True, key="bme680_static_iaq_tab")
        with bme_col2:
            st.plotly_chart(create_trend_chart(data, 'co2_equivalent', '💨 BME680 CO₂ Equivalent Trend', '#10b981', 'ppm'), 
                            use_container_width=True, key="bme680_co2_tab")
            st.plotly_chart(create_trend_chart(data, 'breath_voc', '🫁 BME680 Breath VOC Trend', '#f59e0b', 'ppm'), 
                            use_container_width=True, key="bme680_voc_tab")
    
    with tab4:
        add_col1, add_col2 = st.columns(2)
        with add_col1:
            st.plotly_chart(create_trend_chart(data, 'mq135_value', '🔥 MQ-135 Gas Sensor Trend', '#ef4444', 'Reading'), 
                            use_container_width=True, key="mq135_tab")
        with add_col2:
            st.plotly_chart(create_trend_chart(data, 'tvoc_ens', '☁️ TVOC Trend', '#f59e0b', 'ppb'), 
                            use_container_width=True, key="tvoc_tab")
    


def render_data_table_page(data):
    """Displays the filtered data in a styled table."""
    st.markdown('<h1 style="font-family: Space Grotesk; color: #ffffff;">📋 Sensor Data Table</h1>', unsafe_allow_html=True)
    
    if data.empty:
        st.warning("No data available for the selected date range.")
        return

    st.info(f"Displaying {len(data)} records for the selected period.")
    
    # Define formatting for the columns
    format_dict = {col: "{:.2f}" for col in data.columns if data[col].dtype == 'float64'}
    format_dict['timestamp'] = '{:%Y-%m-%d %H:%M:%S}'

    st.markdown("### Select Columns to Display")
    all_columns = list(data.columns)
    
    # Initialize default columns
    default_columns = ['timestamp', 'temperature', 'humidity', 'aqi_ens', 'eco2_ens']
    available_defaults = [col for col in default_columns if col in all_columns]
    if not available_defaults:
        available_defaults = all_columns[:5] if len(all_columns) >= 5 else all_columns
    
    # Use a callback function to handle column changes
    def on_columns_change():
        st.session_state.persistent_columns = st.session_state.selected_columns_multiselect
    
    # Get current selection from session state or use defaults
    current_selection = st.session_state.get('persistent_columns', available_defaults)
    
    # Ensure current selection is valid
    current_selection = [col for col in current_selection if col in all_columns]
    if not current_selection:
        current_selection = available_defaults
    
    selected_columns = st.multiselect(
        "Select columns to display", 
        all_columns, 
        default=current_selection,
        key='selected_columns_multiselect',
        on_change=on_columns_change
    )
    
    # Update persistent storage
    if selected_columns:
        st.session_state.persistent_columns = selected_columns
    
    if selected_columns:
        display_data = data[selected_columns]
        st.dataframe(display_data.style.format({k: v for k, v in format_dict.items() if k in selected_columns}), 
                     use_container_width=True, height=600)
    else:
        st.warning("Please select at least one column to display.")

def render_ai_predictions_page():
    """Renders the AI Predictions page with detailed charts and analysis."""
    st.markdown('<h1 style="font-family: Space Grotesk; color: #ffffff;">🤖 AI Predictions & Forecasting</h1>', unsafe_allow_html=True)
    
    prediction_end = datetime.now()
    prediction_start = prediction_end - timedelta(days=7)
    prediction_df = load_data(prediction_start, prediction_end)
    
    if prediction_df.empty or len(prediction_df) < 10:
        st.warning("⚠️ Insufficient data for AI predictions. Need at least 10 readings from the last 7 days.")
        st.info("💡 The AI model requires historical data to make accurate predictions. Please ensure your sensors have been collecting data.")
        return
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <h3 style="color: white; margin: 0; font-family: 'Space Grotesk';">🧠 AI Forecasting Engine</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">
            Using Linear Regression with time-based features, rolling averages, and historical patterns to predict future air quality conditions.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    aqi_future_times, aqi_predictions, aqi_accuracy = predict_future_readings(prediction_df, 'aqi_ens', hours_ahead=24)
    co2_future_times, co2_predictions, co2_accuracy = predict_future_readings(prediction_df, 'eco2_ens', hours_ahead=24)
    
    st.markdown('<h2 style="color: #ffffff; margin-top: 30px;">⏰ Next Hour Predictions</h2>', unsafe_allow_html=True)
    
    if aqi_predictions is not None and co2_predictions is not None:
        # Get ACTUAL current values from latest reading (same as dashboard)
        latest = get_latest_reading()
        current_aqi = safe_get(latest, 'aqi_ens', 3) if latest is not None else 3
        current_co2 = safe_get(latest, 'eco2_ens', 800) if latest is not None else 800
        
        next_aqi = aqi_predictions[0] if len(aqi_predictions) > 0 else current_aqi
        next_co2 = co2_predictions[0] if len(co2_predictions) > 0 else current_co2
        
        hour_col1, hour_col2, hour_col3, hour_col4 = st.columns(4)
        
        with hour_col1:
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: #ec4899;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">⏰</div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Current AQI</div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: #ec4899; margin: 8px 0;">
                        {int(current_aqi)}
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.75rem; height: 1.2em;">Now</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with hour_col2:
            trend_arrow = "📈" if next_aqi > current_aqi else "📉" if next_aqi < current_aqi else "➡️"
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: #667eea;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">{trend_arrow}</div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Next Hour AQI</div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: #667eea; margin: 8px 0;">
                        {int(next_aqi)}
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.75rem; height: 1.2em;">+1 Hour</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with hour_col3:
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: #10b981;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">🏭</div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Current CO₂</div>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #10b981; margin: 8px 0;">
                        {int(current_co2)} ppm
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.75rem; height: 1.2em;">Now</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with hour_col4:
            trend_arrow = "📈" if next_co2 > current_co2 else "📉" if next_co2 < current_co2 else "➡️"
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: #3b82f6;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">{trend_arrow}</div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Next Hour CO₂</div>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #3b82f6; margin: 8px 0;">
                        {int(next_co2)} ppm
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.75rem; height: 1.2em;">+1 Hour</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<h2 style="color: #ffffff; margin-top: 40px;">📊 24-Hour Detailed Forecast</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3 style="color: #ffffff;">🌬️ AQI Prediction (Next 24 Hours)</h3>', unsafe_allow_html=True)
        
        if aqi_predictions is not None:
            aqi_chart = create_prediction_chart(
                prediction_df, aqi_future_times, aqi_predictions, 
                'aqi_ens', 'AQI Forecast', '#ec4899'
            )
            st.plotly_chart(aqi_chart, use_container_width=True)
            
            # AQI Statistics - use actual current value
            latest = get_latest_reading()
            current_aqi = safe_get(latest, 'aqi_ens', 3) if latest is not None else 3
            avg_predicted_aqi = np.mean(aqi_predictions)
            max_predicted_aqi = np.max(aqi_predictions)
            min_predicted_aqi = np.min(aqi_predictions)
            
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: #ec4899;">
                <div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;">📊 AQI Forecast Summary</div>
                    <div style="color: #ffffff; line-height: 1.6;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Current:</span> 
                            <span style="color: #ec4899; font-weight: 700;">{int(current_aqi)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>24h Average:</span> 
                            <span style="color: #ec4899; font-weight: 700;">{avg_predicted_aqi:.1f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Expected Range:</span> 
                            <span style="color: #ec4899; font-weight: 700;">{int(min_predicted_aqi)} - {int(max_predicted_aqi)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Model Accuracy:</span> 
                            <span style="color: #10b981; font-weight: 700;">{(aqi_accuracy*100):.1f}%</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Unable to generate AQI predictions. Check data quality.")
    
    with col2:
        st.markdown('<h3 style="color: #ffffff;">🏭 CO₂ Prediction (Next 24 Hours)</h3>', unsafe_allow_html=True)
        
        if co2_predictions is not None:
            co2_chart = create_prediction_chart(
                prediction_df, co2_future_times, co2_predictions, 
                'eco2_ens', 'CO₂ Forecast', '#10b981'
            )
            st.plotly_chart(co2_chart, use_container_width=True)
            
            # CO2 Statistics - use actual current value
            latest = get_latest_reading()
            current_co2 = safe_get(latest, 'eco2_ens', 800) if latest is not None else 800
            avg_predicted_co2 = np.mean(co2_predictions)
            max_predicted_co2 = np.max(co2_predictions)
            min_predicted_co2 = np.min(co2_predictions)
            
            st.markdown(f"""
            <div class="sensor-card" style="--card-color: #10b981;">
                <div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;">📊 CO₂ Forecast Summary</div>
                    <div style="color: #ffffff; line-height: 1.6;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Current:</span> 
                            <span style="color: #10b981; font-weight: 700;">{int(current_co2)} ppm</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>24h Average:</span> 
                            <span style="color: #10b981; font-weight: 700;">{avg_predicted_co2:.0f} ppm</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Expected Range:</span> 
                            <span style="color: #10b981; font-weight: 700;">{int(min_predicted_co2)} - {int(max_predicted_co2)} ppm</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Model Accuracy:</span> 
                            <span style="color: #f59e0b; font-weight: 700;">{(co2_accuracy*100):.1f}%</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Unable to generate CO₂ predictions. Check data quality.")
    
    if aqi_predictions is not None and co2_predictions is not None:
        st.markdown('<h3 style="color: #ffffff; margin-top: 40px;">🧠 AI Insights & Recommendations</h3>', unsafe_allow_html=True)
        
        # Calculate trends for next 6 hours
        aqi_trend = np.mean(np.diff(aqi_predictions[:6]))
        co2_trend = np.mean(np.diff(co2_predictions[:6]))
        
        recommendations = []
        alerts = []
        
        if avg_predicted_aqi > 4:
            alerts.append("🚨 **High AQI Alert**: Air quality expected to be poor")
            recommendations.append("🏠 **Stay Indoors**: Limit outdoor activities")
            recommendations.append("💨 **Use Air Purifiers**: Turn on air filtration systems")
        elif avg_predicted_aqi > 3:
            recommendations.append("⚠️ **Monitor Conditions**: Sensitive individuals should be cautious")
        
        if avg_predicted_co2 > 1000:
            alerts.append("🚨 **High CO₂ Alert**: Ventilation needed")
            recommendations.append("🪟 **Increase Ventilation**: Open windows or improve airflow")
        elif avg_predicted_co2 > 800:
            recommendations.append("🌪️ **Consider Ventilation**: Monitor CO₂ levels")
        
        if aqi_trend > 0.2:
            recommendations.append("📈 **Worsening Trend**: AQI expected to increase")
        elif aqi_trend < -0.2:
            recommendations.append("📉 **Improving Trend**: Air quality getting better")
        
        if co2_trend > 100:
            recommendations.append("⬆️ **Rising CO₂**: Levels trending upward")
        elif co2_trend < -100:
            recommendations.append("⬇️ **Declining CO₂**: Levels trending downward")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if alerts:
                st.markdown("#### 🚨 Alerts")
                for alert in alerts:
                    st.markdown(alert)
            else:
                st.markdown("#### ✅ No Critical Alerts")
                st.markdown("Air quality conditions appear stable.")
        
        with col2:
            st.markdown("#### 💡 Recommendations")
            if recommendations:
                for rec in recommendations:
                    st.markdown(f"• {rec}")
            else:
                st.markdown("• 📊 **Continue Monitoring**: Maintain current conditions")

def render_export_page(data):
    """Provides an option to download the data as a CSV or JSON file."""
    st.markdown('<h1 style="font-family: Space Grotesk; color: #ffffff;">📥 Export Data</h1>', unsafe_allow_html=True)
    
    if data.empty:
        st.warning("No data available to export for the selected date range.")
        return

    st.success(f"✅ Found {len(data)} records to export based on your filters.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Export Options")
        export_all = st.radio("Data to export:", 
                                ["All sensor data", "Custom selection"])
    
    with col2:
        st.markdown("### File Format")
        file_format = st.selectbox("Choose format:", ["CSV", "JSON"])
    
    # Determine columns to export
    export_data = pd.DataFrame()
    if export_all == "All sensor data":
        export_data = data
    else:  # Custom selection
        all_columns = list(data.columns)
        selected_export_cols = st.multiselect("Select columns to export:", all_columns, default=all_columns)
        if selected_export_cols:
            export_data = data[selected_export_cols]
        else:
            st.warning("Please select at least one column to export.")
            return
    
    start_str = start_datetime.strftime('%Y%m%d_%H%M')
    end_str = end_datetime.strftime('%Y%m%d_%H%M')
    
    # Create download based on format
    if not export_data.empty:
        if file_format == "CSV":
            export_file = export_data.to_csv(index=False).encode('utf-8')
            filename = f"sensor_data_{start_str}_to_{end_str}.csv"
            mime_type = "text/csv"
        elif file_format == "JSON":
            export_file = export_data.to_json(orient='records', date_format='iso', indent=2).encode('utf-8')
            filename = f"sensor_data_{start_str}_to_{end_str}.json"
            mime_type = "application/json"

        st.download_button(
            label=f"📥 Download Data as {file_format}",
            data=export_file,
            file_name=filename,
            mime=mime_type,
            key="download-data",
            use_container_width=True
        )

if page == "🏠 Home":
    render_home_page()
elif page == "📊 Dashboard":
    render_dashboard_page(df)
elif page == "🧠 AI Predictions":
    render_ai_predictions_page()
elif page == "📋 Data Table":
    render_data_table_page(df)
elif page == "📥 Export":
    render_export_page(df)

st.markdown("""
<div class="footer">
    <h3 class="footer-title">🌱 Air Quality Monitor</h3>
    <div class="footer-links">
        <a href="https://www.linkedin.com/in/sinamozaffarirad/" target="_blank">👨🏻‍💻 Developed By Sina Mozaffari Rad</a>
        <a href="https://streamlit.io" target="_blank">⚡ Powered by Streamlit</a>
    </div>
    <p class="footer-copyright">© 2025 Department of Computer Engineering, Kashan University</p>
    <p class="footer-copyright">Built for a better environment</p>
</div>
""", unsafe_allow_html=True)
