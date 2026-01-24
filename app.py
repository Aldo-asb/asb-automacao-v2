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

# --- 1. CONFIGURAÇÃO VISUAL (PRESERVADA v8.0) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 10px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 10px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; }
    
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .home-icon { font-size: 40px; margin-bottom: 15px; }
    
    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: sans-serif; position: relative; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
    .msg-admin { align-self: flex-end; background-color: #dcf8c6; border-top-right-radius: 0; }
    .msg-user { align-self: flex-start; background-color: #ffffff; border-top-left-radius: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES AUXILIARES ---
def obter_hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso)

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
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            if remetente and senha:
                msg = MIMEText(f"LOG ASB\nUsuário: {usuario}\nAção: {acao}\nHora: {agora}")
                msg['Subject'] = f"SISTEMA ASB: {acao}"
                msg['From'] = remetente
                msg['To'] = "asbautomacao@gmail.com"
                server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(remetente, senha)
                server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string()); server.quit()
    except: pass

# --- 3. FLUXO DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True
if "click_status" not in st.session_state: st.session_state["click_status"] = None

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-asb'>Sistemas de Supervisão IoT Avançados e Monitoramento em Tempo Real</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
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
    if st.session_state["is_admin"]:
        menu_opcoes.append("👥 Gestão de Usuários")
    
    menu = st.sidebar.radio("Navegação Principal:", menu_opcoes)
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    if st.sidebar.button("Encerrar Sessão"): st.session_state["logado"] = False; st.rerun()

    # --- TELA 0: HOME ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitulo-asb'>Plataforma Integrada de Gestão e Monitoramento IoT</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Conexão ativa com o hardware ESP32.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Análise</h3><p>Telemetria processada em tempo real.</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Auditoria</h3><p>Logs de eventos com carimbo de tempo real.</p></div>""", unsafe_allow_html=True)
        st.info(f"Sistema Conectado. Bem-vindo, {st.session_state['user_nome']}.")

    # --- TELA 1: ACIONAMENTO ---
    elif menu == "🕹️ Acionamento":
        st.header("Controle de Ativos")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"LIGAR {'🟢' if st.session_state['click_status'] == 'ON' else '⚪'}"):
                db.reference("controle/led").set("ON"); st.session_state["click_status"] = "ON"; registrar_evento("LIGOU EQUIPAMENTO"); st.rerun()
        with c2:
            if st.button(f"DESLIGAR {'🔴' if st.session_state['click_status'] == 'OFF' else '⚪'}"):
                db.reference("controle/led").set("OFF"); st.session_state["click_status"] = "OFF"; registrar_evento("DESLIGOU EQUIPAMENTO"); st.rerun()

    # --- TELA 2: MEDIÇÃO (INTEGRAÇÃO REAL) ---
    elif menu == "🌡️ Medição":
        st.header("Telemetria em Tempo Real")
        t = db.reference("sensor/temperatura").get()
        u = db.reference("sensor/umidade").get()
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura Atual", f"{t} °C" if t is not None else "---")
        col_u.metric("Umidade Atual", f"{u} %" if u is not None else "---")
        g1, g2 = st.columns(2)
        with g1: st.bar_chart(pd.DataFrame({"°C": [t if t else 0]}, index=["Sensor 1"]), color="#dc3545")
        with g2: st.bar_chart(pd.DataFrame({"%": [u if u else 0]}, index=["Sensor 1"]), color="#00458d")
        if st.button("🔄 REFRESH DATA"): st.rerun()

    # --- TELA 3: RELATÓRIOS ---
    elif menu == "📊 Relatórios":
        st.header("Histórico e Notificações")
        with st.expander("📲 Enviar Notificação WhatsApp", expanded=False):
            tel = st.text_input("Número do Gestor", value="5562999999999")
            msg_zap = st.text_area("Mensagem", "Alerta ASB: Verificação de telemetria solicitada.")
            if st.button("GERAR LINK"):
                link = f"https://wa.me/{tel}?text={urllib.parse.quote(msg_zap)}"
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">ENVIAR WHATSAPP</div></a>', unsafe_allow_html=True)
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for key in logs:
                val = logs[key]
                user, acao, data = val.get("usuario", "Sistema"), val.get("acao", ""), val.get("data", "")
                classe = "msg-admin" if user == "Admin Master" else "msg-user"
                st.markdown(f'<div class="msg-balao {classe}"><div class="msg-info">{user}</div><div>{acao}</div><div style="font-size:10px; color:#888;">{data}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("🗑️ LIMPAR HISTÓRICO"): db.reference("historico_acoes").delete(); st.rerun()

    # --- TELA 4: DIAGNÓSTICO ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Monitor de Conexão Hardware")
        status = db.reference("sensor/temperatura").get()
        if status is not None:
            st.markdown("<div class='status-ok'>HARDWARE CONECTADO E ENVIANDO DADOS</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-erro'>HARDWARE DESCONECTADO OU SEM INTERNET</div>", unsafe_allow_html=True)
        if st.button("SOLICITAR REBOOT DO ESP32"):
            db.reference("controle/restart").set(True)
            registrar_evento("COMANDO DE REINICIALIZAÇÃO ENVIADO")
            st.success("Comando enviado ao Firebase!")

    # --- TELA 5: GESTÃO DE USUÁRIOS ---
    elif menu == "👥 Gestão de Usuários":
        if st.session_state["is_admin"]:
            st.header("Controle de Acesso")
            with st.form("form_cadastro"):
                n_n, l_n, s_n = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    if n_n and l_n and s_n:
                        db.reference("usuarios_autorizados").push({"nome": n_n, "login": l_n, "senha": s_n, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                        st.success("Operador Cadastrado!"); st.rerun()
            users = db.reference("usuarios_autorizados").get()
            if users:
                for k, v in users.items():
                    st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> ({v.get('login')})</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v8.1
