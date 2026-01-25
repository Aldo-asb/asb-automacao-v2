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

    .card-usuario { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border-left: 5px solid #00458d; 
    }
    
    /* STATUS DE CONEXÃO DETERMINADO */
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
    
    /* CARDS HOME */
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

    /* CARDS MEDIÇÃO ABAULADOS */
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
    
    /* BARRAS AJUSTADAS: 8PX E ANIMAÇÃO DE MOVIMENTO */
    .moving-bar-container { 
        width: 100%; 
        height: 8px; 
        background: #eee; 
        border-radius: 10px; 
        overflow: hidden; 
        position: relative; 
        margin-top: 10px; 
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

    /* ANIMAÇÃO PARA A BOLINHA PISCAR */
    .blink { 
        animation: blinker 1.2s linear infinite; 
        display: inline-block; 
    }
    @keyframes blinker { 50% { opacity: 0; } }

    /* CHAT/LOGS */
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

# --- 2. FUNÇÕES DE NÚCLEO E CONECTIVIDADE (v13.0) ---
def obter_hora_brasilia():
    """Retorna o horário atual ajustado para o fuso de Brasília."""
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

@st.cache_resource
def conectar_firebase():
    """Estabelece a conexão com o banco de dados Firebase Realtime."""
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
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'
            })
            return True
        except Exception as e:
            st.error(f"Erro na Conexão com Firebase: {e}")
            return False
    return True

def registrar_evento(acao, manual=False):
    """Registra logs no Firebase e envia e-mail de notificação se ativo."""
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({
            "data": agora, 
            "usuario": usuario, 
            "acao": acao
        })
        
        if st.session_state.get("email_ativo", True) or manual:
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            
            if remetente and senha:
                msg = MIMEText(f"SISTEMA ASB AUTOMACAO\n\nUsuario: {usuario}\nAcao: {acao}\nData/Hora: {agora}")
                msg['Subject'] = f"LOG DE SISTEMA: {acao}"
                msg['From'] = remetente
                msg['To'] = "asbautomacao@gmail.com"
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(remetente, senha)
                server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string())
                server.quit()
    except Exception as e:
        pass

# --- 3. INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state:
    st.session_state["email_ativo"] = True
if "ciclo_ativo" not in st.session_state:
    st.session_state["ciclo_ativo"] = False
if "hora_inicio_ciclo" not in st.session_state:
    st.session_state["hora_inicio_ciclo"] = None
if "t_auto_temp" not in st.session_state:
    st.session_state["t_auto_temp"] = 5
if "t_pisca_temp" not in st.session_state:
    st.session_state["t_pisca_temp"] = 2

