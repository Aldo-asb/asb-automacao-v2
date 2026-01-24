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

# --- 1. CONFIGURAÇÃO VISUAL (v11.0 - FIDELIDADE TOTAL E EXTENSA) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    /* TITULOS E SUBTITULOS */
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    
    /* ESTILO DOS BOTÕES DE ACIONAMENTO */
    div.stButton > button:first-child {
        width: 100%;
        height: 4.5em;
        font-weight: bold;
        background-color: #00458d;
        color: white;
        border-radius: 10px;
        border: none;
        font-size: 18px;
    }

    /* CARDS DE INTERFACE */
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .gauge-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; }
    .gauge-value { font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; }
    
    /* STATUS DE CONEXÃO (DETERMINADO PELO USUÁRIO) */
    .status-ok { color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 20px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; font-size: 22px; }
    
    /* FAIXAS FINAS (8PX) E ANIMADAS */
    .bar-container { width: 100%; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; position: relative; margin-top: 5px; }
    
    .bar-active-on { 
        height: 100%; width: 100%; 
        background: linear-gradient(90deg, #28a745, #85e085, #28a745); 
        background-size: 200% 100%; 
        animation: moveRight 2s linear infinite; 
    }
    
    .bar-active-off { 
        height: 100%; width: 100%; 
        background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); 
        background-size: 200% 100%; 
        animation: moveRight 2s linear infinite; 
    }
    
    .bar-inativa { height: 100%; width: 100%; background: #eee; }

    @keyframes moveRight {
        0% { background-position: 200% 0; }
        100% { background-position: 0 0; }
    }

    /* EFEITO PISCANTE NAS BOLINHAS */
    .blink { animation: blinker 1.5s linear infinite; font-weight: bold; }
    @keyframes blinker { 50% { opacity: 0; } }

    /* HISTORICO / CHAT */
    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; }
    .msg-balao { max-width: 80%; padding: 12px; border-radius: 15px; background-color: #ffffff; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NUCLEO (PRESERVADAS INTEGRALMENTE) ---
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

def enviar_email_log(usuario, acao, agora):
    try:
        remetente = st.secrets.get("email_user")
        senha = st.secrets.get("email_password")
        if remetente and senha:
            msg = MIMEText(f"LOG DO SISTEMA ASB\n\nOperador: {usuario}\nAção: {acao}\nData/Hora: {agora}")
            msg['Subject'] = f"ALERTA ASB: {acao}"
            msg['From'] = remetente
            msg['To'] = "asbautomacao@gmail.com"
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string())
            server.quit()
    except: pass

def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora, "usuario": usuario, "acao": acao})
        if st.session_state.get("email_ativo", True) or manual:
            enviar_email_log(usuario, acao, agora)
    except: pass

# --- 3. GESTÃO DE ESTADO E LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-asb'>Acesso Restrito ao Sistema IoT</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u_input = st.text_input("Usuário de Acesso")
        p_input = st.text_input("Senha de Acesso", type="password")
        if st.button("AUTENTICAR"):
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
                st.error("Credenciais não reconhecidas.")
