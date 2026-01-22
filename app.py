import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONEXÃO FIREBASE (DESIGN REFORÇADO) ---
def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # Tenta carregar das Secrets (Para acesso 4G/Nuvem)
            if "firebase_creds" in st.secrets:
                creds_dict = json.loads(st.secrets["firebase_creds"])
                cred = credentials.Certificate(creds_dict)
            else:
                # Tenta carregar localmente (Para o seu computador)
                cred = credentials.Certificate("chave_firebase.json..json")
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'
            })
            return True
        except Exception as e:
            st.error(f"Erro de Inicialização: {e}")
            return False
    return True

# --- 2. CONFIGURAÇÕES VISUAIS E CSS ---
st.set_page_config(page_title="ASB INDUSTRIAL", layout="wide", page_icon="📶")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3.5em; font-weight: bold; background-color: #1f2937; color: white; border: 1px solid #4a4a4a;}
    .stButton>button:hover { border-color: #00ff00; color: #00ff00; }
    .status-container { text-align: center; padding: 25px; background-color: #1f2937; border-radius: 15px; border: 2px solid #374151; }
    .status-text { color: #ffffff !important; font-size: 24px !important; font-weight: bold !important; display: block; margin-top: 10px; }
    .report-card { background-color: #2d3748; padding: 15px; border-radius: 10px; border-left: 8px solid #4ade80; margin-bottom: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE APOIO ---
def get_hora_brasil():
    return (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")

def enviar_email_relatorio(destinatario, assunto, corpo):
    try:
        remetente, senha = "asbautomacao@gmail.com", "qmvm fnsn afok jejs"
        msg = MIMEMultipart()
        msg['From'] = remetente; msg['To'] = destinatario; msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg); server.quit()
        return True
    except: return False

# --- 4. EXECUÇÃO PRINCIPAL ---
if inicializar_firebase():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    # --- LOGIN ---
    if not st.session_state['autenticado']:
        st.markdown("<h1 style='text-align:center;'>ASB AUTOMAÇÃO</h1>", unsafe_allow_html=True)
        with st.form("Login"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA"):
                if u == "admin" and s == "asb123":
                    st.session_state.update({'autenticado':True, 'usuario':"ADMIN MESTRE", 'role':"admin"})
                    st.rerun()
                else:
                    usuarios_db = db.reference("config/usuarios").get()
                    if isinstance(usuarios_db, dict):
                        for uid, dados in usuarios_db.items():
                            if dados.get('user') == u and dados.get('pass') == s:
                                st.session_state.update({'autenticado':True, 'usuario':u, 'role':"cliente"})
                                st.rerun()
                    st.error("Credenciais inválidas")
    
    # --- APP LOGADO ---
    else:
        st.sidebar.markdown(f"<h2 style='color:#00ff00;'>Olá, {st.session_state['usuario']}</h2>", unsafe_allow_html=True)
        menu = ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"]
        if st.session_state['role'] == "admin": menu.append("👤 GESTÃO")
        aba = st.sidebar.radio("MENU", menu)
        
        envio_auto = st.sidebar.toggle("E-mail Automático", False)
        email_destino = st.sidebar.text_input("E-mail Alertas", "asbautomacao@gmail.com")

        if st.sidebar.button("SAIR"):
            st.session_state['autenticado'] = False
            st.rerun()

        # TELA DE COMANDO
        if aba == "🕹️ COMANDO":
            st.title("🕹️ CENTRO DE COMANDO")
            c1, c2 = st.columns(2)
            
            with c1:
                if st.button("LIGAR MÁQUINA"):
                    db.reference("controle/led").set("ON")
                    agora = get_hora_brasil()
                    t = db.reference("sensor/temperatura").get() or "0"
                    db.reference("logs/operacao").push({"acao": f"LIGOU ({st.session_state['usuario']})", "temp": t, "data": agora})
                    if envio_auto: enviar_email_relatorio(email_destino, "ASB - LIGADO", f"Ligado por: {st.session_state['usuario']}\nData: {agora}")
                    st.toast("Comando Enviado!")

                if st.button("DESLIGAR MÁQUINA"):
                    db.reference("controle/led").set("OFF")
                    agora = get_hora_brasil()
                    t = db.reference("sensor/temperatura").get() or "0"
                    db.reference("logs/operacao").push({"acao": f"DESLIGOU ({st.session_state['usuario']})", "temp": t, "data": agora})
                    if envio_auto: enviar_email_relatorio(email_destino, "ASB - DESLIGADO", f"Desligado por: {st.session_state['usuario']}\nData: {agora}")
                    st.toast("Máquina Parada!")

            with c2:
                status_placeholder = st.empty()
                @st.fragment(run_every=3)
                def monitor_led():
                    estado = db.reference("controle/led").get() or "OFF"
                    cor, txt = ("🟢", "LIGADA") if "ON" in str(estado).upper() else ("🔴", "DESLIGADA")
                    status_placeholder.markdown(f"<div class='status-container'><span style='font-size:50px;'>{cor}</span><br><span class='status-text'>MÁQUINA {txt}</span></div>", unsafe_allow_html=True)
                monitor_led()

        # TELA DE TELEMETRIA
        elif aba == "📈 TELEMETRIA":
            st.title("📈 MONITORAMENTO WI-FI")
            m1, m2 = st.columns(2)
            p1, p2 = m1.empty(), m2.empty()
            @st.fragment(run_every=4)
            def monitor_sensores():
                t = db.reference('sensor/temperatura').get() or "0"
                u = db.reference('sensor/umidade').get() or "0"
                p1.metric("🌡️ TEMPERATURA", f"{t} °C")
                p2.metric("💧 UMIDADE", f"{u} %")
            monitor_sensores()

        # TELA DE RELATÓRIOS
        elif aba == "📊 RELATÓRIOS":
            st.title("📊 HISTÓRICO DE OPERAÇÃO")
            if st.button("🗑️ LIMPAR LOGS"):
                db.reference("logs/operacao").delete(); st.rerun()
            logs = db.reference("logs/operacao").get()
            if logs:
                for id, info in reversed(list(logs.items())):
                    st.markdown(f"<div class='report-card'><small>{info.get('data')}</small><br><b>{info.get('acao')}</b> | Temp: {info.get('temp')}°C</div>", unsafe_allow_html=True)

        # TELA DE GESTÃO
        elif aba == "👤 GESTÃO":
            st.title("👤 GESTÃO DE USUÁRIOS")
            with st.form("Novo"):
                nu, ns = st.text_input("Usuário"), st.text_input("Senha")
                if st.form_submit_button("CADASTRAR"):
                    db.reference("config/usuarios").push({"user": nu, "pass": ns}); st.success("Cadastrado!"); st.rerun()
            users = db.reference("config/usuarios").get()
            if users:
                for uid, d in users.items():
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"👤 {d.get('user')}")
                    if c2.button("Excluir", key=uid): db.reference(f"config/usuarios/{uid}").delete(); st.rerun()
