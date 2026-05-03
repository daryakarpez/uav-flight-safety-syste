import streamlit as st
import json
import requests
from datetime import datetime

# 1. Налаштування сторінки
st.set_page_config(page_title="UAV Safety Pink System", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF0F5; }
    [data-testid="stSidebar"] { background-color: #FFC0CB; }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .stButton>button {
        background-color: #C71585 !important;
        color: #FFFFFF !important;
        border-radius: 15px;
        border: 2px solid #FFFFFF !important;
        font-weight: bold;
        height: 3em;
        width: 100%;
    }
    input, select, [data-testid="stHeader"] { background: transparent; }
    </style>
    """, unsafe_allow_html=True)

# 2. Математична модель (винесена на початок)
def calculate_safety(weather_item, params):
    wind = weather_item['wind']['speed']
    temp = weather_item['main']['temp']
    hum = weather_item['main']['humidity']
    
    k_wind = max(0, (params['max_wind'] - wind) / params['max_wind'])
    k_hum = max(0, (params['max_humidity'] - hum) / params['max_humidity'])
    
    if temp < params['min_temp'] or temp > params['max_temp'] or hum > params['max_humidity']:
        return 0.0
    return round((k_wind * 0.7) + (k_hum * 0.3), 2)

# 3. Завантаження даних
def load_drones():
    try:
        with open('drones.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

drones_db = load_drones()

st.title("🌸 UAV SAFETY DECISION SUPPORT")

# 4. Бокова панель
st.sidebar.header("⚙️ ПАРАМЕТРИ МІСІЇ")

if drones_db:
    selected_drone = st.sidebar.selectbox("Модель БПЛА", list(drones_db.keys()))
    city = st.sidebar.text_input("Місто", "Kyiv")
    
    st.sidebar.subheader("⏳ Час місії")
    start_dt = st.sidebar.datetime_input("Початок місії", datetime.now())
    end_dt = st.sidebar.datetime_input("Кінець місії", datetime.now())
    
    api_key = "32b44eeafe4783aa188cc888cc0331c6" 

    if st.sidebar.button("РОЗРАХУВАТИ БЕЗПЕКУ"):
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ua"
        response = requests.get(url).json()
        
        if "list" in response:
            st.subheader(f"📊 Аналіз погоди: {selected_drone} у місті {city}")
            
            html_table = """
            <table style="width:100%; border-collapse: collapse; background-color: white; color: #C71585; border-radius: 10px; overflow: hidden;">
                <tr style="background-color: #C71585; color: white;">
                    <th style="padding: 15px; text-align: left;">📅 Прогноз на час</th>
                    <th style="padding: 15px; text-align: center;">🛡️ Індекс (0-1)</th>
                    <th style="padding: 15px; text-align: center;">📝 Статус місії</th>
                </tr>
            """
            
            main_score = 0
            count = 0

            for item in response['list'][:15]: 
                forecast_dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
                score = calculate_safety(item, drones_db[selected_drone])
                
                # Перевірка чи входить час у проміжок користувача
                is_in_range = start_dt <= forecast_dt <= end_dt
                
                if is_in_range:
                    bg_row = "#FFF0F5" if score > 0.5 else "#FFB6C1"
                    status = "🎯 В межах місії"
                    main_score += score
                    count += 1
                else:
                    bg_row = "#FFFFFF"
                    status = "<span style='color: #ccc;'>---</span>"

                html_table += f"""
                <tr style="background-color: {bg_row}; border-bottom: 1px solid #FFC0CB; opacity: {1.0 if is_in_range else 0.4};">
                    <td style="padding: 12px;">{item['dt_txt']}</td>
                    <td style="padding: 12px; text-align: center; font-weight: bold;">{score}</td>
                    <td style="padding: 12px; text-align: center;">{status}</td>
                </tr>
                """
            
            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)

            # Вердикт
            st.write("---")
            if count > 0:
                avg_safety = round(main_score / count, 2)
                if avg_safety > 0.7:
                    st.success(f"💖 Середня безпека у вибраний час: {avg_safety}. Політ дозволено!")
                else:
                    st.error(f"💔 Середня безпека: {avg_safety}. Ризик занадто високий для цього проміжку!")
            else:
                st.warning("⚠️ У вибраному проміжку часу прогнозів не знайдено. Оберіть час на найближчі 3-5 днів.")
        else:
            st.error("❌ Помилка API. Перевірте назву міста.")
