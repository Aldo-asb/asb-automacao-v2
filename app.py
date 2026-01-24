import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd

# --- 1. IDENTIDADE VISUAL ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 4.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .status-ok { color: #28a745; font-weight: bold; padding: 15px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 15px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO FIREBASE ---
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

# --- 3. REGISTRO DE EVENTO ---
def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "operador")
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora, "usuario": usuario, "acao": acao})
        if st.session_state.get("email_ativo", True) or manual:
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            if remetente and senha:
                msg = MIMEText(f"SISTEMA ASB\nAção: {acao}\nHora: {agora}")
                msg['Subject'] = f"LOG: {acao}"
                msg['From'] = remetente
                msg['To'] = "asbautomacao@gmail.com"
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(remetente, senha)
                    server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string())
    except: pass

# --- 4. LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u_input = st.text_input("Usuário")
        p_input = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if u_input == "admin" and p_input == "asb2026":
                st.session_state["logado"] = True
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                usuarios_db = db.reference("usuarios_autorizados").get()
                if usuarios_db:
                    for key, user_data in usuarios_db.items():
                        if user_data['login'] == u_input and user_data['senha'] == p_input:
                            st.session_state["logado"] = True
                            st.session_state["user_nome"] = user_data['nome']
                            st.rerun()
                if not st.session_state["logado"]: st.error("Dados incorretos.")
else:
    conectar_firebase()
    menu = st.sidebar.radio("Menu:", ["Acionamento", "Medição", "Relatórios", "Diagnóstico", "Gestão de Usuários"])
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    
    if st.sidebar.button("SAIR"):
        st.session_state["logado"] = False
        st.rerun()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "Acionamento":
        st.header("🕹️ Controle")
        status_atual = db.reference("controle/led").get()
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"LIGAR {'🟢' if status_atual == 'ON' else '⚪'}"):
                db.reference("controle/led").set("ON")
                registrar_evento("LIGOU LED")
                st.rerun()
        with c2:
            if st.button(f"DESLIGAR {'🔴' if status_atual == 'OFF' else '⚪'}"):
                db.reference("controle/led").set("OFF")
                registrar_evento("DESLIGOU LED")
                st.rerun()

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "Medição":
        st.header("🌡️ Sensores")
        t = db.reference("sensor/temperatura").get()
        u = db.reference("sensor/umidade").get()
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura", f"{t} °C")
        col_u.metric("Umidade", f"{u} %")
        if st.button("SINCRONIZAR"): st.rerun()

    # --- TELA 3: RELATÓRIOS ---
    elif menu == "Relatórios":
        st.header("📊 Histórico")
        logs = db.reference("historico_acoes").get()
        if logs:
            df = pd.DataFrame(list(logs.values())).iloc[::-1]
            st.table(df[['data', 'usuario', 'acao']].head(10))

    # --- TELA 4: DIAGNÓSTICO ---
    elif menu == "Diagnóstico":
        st.header("🛠️ Status")
        try:
            db.reference("sensor/temperatura").get()
            st.markdown("<div class='status-ok'>FIREBASE CONECTADO</div>", unsafe_allow_html=True)
        except:
            st.markdown("<div class='status-erro'>ERRO DE REDE</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v5.7
