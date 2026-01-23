import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. CONFIGURAÇÃO VISUAL E CSS ---
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
                "type": st.secrets["type"], "project_id": st.secrets["project_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"], "token_uri": st.secrets["token_uri"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

# --- 3. FUNÇÃO DE E-MAIL E LOG NO FIREBASE ---
def registrar_acao(usuario, acao):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # 3.1. Salvar no Firebase para aparecer na tela de Relatórios
    try:
        log_ref = db.reference("logs_acoes")
        log_ref.push({
            "usuario": usuario,
            "acao": acao,
            "horario": agora
        })
    except: pass

    # 3.2. Enviar E-mail (Lógica que voltou a funcionar)
    if st.session_state.get("envio_auto", True):
        try:
            remetente = st.secrets["email_user"]
            senha = st.secrets["email_password"]
            destinatario = "asbautomacao@gmail.com"
            
            msg = MIMEText(f"SISTEMA ASB INDUSTRIAL\n\nUSUÁRIO: {usuario}\nAÇÃO: {acao}\nHORA: {agora}")
            msg['Subject'] = f"LOG ASB: {acao}"
            msg['From'] = remetente
            msg['To'] = destinatario
            
            # Usando SMTP_SSL na porta 465 que costuma ser mais estável para Gmail
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(remetente, senha)
                server.sendmail(remetente, destinatario, msg.as_string())
            return True
        except Exception as e:
            st.sidebar.error(f"Erro e-mail: {e}")
            return False

# --- 4. LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "envio_auto" not in st.session_state: st.session_state["envio_auto"] = True

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
            else: st.error("Acesso Negado")
else:
    iniciar_firebase()
    st.sidebar.title("MENU ASB")
    menu = st.sidebar.radio("Navegação:", ["🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "👥 Cadastro", "🛠️ Diagnóstico"])
    st.session_state["envio_auto"] = st.sidebar.toggle("Envio de E-mail Automático", value=st.session_state["envio_auto"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state["logado"] = False
        st.rerun()

    # Watchdog de Comunicação
    try:
        t1 = db.reference("sensor/temperatura").get()
        time.sleep(0.3)
        comunicacao_ok = (t1 != db.reference("sensor/temperatura").get()) or (t1 is not None)
    except: comunicacao_ok = False

    conteudo = st.container()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "🕹️ Acionamento":
        with conteudo:
            st.header("🕹️ Acionamento Manual")
            c1, c2 = st.columns(2)
            if c1.button("LIGAR"):
                db.reference("controle/led").set("ON")
                registrar_acao(st.session_state["user_nome"], "LIGOU O EQUIPAMENTO")
                st.success("Comando LIGAR enviado.")
            if c2.button("DESLIGAR"):
                db.reference("controle/led").set("OFF")
                registrar_acao(st.session_state["user_nome"], "DESLIGOU O EQUIPAMENTO")
                st.warning("Comando DESLIGAR enviado.")

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "🌡️ Medição":
        with conteudo:
            st.header("🌡️ Monitoramento")
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            col_t, col_u = st.columns(2)
            col_t.metric("Temperatura", f"{t} °C")
            col_u.metric("Umidade", f"{u} %")
            time.sleep(2)
            st.rerun()

    # --- TELA 3: RELATÓRIOS (COM TABELA DE AÇÕES) ---
    elif menu == "📊 Relatórios":
        with conteudo:
            st.header("📊 Histórico de Ações e Relatórios")
            
            # Exibir Tabela de Logs do Firebase
            st.subheader("📋 Log de Atividades Recentes")
            try:
                dados_logs = db.reference("logs_acoes").get()
                if dados_logs:
                    df = pd.DataFrame(dados_logs.values())
                    df = df[['horario', 'usuario', 'acao']].sort_index(ascending=False)
                    st.table(df.head(10)) # Mostra as últimas 10 ações
                else:
                    st.info("Nenhuma ação registrada ainda.")
            except:
                st.error("Erro ao carregar histórico.")

            if st.button("ENVIAR STATUS ATUAL POR E-MAIL"):
                registrar_acao(st.session_state["user_nome"], "RELATÓRIO MANUAL SOLICITADO")
                st.success("Relatório enviado!")

    # --- TELA 4: CADASTRO ---
    elif menu == "👥 Cadastro":
        with conteudo:
            st.header("👥 Gestão de Usuários")
            st.text_input("Novo Operador")
            st.button("Salvar")

    # --- TELA 5: DIAGNÓSTICO ---
    elif menu == "🛠️ Diagnóstico":
        with conteudo:
            st.header("🛠️ Diagnóstico de Conexão")
            if comunicacao_ok:
                st.markdown("<div class='status-online'>ESTATUS: COMUNICAÇÃO OK</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-offline'>ESTATUS: FALHA DE COMUNICAÇÃO</div>", unsafe_allow_html=True)
            
            if st.button("REINICIAR ESP32"):
                db.reference("controle/restart").set(True)
                registrar_acao(st.session_state["user_nome"], "REINICIOU O HARDWARE")

st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - v3.5")
