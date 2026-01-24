import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. CONFIGURAÇÃO DE LAYOUT E ESTILO ASB ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .status-ok { color: #28a745; font-weight: bold; padding: 10px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 10px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO COM O FIREBASE ---
@st.cache_resource
def conectar_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"],
                "token_uri": st.secrets["token_uri"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

# --- 3. FUNÇÃO DE REGISTRO DE AÇÕES E ENVIO DE E-MAIL ---
def registrar_evento(acao_detalhada):
    usuario = st.session_state.get("user_nome", "admin")
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # SALVAR NO FIREBASE (Para aparecer na aba Relatórios)
    try:
        db.reference("historico_acoes").push({
            "data": agora,
            "usuario": usuario,
            "acao": acao_detalhada
        })
    except: pass

    # ENVIO DO E-MAIL (LOG AUTOMÁTICO)
    if st.session_state.get("email_ativo", True):
        try:
            remetente = st.secrets["email_user"]
            senha = st.secrets["email_password"]
            destinatario = "asbautomacao@gmail.com"
            
            corpo = f"RELATÓRIO DE EVENTO ASB\n\nAção: {acao_detalhada}\nOperador: {usuario}\nData: {agora}"
            msg = MIMEText(corpo)
            msg['Subject'] = f"LOG ASB: {acao_detalhada}"
            msg['From'] = remetente
            msg['To'] = destinatario
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(remetente, senha)
                server.sendmail(remetente, destinatario, msg.as_string())
        except Exception as e:
            st.sidebar.error(f"Erro no e-mail: {e}")

# --- 4. FLUXO DE ACESSO ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True

if not st.session_state["logado"]:
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if u == "admin" and p == "asb2026":
                st.session_state["logado"] = True
                st.session_state["user_nome"] = u
                st.rerun()
            else: st.error("Acesso negado")
else:
    conectar_firebase()
    st.sidebar.title("MENU")
    aba = st.sidebar.radio("Navegação:", ["Acionamento", "Medição", "Relatórios", "Diagnóstico"])
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state["logado"] = False
        st.rerun()

    conteudo = st.container()

    # --- TELA 1: ACIONAMENTO ---
    if aba == "Acionamento":
        with conteudo:
            st.header("🕹️ Controle de Atuadores")
            c1, c2 = st.columns(2)
            if c1.button("LIGAR EQUIPAMENTO"):
                db.reference("controle/led").set("ON")
                registrar_evento("LIGOU O SISTEMA")
                st.success("Comando enviado!")
            if c2.button("DESLIGAR EQUIPAMENTO"):
                db.reference("controle/led").set("OFF")
                registrar_evento("DESLIGOU O SISTEMA")
                st.warning("Comando enviado!")

    # --- TELA 2: MEDIÇÃO ---
    elif aba == "Medição":
        with conteudo:
            st.header("🌡️ Sensores em Tempo Real")
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            st.metric("Temperatura", f"{t} °C")
            st.metric("Umidade", f"{u} %")
            time.sleep(2)
            st.rerun()

    # --- TELA 3: RELATÓRIOS (TABELA DE AÇÕES) ---
    elif aba == "Relatórios":
        with conteudo:
            st.header("📊 Histórico de Operações")
            try:
                logs = db.reference("historico_acoes").get()
                if logs:
                    df = pd.DataFrame(list(logs.values()))
                    df = df[['data', 'usuario', 'acao']].iloc[::-1] # Mais recentes primeiro
                    st.table(df.head(15))
                else: st.info("Sem logs no momento.")
            except: st.error("Falha ao carregar histórico.")
            
            if st.button("ENVIAR E-MAIL MANUAL"):
                registrar_evento("RELATÓRIO MANUAL")

    # --- TELA 4: DIAGNÓSTICO ---
    elif aba == "Diagnóstico":
        with conteudo:
            st.header("🛠️ Status de Comunicação")
            status = db.reference("sensor/temperatura").get()
            if status is not None:
                st.markdown("<div class='status-ok'>ESP32 CONECTADO</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-erro'>ESP32 DESCONECTADO</div>", unsafe_allow_html=True)
            
            if st.button("RESETAR HARDWARE"):
                db.reference("controle/restart").set(True)
                registrar_evento("RESET REMOTO")

st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - v4.0")
