import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime, timedelta

# --- 1. CONEXÃO DIRETA ---
def conectar():
    if not firebase_admin._apps:
        try:
            # Pega as chaves direto dos segredos do Streamlit
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
                "client_x509_cert_url": st.secrets["client_x509_cert_url"]
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

# --- 2. INTERFACE SIMPLIFICADA ---
st.set_page_config(page_title="ASB INDUSTRIAL", layout="wide")

if conectar():
    st.title("🏭 ASB AUTOMAÇÃO INDUSTRIAL")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕹️ Controles")
        if st.button("LIGAR MÁQUINA"):
            db.reference("controle/led").set("ON")
            st.success("Comando enviado: LIGAR")
            
        if st.button("DESLIGAR MÁQUINA"):
            db.reference("controle/led").set("OFF")
            st.warning("Comando enviado: DESLIGAR")

    with col2:
        st.subheader("📊 Status em Tempo Real")
        status_area = st.empty()
        
        # Fragmento para atualizar só o status sem carregar a página toda
        @st.fragment(run_every=3)
        def check_status():
            estado = db.reference("controle/led").get() or "OFF"
            cor = "🟢 LIGADA" if "ON" in str(estado).upper() else "🔴 DESLIGADA"
            status_area.markdown(f"## Status: {cor}")
            
            t = db.reference("sensor/temperatura").get() or "0"
            u = db.reference("sensor/umidade").get() or "0"
            st.metric("🌡️ Temperatura", f"{t} °C")
            st.metric("💧 Umidade", f"{u} %")
        
        check_status()
