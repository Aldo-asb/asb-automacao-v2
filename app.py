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

# --- 2. INTERFACE INDUSTRIAL ---
st.set_page_config(page_title="ASB INDUSTRIAL V3", layout="wide")

if inicializar_firebase():
    st.sidebar.title("🏭 ASB CONTROL")
    aba = st.sidebar.radio("Navegação", ["Controle Operacional", "Diagnóstico e Wi-Fi"])

    # LÓGICA DE HEARTBEAT (Monitor de Conexão Real)
    # Lemos o contador que o ESP32 está incrementando a cada 3s
    ref_heartbeat = db.reference("sensor/last_seen")
    val1 = ref_heartbeat.get() or 0
    time.sleep(1.2) # Pequena pausa para validar movimento
    val2 = ref_heartbeat.get() or 0
    
    # Se o valor mudou, o ESP32 está ativamente enviando dados
    is_online = (val1 != val2)

    if aba == "Controle Operacional":
        st.title("🕹️ Centro de Comando")
        
        if is_online:
            st.success("● EQUIPAMENTO CONECTADO E OPERANTE")
        else:
            st.error("○ EQUIPAMENTO DESCONECTADO OU TRAVADO")

        c1, c2 = st.columns(2)
        with c1:
            # Botões só funcionam se estiver online para evitar comandos "no vácuo"
            if st.button("🚀 LIGAR MÁQUINA", disabled=not is_online):
                db.reference("controle/led").set("ON")
            if st.button("🛑 DESLIGAR MÁQUINA", disabled=not is_online):
                db.reference("controle/led").set("OFF")
        
        with c2:
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            st.metric("🌡️ Temperatura Real", f"{t} °C")
            st.metric("💧 Umidade Relativa", f"{u} %")

    elif aba == "Diagnóstico e Wi-Fi":
        st.title("🛠️ Gestão de Comunicação")
        st.info("Configuração de Rede: **ASB AUTOMACAO WIFI** | Senha: **asbconect**")
        
        st.markdown("---")
        st.subheader("Recuperação Manual")
        if st.button("🔄 REINICIAR EQUIPAMENTO REMOTAMENTE"):
            db.reference("controle/restart").set(True)
            st.warning("Comando enviado! O ESP32 irá reiniciar em instantes.")

# Auto-refresh para manter o monitoramento de conexão em tempo real
time.sleep(2)
st.rerun()
