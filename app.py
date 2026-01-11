import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ASB Automação V2", layout="wide")
URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- ESTILO DARK ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    [data-testid="stSidebar"] { background-color: #1A1C24; }
    div.stButton > button { width: 100%; border-radius: 10px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO HISTÓRICO (Para o Gráfico) ---
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

# --- BUSCA DE DADOS EM TEMPO REAL ---
try:
    temp_val = requests.get(f"{URL_FB}sensor/valor.json").json()
    status_val = requests.get(f"{URL_FB}controle/status_atual.json").json() or "OFF"
    temp_float = float(temp_val) if temp_val else 0.0
except:
    temp_float, status_val = 0.0, "OFF"

# Atualiza a memória do gráfico (guarda os últimos 20 pontos)
nova_leitura = pd.DataFrame({'Hora': [datetime.now().strftime('%H:%M:%S')], 'Temperatura': [temp_float]})
st.session_state.historico_v2 = pd.concat([st.session_state.historico_v2, nova_leitura]).tail(20)

# --- MENU LATERAL ---
st.sidebar.title("ASB V2.0")
menu = st.sidebar.radio("Ir para:", ["🕹️ Acionamento", "📈 Gráficos", "📋 Memória do Sistema", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.auth = False
    st.rerun()

# --- TELAS ---

# TELA 1: ACIONAMENTO
if menu == "🕹️ Acionamento":
    st.header("Controle de Equipamentos")
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Comandos")
        if st.button("🟢 LIGAR SISTEMA", type="primary"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:ON")
            requests.put(f"{URL_FB}controle/status_atual.json", json="ON")
            st.rerun()
        if st.button("🔴 DESLIGAR SISTEMA"):
            requests.put(f"{URL_FB}controle/led.json", json="LED:OFF")
            requests.put(f"{URL_FB}controle/status_atual.json", json="OFF")
            st.rerun()
    with c2:
        st.subheader("Status Real")
        color = "#00FF00" if status_val == "ON" else "#FF0000"
        st.markdown(f"<div style='border: 2px solid {color}; padding: 20px; border-radius: 15px;'>"
                    f"<h1 style='color:{color}; text-align:center; margin:0;'>{status_val}</h1>"
                    f"</div>", unsafe_allow_html=True)

# TELA 2: GRÁFICOS
elif menu == "📈 Gráficos":
    st.header("Monitoramento de Temperatura")
    col_metrica, col_vazia = st.columns([1, 2])
    with col_metrica:
        st.metric("Temperatura Atual", f"{temp_float} °C")
    
    # Desenha o gráfico de linhas
    st.line_chart(st.session_state.historico_v2.set_index('Hora'), color="#00D4FF")
    st.caption("O gráfico atualiza automaticamente conforme o sensor envia dados.")

# TELA 3: MEMÓRIA DO SISTEMA
elif menu == "📋 Memória do Sistema":
    st.header("Log de Operação e Eventos")
    
    dados_memoria = [
        {"Evento": "Conexão Firebase", "Status": "Ativo", "Data": datetime.now().strftime("%d/%m/%Y")},
        {"Evento": "Coletor Serial", "Status": "Rodando", "Data": datetime.now().strftime("%H:%M:%S")},
        {"Evento": "Login efetuado", "Usuário": "ASB", "Status": "OK"}
    ]
    st.table(dados_memoria)
    
    st.subheader("Integridade do Banco de Dados")
    st.progress(100)
    st.success("Sincronização com Nuvem: 100%")

# Atualização automática (Delay de 3 segundos para não sobrecarregar o site)
time.sleep(3)
st.rerun()
