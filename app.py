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

# --- 1. CONFIGURAÇÃO VISUAL (BASEADA EXATAMENTE NA v8.0) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 20px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; font-size: 22px; }
    
    /* ESTILO HOME v8.0 PRESERVADO */
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .home-icon { font-size: 40px; margin-bottom: 15px; }

    /* ESTILO MEDIÇÃO v8.2 INTEGRADO AO LAYOUT v8.0 */
    .gauge-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; }
    .gauge-value { font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; }
    .bar-temp { height: 20px; width: 100%; background: linear-gradient(90deg, #3a7bd5, #ee0979); border-radius: 10px; }
    .bar-umid { height: 20px; width: 100%; background: linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius: 10px; }
    
    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: sans-serif; position: relative; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
    .msg-admin { align-self: flex-end; background-color: #dcf8c6; border-top-right-radius: 0; }
    .msg-user { align-self: flex-start; background-color: #ffffff; border-top-left-radius: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES AUXILIARES (CONQUISTADAS) ---
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
            remetente, senha = st.secrets.get("email_user"), st.secrets.get("email_password")
            if remetente and senha:
                msg = MIMEText(f"LOG ASB\nUsuário: {usuario}\nAção: {acao}\nHora: {agora}")
                msg['Subject'] = f"SISTEMA ASB: {acao}"; msg['From'] = remetente; msg['To'] = "asbautomacao@gmail.com"
                server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(remetente, senha)
                server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string()); server.quit()
    except: pass

# --- 3. FLUXO DE LOGIN (IDENTICO v8.0) ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True

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
    if st.session_state["is_admin"]: menu_opcoes.append("👥 Gestão de Usuários")
    menu = st.sidebar.radio("Navegação Principal:", menu_opcoes)
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    if st.sidebar.button("Encerrar Sessão"): st.session_state["logado"] = False; st.rerun()

    # --- TELA 0: HOME (EXATA v8.0) ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitulo-asb'>Plataforma Integrada de Gestão e Monitoramento IoT</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Monitoramento contínuo de ativos industriais via nuvem com baixa latência.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Análise de Dados</h3><p>Gráficos em tempo real para tomada de decisão baseada em telemetria precisa.</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Controle de acesso multiusuário e registros de auditoria em todos os acionamentos.</p></div>""", unsafe_allow_html=True)
        st.info(f"Bem-vindo, {st.session_state['user_nome']}.")

    # --- TELA 1: ACIONAMENTO (STATUS BOLINHAS v8.0 LÓGICA CORRIGIDA) ---
    elif menu == "🕹️ Acionamento":
        st.header("Controle de Ativos")
        status_real = db.reference("controle/led").get()
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"LIGAR {'🟢' if status_real == 'ON' else '⚪'}"):
                db.reference("controle/led").set("ON"); registrar_evento("LIGOU EQUIPAMENTO"); st.rerun()
        with c2:
            if st.button(f"DESLIGAR {'🔴' if status_real == 'OFF' else '⚪'}"):
                db.reference("controle/led").set("OFF"); registrar_evento("DESLIGOU EQUIPAMENTO"); st.rerun()

    # --- TELA 2: MEDIÇÃO (LAYOUT v8.2 INTEGRADO) ---
    elif menu == "🌡️ Medição":
        st.header("Telemetria em Tempo Real")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        col1, col2 = st.columns(2)
        with col1: st.markdown(f'<div class="gauge-card"><div>Temperatura (°C)</div><div class="gauge-value">{t}</div><div class="bar-temp"></div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="gauge-card"><div>Umidade (%)</div><div class="gauge-value">{u}</div><div class="bar-umid"></div></div>', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()

    # --- TELA 3: RELATÓRIOS (WHATSAPP + CHAT + LIMPEZA) ---
    elif menu == "📊 Relatórios":
        st.header("Histórico e Notificações")
        if st.button("🗑️ LIMPAR HISTÓRICO"):
            db.reference("historico_acoes").delete()
            registrar_evento("LIMPEZA DE HISTÓRICO", manual=True)
            st.rerun()
            
        with st.expander("📲 Enviar WhatsApp", expanded=False):
            tel = st.text_input("Número", value="5562999999999")
            msg_zap = st.text_area("Mensagem", "Alerta ASB: Verificação de sistema.")
            if st.button("GERAR LINK"):
                st.markdown(f'<a href="https://wa.me/{tel}?text={urllib.parse.quote(msg_zap)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">ABRIR WHATSAPP</div></a>', unsafe_allow_html=True)

        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for key in reversed(list(logs.keys())):
                val = logs[key]; user, acao, data = val.get("usuario"), val.get("acao"), val.get("data")
                classe = "msg-admin" if user == "Admin Master" else "msg-user"
                st.markdown(f'<div class="msg-balao {classe}"><b>{user}</b><br>{acao}<br><small>{data}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TELA 4: DIAGNÓSTICO (PING REAL SEM FALSA CONEXÃO) ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Monitor de Conectividade")
        if st.button("🔍 EXECUTAR PING NO HARDWARE"):
            with st.spinner("Testando resposta do ESP32..."):
                db.reference("sensor/temperatura").delete()
                time.sleep(4)
                if db.reference("sensor/temperatura").get() is not None: st.session_state["net_st"] = "ON"
                else: st.session_state["net_st"] = "OFF"
        
        if st.session_state.get("net_st") == "ON": st.markdown("<div class='status-ok'>CONEXÃO ATIVA</div>", unsafe_allow_html=True)
        elif st.session_state.get("net_st") == "OFF": st.markdown("<div class='status-erro'>HARDWARE OFFLINE</div>", unsafe_allow_html=True)
        
        if st.button("RESETAR HARDWARE"): db.reference("controle/restart").set(True); registrar_evento("RESET REMOTO")

    # --- TELA 5: GESTÃO DE USUÁRIOS (v8.0) ---
    elif menu == "👥 Gestão de Usuários":
        if st.session_state["is_admin"]:
            st.header("Cadastro de Operadores")
            with st.form("f_cad"):
                n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                    st.rerun()
            users = db.reference("usuarios_autorizados").get()
            if users:
                for k, v in users.items(): st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b></div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v9.0
