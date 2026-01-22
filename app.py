import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json

# --- 1. CONEXÃO DIRETA CORRIGIDA ---
def conectar():
    if not firebase_admin._apps:
        try:
            # Pega as chaves campo a campo dos Secrets
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
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            return False
    return True

# --- 2. INTERFACE ---
st.set_page_config(page_title="ASB INDUSTRIAL", layout="wide")

if conectar():
    st.title("🏭 ASB AUTOMAÇÃO")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🕹️ Controles")
        if st.button("LIGAR MÁQUINA"):
            db.reference("controle/led").set("ON")
            st.toast("Ligando...")
            
        if st.button("DESLIGAR MÁQUINA"):
            db.reference("controle/led").set("OFF")
            st.toast("Desligando...")

    with c2:
        st.subheader("📊 Status")
        status_area = st.empty()
        
        @st.fragment(run_every=3)
        def monitor():
            estado = db.reference("controle/led").get() or "OFF"
            txt = "🟢 LIGADA" if "ON" in str(estado).upper() else "🔴 DESLIGADA"
            status_area.markdown(f"## {txt}")
            
            t = db.reference("sensor/temperatura").get() or "0"
            u = db.reference("sensor/umidade").get() or "0"
            st.metric("🌡️ Temp", f"{t} °C")
            st.metric("💧 Umid", f"{u} %")
        monitor()
