import streamlit as st
import json
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# 1. Налаштування сторінки
st.set_page_config(page_title="UAV Mission Planner", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #001233 0%, #000000 100%); font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #000814 0%, #001D3D 100%); border-right: 2px solid #00B4D8; }
    
    /* Контейнер для вікна з тонкими лініями */
    .window-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        /* Тонка напівпрозора неонова лінія */
        border-bottom: 1px solid rgba(0, 180, 216, 0.15);
        box-shadow: 0px 4px 10px -6px rgba(0, 180, 216, 0.2);
    }

    /* Рівні колонки без лишніх елементів */
    .time-col { width: 20%; color: white; font-weight: bold; font-size: 1.1em; }
    .status-col { width: 60%; text-align: center; color: rgba(255,255,255,0.6); font-size: 1em; }
    .wind-col { width: 20%; text-align: right; color: #00B4D8; font-size: 0.9em; }

    .date-sub { color: rgba(0, 180, 216, 0.5); font-size: 0.7em; margin-top: 2px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

def get_safety_status(weather_item, params):
    wind = weather_item['wind']['speed']
    temp = weather_item['main']['temp']
    hum = weather_item['main']['humidity']
    if temp < params['min_temp'] or temp > params['max_temp'] or hum > params['max_humidity'] or wind > params['max_wind']:
        return "RED"
    k_wind = max(0, (params['max_wind'] - wind) / params['max_wind'])
    k_hum = max(0, (params['max_humidity'] - hum) / params['max_humidity'])
    score = (k_wind * 0.7) + (k_hum * 0.3)
    return "GREEN" if score > 0.7 else "YELLOW" if score > 0.4 else "RED"

try:
    with open('drones.json', 'r', encoding='utf-8') as f: drones_db = json.load(f)
except:
    drones_db = {"Autel EVO II": {"max_wind": 12, "min_temp": -10, "max_temp": 45, "max_humidity": 90}}

# Ліва панель
st.sidebar.markdown("### ⚙️ НАЛАШТУВАННЯ")
selected_drone = st.sidebar.selectbox("МОДЕЛЬ БПЛА", list(drones_db.keys()))
city = st.sidebar.text_input("ЛОКАЦІЯ", "Kyiv")
start_dt = st.sidebar.datetime_input("ПОЧАТОК", datetime.now())
end_dt = st.sidebar.datetime_input("ЗАВЕРШЕННЯ", datetime.now() + timedelta(hours=24))

if st.sidebar.button("АНАЛІЗУВАТИ"):
    api_key = "32b44eeafe4783aa188cc888cc0331c6"
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ua"
    res = requests.get(url).json()
    
    if "list" in res:
        html_rows = ""
        for item in res['list']:
            f_dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
            s_dt = datetime.combine(start_dt.date(), start_dt.time())
            e_dt = datetime.combine(end_dt.date(), end_dt.time())
            
            if s_dt <= f_dt <= e_dt:
                status = get_safety_status(item, drones_db[selected_drone])
                
                # Колір тексту поради залежно від статусу (зелений/жовтий/червоний)
                status_color = "#2ECC71" if status == "GREEN" else "#F1C40F" if status == "YELLOW" else "#E74C3C"
                rec_text = "Найкращий час для місії" if status == "GREEN" else \
                           "Можливі пориви вітру" if status == "YELLOW" else \
                           "Ризик втрати борту! Не літати"

                html_rows += f"""
                <div class="window-row">
                    <div class="time-col">
                        {f_dt.strftime('%H:%M')}
                        <div class="date-sub">{f_dt.strftime('%d %b')}</div>
                    </div>
                    <div class="status-col" style="color: {status_color};">
                        {rec_text}
                    </div>
                    <div class="wind-col">
                        Вітер: {item['wind']['speed']} м/с
                    </div>
                </div>
                """
        st.markdown(f"<div>{html_rows}</div>", unsafe_allow_html=True)
