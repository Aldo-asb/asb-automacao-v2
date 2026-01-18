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
    
    .report-card { 
        background-color: #2d3748; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #4ade80; 
        border-left: 10px solid #4ade80; 
        margin-bottom: 15px; 
        color: #ffffff;
    }
    .report-card b { color: #ffffff; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def fb_get(path, default=None):
    try:
        r = requests.get(f"{URL_FB}{path}.json", timeout=3)
        if r.ok and r.json() is not None: return r.json()
        return default
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

# --- FUNÇÃO DE E-MAIL ---
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

# --- LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align:center;'>ASB AUTOMAÇÃO</h1>", unsafe_allow_html=True)
    with st.form("Login"):
        u_input = st.text_input("Usuário")
        s_input = st.text_input("Senha", type="password")
        if st.form_submit_button("ACESSAR SISTEMA"):
            if u_input == "admin" and s_input == "asb123":
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = "ADMIN MESTRE"
                st.session_state['role'] = "admin"
                st.rerun()
            else:
                usuarios_db = fb_get("config/usuarios", {})
                acesso_valido = False
                if isinstance(usuarios_db, dict):
                    for uid, dados in usuarios_db.items():
                        if dados.get('user') == u_input and dados.get('pass') == s_input:
                            st.session_state['autenticado'] = True
                            st.session_state['usuario'] = u_input
                            st.session_state['role'] = "cliente"
                            acesso_valido = True
                            break
                if acesso_valido:
                    st.rerun()
                else: st.error("Usuário ou Senha inválidos.")
else:
    # --- MENU LATERAL ---
    st.sidebar.markdown(f"<h2 style='color:#00ff00;'>Olá, {st.session_state['usuario']}</h2>", unsafe_allow_html=True)
    opcoes_menu = ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"]
    if st.session_state['role'] == "admin":
        opcoes_menu.append("👤 GESTÃO DE ACESSOS")
        
    aba = st.sidebar.radio("MENU", opcoes_menu)
    st.sidebar.divider()
    
    # Restauração do Botão de E-mail Automático
    envio_auto = st.sidebar.toggle("Envio de E-mail Automático", value=False)
    email_destino = st.sidebar.text_input("E-mail para Alertas", value="asbautomacao@gmail.com")
    
    if st.sidebar.button("SAIR"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- TELA: COMANDO ---
    if aba == "🕹️ COMANDO":
        st.title("🕹️ CENTRO DE COMANDO")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("LIGAR MÁQUINA"):
                t = fb_get("sensor/temperatura", "0")
                u = fb_get("sensor/umidade", "0")
                fb_set("controle/led", "ON")
                dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                fb_post("logs/operacao", {"acao": f"LIGOU ({st.session_state['usuario']})", "temp": t, "umid": u, "data": dt})
                
                if envio_auto:
                    enviar_email_relatorio(email_destino, "ASB - MÁQUINA LIGADA", f"Ação por: {st.session_state['usuario']}\nTemp: {t}°C | Umid: {u}%\nData: {dt}")
                
                st.toast("Ligado!")
            
            if st.button("DESLIGAR MÁQUINA"):
                t = fb_get("sensor/temperatura", "0")
                u = fb_get("sensor/umidade", "0")
                fb_set("controle/led", "OFF")
                dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                fb_post("logs/operacao", {"acao": f"DESLIGOU ({st.session_state['usuario']})", "temp": t, "umid": u, "data": dt})
                
                if envio_auto:
                    enviar_email_relatorio(email_destino, "ASB - MÁQUINA PARADA", f"Ação por: {st.session_state['usuario']}\nTemp: {t}°C | Umid: {u}%\nData: {dt}")
                
                st.toast("Desligado!")
        with c2:
            st.subheader("Status da Máquina")
            status_placeholder = st.empty()
            @st.fragment(run_every=4)
            def update_led():
                led = fb_get("controle/led", "OFF")
                cor = "🟢 LIGADA" if "ON" in str(led).upper() else "🔴 DESLIGADA"
                status_placeholder.markdown(f"<div style='border:2px solid #374151;padding:20px;text-align:center;background-color:#1f2937;'><h2>{cor}</h2></div>", unsafe_allow_html=True)
            update_led()

    # --- TELA: TELEMETRIA ---
    elif aba == "📈 TELEMETRIA":
        st.title("📈 MONITORAMENTO")
        col1, col2 = st.columns(2)
        placeholder_t = col1.empty()
        placeholder_u = col2.empty()

        @st.fragment(run_every=4)
        def update_metrics():
            t = fb_get("sensor/temperatura", "0")
            u = fb_get("sensor/umidade", "0")
            placeholder_t.metric("🌡️ TEMPERATURA", f"{t} °C")
            placeholder_u.metric("💧 UMIDADE", f"{u} %")
        update_metrics()

    # --- TELA: RELATÓRIOS ---
    elif aba == "📊 RELATÓRIOS":
        st.title("📊 HISTÓRICO")
        if st.button("🗑️ LIMPAR HISTÓRICO"):
            fb_delete("logs/operacao")
            st.rerun()
            
        logs = fb_get("logs/operacao", {})
        if logs and isinstance(logs, dict):
            for id, info in reversed(list(logs.items())):
                st.markdown(f"""<div class="report-card">
                <small>🕒 {info.get('data', '---')}</small><br>
                <b>🔹 {info.get('acao', '---')}</b><br>
                🌡️ {info.get('temp', '---')} °C | 💧 {info.get('umid', '---')} %
                </div>""", unsafe_allow_html=True)

    # --- TELA: GESTÃO DE ACESSOS ---
    elif aba == "👤 GESTÃO DE ACESSOS":
        st.title("👤 USUÁRIOS")
        with st.form("Novo"):
            new_user = st.text_input("Nome")
            new_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                fb_post("config/usuarios", {"user": new_user, "pass": new_pass})
                st.success("Cadastrado!")
        st.divider()
        users = fb_get("config/usuarios", {})
        if users and isinstance(users, dict):
            for uid, d in users.items():
                c1, c2 = st.columns([3, 1])
                c1.write(f"👤 {d.get('user')}")
                if c2.button("Excluir", key=uid):
                    fb_delete(f"config/usuarios/{uid}"); st.rerun()
