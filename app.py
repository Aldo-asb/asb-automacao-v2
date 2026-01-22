import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONEXÃO FIREBASE (VIA SECRETS TOML) ---
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
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            return False
    return True

# --- 2. DESIGN E CSS INDUSTRIAL ---
st.set_page_config(page_title="ASB INDUSTRIAL V3", layout="wide", page_icon="🏭")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 5px; height: 3.5em; font-weight: bold; 
        background-color: #1f2937; color: white; border: 1px solid #4a4a4a;
    }
    .stButton>button:hover { border-color: #00ff00; color: #00ff00; background-color: #111827; }
    .status-container { 
        text-align: center; padding: 30px; background-color: #1f2937; 
        border-radius: 15px; border: 2px solid #374151; margin-top: 10px; 
    }
    .status-text { color: #ffffff !important; font-size: 24px !important; font-weight: bold !important; display: block; margin-top: 10px; }
    .report-card { 
        background-color: #2d3748; padding: 15px; border-radius: 8px; 
        border-left: 5px solid #4ade80; margin-bottom: 10px; color: white; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---
def get_hora_brasil():
    return (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")

def enviar_email_relatorio(destinatario, assunto, corpo):
    try:
        remetente = "asbautomacao@gmail.com"
        senha = "qmvm fnsn afok jejs" 
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- 4. LÓGICA DO SISTEMA ---
if inicializar_firebase():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    if not st.session_state['autenticado']:
        st.markdown("<h1 style='text-align:center; color:#00ff00;'>ASB AUTOMAÇÃO INDUSTRIAL</h1>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            with st.form("Login"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR SISTEMA"):
                    if u == "admin" and s == "asb123":
                        st.session_state.update({'autenticado':True, 'usuario':"ADMIN", 'role':"admin"})
                        st.rerun()
                    else:
                        usuarios_db = db.reference("config/usuarios").get()
                        if isinstance(usuarios_db, dict):
                            for uid, dados in usuarios_db.items():
                                if dados.get('user') == u and dados.get('pass') == s:
                                    st.session_state.update({'autenticado':True, 'usuario':u, 'role':"cliente"})
                                    st.rerun()
                        st.error("Credenciais inválidas")
    
    else:
        # MENU LATERAL
        st.sidebar.markdown(f"<h2 style='color:#00ff00; text-align:center;'>🏭 ASB INDUSTRIAL</h2>", unsafe_allow_html=True)
        menu = ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"]
        if st.session_state['role'] == "admin": menu.append("👤 GESTÃO")
        aba = st.sidebar.radio("NAVEGAÇÃO", menu)

        envio_auto = st.sidebar.toggle("E-mail Automático", True)
        email_destino = st.sidebar.text_input("E-mail de Alerta", "asbautomacao@gmail.com")

        if st.sidebar.button("SAIR DO SISTEMA"):
            st.session_state['autenticado'] = False
            st.rerun()

        # ABA: COMANDO
        if aba == "🕹️ COMANDO":
            st.title("🕹️ CENTRO DE COMANDO")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🚀 LIGAR SISTEMA"):
                    db.reference("controle/led").set("ON")
                    agora = get_hora_brasil()
                    t = db.reference("sensor/temperatura").get() or "0"
                    db.reference("logs/operacao").push({"acao": "LIGOU", "user": st.session_state['usuario'], "temp": t, "data": agora})
                    if envio_auto:
                        enviar_email_relatorio(email_destino, "ASB: SISTEMA LIGADO", f"Acionado por {st.session_state['usuario']} às {agora}.\nTemp: {t}°C")
                    st.toast("Ligado!")

                if st.button("🛑 DESLIGAR SISTEMA"):
                    db.reference("controle/led").set("OFF")
                    agora = get_hora_brasil()
                    t = db.reference("sensor/temperatura").get() or "0"
                    db.reference("logs/operacao").push({"acao": "DESLIGOU", "user": st.session_state['usuario'], "temp": t, "data": agora})
                    if envio_auto:
                        enviar_email_relatorio(email_destino, "ASB: SISTEMA DESLIGADO", f"Desligado por {st.session_state['usuario']} às {agora}.")
                    st.toast("Desligado!")

            with c2:
                status_placeholder = st.empty()
                @st.fragment(run_every=2)
                def monitor_led():
                    estado = db.reference("controle/led").get() or "OFF"
                    cor, texto = ("🟢", "EM OPERAÇÃO") if "ON" in str(estado).upper() else ("🔴", "DESATIVADA")
                    status_placeholder.markdown(f"<div class='status-container'><span style='font-size:60px;'>{cor}</span><span class='status-text'>MÁQUINA {texto}</span></div>", unsafe_allow_html=True)
                monitor_led()

        # ABA: TELEMETRIA
        elif aba == "📈 TELEMETRIA":
            st.title("📈 TELEMETRIA")
            m1, m2 = st.columns(2)
            t_placeholder = m1.empty()
            u_placeholder = m2.empty()
            @st.fragment(run_every=3)
            def atualizar_metricas():
                temp = db.reference('sensor/temperatura').get() or '0'
                umid = db.reference('sensor/umidade').get() or '0'
                t_placeholder.metric("🌡️ TEMPERATURA", f"{temp} °C")
                u_placeholder.metric("💧 UMIDADE", f"{umid} %")
            atualizar_metricas()

        # ABA: RELATÓRIOS
        elif aba == "📊 RELATÓRIOS":
            st.title("📊 HISTÓRICO")
            if st.button("🗑️ LIMPAR LOGS"):
                db.reference("logs/operacao").delete()
                st.rerun()
            logs = db.reference("logs/operacao").get()
            if logs:
                for id, info in reversed(list(logs.items())):
                    st.markdown(f"<div class='report-card'><small>📅 {info.get('data')}</small><br><b>AÇÃO: {info.get('acao')}</b> | {info.get('user')} | {info.get('temp')}°C</div>", unsafe_allow_html=True)

        # ABA: GESTÃO
        elif aba == "👤 GESTÃO":
            st.title("👤 GESTÃO DE USUÁRIOS")
            with st.form("Novo"):
                nu, ns = st.text_input("Usuário"), st.text_input("Senha")
                if st.form_submit_button("CADASTRAR"):
                    db.reference("config/usuarios").push({"user": nu, "pass": ns})
                    st.success("Cadastrado!"); st.rerun()
