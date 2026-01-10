import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ASB Automação Industrial", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- SISTEMA DE LOGIN ---
def login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito - ASB</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                if usuario == "ASB" and senha == "123":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        return False
    return True

# --- FUNÇÕES DE DADOS ---
def buscar_dados():
    try:
        temp = requests.get(f"{URL_FB}sensor/valor.json").json()
        status = requests.get(f"{URL_FB}controle/status_atual.json").json()
        return (temp if temp else "0.0"), (status if status else "OFF")
    except:
        return "0.0", "OFF"

def enviar_comando(estado):
    requests.put(f"{URL_FB}controle/led.json", json=f"LED:{estado}")
    requests.put(f"{URL_FB}controle/status_atual.json", json=estado)

# --- INTERFACE PRINCIPAL ---
if login():
    # Estilo CSS para modo escuro
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: white; }
        [data-testid="stSidebar"] { background-color: #1A1C24; }
        </style>
        """, unsafe_allow_html=True)

    # Menu Lateral
    st.sidebar.title("🏗️ ASB MENU")
    opcao = st.sidebar.radio("Navegação", ["Painel de Controle", "Gráficos e Sensores", "Falhas e Memória", "Sair"])

    if opcao == "Sair":
        st.session_state.autenticado = False
        st.rerun()

    temp_atual, status_atual = buscar_dados()

    # --- TELA 1: ACIONAMENTO ---
    if opcao == "Painel de Controle":
        st.header("🎮 Controle de Atuadores")
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Comandos")
            if st.button("🟢 LIGAR SISTEMA", use_container_width=True, type="primary"):
                enviar_comando("ON")
            if st.button("🔴 DESLIGAR SISTEMA", use_container_width=True):
                enviar_comando("OFF")
        
        with col2:
            st.subheader("Status Real")
            cor = "green" if status_atual == "ON" else "red"
            st.markdown(f"<div style='background-color:{cor}; padding:20px; border-radius:10px; text-align:center;'><b>SISTEMA: {status_atual}</b></div>", unsafe_allow_html=True)

    # --- TELA 2: TEMPERATURA E GRÁFICOS ---
    elif opcao == "Gráficos e Sensores":
        st.header("🌡️ Monitoramento de Sensores")
        
        if 'historico' not in st.session_state:
            st.session_state.historico = pd.DataFrame(columns=['Hora', 'Temp'])

        # Atualiza histórico
        nova_linha = pd.DataFrame({'Hora': [datetime.now().strftime('%H:%M:%S')], 'Temp': [float(temp_atual)]})
        st.session_state.historico = pd.concat([st.session_state.historico, nova_linha]).tail(15)

        st.metric("Temperatura Atual", f"{temp_atual} °C")
        st.line_chart(st.session_state.historico.set_index('Hora'))

    # --- TELA 3: FALHAS E MEMÓRIA ---
    elif opcao == "Falhas e Memória":
        st.header("📂 Log de Sistema e Falhas")
        st.info("Nenhuma falha crítica detectada no momento.")
        
        # Simulação de Logs
        st.table([
            {"Evento": "Sistema Iniciado", "Hora": "20:00:01", "Status": "OK"},
            {"Evento": "Conexão Firebase", "Hora": "20:00:05", "Status": "Estável"},
            {"Evento": "Leitura Sensor", "Hora": datetime.now().strftime('%H:%M:%S'), "Status": "Ativo"}
        ])
        
        st.subheader("Uso de Memória (Firebase)")
        st.progress(15) # Simulação de uso de 15% da memória

    # Atualização automática a cada 4 segundos (para alinhar com seu ESP32)
    time.sleep(4)
    st.rerun()
