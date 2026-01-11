import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ASB V2 - Industrial", layout="wide")
URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acesso ASB Automação")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "ASB" and pw == "123":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Credenciais Inválidas")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title("🏗️ ASB V2.0")
aba = st.sidebar.radio("Navegação", ["Controle", "Gráficos", "Histórico"])

# --- LÓGICA DE DADOS ---
temp = requests.get(f"{URL_FB}sensor/valor.json").json() or "0.0"

if aba == "Controle":
    st.header("🎮 Painel de Acionamento")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 LIGAR", use_container_width=True):
            requests.put(f"{URL_FB}controle/led.json", json="LED:ON")
    with col2:
        if st.button("🔴 DESLIGAR", use_container_width=True):
            requests.put(f"{URL_FB}controle/led.json", json="LED:OFF")
    st.metric("Temperatura", f"{temp} °C")

elif aba == "Gráficos":
    st.header("📈 Monitoramento em Tempo Real")
    # Aqui vai a lógica do gráfico que fizemos antes
    st.write(f"Leitura atual: {temp} °C")
    st.info("Gráfico sendo alimentado pelo Firebase...")

elif aba == "Histórico":
    st.header("📂 Memória do Sistema")
    st.write("Logs de operação e falhas aparecerão aqui.")

time.sleep(4)
st.rerun()
