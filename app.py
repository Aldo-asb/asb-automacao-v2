import streamlit as st
import requests
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ASB AUTOMACÃO V2", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- ESTILO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
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
aba = st.sidebar.radio("Ir para:", ["🕹️ Painel de Controle", "📈 Monitoramento"])

# --- FRAGMENTO PARA ATUALIZAÇÃO DO STATUS (SÓ ATUALIZA O QUADRADO DO STATUS) ---
@st.fragment(run_every=3)
def atualizar_status_led():
    led = fb_get("controle/led", "OFF")
    led_str = str(led).upper()
    cor_led = "🟢" if "ON" in led_str else "🔴"
    st.markdown(f"""
        <div style='text-align: center; border: 3px solid #444; padding: 25px; border-radius: 15px;'>
            <h2 style='margin:0; color: white;'>Status Atual</h2>
            <h1 style='margin:0;'>{cor_led} {led_str}</h1>
        </div>
    """, unsafe_allow_html=True)

# --- FRAGMENTO PARA ATUALIZAÇÃO DA TEMPERATURA (SÓ ATUALIZA A MÉTRICA) ---
@st.fragment(run_every=2)
def atualizar_temperatura():
    temperatura = fb_get("sensor/temperatura")
    status = fb_get("sensor/status", "ERRO")
    if status == "OK" and isinstance(temperatura, (int, float)):
        st.metric("Temperatura Atual", f"{temperatura:.2f} °C")
    else:
        st.error("⚠️ Sensor Offline")

# --- LÓGICA DE TELAS ---

if aba == "🕹️ Painel de Controle":
    st.header("🕹️ Painel de Controle")
    st.divider()
    
    col_btn, col_view = st.columns(2)
    
    with col_btn:
        st.subheader("Comandos")
        if st.button("🟢 LIGAR SISTEMA"):
            fb_set("controle/led", "ON")
            # Aqui não usamos rerun para não piscar, o fragmento cuidará de mostrar a mudança
            st.toast("Comando Ligar enviado!")

        if st.button("🔴 DESLIGAR SISTEMA"):
            fb_set("controle/led", "OFF")
            st.toast("Comando Desligar enviado!")

    with col_view:
        atualizar_status_led()

elif aba == "📈 Monitoramento":
    st.header("📈 Monitoramento de Temperatura")
    st.divider()
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        atualizar_temperatura()
            
    with c2:
        st.info("Monitoramento em tempo real ativado via Fragmentos (Sem recarregar a tela).")
