import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DE INTERFACE E CSS ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 50px; font-weight: bold; text-align: center; margin-bottom: 30px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #00458d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO FIREBASE ---
@st.cache_resource
def iniciar_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = {
                "type": st.secrets["type"], "project_id": st.secrets["project_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"], "token_uri": st.secrets["token_uri"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

# --- 3. FUNÇÃO DE E-MAIL ---
def enviar_email_log(usuario, acao):
    try:
        remetente = st.secrets["email_user"]
        senha = st.secrets["email_password"]
        destinatario = "asbautomacao@gmail.com"
        msg = MIMEText(f"USUÁRIO: {usuario}\nHORA: {datetime.now()}\nAÇÃO: {acao}")
        msg['Subject'] = f"LOG ASB: {acao}"
        msg['From'] = remetente
        msg['To'] = destinatario
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remetente, senha)
            smtp.sendmail(remetente, destinatario, msg.as_string())
        return True
    except: return False

# --- 4. SISTEMA DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if u == "admin" and p == "asb2026":
                st.session_state["logado"] = True
                st.session_state["user"] = u
                st.rerun()
            else: st.error("Incorreto")
else:
    iniciar_firebase()
    
    # --- 5. NAVEGAÇÃO (ESTRUTURA IDENTICA) ---
    st.sidebar.title("MENU ASB")
    menu = st.sidebar.radio("Selecione a Tela:", 
        ["🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "👥 Cadastro", "🛠️ Diagnóstico"])

    if st.sidebar.button("SAIR"):
        st.session_state["logado"] = False
        st.rerun()

    # CONTAINER ÚNICO PARA EVITAR MISTURA DE TELAS
    conteudo = st.container()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "🕹️ Acionamento":
        with conteudo:
            st.header("🕹️ Acionamento Manual")
            c1, c2 = st.columns(2)
            if c1.button("LIGAR"):
                db.reference("controle/led").set("ON")
                enviar_email_log(st.session_state["user"], "LIGOU")
                st.success("Comando enviado!")
            if c2.button("DESLIGAR"):
                db.reference("controle/led").set("OFF")
                enviar_email_log(st.session_state["user"], "DESLIGOU")
                st.warning("Comando enviado!")

    # --- TELA 2: MEDIÇÃO (O RERUN SÓ ACONTECE AQUI) ---
    elif menu == "🌡️ Medição":
        with conteudo:
            st.header("🌡️ Telemetria")
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            col_t, col_u = st.columns(2)
            with col_t: st.metric("Temperatura", f"{t} °C")
            with col_u: st.metric("Umidade", f"{u} %")
            
            # O SEGREDO PARA NÃO PISCAR EM OUTRAS TELAS:
            time.sleep(2)
            st.rerun()

    # --- TELA 3: RELATÓRIOS ---
    elif menu == "📊 Relatórios":
        with conteudo:
            st.header("📊 Relatórios")
            st.write("Histórico enviado para: asbautomacao@gmail.com")
            if st.button("ENVIAR STATUS AGORA"):
                enviar_email_log(st.session_state["user"], "SOLICITOU RELATÓRIO")

    # --- TELA 4: CADASTRO ---
    elif menu == "👥 Cadastro":
        with conteudo:
            st.header("👥 Cadastro de Usuários")
            st.text_input("Novo Operador")
            st.button("Cadastrar")

    # --- TELA 5: DIAGNÓSTICO ---
    elif menu == "🛠️ Diagnóstico":
        with conteudo:
            st.header("🛠️ Diagnóstico Técnico")
            st.info("Rede: ASB AUTOMACAO WIFI")
            if st.button("RESETAR HARDWARE"):
                db.reference("controle/restart").set(True)

# --- RODAPÉ ---
st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - v3.3")
