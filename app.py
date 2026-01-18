import streamlit as st
import requests
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ASB AUTOMACÃO V2", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- ESTILO PARA LIMPEZA DE TELA ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    /* Esconde elementos que podem causar poluição visual entre trocas */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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

# --- MENU LATERAL ---
st.sidebar.header("⚙️ NAVEGAÇÃO ASB")
aba = st.sidebar.radio("Ir para:", ["🕹️ Painel de Controle", "📈 Gráfico de Temperatura"])

# --- LÓGICA DE TROCA DE TELA (USANDO IF/ELSE E EMPTY) ---

# TELA 1: PAINEL DE CONTROLE
if aba == "🕹️ Painel de Controle":
    # Todo o conteúdo aqui dentro SÓ existe nesta condição
    st.header("🕹️ Painel de Controle")
    st.write("Gerencie o acionamento dos dispositivos abaixo.")
    st.divider()
    
    led = fb_get("controle/led", "OFF")
    
    col_btn, col_view = st.columns(2)
    
    with col_btn:
        st.subheader("Comandos")
        if st.button("🟢 LIGAR SISTEMA"):
            fb_set("controle/led", "ON")
            st.rerun()

        if st.button("🔴 DESLIGAR SISTEMA"):
            fb_set("controle/led", "OFF")
            st.rerun()

    with col_view:
        st.subheader("Status")
        led_str = str(led).upper()
        cor_led = "🟢" if "ON" in led_str else "🔴"
        st.markdown(f"""
            <div style='text-align: center; border: 3px solid #444; padding: 25px; border-radius: 15px;'>
                <h1 style='margin:0;'>{cor_led} {led_str}</h1>
            </div>
        """, unsafe_allow_html=True)

# TELA 2: MONITORAMENTO
elif aba == "📈 Gráfico de Temperatura":
    # Todo o conteúdo aqui dentro DESAPARECE quando você volta para o controle
    st.header("📈 Monitoramento de Temperatura")
    st.write("Leitura em tempo real do sensor DHT11.")
    st.divider()
    
    temperatura = fb_get("sensor/temperatura")
    status = fb_get("sensor/status", "ERRO")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        if status == "OK" and isinstance(temperatura, (int, float)):
            st.metric("Temperatura Atual", f"{temperatura:.2f} °C")
        else:
            st.error("⚠️ Sensor Offline")
            
    with c2:
        st.info("O sistema está monitorando as variações térmicas enviadas pelo coletor local.")

# --- ATUALIZAÇÃO ---
time.sleep(2)
st.rerun()
