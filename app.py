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

# --- 1. CONFIGURAÇÃO VISUAL (PRESERVANDO v8.7 + v9.7 INTEGRAL) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    
    /* BOTÕES PADRÃO */
    div.stButton > button:first-child {
        width: 100%;
        height: 4.5em;
        font-weight: bold;
        background-color: #00458d;
        color: white;
        border-radius: 10px;
        border: none;
    }

    /* CARD DE USUÁRIO E STATUS */
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 20px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; font-size: 22px; }
    
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .home-icon { font-size: 40px; margin-bottom: 15px; }

    /* CARD DE MEDIÇÃO */
    .gauge-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; }
    .gauge-value { font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; }
    
    /* FAIXAS ABAULADAS (CONFORME SOLICITADO) */
    .moving-bar-container { width: 100%; height: 20px; background: #eee; border-radius: 10px; overflow: hidden; position: relative; margin-top: 10px; }
    .bar-temp { height: 100%; width: 50%; background: linear-gradient(90deg, #3a7bd5, #ee0979); border-radius: 10px; animation: moveSide 3s infinite alternate ease-in-out; }
    .bar-umid { height: 100%; width: 50%; background: linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius: 10px; animation: moveSide 4s infinite alternate ease-in-out; }
    
    .bar-on { height: 100%; width: 100%; background: #28a745; border-radius: 10px; box-shadow: 0 0 10px rgba(40, 167, 69, 0.5); }
    .bar-off { height: 100%; width: 100%; background: #dc3545; border-radius: 10px; box-shadow: 0 0 10px rgba(220, 53, 69, 0.5); }
    .bar-inativa { height: 100%; width: 100%; background: #eee; border-radius: 10px; }
    
    @keyframes moveSide {
        0% { transform: translateX(-20%); }
        100% { transform: translateX(120%); }
    }

    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: sans-serif; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); background-color: #ffffff; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES AUXILIARES (PRESERVADAS) ---
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
                msg = MIMEText(f"LOG ASB\nUsuário: {usuario}\nAção: {acao}\nHora: {agora}")
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
    st.markdown("<div class='subtitulo-asb'>Plataforma Integrada de Gestão e Monitoramento IoT</div>", unsafe_allow_html=True)
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
    if st.sidebar.button("Sair"): st.session_state["logado"] = False; st.rerun()

    # --- TELA 0: HOME (RECUPERADA v8.7) ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Monitoramento contínuo via nuvem.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Análise de Dados</h3><p>Telemetria em tempo real.</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Controle de acesso e auditoria.</p></div>""", unsafe_allow_html=True)

    # --- TELA 1: ACIONAMENTO (ESTILO v9.7 COM FAIXA ABAULADA) ---
    elif menu == "🕹️ Acionamento":
        st.header("Controle de Ativos")
        status_real = db.reference("controle/led").get()
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"LIGAR {'🟢' if status_real == 'ON' else '⚪'}"):
                db.reference("controle/led").set("ON"); registrar_evento("LIGOU EQUIPAMENTO"); st.rerun()
            estilo_on = "bar-on" if status_real == "ON" else "bar-inativa"
            st.markdown(f'<div class="moving-bar-container"><div class="{estilo_on}"></div></div>', unsafe_allow_html=True)
        with c2:
            if st.button(f"DESLIGAR {'🔴' if status_real == 'OFF' else '⚪'}"):
                db.reference("controle/led").set("OFF"); registrar_evento("DESLIGOU EQUIPAMENTO"); st.rerun()
            estilo_off = "bar-off" if status_real == "OFF" else "bar-inativa"
            st.markdown(f'<div class="moving-bar-container"><div class="{estilo_off}"></div></div>', unsafe_allow_html=True)

    # --- TELA 2: MEDIÇÃO (REFRESH + CARDS) ---
    elif menu == "🌡️ Medição":
        st.header("Telemetria")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        col1, col2 = st.columns(2)
        with col1: st.markdown(f'<div class="gauge-card">Temperatura (°C)<div class="gauge-value">{t}</div><div class="moving-bar-container"><div class="bar-temp"></div></div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="gauge-card">Umidade (%)<div class="gauge-value">{u}</div><div class="moving-bar-container"><div class="bar-umid"></div></div></div>', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()

    # --- TELA 3: RELATÓRIOS (WHATSAPP + LIMPEZA PRESERVADOS) ---
    elif menu == "📊 Relatórios":
        st.header("Histórico e Notificações")
        if st.button("🗑️ LIMPAR HISTÓRICO"):
            db.reference("historico_acoes").delete(); registrar_evento("LIMPEZA GERAL", manual=True); st.rerun()
        
        with st.expander("📲 Enviar WhatsApp"):
            tel = st.text_input("Número", value="5562999999999")
            msg_w = st.text_area("Mensagem", "Alerta ASB!")
            if st.button("GERAR LINK"):
                st.markdown(f'<a href="https://wa.me/{tel}?text={urllib.parse.quote(msg_w)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">ABRIR WHATSAPP</div></a>', unsafe_allow_html=True)

        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TELA 4: DIAGNÓSTICO (PING DA v8.8 PRESERVADO) ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Status de Conectividade")
        if st.button("🔍 EXECUTAR PING NO HARDWARE"):
            with st.spinner("Sondando ESP32..."):
                db.reference("sensor/temperatura").delete()
                time.sleep(4)
                st.session_state["net_st"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        
        if st.session_state.get("net_st") == "ON": st.markdown("<div class='status-ok'>✅ CONEXÃO ATIVA</div>", unsafe_allow_html=True)
        elif st.session_state.get("net_st") == "OFF": st.markdown("<div class='status-erro'>❌ HARDWARE OFFLINE</div>", unsafe_allow_html=True)
        if st.button("REBOOT REMOTO"): db.reference("controle/restart").set(True); registrar_evento("COMANDO REBOOT")

    # --- TELA 5: GESTÃO DE USUÁRIOS (RECUPERADA v8.7) ---
    elif menu == "👥 Gestão de Usuários":
        if st.session_state["is_admin"]:
            st.header("Operadores Autorizados")
            with st.form("cad"):
                n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha")
                if st.form_submit_button("CADASTRAR"):
                    db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                    st.rerun()
            users = db.reference("usuarios_autorizados").get()
            if users:
                for k, v in users.items(): st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> (Login: {v.get('login')})</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v9.8
