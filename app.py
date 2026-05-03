import streamlit as st
import json
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# 1. Налаштування сторінки
st.set_page_config(page_title="UAV Safety Planner", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #001233 0%, #000000 100%); font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #000814 0%, #001D3D 100%); border-right: 2px solid #00B4D8; }
    h1, h3, .stMarkdown { color: white !important; }
    
    /* Стиль карток-індикаторів */
    .status-pill {
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8em;
        text-transform: uppercase;
    }
    .status-green { background-color: #2ECC71; color: #000; }
    .status-yellow { background-color: #F1C40F; color: #000; }
    .status-red { background-color: #E74C3C; color: #fff; }
    </style>
    """, unsafe_allow_html=True)

def get_safety_status(weather_item, params):
    wind = weather_item['wind']['speed']
    temp = weather_item['main']['temp']
    hum = weather_item['main']['humidity']
    
    # Критичні умови (Червоний)
    if temp < params['min_temp'] or temp > params['max_temp'] or hum > params['max_humidity'] or wind > params['max_wind']:
        return "RED", 0.0
    
    # Розрахунок коефіцієнта для жовтого/зеленого
    k_wind = max(0, (params['max_wind'] - wind) / params['max_wind'])
    k_hum = max(0, (params['max_humidity'] - hum) / params['max_humidity'])
    score = round((k_wind * 0.7) + (k_hum * 0.3), 2)
    
    if score > 0.7: return "GREEN", score
    if score > 0.4: return "YELLOW", score
    return "RED", score

def load_drones():
    try:
        with open('drones.json', 'r', encoding='utf-8') as f: return json.load(f)
    except:
        # Дефолтні налаштування, якщо файл не знайдено
        return {"Autel EVO II": {"max_wind": 12, "min_temp": -10, "max_temp": 45, "max_humidity": 90}}

drones_db = load_drones()

st.write("<h1 style='text-align:center;'>UAV FLIGHT PLANNER</h1>", unsafe_allow_html=True)

# Бокова панель
st.sidebar.markdown("### ⚙️ НАЛАШТУВАННЯ")
selected_drone = st.sidebar.selectbox("МОДЕЛЬ БПЛА", list(drones_db.keys()))
city = st.sidebar.text_input("ЛОКАЦІЯ", "Kyiv")
start_dt = st.sidebar.datetime_input("ПОЧАТОК", datetime.now())
end_dt = st.sidebar.datetime_input("ЗАВЕРШЕННЯ", datetime.now() + timedelta(hours=6))

if st.sidebar.button("ПЕРЕВІРИТИ ПЛАН ПОЛЬОТІВ"):
    api_key = "32b44eeafe4783aa188cc888cc0331c6" 
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ua"
    res = requests.get(url).json()
    
    if "list" in res:
        st.subheader(f"📅 Графік безпеки: {selected_drone} | {city}")
        
        html_table = """
        <table style="width:100%; border-collapse: collapse; color: white;">
            <tr style="border-bottom: 2px solid #00B4D8; text-align: left;">
                <th style="padding: 15px;">ЧАС</th>
                <th style="padding: 15px; text-align: center;">УМОВИ</th>
                <th style="padding: 15px; text-align: right;">РЕКОМЕНДАЦІЯ</th>
            </tr>
        """
        
        found_data = False
        for item in res['list'][:20]:
            f_dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
            s_dt = datetime.combine(start_dt.date(), start_dt.time())
            e_dt = datetime.combine(end_dt.date(), end_dt.time())
            
            if s_dt <= f_dt <= e_dt:
                found_data = True
                status, score = get_safety_status(item, drones_db[selected_drone])
                
                if status == "GREEN":
                    pill = '<span class="status-pill status-green">🟢 Безпечно</span>'
                    note = "Ідеальні умови для місії"
                elif status == "YELLOW":
                    pill = '<span class="status-pill status-yellow">🟡 Ризиковано</span>'
                    note = "Зверніть увагу на вітер/вологість"
                else:
                    pill = '<span class="status-pill status-red">🔴 Заборонено</span>'
                    note = "Критичні погодні умови"

                html_table += f"""
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <td style="padding: 12px;">{f_dt.strftime('%d.%m | %H:%M')}</td>
                    <td style="padding: 12px; text-align: center;">{pill}</td>
                    <td style="padding: 12px; text-align: right; font-size: 0.85em; opacity: 0.7;">{note}</td>
                </tr>
                """
        
        html_table += "</table>"
        
        if found_data:
            components.html(html_table, height=500, scrolling=True)
        else:
            st.warning("⚠️ Немає даних на цей час. Спробуйте вибрати інший часовий проміжок (OpenWeather дає прогноз на 5 днів наперед).")
    else:
        st.error("❌ Не вдалося отримати прогноз. Перевірте назву міста.")
