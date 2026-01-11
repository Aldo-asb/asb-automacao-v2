import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ASB Automação V2", layout="wide")
URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- ESTILO DARK E BOTÕES PROFISSIONAIS ---
st.markdown("""
    <style>
    /* Fundo geral do App */
    .stApp { background-color: #0E1117; color: white; }
    [data-testid="stSidebar"] { background-color: #1A1C24; }
    
    /* Estilização Individual dos Botões via Ordem */
    /* Botão LIGAR (Verde) */
    div.stButton > button:first-child {
        background-color: transparent !important;
        color: #28a745 !important;
        border: 2px solid #28a745 !important;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #28a745 !important;
        color: white !important;
    }

    /* Botão DESLIGAR (Vermelho) */
    /* Localizando o segundo botão da coluna de comandos */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
    }
    
    /* Ajuste específico para o botão de desligar para não herdar o verde */
    section[data-testid="stVerticalBlock"] div.stButton:nth-of-type(2) button {
        background-color: transparent !important;
        color: #dc3545 !important;
        border: 2px solid #dc3545 !important;
    }
    section[data-testid="stVerticalBlock"] div.stButton:nth-of-type(2) button:hover {
        background-color: #dc3545 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO HISTÓRICO ---
if 'historico_v2' not in st.session_state:
    st.session_state.historico_v2 = pd.DataFrame(columns=['Hora', 'Temperatura'])

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🏗️ ASB V2</h1>", unsafe_allow_html=True)
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
                    st.error("Acesso Negado")
    st.stop()

# --- BUSCA DE DADOS ---
try:
    temp_val = requests.get(f"{URL_FB}sensor/valor.json").json()
    status_val = requests.get(f"{URL_FB}controle/status_atual.json").json() or "OFF"
    temp_float = float(temp_val) if temp_val else 0.0
except:
    temp_float, status_val = 0.0, "OFF"

# Atualiza histórico para o gráfico
nova_leitura = pd.DataFrame({'Hora': [datetime.now().strftime('%H:%M:%S')], 'Temperatura': [temp_float]})
st.session_state.historico_v2 = pd.concat([st.session_state.historico_v2, nova_leitura]).tail(20)

# --- MENU LATERAL ---
st.sidebar.title("MENU ASB V2")
menu = st.sidebar.radio("Navegação:", ["🕹️ Painel de Controle", "📈 Gráficos", "📋 Memória", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.auth = False
    st.rerun()

# --- TELAS ---

if menu == "🕹️ Painel de Controle":
    st.header("Controle Operacional")
    st.write("---")
    
    col_btns, col_status = st.columns([1, 1])
    
    with col_btns:
        st.subheader("Comandos")
        # Botão 1
        if st.button("🟢 LIGAR SISTEMA"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:ON")
            requests.put(f"{URL_FB}controle/status_atual.json", json="ON")
            st.rerun()
            
        st.write(" ") # Espaço
        
        # Botão 2
        if st.button("🔴 DESLIGAR SISTEMA"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:OFF")
            requests.put(f"{URL_FB}controle/status_atual.json", json="OFF")
            st.rerun()

    with col_status:
        st.subheader("Status Real-Time")
        cor_status = "#00FF00" if status_val == "ON" else "#FF0000"
        st.markdown(f"""
            <div style="background-color: #1A1C24; padding: 30px; border-radius: 20px; border: 2px solid {cor_status}; text-align: center;">
                <p style="margin:0; font-size: 1.2em; color: white;">SISTEMA ESTÁ:</p>
                <h1 style="color: {cor_status}; font-size: 4em; margin: 0;">{status_val}</h1>
            </div>
        """, unsafe_allow_html=True)

elif menu == "📈 Gráficos":
    st.header("Monitoramento de Temperatura")
    st.metric("Leitura Atual", f"{temp_float} °C")
    st.line_chart(st.session_state.historico_v2.set_index('Hora'), color="#00D4FF")

elif menu == "📋 Memória":
    st.header("Log do Sistema")
    logs = [
        {"Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), "Evento": "Sistema V2 Online", "Status": "Ativo"},
        {"Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), "Evento": "Banco de Dados", "Status": "Sincronizado"}
    ]
    st.table(logs)

# Refresh automático para manter dados vivos
time.sleep(3)
st.rerun()
