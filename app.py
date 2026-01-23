import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time

# --- 1. CONEXÃO FIREBASE (PRESERVADA) ---
def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            creds = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets["universe_domain"]
            }
            cred = credentials.Certificate(creds)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'
            })
            return True
        except: return False
    return True

# --- 2. LAYOUT ORIGINAL PRESERVADO ---
st.set_page_config(page_title="SISTEMA ASB INDUSTRIAL", layout="wide")

# Mantendo o CSS original que você já tinha
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

if inicializar_firebase():
    # --- LOGICA DE STATUS (EM SEGUNDO PLANO) ---
    ref_heartbeat = db.reference("sensor/last_seen")
    v1 = ref_heartbeat.get() or 0
    time.sleep(0.5)
    v2 = ref_heartbeat.get() or 0
    is_online = (v1 != v2)

    # --- TELA PRINCIPAL (IDÊNTICA À ANTERIOR) ---
    st.title("SISTEMA ASB INDUSTRIAL")
    
    # Pequeno indicador de status discreto no topo, sem mudar o layout
    if is_online:
        st.caption("🟢 Equipamento Conectado")
    else:
        st.caption("🔴 Equipamento Offline")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Controle de Atuadores")
        if st.button("LIGAR"):
            db.reference("controle/led").set("ON")
        if st.button("DESLIGAR"):
            db.reference("controle/led").set("OFF")

    with col2:
        st.subheader("Monitoramento")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        st.metric("Temperatura", f"{t} °C")
        st.metric("Umidade", f"{u} %")

    # --- RECURSOS ADICIONAIS (CADASTROS E RELATÓRIOS) ---
    st.markdown("---")
    with st.expander("Relatórios e Histórico"):
        st.write("Dados históricos de operação...")
        # Aqui você pode manter suas funções de dataframe/gráficos anteriores
    
    with st.expander("Administração e Usuários"):
        st.write("Configurações de acesso...")
        # Botão de Reset escondido aqui para não poluir o visual
        if st.button("Reiniciar Hardware (Diagnóstico)"):
            db.reference("controle/restart").set(True)

# Auto-refresh
time.sleep(2)
st.rerun()
