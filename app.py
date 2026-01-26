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

# --- 1. CONFIGURAÇÃO VISUAL INTEGRAL (RESTRICT v13.0 IDENTITY) ---
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
    }

    .card-usuario { 
        background-color: #f0f2f6; padding: 15px; border-radius: 10px; 
        margin-bottom: 10px; border-left: 5px solid #00458d; 
    }
    
    .status-ok { 
        color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; 
        border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; 
    }
    
    .home-card { 
        background-color: #ffffff; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; 
        text-align: center; height: 100%; 
    }
    .home-icon { font-size: 40px; margin-bottom: 15px; }

    .gauge-card { 
        background: white; padding: 30px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; 
    }
    .gauge-value { 
        font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; 
    }
    
    .moving-bar-container { 
        width: 100%; height: 8px; background: #eee; border-radius: 10px; 
        overflow: hidden; position: relative; margin-top: 10px; 
    }
    
    .bar-on { height: 100%; width: 100%; background: linear-gradient(90deg, #28a745, #85e085, #28a745); background-size: 200% 100%; animation: moveRight 2s linear infinite; }
    .bar-off { height: 100%; width: 100%; background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); background-size: 200% 100%; animation: moveRight 2s linear infinite; }
    .bar-inativa { height: 100%; width: 100%; background: #eee; border-radius: 10px; }

    @keyframes moveRight { 0% { background-position: 200% 0; } 100% { background-position: 0 0; } }
    .blink { animation: blinker 1.2s linear infinite; display: inline-block; }
    @keyframes blinker { 50% { opacity: 0; } }

    .chat-container { background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; background-color: #ffffff; margin-bottom: 5px; border-left: 5px solid #00458d; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NÚCLEO E COMUNICAÇÃO ---
def obter_hora_brasilia():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

def enviar_email(assunto, mensagem):
    if not st.session_state.get("email_ativo", True): return
    try:
        remetente = st.secrets.get("email_user", "seu_email@gmail.com")
        senha = st.secrets.get("email_password", "sua_senha")
        msg = MIMEText(mensagem)
        msg['Subject'], msg['From'], msg['To'] = assunto, remetente, remetente
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(remetente, senha)
            server.send_message(msg)
    except: pass

@st.cache_resource
def conectar_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"],
                "token_uri": st.secrets["token_uri"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

def registrar_evento(acao):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora_f = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora_f, "usuario": usuario, "acao": acao})
        enviar_email(f"ASB: {acao}", f"Evento: {acao}\nUsuário: {usuario}\nData: {agora_f}")
    except: pass

# --- 3. ESTADOS E LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True
if "modo_operacao" not in st.session_state: st.session_state["modo_operacao"] = "MANUAL"
if "ciclo_ativo" not in st.session_state: st.session_state["ciclo_ativo"] = False

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
                            st.session_state["is_admin"] = False; st.rerun()
                st.error("Credenciais inválidas.")
else:
    conectar_firebase()
    
    # --- 5. MENU LATERAL ---
    st.sidebar.title("MENU PRINCIPAL")
    opts = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]: opts.append("👥 Gestão de Usuários")
    menu = st.sidebar.radio("Navegação:", opts)
    
    st.sidebar.divider()
    texto_wa = urllib.parse.quote(f"Olá, sou {st.session_state['user_nome']}. Gostaria de reportar uma ocorrência no sistema ASB.")
    st.sidebar.markdown(f'[💬 Suporte WhatsApp](https://wa.me/5500000000000?text={texto_wa})')
    
    if st.sidebar.button("Encerrar Sessão"): st.session_state["logado"] = False; st.rerun()

    # --- 6. TELAS ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Monitoramento contínuo de ativos industriais via nuvem com baixa latência.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Análise de Dados</h3><p>Gráficos em tempo real para tomada de decisões baseada em telemetria precisa.</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Controle de acesso multi usuários e registros de auditorias em todos os acionamentos.</p></div>""", unsafe_allow_html=True)

    elif menu == "🕹️ Acionamento":
        st.header("Controle de Ativos")
        st.session_state["modo_operacao"] = st.radio("Modo:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        status_real = db.reference("controle/led").get()
        if st.session_state["modo_operacao"] == "MANUAL":
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
            st.session_state["t_auto_v"] = ca1.number_input("Tempo Ciclo (min)", value=5)
            st.session_state["t_pisca_v"] = ca2.number_input("Velocidade Pisca (seg)", value=2)
            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR"): st.session_state["ciclo_ativo"], st.session_state["hora_inicio_ciclo"] = True, time.time(); st.rerun()
            else:
                if st.button("⏹️ PARAR"): st.session_state["ciclo_ativo"] = False; db.reference("controle/led").set("OFF"); st.rerun()
                restante = st.session_state["t_auto_v"] - ((time.time() - st.session_state["hora_inicio_ciclo"]) / 60)
                st.success(f"⚡ Operando: {restante:.2f} min"); time.sleep(1); st.rerun()

    elif menu == "🌡️ Medição":
        st.header("Telemetria Industrial")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        pct_t, pct_u = min(max((t / 60) * 100, 0), 100), min(max(u, 0), 100)
        col1, col2 = st.columns(2)
        with col1: st.markdown(f'''<div class="gauge-card">Temperatura (°C)<div class="gauge-value">{t}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        with col2: st.markdown(f'''<div class="gauge-card">Umidade (%)<div class="gauge-value">{u}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 ATUALIZAR AGORA"): 
            db.reference("historico_sensores").push({"t": t, "u": u, "data": obter_hora_brasilia().strftime('%H:%M:%S')})
            st.rerun()

    elif menu == "📊 Relatórios":
        st.header("Histórico de Atividades")
        
        # BOTÃO PARA LIMPAR HISTÓRICO (SOMENTE ADMIN)
        if st.session_state["is_admin"]:
            if st.button("🗑️ LIMPAR HISTÓRICO DE RELATÓRIOS"):
                db.reference("historico_acoes").delete()
                db.reference("historico_sensores").delete()
                st.success("Histórico excluído com sucesso!"); time.sleep(1); st.rerun()

        dados_s = db.reference("historico_sensores").get()
        if dados_s:
            df_export = pd.DataFrame(list(dados_s.values()))
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button("📥 BAIXAR RELATÓRIO DE SENSORES (CSV)", csv, "relatorio_asb.csv", "text/csv")
        st.divider()
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]; st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "🛠️ Diagnóstico":
        st.header("Status de Rede")
        st.session_state["email_ativo"] = st.checkbox("Habilitar Alertas por E-mail", value=st.session_state["email_ativo"])
        
        ultimo_p = db.reference("sensor/ultimo_pulso").get()
        online = (time.time()*1000 - ultimo_p) < 45000 if ultimo_p else False
        if online: st.markdown("<div class='status-ok'>✅ SISTEMA ONLINE</div>", unsafe_allow_html=True)
        else: st.markdown("<div class='status-alert' style='color:#dc3545; border:2px solid #dc3545; padding:20px; text-align:center; border-radius:8px; background-color:#fdecea; font-weight:bold; font-size:22px;'>⚠️ SISTEMA OFFLINE</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔁 REBOOT ESP32"): db.reference("controle/restart").set(True); st.rerun()
        with c2:
            if st.button("📡 NOVO WI-FI"): db.reference("controle/restart").set(True); st.rerun()

    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Gerenciamento de Operadores")
        with st.form("cad_u"):
            n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.rerun()

# ASB AUTOMAÇÃO INDUSTRIAL - v75.0 (Integrity Restricted)
