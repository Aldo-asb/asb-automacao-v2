import streamlit as st
import requests
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- DESIGN INDUSTRIAL ASB ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3.5em; font-weight: bold; background-color: #1f2937; color: white; border: 1px solid #4a4a4a;}
    .stButton>button:hover { border-color: #00ff00; color: #00ff00; }
    [data-testid="stMetricValue"] { color: #00ff00; font-family: 'Courier New', monospace; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 2px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def fb_get(path, default=None):
    try:
        r = requests.get(f"{URL_FB}{path}.json", timeout=2)
        return r.json() if r.ok else default
    except: return default

def fb_set(path, value):
    try: requests.put(f"{URL_FB}{path}.json", json=value, timeout=2)
    except: pass

def fb_post(path, data):
    try: requests.post(f"{URL_FB}{path}.json", json=data, timeout=2)
    except: pass

# --- FUNÇÃO DE ENVIO DE E-MAIL REAL ---
def enviar_email_relatorio(destinatario, assunto, corpo):
    try:
        remetente = "asbautomacao@gmail.com"
        # SENHA DE APP GERADA PELO ALDO:
        senha_app = "qmvm fnsn afok jejs" 

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align:center;'>ASB AUTOMAÇÃO</h1>", unsafe_allow_html=True)
    with st.form("Login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("ACESSAR"):
            if u == "admin" and s == "asb123":
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = u
                log_acesso = {"usuario": u, "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
                fb_post("logs/acessos", log_acesso)
                st.rerun()
            else: st.error("Erro")
else:
    # --- MENU LATERAL ---
    st.sidebar.title("ASB INDUSTRIAL")
    aba = st.sidebar.radio("MENU", ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"])
    
    if st.sidebar.button("SAIR"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- TELAS ---
    if aba == "🕹️ COMANDO":
        st.title("🕹️ CENTRO DE COMANDO")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("LIGAR MÁQUINA"):
                fb_set("controle/led", "ON")
                fb_post("logs/operacao", {"acao": "LIGOU", "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})
                st.toast("Máquina Iniciada")
            if st.button("DESLIGAR MÁQUINA"):
                fb_set("controle/led", "OFF")
                fb_post("logs/operacao", {"acao": "DESLIGOU", "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})
                st.toast("Máquina Parada")
        with c2:
            @st.fragment(run_every=3)
            def show_status():
                led = fb_get("controle/led", "OFF")
                cor = "🟢" if "ON" in str(led).upper() else "🔴"
                st.markdown(f"<div style='border:2px solid #374151;padding:20px;text-align:center;'><h2>{cor} {led}</h2></div>", unsafe_allow_html=True)
            show_status()

    elif aba == "📈 TELEMETRIA":
        st.title("📈 MONITORAMENTO REALTIME")
        @st.fragment(run_every=2)
        def show_temp():
            t = fb_get("sensor/temperatura")
            s = fb_get("sensor/status", "ERRO")
            if s == "OK": st.metric("TEMPERATURA", f"{t} °C")
            else: st.error("SENSOR OFFLINE")
        show_temp()

    elif aba == "📊 RELATÓRIOS":
        st.title("📊 RELATÓRIOS E LOGS")
        tab1, tab2 = st.tabs(["Histórico Operacional", "Log de Acessos"])
        
        with tab1:
            st.subheader("Registros da Máquina")
            logs = fb_get("logs/operacao", {})
            texto_relatorio = "RELATÓRIO DE OPERAÇÃO ASB AUTOMAÇÃO\n\n"
            if logs:
                for id, info in reversed(list(logs.items())):
                    linha = f"🕒 {info['data']} - {info['acao']}"
                    st.write(linha)
                    texto_relatorio += linha + "\n"
            st.divider()
            st.subheader("📧 Enviar para Cliente")
            email_cliente = st.text_input("Digite o e-mail do destinatário:")
            if st.button("ENVIAR AGORA"):
                if email_cliente:
                    if enviar_email_relatorio(email_cliente, "Relatório Operacional ASB", texto_relatorio):
                        st.success(f"Relatório enviado com sucesso para {email_cliente}!")
                else:
                    st.warning("Por favor, digite um e-mail válido.")

        with tab2:
            st.subheader("Usuários que acessaram")
            acessos = fb_get("logs/acessos", {})
            if acessos:
                for id, info in reversed(list(acessos.items())):
                    st.write(f"👤 {info['usuario']} - {info['data']}")
