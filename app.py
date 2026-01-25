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

# --- 1. CONFIGURAÇÃO VISUAL INTEGRAL (v13.0 - COM AS MUDANÇAS SOLICITADAS) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .subtitulo-asb { color: #555; font-size: 20px; text-align: center; margin-bottom: 30px; }
    
    /* BOTÕES COM TAMANHO PADRONIZADO v8.7 - PRESERVADO */
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
    
    /* STATUS DE CONEXÃO DETERMINADO */
    .status-ok { color: #28a745; font-weight: bold; padding: 20px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; font-size: 22px; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 20px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; font-size: 22px; }
    
    /* CARDS HOME */
    .home-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #00458d; text-align: center; height: 100%; }
    .home-icon { font-size: 40px; margin-bottom: 15px; }

    /* CARDS MEDIÇÃO ABAULADOS */
    .gauge-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border: 1px solid #f0f0f0; }
    .gauge-value { font-size: 50px; font-weight: 800; color: #333; margin: 15px 0; }
    
    /* BARRAS AJUSTADAS: 8PX E ANIMAÇÃO DE MOVIMENTO */
    .moving-bar-container { width: 100%; height: 8px; background: #eee; border-radius: 10px; overflow: hidden; position: relative; margin-top: 10px; }
    
    .bar-on { 
        height: 100%; width: 100%; background: linear-gradient(90deg, #28a745, #85e085, #28a745); 
        background-size: 200% 100%; animation: moveRight 2s linear infinite; 
    }
    .bar-off { 
        height: 100%; width: 100%; background: linear-gradient(90deg, #dc3545, #ff8585, #dc3545); 
        background-size: 200% 100%; animation: moveRight 2s linear infinite; 
    }
    .bar-inativa { height: 100%; width: 100%; background: #eee; border-radius: 10px; }

    @keyframes moveRight {
        0% { background-position: 200% 0; }
        100% { background-position: 0 0; }
    }

    /* ANIMAÇÃO PARA A BOLINHA PISCAR */
    .blink { animation: blinker 1.2s linear infinite; display: inline-block; }
    @keyframes blinker { 50% { opacity: 0; } }

    /* CHAT/LOGS */
    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: sans-serif; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); background-color: #ffffff; margin-bottom: 5px; }
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
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state:
    st.session_state["email_ativo"] = True
if "ciclo_ativo" not in st.session_state:
    st.session_state["ciclo_ativo"] = False

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
                st.session_state["logado"] = True
                st.session_state["user_nome"] = "Admin Master"
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                conectar_firebase()
                usuarios_db = db.reference("usuarios_autorizados").get()
                if usuarios_db:
                    for key, user_data in usuarios_db.items():
                        if user_data['login'] == u_input and user_data['senha'] == p_input:
                            st.session_state["logado"] = True
                            st.session_state["user_nome"] = user_data['nome']
                            st.session_state["is_admin"] = False
                            st.rerun()
                st.error("Credenciais inválidas.")

else:
    conectar_firebase()
    
    menu_opcoes = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]:
        menu_opcoes.append("👥 Gestão de Usuários")
        
    menu = st.sidebar.radio("Navegação:", menu_opcoes)
    
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    
    if st.sidebar.button("Encerrar Sessão"): 
        st.session_state["logado"] = False
        st.rerun()

    # --- TELA: HOME ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Nuvem em tempo real.</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Análise</h3><p>Telemetria avançada.</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Auditoria completa.</p></div>""", unsafe_allow_html=True)

    # --- TELA: ACIONAMENTO (v23.1 - LED FÍSICO COM TEXTO BASE v13.0) ---
    elif menu == "🕹️ Acionamento":
        st.header("Controle de Ativos")
        
        modo = st.radio("Seletor de Operação:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        status_real = db.reference("controle/led").get()

        if modo == "MANUAL":
            st.session_state["ciclo_ativo"] = False
            c1, c2 = st.columns(2)
            with c1:
                bola_v = "<span class='blink'>🟢</span>" if status_real == 'ON' else "⚪"
                if st.button(f"LIGAR"):
                    db.reference("controle/led").set("ON")
                    registrar_evento("LIGOU")
                    st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:0;'>{bola_v}</p>", unsafe_allow_html=True)
                estilo_on = "bar-on" if status_real == "ON" else "bar-inativa"
                st.markdown(f'<div class="moving-bar-container"><div class="{estilo_on}"></div></div>', unsafe_allow_html=True)
            with c2:
                bola_r = "<span class='blink'>🔴</span>" if status_real == 'OFF' else "⚪"
                if st.button(f"DESLIGAR"):
                    db.reference("controle/led").set("OFF")
                    registrar_evento("DESLIGOU")
                    st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:0;'>{bola_r}</p>", unsafe_allow_html=True)
                estilo_off = "bar-off" if status_real == "OFF" else "bar-inativa"
                st.markdown(f'<div class="moving-bar-container"><div class="{estilo_off}"></div></div>', unsafe_allow_html=True)
        
        else: # AUTOMÁTICO
            st.info("🤖 MODO AUTOMÁTICO: Ciclo controlado por tempo.")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                t_trabalho = st.number_input("Tempo de Trabalho (min)", min_value=1, value=5)
            with col_t2:
                t_pisca = st.number_input("Velocidade Pisca (seg)", min_value=1, value=2)
            
            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR CICLO"):
                    st.session_state["ciclo_ativo"] = True
                    registrar_evento("INICIOU CICLO AUTO")
                    st.rerun()
            else:
                if st.button("⏹️ PARAR CICLO"):
                    st.session_state["ciclo_ativo"] = False
                    db.reference("controle/led").set("OFF")
                    st.rerun()
                
                agora = obter_hora_brasilia()
                if agora.minute < t_trabalho:
                    # LÓGICA DE PULSO PARA O LED FÍSICO
                    estado = "ON" if (agora.second // t_pisca) % 2 == 0 else "OFF"
                    db.reference("controle/led").set(estado)
                    
                    if estado == "ON":
                        st.success("⚡ CICLO ATIVO: PULSANDO (ON)")
                    else:
                        st.warning("⚡ CICLO ATIVO: PULSANDO (OFF)")
                    time.sleep(1)
                    st.rerun()
                else:
                    db.reference("controle/led").set("OFF")
                    st.info("⏳ CICLO FINALIZADO. AGUARDANDO PRÓXIMA HORA.")
                    time.sleep(5)
                    st.rerun()

    # --- TELA: MEDIÇÃO (v13.0 + REFRESH) ---
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
            
        if st.button("🔄 REFRESH"):
            st.rerun()

    # --- TELA: RELATÓRIOS ---
    elif menu == "📊 Relatórios":
        st.header("Histórico de Atividades")
        
        if st.button("🗑️ LIMPAR HISTÓRICO"):
            db.reference("historico_acoes").delete()
            registrar_evento("LIMPEZA", manual=True)
            st.rerun()
        
        with st.expander("📲 Notificar via WhatsApp"):
            tel = st.text_input("Número (com DDD)", value="5562999999999")
            msg_w = st.text_area("Mensagem", "Relatório ASB: Equipamento operando normalmente.")
            if st.button("ABRIR CONVERSA"):
                link = f"https://wa.me/{tel}?text={urllib.parse.quote(msg_w)}"
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">ENVIAR AGORA</div></a>', unsafe_allow_html=True)

        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f'<div class="msg-balao"><b>{v.get("usuario")}</b>: {v.get("acao")} <br><small>{v.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TELA: DIAGNÓSTICO ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Status de Conectividade")
        
        if st.button("🔍 EXECUTAR PING NO HARDWARE"):
            with st.spinner("Sondando ESP32..."):
                db.reference("sensor/temperatura").delete()
                time.sleep(4)
                st.session_state["net_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        
        if st.session_state.get("net_status") == "ON":
            st.markdown("<div class='status-ok'>✅ CONEXÃO ATIVA</div>", unsafe_allow_html=True)
        elif st.session_state.get("net_status") == "OFF":
            st.markdown("<div class='status-erro'>❌ HARDWARE OFFLINE</div>", unsafe_allow_html=True)
            
        if st.button("REBOOT REMOTO"):
            db.reference("controle/restart").set(True)
            registrar_evento("COMANDO REBOOT ENVIADO")
            st.warning("Comando enviado.")

    # --- TELA: USUÁRIOS ---
    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Gerenciamento de Operadores")
        
        with st.form("cad_user"):
            new_n = st.text_input("Nome Completo")
            new_l = st.text_input("Login de Acesso")
            new_s = st.text_input("Senha", type="password")
            
            if st.form_submit_button("CADASTRAR NOVO USUÁRIO"):
                db.reference("usuarios_autorizados").push({
                    "nome": new_n, 
                    "login": new_l, 
                    "senha": new_s, 
                    "data": obter_hora_brasilia().strftime('%d/%m/%Y')
                })
                st.success("Usuário cadastrado com sucesso!")
                st.rerun()
        
        st.subheader("Usuários Cadastrados")
        users = db.reference("usuarios_autorizados").get()
        if users:
            for k, v in users.items():
                st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> | Login: {v.get('login')} | Desde: {v.get('data')}</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v23.1
