import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd
import time
import pytz

# --- 1. CONFIGURAÇÃO VISUAL INTEGRAL (PADRÃO v13.0 / v37.0) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { 
        color: #00458d; 
        font-size: 55px; 
        font-weight: bold; 
        text-align: center; 
        margin-top: 40px; 
        border-bottom: 3px solid #00458d; 
    }
    .subtitulo-asb { 
        color: #555; 
        font-size: 20px; 
        text-align: center; 
        margin-bottom: 30px; 
    }
    
    div.stButton > button:first-child {
        width: 100%;
        height: 4.5em;
        font-weight: bold;
        background-color: #00458d;
        color: white;
        border-radius: 10px;
        border: none;
        display: block;
        margin: auto;
    }

    .card-usuario { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border-left: 5px solid #00458d; 
    }
    
    .status-ok { 
        color: #28a745; 
        font-weight: bold; 
        padding: 20px; 
        border: 2px solid #28a745; 
        border-radius: 8px; 
        text-align: center; 
        background-color: #e8f5e9; 
        font-size: 22px; 
    }
    
    .home-card { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border-top: 5px solid #00458d; 
        text-align: center; 
        height: 100%; 
    }
    .home-icon { 
        font-size: 40px; 
        margin-bottom: 15px; 
    }

    .gauge-card { 
        background: white; 
        padding: 30px; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        text-align: center; 
        border: 1px solid #f0f0f0; 
    }
    .gauge-value { 
        font-size: 50px; 
        font-weight: 800; 
        color: #333; 
        margin: 15px 0; 
    }
    
    .moving-bar-container { 
        width: 100%; 
        height: 8px; 
        background: #eee; 
        border-radius: 10px; 
        overflow: hidden; 
        position: relative; 
        margin-top: 20px; 
    }
    
    .bar-on { 
        height: 100%; 
        width: 100%; 
        background: linear-gradient(90deg, #28a745, #85e085, #28a745); 
        background-size: 200% 100%; 
        animation: moveRight 2s linear infinite; 
    }
    .bar-off { 
        height: 100%; 
        width: 100%; 
        background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); 
        background-size: 200% 100%; 
        animation: moveRight 2s linear infinite; 
    }
    .bar-inativa { 
        height: 100%; 
        width: 100%; 
        background: #eee; 
        border-radius: 10px; 
    }

    .chat-container { 
        display: flex; 
        flex-direction: column; 
        gap: 10px; 
        background-color: #e5ddd5; 
        padding: 20px; 
        border-radius: 15px; 
        max-height: 400px; 
        overflow-y: auto; 
        margin-bottom: 20px; 
    }
    .msg-balao { 
        max-width: 70%; 
        padding: 10px 15px; 
        border-radius: 15px; 
        font-family: sans-serif; 
        box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); 
        background-color: #ffffff; 
        margin-bottom: 5px; 
        border-left: 5px solid #00458d;
    }

    @keyframes moveRight {
        0% { background-position: 200% 0; }
        100% { background-position: 0 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NÚCLEO E E-MAIL ---
def obter_hora_brasilia():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M:%S')

def enviar_email_alerta(temp):
    try:
        msg = MIMEText(f"ALERTA CRÍTICO: Temperatura atingiu {temp}°C em {obter_hora_brasilia()}.")
        msg['Subject'] = '⚠️ ALERTA ASB - TEMPERATURA'
        msg['From'] = 'asbalerta@gmail.com'
        msg['To'] = 'asbconsultoria@gmail.com'
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('asbalerta@gmail.com', 'sua_senha_app')
            server.send_message(msg)
        return True
    except: return False

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

# --- 3. INICIALIZAÇÃO DE ESTADOS ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ciclo_ativo" not in st.session_state: st.session_state["ciclo_ativo"] = False
if "hora_inicio_ciclo" not in st.session_state: st.session_state["hora_inicio_ciclo"] = None
if "modo_operacao" not in st.session_state: st.session_state["modo_operacao"] = "MANUAL"

# --- 4. LOGIN ---
if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-asb'>Plataforma Integrada IoT</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if u == "admin" and p == "asb2026":
                st.session_state["logado"], st.session_state["user_nome"], st.session_state["is_admin"] = True, "Admin Master", True
                st.rerun()
            else:
                conectar_firebase()
                usrs = db.reference("usuarios_autorizados").get()
                if usrs:
                    for k, v in usrs.items():
                        if v['login'] == u and v['senha'] == p:
                            st.session_state["logado"], st.session_state["user_nome"] = True, v['nome']
                            st.rerun()
                st.error("Credenciais inválidas.")
else:
    conectar_firebase()
    
    # --- 5. LÓGICA DE SEGURANÇA ---
    if st.session_state["modo_operacao"] == "AUTOMÁTICO" and st.session_state["ciclo_ativo"]:
        agora = time.time()
        decorrido = (agora - st.session_state["hora_inicio_ciclo"]) / 60
        if decorrido < st.session_state.get("t_auto_temp", 5):
            est = "ON" if (int(agora) // st.session_state.get("t_pisca_temp", 2)) % 2 == 0 else "OFF"
            if st.session_state.get("last_s") != est:
                db.reference("controle/led").set(est)
                st.session_state["last_s"] = est
        else:
            db.reference("controle/led").set("OFF")
            st.session_state["ciclo_ativo"] = False

    # --- 6. MENU ---
    st.sidebar.title("MENU PRINCIPAL")
    opts = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]: opts.append("👥 Gestão de Usuários")
    menu = st.sidebar.radio("Selecione:", opts)
    if st.sidebar.button("Sair"): st.session_state["logado"] = False; st.rerun()

    # --- 7. TELAS ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitulo-asb'>Bem-vindo ao Centro de Controle de Operações</div>", unsafe_allow_html=True)
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Controle e monitoramento em nuvem em tempo real.</p></div>""", unsafe_allow_html=True)
        with col_h2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Telemetria</h3><p>Análise de dados industriais e sensores.</p></div>""", unsafe_allow_html=True)
        with col_h3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Histórico completo de auditoria e logs.</p></div>""", unsafe_allow_html=True)

    elif menu == "🕹️ Acionamento":
        st.header("Painel de Comando de Ativos")
        st.session_state["modo_operacao"] = st.radio("Modo:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        status = db.reference("controle/led").get()
        if st.session_state["modo_operacao"] == "MANUAL":
            c1, c0, c2 = st.columns(3)
            with c1:
                st.write(f"Status: {'🟢' if status == 'ON' else '⚪'}")
                if st.button("LIGAR"): db.reference("controle/led").set("ON"); st.rerun()
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-on" if status == "ON" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
            with c0:
                st.write("Status: 💤")
                if st.button("REPOUSO"): db.reference("controle/led").set("REPOUSO"); st.rerun()
                st.markdown('<div class="moving-bar-container"><div class="bar-inativa"></div></div>', unsafe_allow_html=True)
            with c2:
                st.write(f"Status: {'🔴' if status == 'OFF' else '⚪'}")
                if st.button("DESLIGAR"): db.reference("controle/led").set("OFF"); st.rerun()
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-off" if status == "OFF" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
        else:
            st.info("🤖 MODO AUTOMÁTICO")
            c_a1, c_a2 = st.columns(2)
            st.session_state["t_auto_temp"] = c_a1.number_input("Minutos", value=5)
            st.session_state["t_pisca_temp"] = c_a2.number_input("Segundos", value=2)
            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR"): st.session_state["ciclo_ativo"], st.session_state["hora_inicio_ciclo"] = True, time.time(); st.rerun()
            else:
                if st.button("⏹️ PARAR"): st.session_state["ciclo_ativo"] = False; db.reference("controle/led").set("OFF"); st.rerun()
                restante = st.session_state["t_auto_temp"] - ((time.time() - st.session_state["hora_inicio_ciclo"]) / 60)
                st.success(f"Tempo: {restante:.2f} min"); time.sleep(1); st.rerun()

    elif menu == "🌡️ Medição":
        st.header("Monitoramento de Sensores")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        if t > 45: enviar_email_alerta(t); st.error("⚠️ ALERTA ENVIADO!")
        pct_t, pct_u = min(max((t/60)*100, 0), 100), min(max(u, 0), 100)
        col_s1, col_s2 = st.columns(2)
        with col_s1: st.markdown(f'''<div class="gauge-card">Temp (°C)<div class="gauge-value">{t}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        with col_s2: st.markdown(f'''<div class="gauge-card">Umid (%)<div class="gauge-value">{u}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()

    elif menu == "📊 Relatórios":
        st.header("Histórico Logístico")
        if st.button("🗑️ LIMPAR REGISTROS"): db.reference("historico_acoes").delete(); st.rerun()
        hist = db.reference("historico_acoes").get()
        if hist:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(hist.keys())):
                i = hist[k]
                st.markdown(f'<div class="msg-balao"><b>{i.get("usuario")}:</b> {i.get("acao")}<br><small>{i.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "🛠️ Diagnóstico":
        st.header("Estado de Rede e Hardware")
        c_d1, c_d2 = st.columns(2)
        if c_d1.button("🔍 PING REDE"):
            db.reference("sensor/temperatura").delete(); time.sleep(4)
            st.session_state["ping"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        if c_d2.button("⚠️ RESET ESP32"): db.reference("controle/sistema").set("RESET"); st.warning("Comando enviado.")
        if st.session_state.get("ping") == "ON": st.success("SISTEMA ONLINE")

# ASB AUTOMAÇÃO INDUSTRIAL - v51.0
