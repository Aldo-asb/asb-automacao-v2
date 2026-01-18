import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ASB AUTOMACÃO V2", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- ESTILO PARA MELHORAR O VISUAL ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    [data-testid="stMetricValue"] { font-size: 40px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE COMUNICAÇÃO FIREBASE ---
def fb_get(path, default=None):
    try:
        r = requests.get(f"{URL_FB}{path}.json", timeout=2)
        return r.json() if r.ok else default
    except:
        return default

def fb_set(path, value):
    try:
        requests.put(f"{URL_FB}{path}.json", json=value, timeout=2)
    except:
        pass

# --- MENU LATERAL (ORGANIZAÇÃO DAS TELAS) ---
st.sidebar.title("MENU DE CONTROLE")
aba_selecionada = st.sidebar.radio("Selecione a Tela:", ["🕹️ Controle de Dispositivos", "📈 Monitoramento de Temperatura"])

# --- LÓGICA DE SEPARAÇÃO DE TELAS ---

# TELA 1: CONTROLE DE DISPOSITIVOS
if aba_selecionada == "🕹️ Controle de Dispositivos":
    st.header("🕹️ Controle de Dispositivos")
    st.divider()
    
    led = fb_get("controle/led", "OFF")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Comandos")
        if st.button("🟢 LIGAR LED"):
            fb_set("controle/led", "ON")
            st.rerun()

        if st.button("🔴 DESLIGAR LED"):
            fb_set("controle/led", "OFF")
            st.rerun()

    with col2:
        st.subheader("Status Atual")
        # Garante que tratamos o valor como string para evitar erro
        led_str = str(led)
        cor = "🟢" if "ON" in led_str.upper() else "🔴"
        st.markdown(f"<div style='text-align: center; border: 2px solid grey; padding: 20px; border-radius: 10px;'>"
                    f"<h1>{cor} {led_str}</h1>"
                    f"</div>", unsafe_allow_html=True)

# TELA 2: MONITORAMENTO DE TEMPERATURA
elif aba_selecionada == "📈 Monitoramento de Temperatura":
    st.header("📈 Monitoramento de Temperatura")
    st.divider()
    
    temperatura = fb_get("sensor/temperatura")
    status = fb_get("sensor/status", "ERRO")
    
    col_metrica, col_info = st.columns([1, 2])
    
    with col_metrica:
        if status == "OK" and isinstance(temperatura, (int, float)):
            st.metric("Temperatura Atual", f"{temperatura:.2f} °C")
        else:
            st.error("Falha na leitura do sensor")
            
    with col_info:
        st.info("Os dados são atualizados em tempo real vindos do coletor local.")

# --- ATUALIZAÇÃO AUTOMÁTICA ---
time.sleep(2)
st.rerun()
