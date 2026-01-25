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

# --- 1. CONFIGURAÇÃO VISUAL INTEGRAL (v13.0 - MANUTENÇÃO ABSOLUTA DO PADRÃO) ---
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
    .status-erro { 
        color: #dc3545; 
        font-weight: bold; 
        padding: 20px; 
        border: 2px solid #dc3545; 
        border-radius: 8px; 
        text-align: center; 
        background-color: #ffebee; 
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

    @keyframes moveRight {
        0% { background-position: 200% 0; }
        100% { background-position: 0 0; }
    }

    .blink { 
        animation: blinker 1.2s linear infinite; 
        display: inline-block; 
    }
    @keyframes blinker { 50% { opacity: 0; } }

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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE NÚCLEO E CONECTIVIDADE ---
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
            st.error(f"Erro na Conexão: {e}")
            return False
    return True

# --- 3. INICIALIZAÇÃO DE ESTADOS ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True
if "ciclo_ativo" not in st.session_state: st.session_state["ciclo_ativo"] = False
if "hora_inicio_ciclo" not in st.session_state: st.session_state["hora_inicio_ciclo"] = None
if "t_auto_temp" not in st.session_state: st.session_state["t_auto_temp"] = 5
if "t_pisca_temp" not in st.session_state: st.session_state["t_pisca_temp"] = 2
if "modo_operacao_selecionado" not in st.session_state: st.session_state["modo_operacao_selecionado"] = "MANUAL"

# --- 4. LOGIN ---
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
                            st.session_state["logado"], st.session_state["user_nome"] = True, user_data['nome']
                            st.rerun()
                st.error("Credenciais inválidas.")
else:
    conectar_firebase()
    
    # --- 5. LÓGICA DE SEGURANÇA GLOBAL (v41.0) ---
    # O Ciclo automático SÓ envia comandos se o seletor estiver em "AUTOMÁTICO"
    if st.session_state["modo_operacao_selecionado"] == "AUTOMÁTICO":
        if st.session_state["ciclo_ativo"] and st.session_state["hora_inicio_ciclo"]:
            agora_atual = time.time()
            tempo_decorrido = (agora_atual - st.session_state["hora_inicio_ciclo"]) / 60
            if tempo_decorrido < st.session_state["t_auto_temp"]:
                estado_calculado = "ON" if (int(agora_atual) // st.session_state["t_pisca_temp"]) % 2 == 0 else "OFF"
                if st.session_state.get("last_auto_state") != estado_calculado:
                    db.reference("controle/led").set(estado_calculado)
                    st.session_state["last_auto_state"] = estado_calculado
            else:
                db.reference("controle/led").set("OFF")
                st.session_state["ciclo_ativo"] = False

    # --- 6. BARRA LATERAL ---
    st.sidebar.title("MENU PRINCIPAL")
    menu_opcoes = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]: menu_opcoes.append("👥 Gestão de Usuários")
    menu = st.sidebar.radio("Selecione a tela:", menu_opcoes)
    st.sidebar.markdown("---")
    st.session_state["email_ativo"] = st.sidebar.toggle("Notificações por E-mail", value=st.session_state["email_ativo"])
    if st.sidebar.button("Sair do Sistema"): st.session_state["logado"] = False; st.rerun()

    # --- 7. TELAS ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Controle e monitoramento em nuvem em tempo real.</p></div>""", unsafe_allow_html=True)
        with col_h2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Telemetria</h3><p>Análise de dados industriais e sensores.</p></div>""", unsafe_allow_html=True)
        with col_h3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Histórico completo de auditoria e logs.</p></div>""", unsafe_allow_html=True)
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    elif menu == "🕹️ Acionamento":
        st.header("Painel de Comando de Ativos")
        # Seletor de Modo Global
        st.session_state["modo_operacao_selecionado"] = st.radio("Selecione o Modo de Operação:", ["MANUAL", "AUTOMÁTICO"], horizontal=True, index=0 if st.session_state["modo_operacao_selecionado"] == "MANUAL" else 1)
        
        status_atual_led = db.reference("controle/led").get()
        
        if st.session_state["modo_operacao_selecionado"] == "MANUAL":
            col_m1, col_m0, col_m2 = st.columns(3)
            with col_m1:
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:10px;'>{'🟢' if status_atual_led == 'ON' else '⚪'}</p>", unsafe_allow_html=True)
                if st.button("LIGAR ATIVO"):
                    db.reference("controle/led").set("ON")
                    st.rerun()
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-on" if status_atual_led == "ON" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
            with col_m0:
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:10px;'>💤</p>", unsafe_allow_html=True)
                if st.button("REPOUSO"):
                    db.reference("controle/led").set("REPOUSO")
                    st.rerun()
                st.markdown('<div class="moving-bar-container"><div class="bar-inativa"></div></div>', unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:10px;'>{'🔴' if status_atual_led == 'OFF' else '⚪'}</p>", unsafe_allow_html=True)
                if st.button("DESLIGAR ATIVO"):
                    db.reference("controle/led").set("OFF")
                    st.rerun()
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-off" if status_atual_led == "OFF" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
        
        else: # AUTOMÁTICO
            st.info("🤖 MODO AUTOMÁTICO ATIVO - Comandos manuais bloqueados por segurança.")
            c_a1, c_a2 = st.columns(2)
            with c_a1: st.session_state["t_auto_temp"] = st.number_input("Tempo de Ciclo (min)", min_value=1, value=st.session_state["t_auto_temp"])
            with c_a2: st.session_state["t_pisca_temp"] = st.number_input("Velocidade Pisca (seg)", min_value=1, value=st.session_state["t_pisca_temp"])
            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR CICLO"): st.session_state["ciclo_ativo"], st.session_state["hora_inicio_ciclo"] = True, time.time(); st.rerun()
            else:
                if st.button("⏹️ PARAR OPERAÇÃO"): st.session_state["ciclo_ativo"] = False; db.reference("controle/led").set("OFF"); st.rerun()
                restante = st.session_state["t_auto_temp"] - ((time.time() - st.session_state["hora_inicio_ciclo"]) / 60)
                st.success(f"⚡ OPERAÇÃO EM CURSO - Restante: {restante:.2f} min"); time.sleep(1); st.rerun()

    elif menu == "🌡️ Medição":
        st.header("Monitoramento de Sensores")
        temp_val, umid_val = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        pct_t, pct_u = min(max((temp_val/60)*100, 0), 100), min(max(umid_val, 0), 100)
        col_s1, col_s2 = st.columns(2)
        with col_s1: st.markdown(f'''<div class="gauge-card">Temperatura (°C)<div class="gauge-value">{temp_val}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        with col_s2: st.markdown(f'''<div class="gauge-card">Umidade (%)<div class="gauge-value">{umid_val}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        if st.button("🔄 ATUALIZAR LEITURAS"): st.rerun()
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    elif menu == "📊 Relatórios":
        st.header("Histórico Logístico")
        if st.button("🗑️ LIMPAR REGISTROS"): db.reference("historico_acoes").delete(); st.rerun()
        historico = db.reference("historico_acoes").get()
        if historico:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for key in reversed(list(historico.keys())):
                item = historico[key]; st.markdown(f'<div class="msg-balao"><b>{item.get("usuario")}</b><br>{item.get("acao")}<br><small>{item.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    elif menu == "🛠️ Diagnóstico":
        st.header("Estado de Rede")
        if st.button("🔍 PING"):
            db.reference("sensor/temperatura").delete(); time.sleep(4)
            st.session_state["ping_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        if st.session_state.get("ping_status") == "ON": st.markdown("<div class='status-ok'>✅ ONLINE</div>", unsafe_allow_html=True)
        elif st.session_state.get("ping_status") == "OFF": st.markdown("<div class='status-erro'>❌ OFFLINE</div>", unsafe_allow_html=True)
        if st.button("REBOOT"): db.reference("controle/restart").set(True); st.warning("Enviado.")
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Operadores")
        with st.form("f_cad"):
            n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.rerun()
        lista = db.reference("usuarios_autorizados").get()
        if lista:
            for k, v in lista.items(): st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b></div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v41.0
