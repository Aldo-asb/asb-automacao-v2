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

# --- 1. CONFIGURAÇÃO VISUAL INTEGRAL (PADRÃO v13.0 / v37.0 - CORREÇÃO DE ALINHAMENTO) ---
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
    
    /* PADRONIZAÇÃO DOS BOTÕES PARA ALINHAMENTO PERFEITO */
    div.stButton > button:first-child {
        width: 100%;
        height: 4.5em;
        font-weight: bold;
        background-color: #00458d;
        color: white;
        border-radius: 10px;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
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

    .gauge-card { 
        background: white; 
        padding: 30px; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        text-align: center; 
        border: 1px solid #f0f0f0; 
    }
    
    /* BARRAS DE STATUS 8PX COM ALINHAMENTO FIXO */
    .moving-bar-container { 
        width: 100%; 
        height: 8px; 
        background: #eee; 
        border-radius: 10px; 
        overflow: hidden; 
        position: relative; 
        margin-top: 15px; 
    }
    
    .bar-on { 
        height: 100%; width: 100%; 
        background: linear-gradient(90deg, #28a745, #85e085, #28a745); 
        background-size: 200% 100%; animation: moveRight 2s linear infinite; 
    }
    .bar-off { 
        height: 100%; width: 100%; 
        background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); 
        background-size: 200% 100%; animation: moveRight 2s linear infinite; 
    }
    .bar-inativa { height: 100%; width: 100%; background: #eee; border-radius: 10px; }

    @keyframes moveRight { 0% { background-position: 200% 0; } 100% { background-position: 0 0; } }
    .blink { animation: blinker 1.2s linear infinite; display: inline-block; }
    @keyframes blinker { 50% { opacity: 0; } }

    .chat-container { 
        background-color: #e5ddd5; 
        padding: 20px; 
        border-radius: 15px; 
        max-height: 400px; 
        overflow-y: auto; 
    }
    .msg-balao { 
        max-width: 70%; padding: 10px 15px; border-radius: 15px; background-color: #ffffff; 
        margin-bottom: 5px; border-left: 5px solid #00458d; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NÚCLEO ---
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
    agora_f = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora_f, "usuario": usuario, "acao": acao})
        if st.session_state.get("email_ativo", True) or manual:
            remetente, senha = st.secrets.get("email_user"), st.secrets.get("email_password")
            if remetente and senha:
                msg = MIMEText(f"SISTEMA ASB AUTOMACAO\n\nUsuario: {usuario}\nAcao: {acao}\nData/Hora: {agora_f}")
                msg['Subject'] = f"LOG ASB: {acao}"; msg['From'] = remetente; msg['To'] = "asbautomacao@gmail.com"
                with smtplib.SMTP('smtp.gmail.com', 587) as s:
                    s.starttls(); s.login(remetente, senha); s.send_message(msg)
    except: pass

# --- 3. INICIALIZAÇÃO E LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True
if "modo_operacao" not in st.session_state: st.session_state["modo_operacao"] = "MANUAL"
if "ciclo_ativo" not in st.session_state: st.session_state["ciclo_ativo"] = False

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
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
                            st.session_state["is_admin"] = False; st.rerun()
                st.error("Credenciais inválidas.")
else:
    conectar_firebase()
    
    # --- 4. LÓGICA AUTO ---
    if st.session_state["modo_operacao"] == "AUTOMÁTICO" and st.session_state["ciclo_ativo"]:
        agora_seg = time.time()
        decorrido = (agora_seg - st.session_state.get("hora_inicio_ciclo", 0)) / 60
        if decorrido < st.session_state.get("t_auto_v", 5):
            est = "ON" if (int(agora_seg) // st.session_state.get("t_pisca_v", 2)) % 2 == 0 else "OFF"
            if st.session_state.get("last_auto_s") != est:
                db.reference("controle/led").set(est); st.session_state["last_auto_s"] = est
        else:
            db.reference("controle/led").set("OFF"); st.session_state["ciclo_ativo"] = False

    # --- 5. MENU ---
    st.sidebar.title("MENU PRINCIPAL")
    opts = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]: opts.append("👥 Gestão de Usuários")
    menu = st.sidebar.radio("Navegação:", opts)
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    if st.sidebar.button("Sair"): st.session_state["logado"] = False; st.rerun()

    # --- 6. TELAS ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitulo-asb'>Centro de Controle de Operações</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class='home-card'><h3>Supervisão IoT</h3><p>Tempo real.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class='home-card'><h3>Análise</h3><p>Telemetria.</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class='home-card'><h3>Segurança</h3><p>Auditoria.</p></div>""", unsafe_allow_html=True)

    elif menu == "🕹️ Acionamento":
        st.header("Painel de Controle")
        st.session_state["modo_operacao"] = st.radio("Selecione:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        status_real = db.reference("controle/led").get()
        
        if st.session_state["modo_operacao"] == "MANUAL":
            # ALINHAMENTO CORRIGIDO EM 3 COLUNAS IGUAIS
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("LIGAR"): db.reference("controle/led").set("ON"); registrar_evento("LIGOU"); st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px;'>{'<span class=\"blink\">🟢</span>' if status_real == 'ON' else '⚪'}</p>", unsafe_allow_html=True)
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-on" if status_real == "ON" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
            with c2:
                if st.button("REPOUSO"): db.reference("controle/led").set("REPOUSO"); registrar_evento("REPOUSO"); st.rerun()
                st.markdown("<p style='text-align:center; font-size:25px;'>💤</p>", unsafe_allow_html=True)
                st.markdown('<div class="moving-bar-container"><div class="bar-inativa"></div></div>', unsafe_allow_html=True)
            with c3:
                if st.button("DESLIGAR"): db.reference("controle/led").set("OFF"); registrar_evento("DESLIGOU"); st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px;'>{'<span class=\"blink\">🔴</span>' if status_real == 'OFF' else '⚪'}</p>", unsafe_allow_html=True)
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-off" if status_real == "OFF" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
        else:
            st.info("🤖 MODO AUTOMÁTICO ATIVO")
            ca1, ca2 = st.columns(2)
            st.session_state["t_auto_v"] = ca1.number_input("Minutos", value=5)
            st.session_state["t_pisca_v"] = ca2.number_input("Segundos", value=2)
            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR"): st.session_state["ciclo_ativo"], st.session_state["hora_inicio_ciclo"] = True, time.time(); st.rerun()
            else:
                if st.button("⏹️ PARAR"): st.session_state["ciclo_ativo"] = False; db.reference("controle/led").set("OFF"); st.rerun()
                st.success(f"⚡ Operando... {((time.time() - st.session_state['hora_inicio_ciclo'])/60):.2f} min"); time.sleep(1); st.rerun()

    elif menu == "🌡️ Medição":
        st.header("Sensores")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        if t > 45 and st.session_state["email_ativo"]: registrar_evento(f"ALERTA TEMP: {t}C")
        pct_t, pct_u = min(max((t/60)*100, 0), 100), min(max(u, 0), 100)
        col1, col2 = st.columns(2)
        with col1: st.markdown(f'''<div class="gauge-card">Temperatura (°C)<div class="gauge-value">{t}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        with col2: st.markdown(f'''<div class="gauge-card">Umidade (%)<div class="gauge-value">{u}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()

    elif menu == "📊 Relatórios":
        st.header("Logs")
        if st.button("🗑️ LIMPAR HISTÓRICO"): db.reference("historico_acoes").delete(); st.rerun()
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "🛠️ Diagnóstico":
        st.header("Hardware")
        c1, c2 = st.columns(2)
        if c1.button("🔍 PING"):
            db.reference("sensor/temperatura").delete(); time.sleep(4)
            st.session_state["net_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        if c2.button("⚠️ RESET"): db.reference("controle/sistema").set("RESET"); st.warning("Reset enviado.")
        if st.session_state.get("net_status") == "ON": st.markdown("<div class='status-ok'>✅ ONLINE</div>", unsafe_allow_html=True)

    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Usuários")
        with st.form("cad_u"):
            n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.success("Cadastrado!"); st.rerun()
        users = db.reference("usuarios_autorizados").get()
        if users:
            for k, v in users.items():
                st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> | Login: {v.get('login')}</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v54.0