# --- 4. CONTROLE DE ACESSO ---
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
    
    # --- 5. LÓGICA DE CICLO GLOBAL (v35.0) ---
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
            registrar_evento("CICLO AUTOMÁTICO FINALIZADO")

    # --- 6. BARRA LATERAL ---
    st.sidebar.title("MENU PRINCIPAL")
    menu_opcoes = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
    if st.session_state["is_admin"]:
        menu_opcoes.append("👥 Gestão de Usuários")
        
    menu = st.sidebar.radio("Selecione a tela:", menu_opcoes)
    st.sidebar.markdown("---")
    st.session_state["email_ativo"] = st.sidebar.toggle("Notificações por E-mail", value=st.session_state["email_ativo"])
    
    if st.sidebar.button("Sair do Sistema"): 
        st.session_state["logado"] = False
        st.rerun()

    # --- 7. TELAS ---

    # --- TELA: HOME ---
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1: st.markdown("""<div class='home-card'><div class='home-icon'>🚀</div><h3>Supervisão IoT</h3><p>Controle em nuvem em tempo real.</p></div>""", unsafe_allow_html=True)
        with col_h2: st.markdown("""<div class='home-card'><div class='home-icon'>📈</div><h3>Telemetria</h3><p>Análise de dados industriais.</p></div>""", unsafe_allow_html=True)
        with col_h3: st.markdown("""<div class='home-card'><div class='home-icon'>🛡️</div><h3>Segurança</h3><p>Histórico completo de auditoria.</p></div>""", unsafe_allow_html=True)
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    # --- TELA: ACIONAMENTO (v35.0 - ESTADO EM REPOUSO) ---
    elif menu == "🕹️ Acionamento":
        st.header("Painel de Comando de Ativos")
        modo_operacao = st.radio("Selecione o Modo de Operação:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        status_atual_led = db.reference("controle/led").get()

        if modo_operacao == "MANUAL":
            # Adicionado o Botão de Repouso (Estado 0) para evitar conflitos
            col_m1, col_m0, col_m2 = st.columns(3)
            
            with col_m1:
                indicador_v = "<span class='blink'>🟢</span>" if status_atual_led == 'ON' else "⚪"
                if st.button("LIGAR ATIVO"):
                    db.reference("controle/led").set("ON")
                    registrar_evento("MANUAL: LIGADO")
                    st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:0;'>{indicador_v}</p>", unsafe_allow_html=True)
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-on" if status_atual_led == "ON" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
            
            with col_m0: # BOTÃO DE ESTADO 0 / REPOUSO
                st.markdown("<p style='text-align:center; color:#555; font-weight:bold; margin-top:10px;'>ESTADO 0</p>", unsafe_allow_html=True)
                if st.button("REPOUSO (OFF)"):
                    db.reference("controle/led").set("OFF")
                    registrar_evento("MANUAL: REPOUSO")
                    st.rerun()
                st.markdown("<p style='text-align:center; font-size:25px; margin-bottom:0;'>💤</p>", unsafe_allow_html=True)
                st.markdown('<div class="moving-bar-container"><div class="bar-inativa"></div></div>', unsafe_allow_html=True)

            with col_m2:
                indicador_r = "<span class='blink'>🔴</span>" if status_atual_led == 'OFF' else "⚪"
                if st.button("DESLIGAR ATIVO"):
                    db.reference("controle/led").set("OFF")
                    registrar_evento("MANUAL: DESLIGADO")
                    st.rerun()
                st.markdown(f"<p style='text-align:center; font-size:25px; margin-bottom:0;'>{indicador_r}</p>", unsafe_allow_html=True)
                st.markdown(f'<div class="moving-bar-container"><div class="{"bar-off" if status_atual_led == "OFF" else "bar-inativa"}"></div></div>', unsafe_allow_html=True)
        
        else: # AUTOMÁTICO
            st.info("🤖 MODO AUTOMÁTICO ATIVO")
            col_a1, col_a2 = st.columns(2)
            with col_a1: st.session_state["t_auto_temp"] = st.number_input("Tempo de Ciclo (min)", min_value=1, value=st.session_state["t_auto_temp"])
            with col_a2: st.session_state["t_pisca_temp"] = st.number_input("Velocidade Pisca (seg)", min_value=1, value=st.session_state["t_pisca_temp"])
            
            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR CICLO"):
                    st.session_state["ciclo_ativo"] = True
                    st.session_state["hora_inicio_ciclo"] = time.time()
                    registrar_evento("INICIOU CICLO AUTO")
                    st.rerun()
            else:
                if st.button("⏹️ PARAR OPERAÇÃO"):
                    st.session_state["ciclo_ativo"] = False
                    st.session_state["hora_inicio_ciclo"] = None
                    db.reference("controle/led").set("OFF")
                    st.rerun()
                restante = st.session_state["t_auto_temp"] - ((time.time() - st.session_state["hora_inicio_ciclo"]) / 60)
                st.success(f"⚡ OPERAÇÃO EM CURSO - Restante: {restante:.2f} min")
                time.sleep(1); st.rerun()

    # --- TELA: MEDIÇÃO (v13.0 + REFRESH) ---
    elif menu == "🌡️ Medição":
        st.header("Monitoramento de Sensores")
        temp_val = db.reference("sensor/temperatura").get() or 0
        umid_val = db.reference("sensor/umidade").get() or 0
        pct_t, pct_u = min(max((temp_val/60)*100, 0), 100), min(max(umid_val, 0), 100)
        col_s1, col_s2 = st.columns(2)
        with col_s1: st.markdown(f'''<div class="gauge-card">Temperatura (°C)<div class="gauge-value">{temp_val}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_t}%; background:linear-gradient(90deg, #3a7bd5, #ee0979); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        with col_s2: st.markdown(f'''<div class="gauge-card">Umidade (%)<div class="gauge-value">{umid_val}</div><div class="moving-bar-container"><div style="height:100%; width:{pct_u}%; background:linear-gradient(90deg, #00d2ff, #3a7bd5); border-radius:10px;"></div></div></div>''', unsafe_allow_html=True)
        if st.button("🔄 REFRESH"): st.rerun()
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    # --- TELA: RELATÓRIOS ---
    elif menu == "📊 Relatórios":
        st.header("Histórico Logístico")
        if st.button("🗑️ LIMPAR REGISTROS"): db.reference("historico_acoes").delete(); st.rerun()
        with st.expander("📲 WhatsApp"):
            tel_w = st.text_input("Número", value="5562999999999")
            msg_w = st.text_area("Mensagem", "Relatório ASB.")
            if st.button("GERAR LINK"):
                link_w = f"https://wa.me/{tel_w}?text={urllib.parse.quote(msg_w)}"
                st.markdown(f'<a href="{link_w}" target="_blank">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
        historico = db.reference("historico_acoes").get()
        if historico:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for key in reversed(list(historico.keys())):
                item = historico[key]; st.markdown(f'<div class="msg-balao"><b>{item.get("usuario")}</b><br>{item.get("acao")}<br><small>{item.get("data")}</small></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    # --- TELA: DIAGNÓSTICO ---
    elif menu == "🛠️ Diagnóstico":
        st.header("Estado de Rede")
        if st.button("🔍 PING"):
            db.reference("sensor/temperatura").delete(); time.sleep(4)
            st.session_state["ping_status"] = "ON" if db.reference("sensor/temperatura").get() is not None else "OFF"
        if st.session_state.get("ping_status") == "ON": st.markdown("<div class='status-ok'>✅ ONLINE</div>", unsafe_allow_html=True)
        elif st.session_state.get("ping_status") == "OFF": st.markdown("<div class='status-erro'>❌ OFFLINE</div>", unsafe_allow_html=True)
        if st.button("REBOOT"): db.reference("controle/restart").set(True); st.warning("Enviado.")
        if st.session_state["ciclo_ativo"]: time.sleep(1); st.rerun()

    # --- TELA: GESTÃO DE USUÁRIOS ---
    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.header("Operadores")
        with st.form("f_cad"):
            n, l, s = st.text_input("Nome"), st.text_input("Login"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                db.reference("usuarios_autorizados").push({"nome": n, "login": l, "senha": s, "data": obter_hora_brasilia().strftime('%d/%m/%Y')})
                st.success("OK!"); st.rerun()
        lista = db.reference("usuarios_autorizados").get()
        if lista:
            for k, v in lista.items(): st.markdown(f"<div class='card-usuario'><b>{v.get('nome')}</b> | {v.get('login')}</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v35.0
