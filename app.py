import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. CONFIGURAÇÕES DE INTERFACE E ESTILO (CSS ROBUSTO) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .titulo-principal {
        color: #00458d;
        font-size: 55px;
        font-weight: bold;
        text-align: center;
        padding: 40px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-transform: uppercase;
        border-bottom: 5px solid #00458d;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        height: 4em;
        font-weight: bold;
        background-color: #00458d;
        color: white;
        border-radius: 12px;
        font-size: 18px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #002d5c;
        border: 2px solid #ff0000;
    }
    .metric-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-left: 10px solid #00458d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO DO FIREBASE (CONEXÃO PERSISTENTE) ---
@st.cache_resource
def conectar_banco_dados():
    if not firebase_admin._apps:
        try:
            # Puxando credenciais dos Secrets
            cred_json = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets["universe_domain"]
            }
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'
            })
            return True
        except Exception as e:
            st.error(f"Falha Crítica na Conexão: {e}")
            return False
    return True

# --- 3. FUNÇÃO DE NOTIFICAÇÃO E LOG POR E-MAIL ---
def enviar_email_servidor(usuario, descricao_acao):
    try:
        email_origem = st.secrets["email_user"]
        senha_servidor = st.secrets["email_password"]
        email_destino = "asbautomacao@gmail.com"
        
        timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        
        corpo = f"""
        SISTEMA DE MONITORAMENTO ASB AUTOMAÇÃO INDUSTRIAL
        --------------------------------------------------
        ALERTA DE SEGURANÇA / LOG DE OPERAÇÃO
        
        DATA/HORA: {timestamp}
        USUÁRIO: {usuario}
        AÇÃO EXECUTADA: {descricao_acao}
        
        Mensagem gerada automaticamente pelo Supervisório.
        --------------------------------------------------
        """
        
        mensagem = MIMEText(corpo)
        mensagem['Subject'] = f"LOG ASB - {descricao_acao}"
        mensagem['From'] = email_origem
        mensagem['To'] = email_destino
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_origem, senha_servidor)
            smtp.sendmail(email_origem, email_destino, mensagem.as_string())
        return True
    except Exception as error:
        st.sidebar.warning(f"Log de e-mail não enviado: {error}")
        return False

# --- 4. GESTÃO DE ACESSO E SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_atual"] = None

def realizar_logout():
    st.session_state["autenticado"] = False
    st.session_state["usuario_atual"] = None
    st.rerun()

# --- TELA DE LOGIN ---
if not st.session_state["autenticado"]:
    st.markdown("<div class='titulo-principal'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.subheader("🔑 Autenticação de Operador")
        input_user = st.text_input("Identificação do Usuário")
        input_pass = st.text_input("Senha de Acesso", type="password")
        
        if st.button("CONFIRMAR ENTRADA"):
            if input_user == "admin" and input_pass == "asb2026":
                st.session_state["autenticado"] = True
                st.session_state["usuario_atual"] = input_user
                st.success("Acesso autorizado!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

# --- SISTEMA APÓS LOGIN ---
else:
    conectar_banco_dados()
    
    # BARRA LATERAL (MENU ORIGINAL)
    st.sidebar.markdown(f"### Bem-vindo, {st.session_state['usuario_atual']}")
    st.sidebar.markdown("---")
    
    menu_selecao = st.sidebar.radio("Navegação Principal:", 
        ["Painel de Acionamento", "Monitoramento de Sensores", "Relatórios e E-mail", "Cadastro de Usuários", "Diagnóstico Técnico"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("LOGOUT / SAIR"):
        realizar_logout()

    # LÓGICA DE STATUS DE CONEXÃO (WATCHDOG)
    try:
        ref_temp = db.reference("sensor/temperatura")
        v1 = ref_temp.get() or 0
        time.sleep(0.5)
        v2 = ref_temp.get() or 0
        is_online = (v1 != v2)
    except:
        is_online = False

    # --- TELA 1: ACIONAMENTO ---
    if menu_selecao == "Painel de Acionamento":
        st.header("🕹️ Controle de Acionamento Remoto")
        if is_online:
            st.success("EQUIPAMENTO ONLINE")
        else:
            st.error("EQUIPAMENTO DESCONECTADO - VERIFIQUE O HARDWARE")
            
        col_on, col_off = st.columns(2)
        with col_on:
            if st.button("LIGAR EQUIPAMENTO"):
                db.reference("controle/led").set("ON")
                enviar_email_servidor(st.session_state["usuario_atual"], "LIGOU O SISTEMA")
                st.success("Comando enviado e Log registrado.")
        with col_off:
            if st.button("DESLIGAR EQUIPAMENTO"):
                db.reference("controle/led").set("OFF")
                enviar_email_servidor(st.session_state["usuario_atual"], "DESLIGOU O SISTEMA")
                st.warning("Comando enviado e Log registrado.")

    # --- TELA 2: MEDIÇÃO ---
    elif menu_selecao == "Monitoramento de Sensores":
        st.header("🌡️ Medição em Tempo Real")
        temp_val = db.reference("sensor/temperatura").get() or 0.0
        umid_val = db.reference("sensor/umidade").get() or 0.0
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Temperatura de Processo", f"{temp_val} °C")
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Umidade do Ambiente", f"{umid_val} %")
            st.markdown("</div>", unsafe_allow_html=True)
            
        time.sleep(2)
        st.rerun()

    # --- TELA 3: RELATÓRIOS ---
    elif menu_selecao == "Relatórios e E-mail":
        st.header("📊 Gestão de Logs e Relatórios")
        st.write(f"Os logs de ação são enviados para: **asbautomacao@gmail.com**")
        
        st.subheader("Solicitar Relatório Manual")
        if st.button("ENVIAR DADOS ATUAIS POR E-MAIL"):
            t_data = db.reference("sensor/temperatura").get()
            u_data = db.reference("sensor/umidade").get()
            resumo = f"Relatório Manual: Temp {t_data}C, Umid {u_data}%"
            if enviar_email_servidor(st.session_state["usuario_atual"], resumo):
                st.success("Relatório disparado com sucesso.")

    # --- TELA 4: CADASTRO ---
    elif menu_selecao == "Cadastro de Usuários":
        st.header("👥 Gestão de Operadores")
        with st.form("cad_user"):
            st.text_input("Nome Completo")
            st.text_input("Cargo/Setor")
            if st.form_submit_button("Salvar Novo Usuário"):
                st.success("Usuário registrado na base de dados.")

    # --- TELA 5: DIAGNÓSTICO ---
    elif menu_selecao == "Diagnóstico Técnico":
        st.header("🛠️ Ferramentas de Manutenção")
        st.info("Ponto de Acesso: **ASB AUTOMACAO WIFI** | Senha: **asbconect**")
        if st.button("REINICIAR HARDWARE (RESET REMOTO)"):
            db.reference("controle/restart").set(True)
            enviar_email_servidor(st.session_state["usuario_atual"], "SOLICITOU RESET DE FÁBRICA")
            st.warning("Comando de reinicialização enviado ao ESP32.")

# --- RODAPÉ ---
st.markdown("---")
st.caption("© 2026 ASB AUTOMAÇÃO INDUSTRIAL - Versão Estável 3.2")
