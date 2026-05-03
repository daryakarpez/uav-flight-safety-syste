import streamlit as st
import json
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# 1. Налаштування сторінки
st.set_page_config(page_title="UAV Flight Safety System", layout="wide")

st.markdown("""
    <style>
    /* Головний фон */
    .stApp {
        background: radial-gradient(circle at center, #001233 0%, #000000 100%);
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Бокова панель з неоновим ефектом */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #000814 0%, #001D3D 100%);
        border-right: 2px solid #00B4D8;
        box-shadow: 5px 0px 15px rgba(0, 180, 216, 0.2);
    }
    
    /* Заголовки */
    h1 {
        color: #FFFFFF !important;
        text-align: center;
        letter-spacing: 3px;
        font-weight: 700 !important;
        margin-top: -20px;
    }
    .sub-title {
        color: #00B4D8;
        text-align: center;
        letter-spacing: 1px;
        font-size: 1em;
        margin-bottom: 40px;
        opacity: 0.8;
    }

    /* Кнопка */
    .stButton>button {
        background-color: rgba(0, 180, 216, 0.05) !important;
        color: #FFFFFF !important;
        border: 1px solid #00B4D8 !important;
        border-radius: 4px;
        width: 100%;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #00B4D8 !important;
        box-shadow: 0 0 15px rgba(0, 180, 216, 0.5);
        color: #000000 !important;
    }

    /* Поля вводу */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(0, 180, 216, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def calculate_safety(weather_item, params):
    wind = weather_item['wind']['speed']
    temp = weather_item['main']['temp']
    hum = weather_item['main']['humidity']
    k_wind = max(0, (params['max_wind'] - wind) / params['max_wind'])
    k_hum = max(0, (params['max_humidity'] - hum) / params['max_humidity'])
    if temp < params['min_temp'] or temp > params['max_temp'] or hum > params['max_humidity']:
        return 0.0
    return round((k_wind * 0.7) + (k_hum * 0.3), 2)

def load_drones():
    try:
        with open('drones.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"DJI Mavic 3": {"max_wind": 12, "min_temp": -10, "max_temp": 40, "max_humidity": 85}}

drones_db = load_drones()

# Шапка сайту
st.write("<h1>UAV SAFETY SYSTEM</h1>", unsafe_allow_html=True)
st.write("<p class='sub-title'>МОНІТОРИНГ ТА АНАЛІЗ УМОВ ДЛЯ ПОЛЬОТІВ</p>", unsafe_allow_html=True)

# Бокова панель
st.sidebar.markdown("### ⚙️ НАЛАШТУВАННЯ МІСІЇ")

if drones_db:
    selected_drone = st.sidebar.selectbox("МОДЕЛЬ БПЛА", list(drones_db.keys()))
    city = st.sidebar.text_input("ЛОКАЦІЯ", "Kyiv")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 ЧАСОВИЙ ПРОМІЖОК")
    start_dt = st.sidebar.datetime_input("ПОЧАТОК", datetime.now())
    end_dt = st.sidebar.datetime_input("ЗАВЕРШЕННЯ", datetime.now() + timedelta(hours=3))
    
    api_key = "32b44eeafe4783aa188cc888cc0331c6" 

    if st.sidebar.button("АНАЛІЗУВАТИ БЕЗПЕКУ"):
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ua"
        response = requests.get(url).json()
        
        if "list" in response:
            st.subheader(f"📊 ПАРАМЕТРИ ПОГОДИ: {selected_drone} | {city}")
            
            html_table = """
            <table style="width:100%; border-collapse: collapse; font-family: sans-serif; color: white; border: 1px solid rgba(0, 180, 216, 0.1);">
                <tr style="background-color: rgba(0, 180, 216, 0.1);">
                    <th style="padding: 15px; text-align: left;">ЧАС</th>
                    <th style="padding: 15px; text-align: center;">КОЕФІЦІЄНТ</th>
                    <th style="padding: 15px; text-align: center;">СТАТУС</th>
                </tr>
            """
            
            total_score = 0
            count = 0

            for item in response['list'][:15]: 
                f_dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
                s_dt = datetime.combine(start_dt.date(), start_dt.time())
                e_dt = datetime.combine(end_dt.date(), end_dt.time())
                
                # Похибка 1.5 години для точок прогнозу
                is_active = (s_dt - timedelta(hours=1, minutes=30)) <= f_dt <= (e_dt + timedelta(hours=1, minutes=30))
                
                score = calculate_safety(item, drones_db[selected_drone])
                
                row_opacity = "1.0" if is_active else "0.3"
                row_bg = "rgba(0, 180, 216, 0.1)" if is_active else "transparent"
                status_txt = "ДОЗВОЛЕНО" if is_active else "---"
                
                if is_active:
                    total_score += score
                    count += 1

                html_table += f"""
                <tr style="background-color: {row_bg}; opacity: {row_opacity}; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 12px; font-size: 0.9em;">{item['dt_txt']}</td>
                    <td style="padding: 12px; text-align: center; font-weight: bold; color: #00B4D8;">{score}</td>
                    <td style="padding: 12px; text-align: center; font-size: 0.8em;">{status_txt}</td>
                </tr>
                """
            
            html_table += "</table>"
            components.html(html_table, height=450, scrolling=True)

            st.markdown("---")
            if count > 0:
                avg = round(total_score / count, 2)
                if avg > 0.7:
                    st.success(f"✅ ПОЛІТ МОЖЛИВИЙ. СЕРЕДНІЙ ІНДЕКС БЕЗПЕКИ: {avg}")
                else:
                    st.error(f"❌ ВИСОКИЙ РИЗИК. СЕРЕДНІЙ ІНДЕКС БЕЗПЕКИ: {avg}")
            else:
                st.info("ℹ️ ДАНІ ВІДСУТНІ. БУДЬ ЛАСКА, РОЗШИРТЕ ЧАСОВИЙ ПРОМІЖОК У МЕНЮ ЗЛІВА.")
        else:
            st.error("❌ ЛОКАЦІЮ НЕ ЗНАЙДЕНО. ПЕРЕВІРТЕ НАЗВУ МІСТА.")
