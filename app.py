import streamlit as st
import json
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# Налаштування сторінки
st.set_page_config(page_title="UAV Quantum Analysis", layout="wide")

# Google Fonts та розширений CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');

    .stApp {
        background: radial-gradient(circle at top right, #001d3d, #000000);
        font-family: 'Rajdhani', sans-serif;
    }

    /* Стилізація заголовка */
    .main-title {
        font-family: 'Orbitron', sans-serif;
        color: #FFFFFF;
        text-align: center;
        font-size: 3.5rem;
        text-shadow: 0 0 20px #00b4d8, 0 0 40px #00b4d8;
        margin-bottom: 0px;
    }

    /* Картки дронів (3D ефект) */
    .drone-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 180, 216, 0.3);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
    }

    .drone-card:hover {
        transform: translateY(-10px) scale(1.05);
        border-color: #00b4d8;
        box-shadow: 0 10px 30px rgba(0, 180, 216, 0.4);
        background: rgba(0, 180, 216, 0.1);
    }

    /* Бокова панель "Cyber" */
    [data-testid="stSidebar"] {
        background: #000814 !important;
        border-right: 1px solid #00b4d8;
    }

    /* Кнопка аналізу */
    .stButton>button {
        font-family: 'Orbitron', sans-serif;
        background: transparent !important;
        color: #00b4d8 !important;
        border: 2px solid #00b4d8 !important;
        border-radius: 0px !important;
        clip-path: polygon(10% 0, 100% 0, 90% 100%, 0% 100%);
        height: 50px;
        transition: 0.3s;
    }

    .stButton>button:hover {
        background: #00b4d8 !important;
        color: black !important;
        box-shadow: 0 0 20px #00b4d8;
    }
    </style>
    """, unsafe_allow_html=True)

# Функція завантаження (додаємо посилання на картинки)
def load_drones():
    # В реальному проекті додай сюди реальні URL картинок
    return {
        "DJI Mavic 3": {"img": "https://cdn-icons-png.flaticon.com/512/3233/3233475.png", "max_wind": 12, "min_temp": -10, "max_temp": 40, "max_humidity": 85},
        "Autel EVO II": {"img": "https://cdn-icons-png.flaticon.com/512/2564/2564031.png", "max_wind": 15, "min_temp": -10, "max_temp": 45, "max_humidity": 90},
        "FPV Strike": {"img": "https://cdn-icons-png.flaticon.com/512/683/683053.png", "max_wind": 20, "min_temp": -20, "max_temp": 50, "max_humidity": 95}
    }

drones_db = load_drones()

st.markdown("<h1 class='main-title'>UAV QUANTUM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#00b4d8;'>INTELLIGENT FLIGHT PREDICTION</p>", unsafe_allow_html=True)

# Секція вибору дрона з "3D" картками
st.write("### 🛸 ОБЕРІТЬ ПЛАТФОРМУ")
cols = st.columns(len(drones_db))
selected_drone = st.session_state.get('selected_drone', list(drones_db.keys())[0])

for i, (name, specs) in enumerate(drones_db.items()):
    with cols[i]:
        # Створюємо клікабельну картку через HTML
        st.markdown(f"""
            <div class="drone-card">
                <img src="{specs['img']}" width="100" style="filter: drop-shadow(0 0 10px #00b4d8);">
                <h3 style="color:white; margin-top:10px;">{name}</h3>
                <p style="color:#00b4d8; font-size:0.8em;">Max Wind: {specs['max_wind']} m/s</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(f"ОБРАТИ {name.split()[0]}", key=f"btn_{name}"):
            st.session_state['selected_drone'] = name

st.sidebar.markdown(f"**ОБРАНО:** \n## {selected_drone}")
city = st.sidebar.text_input("📍 ЛОКАЦІЯ", "Kyiv")
start_dt = st.sidebar.datetime_input("⏱️ ПОЧАТОК", datetime.now())
end_dt = st.sidebar.datetime_input("⏱️ ЗАВЕРШЕННЯ", datetime.now() + timedelta(hours=3))

# Логіка API та таблиці (залишається твоя з попереднього кроку)
# ... [тут твій код розрахунку] ...

if st.sidebar.button("ЗАПУСТИТИ СИСТЕМУ"):
    # (Тут твій блок requests.get та формування html_table)
    # Додай у таблицю стиль шрифту 'Courier New' для ефекту коду
    st.success(f"АНАЛІЗ ЗАПУЩЕНО ДЛЯ {selected_drone}")
