import streamlit as st
import json
import requests
import pandas as pd
from datetime import datetime

# 1. Налаштування сторінки
st.set_page_config(page_title="UAV Safety Pink System", layout="wide")

st.markdown("""
    <style>
    /* Ніжно-рожевий фон всього сайту */
    .stApp {
        background-color: #FFF0F5; 
    }

    /* Бокова панель */
    [data-testid="stSidebar"] {
        background-color: #FFC0CB; 
    }

    /* Білий текст для заголовків та підписів з легкою тінню */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    /* Темно-рожеві кнопки з білим текстом */
    .stButton>button {
        background-color: #C71585 !important; /* Темно-рожевий */
        color: #FFFFFF !important;           /* Білий текст */
        border-radius: 15px;
        border: 2px solid #FFFFFF !important;
        font-weight: bold;
        height: 3em;
        width: 100%;
        transition: 0.3s;
    }

    /* Ефект при наведенні на кнопку */
    .stButton>button:hover {
        background-color: #FF1493 !important; /* Яскравіший рожевий */
        transform: scale(1.02);
    }

    /* Поля вводу: білий фон, темний текст (щоб бачити, що пишеш) */
    input, select, .stSelectbox>div>div>div {
        color: #C71585 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Колір іконок календаря та годинника */
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌸 UAV SAFETY DECISION SUPPORT")

# 2. Функція завантаження бази даних дронів
def load_drones():
    try:
        with open('drones.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Помилка: Файл drones.json не знайдено!")
        return {}

drones_db = load_drones()

# 3. Бокова панель керування
st.sidebar.header("⚙️ ПАРАМЕТРИ МІСІЇ")

if drones_db:
    selected_drone = st.sidebar.selectbox("Модель БПЛА", list(drones_db.keys()))
    city = st.sidebar.text_input("Місто", "Kyiv")
    
    # Вибір дати та часу (візуальний елемент)
    mission_date = st.sidebar.date_input("Дата польоту", datetime.now())
    mission_time = st.sidebar.time_input("Час польоту", datetime.now())
    
    api_key = "32b44eeafe4783aa188cc888cc0331c6" 

    # 4. Математична модель розрахунку
    def calculate_safety(weather_item, params):
        wind = weather_item['wind']['speed']
        temp = weather_item['main']['temp']
        hum = weather_item['main']['humidity']
        
        # Розрахунок коефіцієнтів
        k_wind = max(0, (params['max_wind'] - wind) / params['max_wind'])
        k_hum = max(0, (params['max_humidity'] - hum) / params['max_humidity'])
        
        # Перевірка критичних меж
        if temp < params['min_temp'] or temp > params['max_temp'] or hum > params['max_humidity']:
            return 0.0
            
        return round((k_wind * 0.7) + (k_hum * 0.3), 2)

    # 5. Головна кнопка
    if st.sidebar.button("РОЗРАХУВАТИ БЕЗПЕКУ"):
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ua"
        response = requests.get(url).json()
        
        if "list" in response:
            results = []
            for item in response['list'][:10]: # Беремо найближчі 10 прогнозів
                score = calculate_safety(item, drones_db[selected_drone])
                results.append({"Час": item['dt_txt'], "Індекс": score})
            
            st.subheader(f"📊 Прогноз для {selected_drone} ({city})")
            st.write(f"Планований час місії: {mission_date} о {mission_time}")

        # 6. HTML Таблиця 
            html_table = """
            <table style="width:100%; border-collapse: collapse; background-color: white; color: #C71585; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <tr style="background-color: #C71585; color: white;">
                    <th style="padding: 15px; text-align: left;">📅 Час прогнозу</th>
                    <th style="padding: 15px; text-align: center;">🛡️ Індекс безпеки (0-1)</th>
                </tr>
            """
            for res in results:
                bg_row = "#FFF0F5" if res['Індекс'] > 0.5 else "#FFB6C1"
                html_table += f"""
                <tr style="background-color: {bg_row}; border-bottom: 1px solid #FFC0CB;">
                    <td style="padding: 12px; font-weight: 500;">{res['Час']}</td>
                    <td style="padding: 12px; text-align: center; font-weight: bold;">{res['Індекс']}</td>
                </tr>
                """
            html_table += "</table>"
            
            st.markdown(html_table, unsafe_allow_html=True)

            # 7. Фінальний вердикт
            current_safety = results[0]['Індекс']
            st.write("---")
            if current_safety > 0.7:
                st.success(f"💖 Умови чудові! Можна літати. Індекс: {current_safety}")
            elif current_safety > 0.4:
                st.warning(f"🌸 Будьте обережні! Є ризики. Індекс: {current_safety}")
            else:
                st.error(f"💔 ПОЛІТ НЕБЕЗПЕЧНИЙ! Скасуйте місію. Індекс: {current_safety}")
        else:
            st.error("❌ Не вдалося отримати дані. Перевірте назву міста.")
else:
    st.warning("Будь ласка, переконайтеся, що файл drones.json знаходиться в папці з проєктом.")
