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

# --- 1. CONFIGURAÇÃO VISUAL INTEGRAL (v16.0 - FIDELIDADE TOTAL v13.0 + ACIONAMENTO) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    
    /* BOTÕES COM TAMANHO PADRONIZADO E SIMÉTRICOS */
    div.stButton > button {
        width: 100% !important;
        height: 4.5em !important;
        font-weight: bold !important;
        background-color: #00458d !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
    }

    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    
    .status-ok { color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 20px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; font-size: 22px; }
    
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .home-icon { font-size: 40px; margin-bottom: 15px; }

    .gauge-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; }
    .gauge-value { font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; }
    
    .moving-bar-container { width: 100%; height: 8px; background: #eee; border-radius: 10px; overflow: hidden; position: relative; margin-top: 10px; }
    .bar-on { height: 100%; width: 100%; background: linear-gradient(90deg, #28a745, #85e085, #28a745); background-size: 200% 100%; animation: moveRight 2s linear infinite; }
    .bar-off { height: 100%; width: 100%; background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); background-size: 200% 100%; animation: moveRight 2s linear infinite; }
    .bar-inativa { height: 100%; width: 100%; background: #eee; border-radius: 10px; }

    @keyframes moveRight { 0% { background-position: 200% 0; } 100% { background-position: 0 0; } }
    .blink { animation: blinker 1.2s linear infinite; display: inline-block; }
    @keyframes blinker { 50% { opacity: 0; } }

    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: sans-serif; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); background-color: #ffffff; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NÚCLEO (IDENTICAS v13.0) ---
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
        except Exception as e:
            st.error(f"Erro Conexão: {e}")
            return False
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
                msg = MIMEText(f"SISTEMA ASB AUTOMACAO\n\nUsuario: {usuario}\nAcao: {acao}\nData/Hora: {agora}")
                msg['Subject'] = f"LOG: {acao}"
                msg['From'] = remetente
                msg['To'] = "asbautomacao@gmail.com"
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(remetente, senha)
                server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string())
                server.quit()
    except:
        pass

# --- 3. CONTROLE DE ACESSO ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-asb'>Plataforma Integrada IoT</div>", unsafe_allow_html=True)
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
    if st.sidebar.button("Encerrar Sessão"): 
        st.session_state["logado"] = False
        st.rerun()

    # --- TELA: HOME (IDENTICA v13.0) ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Nuvem em tempo real.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Análise</h3><p>Telemetria avançada.</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Auditoria completa.</p></div>""", unsafe_allow_html=True)

    # --- TELA: ACIONAMENTO (MUDANÇA SOLICITADA) ---
    elif menu == "🕹️ Acionamento":
        st.header("Controle de Ativos")
        modo = st.radio("Operação:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        status_real = db.reference("controle/led").get()

        if modo == "MANUAL":
            c1, c2 = st.columns(2)
            with c1:
                bola_v = "<span class='blink'>🟢</span>" if status_real == 'ON' else "⚪"
                if st.button(f"LIGAR"):
                    db.reference("controle/led").set("ON"); registrar_evento("LIGOU"); st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:0;'>{bola_v}</p>", unsafe_allow_html=True)
                estilo_on = "bar-on" if status_real == "ON" else "bar-inativa"
                st.markdown(f'<div class="moving-bar-container"><div class="{estilo_on}"></div></div>', unsafe_allow_html=True)
            with c2:
                bola_r = "<span class='blink'>🔴</span>" if status_real == 'OFF' else "⚪"
                if st.button(f"DESLIGAR"):
                    db.reference("controle/led").set("OFF"); registrar_evento("DESLIGOU"); st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:0;'>{bola_r}</p>", unsafe_allow_html=True)
                estilo_off = "bar-off" if status_real == "OFF" else "bar-inativa"
                st.markdown(f'<div class="moving-bar-container"><div class="{estilo_off}"></div></div>', unsafe_allow_html=True)
        
        else: # MODO AUTOMÁTICO
            st.info("🤖 MODO AUTOMÁTICO ATIVO")
            c_a1, c_a2 = st.columns(2)
            with c_a1: t_lig = st.number_input("Tempo de Ciclo (minutos)", min_value=1, value=5)
            with c_a2: t_pisca = st.number_input("Velocidade do Pisca (seg)", min_value=1, value=2)
            
            # Lógica de precisão por hora
            agora = obter_hora_brasilia()
            if agora.minute < t_lig:
                if (agora.second // t_pisca) % 2 == 0:
                    db.reference("controle/led").set("ON")
                    st.success("⚡ EXECUTANDO CICLO: LIGADO")
                else:
                    db.reference("controle/led").set("OFF")
                    st.warning("⚡ EXECUTANDO CICLO: DESLIGADO")
                time.sleep(1); st.rerun()
            else:
                db.reference("controle/led").set("OFF")
                st.info("⏳ AGUARDANDO PRÓXIMA HORA...")
                time.sleep(10); st.rerun()

    # --- TELA: MEDIÇÃO (IDENTICA v13.0) ---
    elif menu == "🌡️ Medição":
        st.header("Telemetria Industrial")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        pct_t = min(max((t / 60) * 100, 0), 100)
        pct_u = min(max(u, 0), 100)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''<div class="gauge-card">Temperatura (°C)<div class="gauge-value">{t}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:10px; transition:0.8s;"></div></div></div>''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''<div class="gauge-card">Umidade (%)<div class="gauge-value">{u}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:10px; transition:0.8s;"></div></div></div>''', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()

    # --- TELA: RELATÓRIOS (IDENTICA v13.0) ---
    elif menu == "📊 Relatórios":
        st.header("Histórico de Atividades")
        if st.button("🗑️ LIMPAR HISTÓRICO"):
            db.reference("historico_acoes").delete(); registrar_evento("LIMPEZA", manual=True); st.rerun()
        with st.expander("📲 WhatsApp"):
            tel = st.text_input("Número", value="5562999999999")
            msg_w = st.text_area("Mensagem", "Relatório ASB")
            if st.button("ABRIR"):
                st.markdown(f'<a href="https://wa.me/{tel}?text={urllib.parse.quote(msg_w)}" target="_blank">ENVIAR</a>', unsafe_allow_html=True)
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TELA: DIAGNÓSTICO (IDENTICA v13.0) ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Integridade do Sistema")
        if st.button("🔍 EXECUTAR TESTE DE PING"):
            db.reference("sensor/temperatura").delete(); time.sleep(4)
            st.session_state["net_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        if st.session_state.get("net_status") == "ON": st.markdown("<div class='status-ok'>✅ CONEXÃO ATIVA</div>", unsafe_allow_html=True)
        elif st.session_state.get("net_status") == "OFF": st.markdown("<div class='status-erro'>❌ HARDWARE OFFLINE</div>", unsafe_allow_html=True)
        if st.button("REBOOT REMOTO"): db.reference("controle/restart").set(True); st.rerun()

    # --- TELA: GESTÃO DE USUÁRIOS (IDENTICA v13.0) ---
    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Gerenciamento")
        with st.form("cad_u"):
            new_n, new_l, new_s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha")
            if st.form_submit_button("CADASTRAR"):
                db.reference("usuarios_autorizados").push({"nome": new_n, "login": new_l, "senha": new_s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.rerun()
        users = db.reference("usuarios_autorizados").get()
        if users:
            for k, v in users.items(): st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> ({v.get('login')})</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v16.0
