import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .status-online { color: #28a745; font-weight: bold; font-size: 20px; border: 2px solid #28a745; padding: 10px; border-radius: 5px; text-align: center; background-color: #e8f5e9; }
    .status-offline { color: #dc3545; font-weight: bold; font-size: 20px; border: 2px solid #dc3545; padding: 10px; border-radius: 5px; text-align: center; background-color: #ffebee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO FIREBASE ---
@st.cache_resource
def iniciar_firebase():
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

# --- 3. FUNÇÃO DE E-MAIL E LOG (CORRIGIDA) ---
def registrar_acao(acao):
    # Recupera o usuário de forma segura para evitar KeyError
    usuario = st.session_state.get("user_nome", "Sistema")
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # 3.1 Salvar no Firebase para a tela de Relatórios
    try:
        db.reference("logs_acoes").push({
            "usuario": usuario,
            "acao": acao,
            "horario": agora
        })
    except: pass

    # 3.2 Enviar E-mail (Ajustado para evitar SPAM e bloqueio)
    if st.session_state.get("envio_auto", True):
        try:
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            if remetente and senha:
                destinatario = "asbautomacao@gmail.com"
                corpo = f"RELATÓRIO DE EVENTO ASB\n\nOPERADOR: {usuario}\nAÇÃO: {acao}\nDATA/HORA: {agora}"
                msg = MIMEText(corpo)
                msg['Subject'] = f"LOG ASB: {acao}"
                msg['From'] = remetente
                msg['To'] = destinatario
                
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(remetente, senha)
                    server.sendmail(remetente, destinatario, msg.as_string())
        except Exception as e:
            st.sidebar.error(f"E-mail falhou: {e}")

# --- 4. CONTROLE DE ACESSO ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "envio_auto" not in st.session_state: st.session_state["envio_auto"] = True
if "user_nome" not in st.session_state: st.session_state["user_nome"] = "admin"

if not st.session_state["logado"]:
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            if u == "admin" and p == "asb2026":
                st.session_state["logado"] = True
                st.session_state["user_nome"] = u
                st.rerun()
            else: st.error("Incorreto")
else:
    iniciar_firebase()
    st.sidebar.title("MENU ASB")
    menu = st.sidebar.radio("Navegação:", ["Acionamento", "Medição", "Relatórios", "Usuários", "Diagnóstico"])
    st.session_state["envio_auto"] = st.sidebar.toggle("Envio Automático de E-mail", value=st.session_state["envio_auto"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state["logado"] = False
        st.rerun()

    # Diagnóstico rápido de conexão
    try:
        comunicacao_ok = db.reference("sensor/temperatura").get() is not None
    except: comunicacao_ok = False

    conteudo = st.container()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "Acionamento":
        with conteudo:
            st.header("🕹️ Acionamento Manual")
            c1, c2 = st.columns(2)
            if c1.button("LIGAR"):
                db.reference("controle/led").set("ON")
                registrar_acao("LIGOU O EQUIPAMENTO")
                st.success("Comando LIGAR executado.")
            if c2.button("DESLIGAR"):
                db.reference("controle/led").set("OFF")
                registrar_acao("DESLIGOU O EQUIPAMENTO")
                st.warning("Comando DESLIGAR executado.")

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "Medição":
        with conteudo:
            st.header("🌡️ Monitoramento")
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            st.metric("Temperatura", f"{t} °C")
            st.metric("Umidade", f"{u} %")
            time.sleep(2.5)
            st.rerun()

    # --- TELA 3: RELATÓRIOS (EXIBE AÇÕES NA TELA) ---
    elif menu == "Relatórios":
        with conteudo:
            st.header("📊 Histórico de Ações")
            try:
                logs = db.reference("logs_acoes").get()
                if logs:
                    df = pd.DataFrame(list(logs.values()))
                    df = df[['horario', 'usuario', 'acao']].iloc[::-1] # Inverte para ver os mais novos
                    st.table(df.head(15))
                else: st.info("Sem logs.")
            except: st.error("Erro ao carregar tabela.")

            if st.button("ENVIAR E-MAIL MANUAL"):
                registrar_acao("RELATÓRIO MANUAL SOLICITADO")

    # --- TELA 4: USUÁRIOS ---
    elif menu == "Usuários":
        with conteudo:
            st.header("👥 Gestão de Operadores")
            st.text_input("Novo Nome")
            st.button("Cadastrar")

    # --- TELA 5: DIAGNÓSTICO ---
    elif menu == "Diagnóstico":
        with conteudo:
            st.header("🛠️ Diagnóstico do Sistema")
            if comunicacao_ok:
                st.markdown("<div class='status-online'>COMUNICAÇÃO OK</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-offline'>FALHA DE COMUNICAÇÃO</div>", unsafe_allow_html=True)
            
            if st.button("REINICIAR HARDWARE"):
                db.reference("controle/restart").set(True)
                registrar_acao("RESET DE HARDWARE")

st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - v3.7")
