import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd
import time
import pytz
import urllib.parse 

# --- 1. CONFIGURAÇÃO VISUAL (v12.0 - FIDELIDADE TOTAL AO LAYOUT ORIGINAL) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    
    /* PRESERVANDO EXATAMENTE O BOTÃO ORIGINAL */
    div.stButton > button:first-child {
        width: 100%;
        height: 4.5em;
        font-weight: bold;
        background-color: #00458d;
        color: white;
        border-radius: 10px;
        border: none;
    }

    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 20px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; font-size: 22px; }
    
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .gauge-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; }
    .gauge-value { font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; }
    
    /* FAIXA FINA (8PX) CONFORME SOLICITADO */
    .bar-container { width: 100%; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; position: relative; margin-top: 5px; }
    
    /* MOVIMENTO PARA A DIREITA QUANDO ATIVO */
    .bar-moving-on { height: 100%; width: 100%; background: linear-gradient(90deg, #28a745, #85e085, #28a745); background-size: 200% 100%; animation: moveRight 2s linear infinite; }
    .bar-moving-off { height: 100%; width: 100%; background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); background-size: 200% 100%; animation: moveRight 2s linear infinite; }
    .bar-static { height: 100%; width: 100%; background: #eee; }

    @keyframes moveRight {
        0% { background-position: 200% 0; }
        100% { background-position: 0 0; }
    }

    /* BOLINHA PISCANTE */
    .blink-ball { animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0.2; } }

    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; background-color: #ffffff; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NÚCLEO (PRESERVADAS) ---
def obter_hora_brasilia():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

@st.cache_resource
def conectar_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = {
                "type": st.secrets.get("type"),
                "project_id": st.secrets.get("project_id"),
                "private_key": st.secrets.get("private_key", "").replace('\\n', '\n'),
                "client_email": st.secrets.get("client_email"),
                "token_uri": st.secrets.get("token_uri")
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora, "usuario": usuario, "acao": acao})
        if st.session_state.get("email_ativo", True) or manual:
            remetente, senha = st.secrets.get("email_user"), st.secrets.get("email_password")
            if remetente and senha:
                msg = MIMEText(f"LOG ASB\nUsuario: {usuario}\nAcao: {acao}\nHora: {agora}")
                msg['Subject'] = f"SISTEMA ASB: {acao}"; msg['From'] = remetente; msg['To'] = "asbautomacao@gmail.com"
                server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(remetente, senha)
                server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string()); server.quit()
    except: pass

# --- 3. FLUXO DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u_input = st.text_input("Usuário")
        p_input = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if u_input == "admin" and p_input == "asb2026":
                st.session_state["logado"], st.session_state["user_nome"], st.session_state["is_admin"] = True, "Admin Master", True
                st.rerun()
            else:
                conectar_firebase()
                usuarios_db = db.reference("usuarios_autorizados").get()
                if usuarios_db:
                    for key, user_data in usuarios_db.items():
                        if user_data['login'] == u_input and user_data['senha'] == p_input:
                            st.session_state["logado"], st.session_state["user_nome"], st.session_state["is_admin"] = True, user_data['nome'], False
                            st.rerun()
                st.error("Credenciais inválidas.")
else:
    conectar_firebase()
    menu_opcoes = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]: menu_opcoes.append("👥 Gestão de Usuários")
    menu = st.sidebar.radio("Navegação:", menu_opcoes)
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    if st.sidebar.button("Sair"): st.session_state["logado"] = False; st.rerun()

    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("<div class='home-card'><h3>Supervisão</h3><p>IoT em tempo real.</p></div>", unsafe_allow_html=True)
        with c2: st.markdown("<div class='home-card'><h3>Análise</h3><p>Dados de sensores.</p></div>", unsafe_allow_html=True)
        with c3: st.markdown("<div class='home-card'><h3>Segurança</h3><p>Auditoria completa.</p></div>", unsafe_allow_html=True)

    elif menu == "🕹️ Acionamento":
        st.header("Controle de Equipamentos")
        status_real = db.reference("controle/led").get()
        c1, c2 = st.columns(2)
        with c1:
            # Bolinha pisca apenas se estiver ON
            bola_on = "<span class='blink-ball'>🟢</span>" if status_real == "ON" else "⚪"
            if st.button(f"LIGAR"):
                db.reference("controle/led").set("ON"); registrar_evento("LIGOU EQUIPAMENTO"); st.rerun()
            st.markdown(f"<p style='text-align:center; font-size:20px;'>{bola_on}</p>", unsafe_allow_html=True)
            estilo_f = "bar-moving-on" if status_real == "ON" else "bar-static"
            st.markdown(f'<div class="bar-container"><div class="{estilo_f}"></div></div>', unsafe_allow_html=True)
        with c2:
            # Bolinha pisca apenas se estiver OFF
            bola_off = "<span class='blink-ball'>🔴</span>" if status_real == "OFF" else "⚪"
            if st.button(f"DESLIGAR"):
                db.reference("controle/led").set("OFF"); registrar_evento("DESLIGOU EQUIPAMENTO"); st.rerun()
            st.markdown(f"<p style='text-align:center; font-size:20px;'>{bola_off}</p>", unsafe_allow_html=True)
            estilo_f = "bar-moving-off" if status_real == "OFF" else "bar-static"
            st.markdown(f'<div class="bar-container"><div class="{estilo_f}"></div></div>', unsafe_allow_html=True)

    elif menu == "🌡️ Medição":
        st.header("Telemetria Industrial")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        p_t, p_u = min(max((t/60)*100, 0), 100), min(max(u, 0), 100)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="gauge-card">Temperatura: {t}°C<div class="bar-container"><div style="height:100%; width:{p_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:4px; transition:1s;"></div></div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="gauge-card">Umidade: {u}%<div class="bar-container"><div style="height:100%; width:{p_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:4px; transition:1s;"></div></div></div>', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()

    elif menu == "📊 Relatórios":
        st.header("Histórico e Mensagens")
        if st.button("🗑️ LIMPAR HISTÓRICO"): db.reference("historico_acoes").delete(); st.rerun()
        with st.expander("📲 Notificar WhatsApp"):
            tel = st.text_input("Número", "5562999999999")
            msg_w = st.text_area("Mensagem", "Alerta ASB!")
            if st.button("GERAR LINK"):
                st.markdown(f'<a href="https://wa.me/{tel}?text={urllib.parse.quote(msg_w)}" target="_blank">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "🛠️ Diagnóstico":
        st.header("Status de Conexão")
        if st.button("🔍 EXECUTAR PING"):
            db.reference("sensor/temperatura").delete(); time.sleep(4)
            st.session_state["net_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        if st.session_state.get("net_status") == "ON": st.markdown("<div class='status-ok'>✅ CONEXÃO ATIVA</div>", unsafe_allow_html=True)
        elif st.session_state.get("net_status") == "OFF": st.markdown("<div class='status-erro'>❌ HARDWARE OFFLINE</div>", unsafe_allow_html=True)
        if st.button("REBOOT REMOTO"): db.reference("controle/restart").set(True); registrar_evento("REBOOT")

    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Usuários Cadastrados")
        with st.form("u"):
            n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha")
            if st.form_submit_button("CADASTRAR"):
                db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.rerun()
        users = db.reference("usuarios_autorizados").get()
        if users:
            for k, v in users.items(): st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> ({v.get('login')})</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v12.0
