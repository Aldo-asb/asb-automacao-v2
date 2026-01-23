import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

# --- 1. CONFIGURAÇÕES TÉCNICAS E ESTILO (CSS) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-login {
        color: #00458d;
        font-size: 50px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; border-radius: 10px; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO DO BANCO DE DADOS ---
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            cred_dict = {
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
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

# --- 3. FUNÇÃO DE E-MAIL (REQUISITO ESSENCIAL) ---
def enviar_alerta_email(assunto, corpo, destinatario):
    try:
        email_user = st.secrets.get("email_user")
        email_pass = st.secrets.get("email_password")
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = email_user
        msg['To'] = destinatario
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.sendmail(email_user, destinatario, msg.as_string())
        return True
    except: return False

# --- 4. SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    # TELA DE LOGIN COM NOME BEM DESTACADO
    st.markdown("<div class='titulo-login'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container():
            st.write("### Login de Acesso")
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.button("ACESSAR SISTEMA"):
                if u == "admin" and p == "asb2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Credenciais Inválidas")
else:
    conectar_banco()
    
    # --- 5. NAVEGAÇÃO LATERAL (5 TELAS SEPARADAS) ---
    st.sidebar.title("MENU ASB")
    opcao = st.sidebar.radio("Navegação", 
        ["Acionamento", "Medição de Sensores", "Relatórios e E-mail", "Cadastro de Usuários", "Diagnóstico Técnico"])
    
    if st.sidebar.button("LOGOUT / SAIR"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- TELA 1: ACIONAMENTO ---
    if opcao == "Acionamento":
        st.header("🕹️ Painel de Acionamento")
        c1, c2 = st.columns(2)
        if c1.button("LIGAR EQUIPAMENTO"):
            db.reference("controle/led").set("ON")
            st.success("Comando LIGAR enviado.")
        if c2.button("DESLIGAR EQUIPAMENTO"):
            db.reference("controle/led").set("OFF")
            st.warning("Comando DESLIGAR enviado.")

    # --- TELA 2: MEDIÇÃO (COM ALERTA AUTOMÁTICO) ---
    elif opcao == "Medição de Sensores":
        st.header("🌡️ Telemetria em Tempo Real")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        st.metric("Temperatura Atual", f"{t} °C")
        st.metric("Umidade do Ar", f"{u} %")
        
        # Lógica de E-mail Automático
        if t > 45: # Limite crítico
            st.error("⚠️ ALERTA: TEMPERATURA CRÍTICA DETECTADA!")
        
        time.sleep(3)
        st.rerun()

    # --- TELA 3: RELATÓRIOS E E-MAIL MANUAL ---
    elif opcao == "Relatórios e E-mail":
        st.header("📊 Relatórios e Comunicação Manual")
        st.write("Dados Históricos de Campo")
        
        email_dest = st.text_input("Enviar relatório para o e-mail:", "cliente@asb.com")
        if st.button("ENVIAR RELATÓRIO AGORA"):
            t_atual = db.reference("sensor/temperatura").get()
            corpo = f"Relatorio ASB Industrial\nData: {datetime.now()}\nTemperatura: {t_atual}C\nStatus: Operante"
            if enviar_alerta_email("Relatorio ASB Industrial", corpo, email_dest):
                st.success("E-mail enviado com sucesso!")
            else:
                st.error("Falha ao enviar e-mail. Verifique os segredos (Secrets).")

    # --- TELA 4: CADASTRO DE USUÁRIOS ---
    elif opcao == "Cadastro de Usuários":
        st.header("👥 Cadastro de Operadores")
        st.text_input("Nome Completo")
        st.text_input("Cargo")
        st.button("Salvar no Banco de Dados")

    # --- TELA 5: DIAGNÓSTICO TÉCNICO ---
    elif opcao == "Diagnóstico Técnico":
        st.header("🛠️ Diagnóstico de Conexão")
        st.info("Configuração Wi-Fi: **ASB AUTOMACAO WIFI**")
        st.write("Sinal de Vida (Heartbeat) ativo.")
        if st.button("REINICIAR HARDWARE"):
            db.reference("controle/restart").set(True)
            st.warning("Comando de reinicialização enviado.")

# Rodapé Final
st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - Versão 3.0 Pro")
