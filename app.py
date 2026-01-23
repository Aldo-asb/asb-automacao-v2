import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-login { color: #00458d; font-size: 60px; font-weight: bold; text-align: center; margin-top: 50px; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO FIREBASE ---
@st.cache_resource
def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets["universe_domain"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

# --- 3. FUNÇÃO DE ENVIO DE E-MAIL (LOG DE AÇÕES) ---
def enviar_log_email(usuario, acao):
    try:
        # Puxa as configurações dos Secrets do Streamlit
        remetente = st.secrets["email_user"]
        senha_app = st.secrets["email_password"]
        destinatario = "asbautomacao@gmail.com" # Seu e-mail solicitado
        
        agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        corpo = f"""
        LOG DE AÇÃO - ASB AUTOMAÇÃO
        ----------------------------------
        USUÁRIO: {usuario}
        HORÁRIO: {agora}
        AÇÃO REALIZADA: {acao}
        ----------------------------------
        Sistema Industrial Monitorado.
        """
        
        msg = MIMEText(corpo)
        msg['Subject'] = f"ALERTA DE AÇÃO: {acao}"
        msg['From'] = remetente
        msg['To'] = destinatario
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remetente, senha_app)
            server.sendmail(remetente, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"Erro e-mail: {e}")
        return False

# --- 4. CONTROLE DE ACESSO ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<div class='titulo-login'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            if u == "admin" and p == "asb2026":
                st.session_state["autenticado"] = True
                st.session_state["user_nome"] = u
                st.rerun()
            else: st.error("Dados incorretos")
else:
    inicializar_firebase()
    st.sidebar.title("MENU ASB")
    menu = st.sidebar.radio("Navegação", ["Acionamento", "Medição", "Relatórios", "Usuários", "Diagnóstico"])
    
    # Verificação simples de conexão
    t_check = db.reference("sensor/temperatura").get()
    time.sleep(0.4)
    is_online = (t_check != db.reference("sensor/temperatura").get())

    if st.sidebar.button("LOGOUT"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- TELA 1: ACIONAMENTO (COM DISPARO DE E-MAIL) ---
    if menu == "Acionamento":
        st.header("🕹️ Acionamento e Controle")
        if not is_online: st.error("⚠️ SISTEMA OFFLINE")
        
        c1, c2 = st.columns(2)
        if c1.button("LIGAR EQUIPAMENTO"):
            db.reference("controle/led").set("ON")
            enviar_log_email(st.session_state["user_nome"], "LIGOU O EQUIPAMENTO")
            st.success("Comando enviado e E-mail de Log disparado!")
            
        if c2.button("DESLIGAR EQUIPAMENTO"):
            db.reference("controle/led").set("OFF")
            enviar_log_email(st.session_state["user_nome"], "DESLIGOU O EQUIPAMENTO")
            st.warning("Comando enviado e E-mail de Log disparado!")

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "Medição":
        st.header("🌡️ Telemetria")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        st.metric("Temperatura", f"{t} °C")
        st.metric("Umidade", f"{u} %")
        time.sleep(2)
        st.rerun()

    # --- TELA 3: RELATÓRIOS ---
    elif menu == "Relatórios":
        st.header("📊 Relatórios de Atividades")
        st.write("Histórico de ações enviadas para: asbautomacao@gmail.com")
        if st.button("Enviar Relatório de Status Agora"):
            if enviar_log_email(st.session_state["user_nome"], "SOLICITOU RELATÓRIO MANUAL"):
                st.success("E-mail enviado!")

    # --- TELA 4: USUÁRIOS ---
    elif menu == "Usuários":
        st.header("👥 Cadastro")
        st.text_input("Novo Operador")
        st.button("Salvar")

    # --- TELA 5: DIAGNÓSTICO ---
    elif menu == "Diagnóstico":
        st.header("🛠️ Diagnóstico")
        if st.button("RESETAR ESP32"):
            db.reference("controle/restart").set(True)
