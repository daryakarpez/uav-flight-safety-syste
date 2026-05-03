import streamlit as st
import json
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# 1. Налаштування сторінки
st.set_page_config(page_title="UAV Mission Planner", layout="wide")

# Всі стилі в одному місці
st.markdown("""
    <style>
    /* Фон та загальний шрифт */
    .stApp { 
        background: radial-gradient(circle at center, #001233 0%, #000000 100%); 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Ліва панель - залишаємо як була */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #000814 0%, #001D3D 100%); 
        border-right: 2px solid #00B4D8; 
    }
    
    /* Контейнер для списку вікон */
    .mission-container {
        margin-top: 20px;
        width: 100%;
    }

    /* Рядок-лінійка (Line-effect) */
    .window-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 0;
        margin: 0;
        /* Тонка неонова лінія */
        border-bottom: 1px solid rgba(0, 180, 216, 0.2);
        /* М'яке світіння під лінією */
        box-shadow: 0px 4px 8px -4px rgba(0, 180, 216, 0.3);
    }

    /* Індикатори статусу */
    .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 15px; }
    .dot-green { background-color: #2ECC71; box-shadow: 0 0 10px #2ECC71; }
    .dot-yellow { background-color: #F1C40F; box-shadow: 0 0 10px #F1C40F; }
    .dot-red { background-color: #E74C3C; box-shadow: 0 0 10px #E74C3C; }

    /* Колонки для вирівнювання тексту */
    .col-left { width: 20%; display: flex; align-items: center; }
    .col-center { width: 60%; text-align: center; color: rgba(255,255,255,0.6); font-size: 0.95em; }
    .col-right { width: 20%; text-align: right; line-height: 1.4; }

    /* Приховуємо сміття від Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def get_safety_status(weather_item, params):
    wind = weather_item['wind']['speed']
    temp = weather_item['main']['temp']
    hum = weather_item['main']['humidity']
    if temp < params['min_temp'] or temp > params['max_temp'] or hum > params['max_humidity'] or wind > params['max_wind']:
        return "RED", 0.0
    k_wind = max(0, (params['max_wind'] - wind) / params['max_wind'])
    k_hum = max(0, (params['max_humidity'] - hum) / params['max_humidity'])
    score = round((k_wind * 0.7) + (k_hum * 0.3), 2)
    if score > 0.7: return "GREEN", score
    if score > 0.4: return "YELLOW", score
    return "RED", score

# Завантаження дронів
try:
    with open('drones.json', 'r', encoding='utf-8') as f: drones_db = json.load(f)
except:
    drones_db = {"Autel EVO II": {"max_wind": 12, "min_temp": -10, "max_temp": 45, "max_humidity": 90}}

# Сейдбар (дизайн без змін)
st.sidebar.markdown("### ⚙️ НАЛАШТУВАННЯ МІСІЇ")
selected_drone = st.sidebar.selectbox("МОДЕЛЬ БПЛА", list(drones_db.keys()))
city = st.sidebar.text_input("ЛОКАЦІЯ", "Kyiv")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 ЧАСОВИЙ ПРОМІЖОК")
start_dt = st.sidebar.datetime_input("ПОЧАТОК", datetime.now())
end_dt = st.sidebar.datetime_input("ЗАВЕРШЕННЯ", datetime.now() + timedelta(hours=24))

if st.sidebar.button("АНАЛІЗУВАТИ БЕЗПЕКУ"):
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
                status, score = get_safety_status(item, drones_db[selected_drone])
                
                dot_class = f"dot-{status.lower()}"
                rec_text = "Найкращий час для тривалої місії" if status == "GREEN" else \
                           "Можливі пориви вітру, будьте обережні" if status == "YELLOW" else \
                           "Ризик втрати борту! Політ не рекомендується"

                # Кожен рядок — це рівна структура
                html_rows += f"""
                <div class="window-row">
                    <div class="col-left">
                        <div class="dot {dot_class}"></div>
                        <div>
                            <div style="color: white; font-weight: bold; font-size: 1.1em;">{f_dt.strftime('%H:%M')}</div>
                            <div style="color: #00B4D8; font-size: 0.75em;">{f_dt.strftime('%d %b')}</div>
                        </div>
                    </div>
                    <div class="col-center">
                        {rec_text}
                    </div>
                    <div class="col-right">
                        <div style="color: white; font-size: 0.85em;">Вітер: {item['wind']['speed']} м/с</div>
                        <div style="color: rgba(0, 180, 216, 0.5); font-size: 0.75em;">Коеф: {score}</div>
                    </div>
                </div>
                """
        
        # Вивід фінального блоку
        st.markdown(f'<div class="mission-container">{html_rows}</div>', unsafe_allow_html=True)
    else:
        st.error("Помилка отримання даних.")
