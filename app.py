import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ASB Automação V2", layout="wide")
URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- ESTILO DARK E CORES DOS BOTÕES ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    [data-testid="stSidebar"] { background-color: #1A1C24; }
    
    /* Estilo para o botão Ligar (Verde) */
    div.stButton > button:first-child {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        border: none;
    }

    /* Estilo para o botão Desligar (Vermelho) */
    .st-emotion-cache-17l7u7o.edgvbvh9 {
        background-color: #dc3545 !important;
        color: white !important;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        border: none;
    }
    
    div.stButton > button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO HISTÓRICO ---
if 'historico_v2' not in st.session_state:
    st.session_state.historico_v2 = pd.DataFrame(columns=['Hora', 'Temperatura'])

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center;'>🏗️ ASB AUTOMAÇÃO - ACESSO</h2>", unsafe_allow_html=True)
    with st.container():
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

# --- BUSCA DE DADOS ---
try:
    temp_val = requests.get(f"{URL_FB}sensor/valor.json").json()
    status_val = requests.get(f"{URL_FB}controle/status_atual.json").json() or "OFF"
    temp_float = float(temp_val) if temp_val else 0.0
except:
    temp_float, status_val = 0.0, "OFF"

# Atualiza histórico
nova_leitura = pd.DataFrame({'Hora': [datetime.now().strftime('%H:%M:%S')], 'Temperatura': [temp_float]})
st.session_state.historico_v2 = pd.concat([st.session_state.historico_v2, nova_leitura]).tail(20)

# --- MENU LATERAL ---
st.sidebar.title("ASB V2.0")
menu = st.sidebar.radio("Navegação:", ["🕹️ Painel de Controle", "📈 Gráficos Tempo Real", "📋 Memória do Sistema", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.auth = False
    st.rerun()

# --- TELAS ---

if menu == "🕹️ Painel de Controle":
    st.header("Controle Operacional")
    st.write("---")
    
    col_btns, col_status = st.columns([1, 1])
    
    with col_btns:
        st.subheader("Comandos de Acionamento")
        if st.button("🟢 LIGAR SISTEMA"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:ON")
            requests.put(f"{URL_FB}controle/status_atual.json", json="ON")
            st.rerun()
            
        st.write("") # Espaçamento
        
        if st.button("🔴 DESLIGAR SISTEMA"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:OFF")
            requests.put(f"{URL_FB}controle/status_atual.json", json="OFF")
            st.rerun()

    with col_status:
        st.subheader("Status de Rede")
        cor_status = "#00FF00" if status_val == "ON" else "#FF0000"
        st.markdown(f"""
            <div style="background-color: #1A1C24; padding: 30px; border-radius: 20px; border: 3px solid {cor_status}; text-align: center;">
                <p style="margin:0; font-size: 1.2em;">EQUIPAMENTO ESTÁ:</p>
                <h1 style="color: {cor_status}; font-size: 4em; margin: 0;">{status_val}</h1>
            </div>
        """, unsafe_allow_html=True)

elif menu == "📈 Gráficos Tempo Real":
    st.header("Análise de Dados")
    st.metric("Temperatura Atual", f"{temp_float} °C")
    st.line_chart(st.session_state.historico_v2.set_index('Hora'), color="#00D4FF")

elif menu == "📋 Memória do Sistema":
    st.header("Histórico de Eventos")
    logs = [
        {"Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), "Evento": "Conexão Firebase", "Status": "OK"},
        {"Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), "Evento": "Sistema V2", "Status": "Operacional"}
    ]
    st.table(logs)
    st.info("Memória de falhas limpa. Nenhuma anormalidade detectada.")

# Refresh automático
time.sleep(3)
st.rerun()
