# ASB Automação V2 – ESP32 WiFi
import streamlit as st
import requests
import time
from datetime import datetime

# ===== CONFIGURAÇÃO =====
st.set_page_config(page_title="ASB Automação V2", layout="wide")
URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# ===== ESTILO DARK =====
st.markdown("""
<style>
.stApp { background-color: #0E1117; color: white; }
[data-testid="stSidebar"] { background-color: #1A1C24; }
div.stButton > button { width: 100%; border-radius: 10px; height: 3em; }
</style>
""", unsafe_allow_html=True)

# ===== LOGIN =====
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>🏗️ ASB AUTOMAÇÃO - ACESSO</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PAINEL"):
            if u == "ASB" and p == "123":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Credenciais incorretas")
    st.stop()

# ===== FUNÇÃO FIREBASE =====
def fb_get(path, default="--"):
    try:
        r = requests.get(f"{URL_FB}{path}.json", timeout=2)
        return r.json() if r.ok and r.json() is not None else default
    except:
        return default

# ===== LEITURA DOS DADOS =====
temperatura = fb_get("sensor/temperatura", "--")
sensor_status = fb_get("sensor/status", "ERRO")
led_raw = fb_get("controle/led", "LED:OFF")

# ===== TRATAMENTO DO STATUS DO LED =====
if led_raw == "LED:ON":
    led_status = "LIGADO"
    cor_led = "#00FF00"
else:
    led_status = "DESLIGADO"
    cor_led = "#FF0000"

# ===== MENU =====
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4231/4231015.png", width=100)
st.sidebar.title("ASB V2.0")
menu = st.sidebar.radio("Ir para:", ["🕹️ Acionamento", "📈 Monitoramento", "📋 Logs", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.auth = False
    st.rerun()

# ===== TELAS =====
if menu == "🕹️ Acionamento":
    st.header("Controle de Equipamentos")
    st.write("---")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Controle LED")

        if st.button("🟢 LIGAR", type="primary"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:ON")
            st.rerun()

        if st.button("🔴 DESLIGAR"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:OFF")
            st.rerun()

    with c2:
        st.subheader("Status Atual")
        st.markdown(
            f"<h1 style='color:{cor_led}; text-align:center;'>{led_status}</h1>",
            unsafe_allow_html=True
        )

elif menu == "📈 Monitoramento":
    st.header("Temperatura do Sistema")

    if sensor_status == "OK":
        st.metric("Temperatura Atual", f"{temperatura} °C")
    else:
        st.error("Falha na leitura do sensor")

elif menu == "📋 Logs":
    st.header("Eventos do Sistema")
    st.table([{
        "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Evento": "Sistema Online",
        "Status": sensor_status
    }])

# ===== ATUALIZAÇÃO AUTOMÁTICA =====
time.sleep(3)
st.rerun()
