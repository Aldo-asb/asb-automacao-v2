import streamlit as st
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- FUNÇÃO HORÁRIO DE BRASÍLIA ---
def get_hora_brasil():
    # Ajuste manual para UTC-3
    return (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")

# --- DESIGN E CORREÇÃO DE CORES ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3.5em; font-weight: bold; background-color: #1f2937; color: white; border: 1px solid #4a4a4a;}
    
    /* Card de Status da Máquina */
    .status-container {
        text-align: center;
        padding: 30px;
        background-color: #1f2937;
        border-radius: 15px;
        border: 2px solid #374151;
        margin-top: 10px;
    }
    .status-text {
        color: #ffffff !important; 
        font-size: 24px !important;
        font-weight: bold !important;
        display: block;
        margin-top: 10px;
    }
    
    /* Card de Relatório */
    .report-card { 
        background-color: #2d3748; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 10px solid #4ade80; 
        margin-bottom: 15px; 
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES BANCO DE DADOS ---
def fb_get(path, default=None):
    try:
        r = requests.get(f"{URL_FB}{path}.json", timeout=3)
        return r.json() if r.ok and r.json() is not None else default
    except: return default

def fb_set(path, value):
    try: requests.put(f"{URL_FB}{path}.json", json=value, timeout=3)
    except: pass

def fb_post(path, data):
    try: requests.post(f"{URL_FB}{path}.json", json=data, timeout=3)
    except: pass

def fb_delete(path):
    try: requests.delete(f"{URL_FB}{path}.json", timeout=3)
    except: pass

def enviar_email_relatorio(destinatario, assunto, corpo):
    try:
        remetente, senha = "asbautomacao@gmail.com", "qmvm fnsn afok jejs"
        msg = MIMEMultipart(); msg['From'] = remetente; msg['To'] = destinatario; msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(remetente, senha); server.send_message(msg); server.quit()
        return True
    except: return False

# --- LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align:center;'>ASB AUTOMAÇÃO</h1>", unsafe_allow_html=True)
    with st.form("Login"):
        u, s = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.form_submit_button("ACESSAR SISTEMA"):
            if u == "admin" and s == "asb123":
                st.session_state.update({'autenticado':True, 'usuario':"ADMIN", 'role':"admin"})
                st.rerun()
            else:
                db = fb_get("config/usuarios", {})
                if isinstance(db, dict):
                    for uid, d in db.items():
                        if d.get('user') == u and d.get('pass') == s:
                            st.session_state.update({'autenticado':True, 'usuario':u, 'role':"cliente"})
                            st.rerun()
                st.error("Credenciais inválidas")
else:
    # --- SIDEBAR ---
    st.sidebar.title(f"Olá, {st.session_state['usuario']}")
    menu = ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"]
    if st.session_state['role'] == "admin": menu.append("👤 GESTÃO")
    aba = st.sidebar.radio("MENU", menu)
    
    envio_auto = st.sidebar.toggle("E-mail Automático", False)
    email_destino = st.sidebar.text_input("E-mail Destino", "asbautomacao@gmail.com")
    
    if st.sidebar.button("SAIR"): st.session_state['autenticado'] = False; st.rerun()

    # --- ABA: COMANDO ---
    if aba == "🕹️ COMANDO":
        st.title("🕹️ CENTRO DE COMANDO")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("LIGAR MÁQUINA"):
                t, u = fb_get("sensor/temperatura", "0"), fb_get("sensor/umidade", "0")
                fb_set("controle/led", "ON")
                agora = get_hora_brasil()
                fb_post("logs/operacao", {"acao": f"LIGOU ({st.session_state['usuario']})", "temp": t, "umid": u, "data": agora})
                if envio_auto: enviar_email_relatorio(email_destino, "ASB - LIGADO", f"Ação: LIGAR\nPor: {st.session_state['usuario']}\nTemp: {t}C\nData: {agora}")
                st.toast("Comando enviado!")

            if st.button("DESLIGAR MÁQUINA"):
                t, u = fb_get("sensor/temperatura", "0"), fb_get("sensor/umidade", "0")
                fb_set("controle/led", "OFF")
                agora = get_hora_brasil()
                fb_post("logs/operacao", {"acao": f"DESLIGOU ({st.session_state['usuario']})", "temp": t, "umid": u, "data": agora})
                if envio_auto: enviar_email_relatorio(email_destino, "ASB - DESLIGADO", f"Ação: DESLIGAR\nPor: {st.session_state['usuario']}\nTemp: {t}C\nData: {agora}")
                st.toast("Comando enviado!")

        with c2:
            st.subheader("Status Real")
            placeholder_status = st.empty()
            @st.fragment(run_every=2)
            def monitor_led():
                estado = fb_get("controle/led", "OFF")
                if "ON" in str(estado).upper():
                    cor, texto = "🟢", "MÁQUINA LIGADA"
                else:
                    cor, texto = "🔴", "MÁQUINA DESLIGADA"
                
                placeholder_status.markdown(f"""
                    <div class="status-container">
                        <span style="font-size: 50px;">{cor}</span>
                        <span class="status-text">{texto}</span>
                    </div>
                """, unsafe_allow_html=True)
            monitor_led()

    # --- ABA: TELEMETRIA ---
    elif aba == "📈 TELEMETRIA":
        st.title("📈 MONITORAMENTO")
        col1, col2 = st.columns(2)
        m1, m2 = col1.empty(), col2.empty()
        @st.fragment(run_every=4)
        def monitor_sensores():
            m1.metric("🌡️ TEMPERATURA", f"{fb_get('sensor/temperatura', '0')} °C")
            m2.metric("💧 UMIDADE", f"{fb_get('sensor/umidade', '0')} %")
        monitor_sensores()

    # --- ABA: RELATÓRIOS ---
    elif aba == "📊 RELATÓRIOS":
        st.title("📊 HISTÓRICO (Brasília)")
        if st.button("🗑️ LIMPAR TUDO"): fb_delete("logs/operacao"); st.rerun()
        logs = fb_get("logs/operacao", {})
        if logs and isinstance(logs, dict):
            for id, info in reversed(list(logs.items())):
                st.markdown(f"""<div class="report-card">
                    <small>🕒 {info.get('data')}</small><br>
                    <b>🔹 {info.get('acao')}</b><br>
                    🌡️ {info.get('temp')}°C | 💧 {info.get('umid')}%
                </div>""", unsafe_allow_html=True)

    # --- ABA: GESTÃO ---
    elif aba == "👤 GESTÃO":
        st.title("👤 GESTÃO DE ACESSOS")
        with st.form("Novo"):
            nu, ns = st.text_input("Usuário"), st.text_input("Senha")
            if st.form_submit_button("CADASTRAR"):
                fb_post("config/usuarios", {"user": nu, "pass": ns})
                st.success("Usuário cadastrado com sucesso!")
