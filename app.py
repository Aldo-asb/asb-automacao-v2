import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. IDENTIDADE VISUAL (MANTIDA) ---
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

# --- 3. REGISTRO DE EVENTO E E-MAIL ---
def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora, "usuario": usuario, "acao": acao})
        if st.session_state.get("email_ativo", True) or manual:
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            if remetente and senha:
                msg = MIMEText(f"LOG ASB\nUsuário: {usuario}\nAção: {acao}\nHora: {agora}")
                msg['Subject'] = f"SISTEMA ASB: {acao}"
                msg['From'] = remetente
                msg['To'] = "asbautomacao@gmail.com"
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(remetente, senha)
                    server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string())
    except: pass

# --- 4. FLUXO DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True
if "ultimo_comando" not in st.session_state: st.session_state["ultimo_comando"] = None

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
                st.session_state["user_nome"] = "Admin Master"
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                usuarios_db = db.reference("usuarios_autorizados").get()
                sucesso = False
                if usuarios_db:
                    for key, user_data in usuarios_db.items():
                        if user_data['login'] == u_input and user_data['senha'] == p_input:
                            st.session_state["logado"] = True
                            st.session_state["user_nome"] = user_data['nome']
                            st.session_state["is_admin"] = False
                            sucesso = True
                            st.rerun()
                if not sucesso: st.error("Usuário ou senha incorretos.")
else:
    conectar_firebase()
    
    opcoes_menu = ["Acionamento", "Medição", "Relatórios", "Diagnóstico"]
    if st.session_state["is_admin"]:
        opcoes_menu.append("Gestão de Usuários")
    
    menu = st.sidebar.radio("Navegação:", opcoes_menu)
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    
    if st.sidebar.button("SAIR"):
        st.session_state["logado"] = False
        st.session_state["ultimo_comando"] = None
        st.rerun()

    # --- TELA 1: ACIONAMENTO (STATUS VISÍVEL APENAS APÓS CLIQUE) ---
    if menu == "Acionamento":
        st.header("🕹️ Controle Operacional")
        c1, c2 = st.columns(2)
        
        status_sessao = st.session_state["ultimo_comando"]
        
        with c1:
            btn_ligar = f"LIGAR {'🟢' if status_sessao == 'ON' else '⚪'}"
            if st.button(btn_ligar):
                db.reference("controle/led").set("ON")
                st.session_state["ultimo_comando"] = "ON"
                registrar_evento("LIGOU EQUIPAMENTO")
                st.rerun()
        with c2:
            btn_desligar = f"DESLIGAR {'🔴' if status_sessao == 'OFF' else '⚪'}"
            if st.button(btn_desligar):
                db.reference("controle/led").set("OFF")
                st.session_state["ultimo_comando"] = "OFF"
                registrar_evento("DESLIGOU EQUIPAMENTO")
                st.rerun()

    # --- TELA 2: MEDIÇÃO (PRESERVADO) ---
    elif menu == "Medição":
        st.header("🌡️ Monitoramento Real")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura", f"{t} °C")
        col_u.metric("Umidade", f"{u} %")
        time.sleep(2)
        st.rerun()

    # --- TELA 3: RELATÓRIOS (PRESERVADO) ---
    elif menu == "Relatórios":
        st.header("📊 Histórico de Ações")
        if st.button("📧 ENVIAR RELATÓRIO POR E-MAIL"):
            registrar_evento("RELATÓRIO MANUAL SOLICITADO", manual=True)
            st.success("Relatório enviado com sucesso!")
        
        logs = db.reference("historico_acoes").get()
        if logs:
            df = pd.DataFrame(list(logs.values())).iloc[::-1]
            st.table(df[['data', 'usuario', 'acao']].head(15))

    # --- TELA 4: DIAGNÓSTICO (PRESERVADO) ---
    elif menu == "Diagnóstico":
        st.header("🛠️ Diagnóstico do Sistema")
        try:
            teste_conexao = db.reference("sensor/temperatura").get()
            if teste_conexao is not None:
                st.markdown("<div class='status-ok'>SISTEMA ONLINE (COMUNICAÇÃO ATIVA)</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-erro'>SISTEMA OFFLINE (SEM RESPOSTA DO HARDWARE)</div>", unsafe_allow_html=True)
        except:
            st.markdown("<div class='status-erro'>ERRO DE CONEXÃO COM O BANCO</div>", unsafe_allow_html=True)

        if st.button("REINICIAR MÓDULO ESP32"):
            db.reference("controle/restart").set(True)
            registrar_evento("RESTART VIA DASHBOARD")

    # --- TELA 5: GESTÃO DE USUÁRIOS (PRESERVADO) ---
    elif menu == "Gestão de Usuários":
        if st.session_state["is_admin"]:
            st.header("👥 Gestão de Operadores")
            with st.form("cadastro"):
                n = st.text_input("Nome")
                l = st.text_input("Login")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    if n and l and s:
                        db.reference("usuarios_autorizados").push({
                            "nome": n, "login": l, "senha": s,
                            "data_criacao": datetime.now().strftime('%d/%m/%Y')
                        })
                        st.success(f"Operador {n} cadastrado!")
                        registrar_evento(f"CADASTROU: {l}")

# ASB AUTOMAÇÃO INDUSTRIAL - v5.1
