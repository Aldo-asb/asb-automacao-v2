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
    .report-card { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4ade80; border-left: 10px solid #4ade80; margin-bottom: 15px; color: #ffffff; }
    .fail-card { background-color: #3d2b2b; padding: 20px; border-radius: 10px; border: 1px solid #ff4b4b; border-left: 10px solid #ff4b4b; margin-bottom: 15px; color: #ffffff; }
    .card-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; display: block; }
    .card-text { font-size: 15px; font-family: 'Courier New', monospace; }
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

def fb_delete(path):
    try: requests.delete(f"{URL_FB}{path}.json", timeout=2)
    except: pass

# --- FUNÇÃO DE ENVIO DE E-MAIL ---
def enviar_email_relatorio(destinatario, assunto, corpo):
    try:
        remetente = "asbautomacao@gmail.com"
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
    except: return False

# --- LOGIN ---
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
                fb_post("logs/acessos", {"usuario": u, "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})
                st.rerun()
            else: st.error("Erro")
else:
    # --- MENU LATERAL ---
    st.sidebar.markdown("<h2 style='color:#00ff00;'>ASB V2</h2>", unsafe_allow_html=True)
    aba = st.sidebar.radio("MENU", ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"])
    
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Configurações")
    envio_auto = st.sidebar.toggle("Envio de E-mail Automático", value=False)
    email_destino = st.sidebar.text_input("E-mail para Auto-Envio", value="asbautomacao@gmail.com")
    
    if st.sidebar.button("SAIR"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- TELAS ---
    if aba == "🕹️ COMANDO":
        st.title("🕹️ CENTRO DE COMANDO")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("LIGAR MÁQUINA"):
                t = fb_get("sensor/temperatura", "---")
                st.toast("Ligando...")
                fb_set("controle/led", "ON")
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                fb_post("logs/operacao", {"acao": "LIGOU", "temp": t, "data": data_hora})
                if envio_auto:
                    corpo = f"ALERTA ASB: Máquina LIGADA\nData: {data_hora}\nTemp: {t}°C"
                    enviar_email_relatorio(email_destino, "NOTIFICAÇÃO AUTOMÁTICA - LIGOU", corpo)

            if st.button("DESLIGAR MÁQUINA"):
                t = fb_get("sensor/temperatura", "---")
                st.toast("Desligando...")
                fb_set("controle/led", "OFF")
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                fb_post("logs/operacao", {"acao": "DESLIGOU", "temp": t, "data": data_hora})
                if envio_auto:
                    corpo = f"ALERTA ASB: Máquina DESLIGADA\nData: {data_hora}\nTemp: {t}°C"
                    enviar_email_relatorio(email_destino, "NOTIFICAÇÃO AUTOMÁTICA - DESLIGOU", corpo)
        with c2:
            @st.fragment(run_every=3)
            def show_status():
                led = fb_get("controle/led", "OFF")
                cor = "🟢" if "ON" in str(led).upper() else "🔴"
                st.markdown(f"<div style='border:2px solid #374151;padding:20px;text-align:center;background-color:#1f2937;'><h2>{cor} {led}</h2></div>", unsafe_allow_html=True)
            show_status()

    elif aba == "📈 TELEMETRIA":
        st.title("📈 TELEMETRIA")
        @st.fragment(run_every=2)
        def show_temp():
            t = fb_get("sensor/temperatura")
            s = fb_get("sensor/status", "ERRO")
            if s == "OK": st.metric("TEMPERATURA ATUAL", f"{t} °C")
            else: st.error("⚠️ SENSOR OFFLINE")
        show_temp()

    elif aba == "📊 RELATÓRIOS":
        st.title("📊 RELATÓRIOS")
        
        col_rel, col_btn = st.columns([4, 1])
        with col_btn:
            if st.button("🗑️ APAGAR DADOS", type="secondary"):
                fb_delete("logs/operacao")
                st.success("Histórico limpo!")
                time.sleep(1)
                st.rerun()

        tab1, tab2 = st.tabs(["📌 Histórico", "🔒 Acessos"])
        with tab1:
            logs = fb_get("logs/operacao", {})
            texto_email = "RELATÓRIO ASB\n" + "="*20 + "\n"
            if logs:
                for id, info in reversed(list(logs.items())):
                    val_t = info.get('temp', '---')
                    st.markdown(f"""<div class="report-card">
                    <span class="card-title">✅ {info['acao']}</span>
                    <span class="card-text">🕒 {info['data']} | 🌡️ {val_t} °C</span>
                    </div>""", unsafe_allow_html=True)
                    texto_email += f"{info['data']} - {info['acao']} - {val_t}C\n"
                
                st.divider()
                dest = st.text_input("Enviar este histórico manualmente para:", value=email_destino)
                if st.button("ENVIAR MANUALMENTE"):
                    if enviar_email_relatorio(dest, "Relatório Manual ASB", texto_email):
                        st.success("E-mail enviado!")
            else:
                st.info("Nenhum dado registrado.")

        with tab2:
            acessos = fb_get("logs/acessos", {})
            if acessos:
                for id, info in reversed(list(acessos.items())):
                    st.info(f"👤 {info['usuario']} | {info['data']}")