else:
    conectar_firebase()
    menu_lista = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]: menu_lista.append("👥 Gestão de Usuários")
    
    menu = st.sidebar.radio("Navegação do Sistema:", menu_lista)
    st.session_state["email_ativo"] = st.sidebar.toggle("Notificações por E-mail", value=st.session_state["email_ativo"])
    if st.sidebar.button("Encerrar Sessão"): st.session_state["logado"] = False; st.rerun()

    # --- TELA 1: HOME ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown("<div class='home-card'><h3>Supervisão</h3><p>Monitoramento em tempo real via Firebase.</p></div>", unsafe_allow_html=True)
        with col2: st.markdown("<div class='home-card'><h3>Telemetria</h3><p>Dados de sensores processados na nuvem.</p></div>", unsafe_allow_html=True)
        with col3: st.markdown("<div class='home-card'><h3>Controle</h3><p>Acionamento remoto de ativos industriais.</p></div>", unsafe_allow_html=True)

    # --- TELA 2: ACIONAMENTO (BARRAS FINAS E BOLINHAS PISCANTES) ---
    elif menu == "🕹️ Acionamento":
        st.header("Controle de Equipamentos")
        status_real = db.reference("controle/led").get()
        c1, c2 = st.columns(2)
        
        with c1:
            # Lógica da bolinha pulsante no texto do botão
            label_ligar = "LIGAR <span class='blink'>🟢</span>" if status_real == "ON" else "LIGAR ⚪"
            if st.button("LIGAR EQUIPAMENTO", key="btn_on", help="Clique para ligar o sistema"):
                db.reference("controle/led").set("ON"); registrar_evento("LIGOU EQUIPAMENTO"); st.rerun()
            st.markdown(f"<div style='text-align:center;'>{label_ligar}</div>", unsafe_allow_html=True)
            # Faixa fina com movimento
            bar_style = "bar-active-on" if status_real == "ON" else "bar-inativa"
            st.markdown(f'<div class="bar-container"><div class="{bar_style}"></div></div>', unsafe_allow_html=True)

        with c2:
            label_desligar = "DESLIGAR <span class='blink'>🔴</span>" if status_real == "OFF" else "DESLIGAR ⚪"
            if st.button("DESLIGAR EQUIPAMENTO", key="btn_off", help="Clique para desligar o sistema"):
                db.reference("controle/led").set("OFF"); registrar_evento("DESLIGOU EQUIPAMENTO"); st.rerun()
            st.markdown(f"<div style='text-align:center;'>{label_desligar}</div>", unsafe_allow_html=True)
            # Faixa fina com movimento
            bar_style = "bar-active-off" if status_real == "OFF" else "bar-inativa"
            st.markdown(f'<div class="bar-container"><div class="{bar_style}"></div></div>', unsafe_allow_html=True)

    # --- TELA 3: MEDIÇÃO (BARRAS PROPORCIONAIS) ---
    elif menu == "🌡️ Medição":
        st.header("Telemetria de Sensores")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        
        # Proporcionalidade: Temp (0-60) Umid (0-100)
        p_t = min(max((t/60)*100, 0), 100)
        p_u = min(max(u, 0), 100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''<div class="gauge-card">Temperatura: {t}°C<div class="bar-container"><div style="height:100%; width:{p_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:4px; transition:1.2s ease-out;"></div></div></div>''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''<div class="gauge-card">Umidade: {u}%<div class="bar-container"><div style="height:100%; width:{p_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:4px; transition:1.2s ease-out;"></div></div></div>''', unsafe_allow_html=True)
        if st.button("🔄 REFRESH DADOS"): st.rerun()

    # --- TELA 4: RELATÓRIOS (HISTÓRICO + WHATSAPP) ---
    elif menu == "📊 Relatórios":
        st.header("Histórico Industrial")
        if st.button("🗑️ LIMPAR TODOS OS LOGS"):
            db.reference("historico_acoes").delete(); registrar_evento("LIMPEZA DE HISTÓRICO", manual=True); st.rerun()
        
        with st.expander("📲 Enviar Alerta via WhatsApp"):
            tel = st.text_input("Número (Ex: 5562999999999)", value="5562999999999")
            txt = st.text_area("Mensagem", "SISTEMA ASB: Relatório disponível.")
            if st.button("GERAR LINK WHATSAPP"):
                link = f"https://wa.me/{tel}?text={urllib.parse.quote(txt)}"
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">ENVIAR AGORA</div></a>', unsafe_allow_html=True)

        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TELA 5: DIAGNÓSTICO (PING E STATUS ORIGINAL) ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Integridade da Rede")
        if st.button("🔍 EXECUTAR TESTE DE PING NO HARDWARE"):
            with st.spinner("Aguardando resposta do ESP32..."):
                db.reference("sensor/temperatura").delete()
                time.sleep(4)
                st.session_state["net_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        
        if st.session_state.get("net_status") == "ON":
            st.markdown("<div class='status-ok'>✅ CONEXÃO ATIVA</div>", unsafe_allow_html=True)
        elif st.session_state.get("net_status") == "OFF":
            st.markdown("<div class='status-erro'>❌ HARDWARE OFFLINE</div>", unsafe_allow_html=True)
            
        if st.button("REBOOT REMOTO DO SISTEMA"):
            db.reference("controle/restart").set(True)
            registrar_evento("COMANDO REBOOT DISPARADO", manual=True)
            st.warning("Comando enviado. O hardware irá reiniciar.")

    # --- TELA 6: GESTÃO DE USUÁRIOS (ADMIN) ---
    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Controle de Operadores")
        with st.form("cadastro"):
            n_nome = st.text_input("Nome Completo")
            n_login = st.text_input("Login")
            n_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR OPERADOR"):
                db.reference("usuarios_autorizados").push({"nome": n_nome, "login": n_login, "senha": n_senha, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.success("Usuário registrado com sucesso.")
                st.rerun()
        
        st.subheader("Lista de Acessos")
        users = db.reference("usuarios_autorizados").get()
        if users:
            for k, v in users.items():
                st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> | Login: {v.get('login')}</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v11.0
