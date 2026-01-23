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

# --- 2. INICIALIZAÇÃO FIREBASE (COM PROTEÇÃO DE ERRO) ---
@st.cache_resource
def iniciar_firebase():
    if not firebase_admin._apps:
        try:
            # Uso do .get() para evitar o KeyError
            cred_dict = {
                "type": st.secrets.get("type"),
                "project_id": st.secrets.get("project_id"),
                "private_key_id": st.secrets.get("private_key_id"),
                "private_key": st.secrets.get("private_key", "").replace('\\n', '\n'),
                "client_email": st.secrets.get("client_email"),
                "client_id": st.secrets.get("client_id"),
                "auth_uri": st.secrets.get("auth_uri"),
                "token_uri": st.secrets.get("token_uri"),
                "auth_provider_x509_cert_url": st.secrets.get("auth_provider_x509_cert_url"),
                "client_x509_cert_url": st.secrets.get("client_x509_cert_url"),
                "universe_domain": st.secrets.get("universe_domain")
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except Exception as e:
            st.error(f"Erro nas Credenciais do Firebase: {e}")
            return False
    return True

# --- 3. FUNÇÃO DE E-MAIL E LOG ---
def registrar_acao(usuario, acao):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # Salvar no Firebase para a tela de Relatórios
    try:
        db.reference("logs_acoes").push({
            "usuario": usuario,
            "acao": acao,
            "horario": agora
        })
    except: pass

    # Enviar E-mail
    if st.session_state.get("envio_auto", True):
        try:
            # Uso do .get() para evitar que o app pare se o segredo sumir
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            
            if not remetente or not senha:
                st.sidebar.error("E-mail não configurado nos Secrets!")
                return False

            destinatario = "asbautomacao@gmail.com"
            msg = MIMEText(f"SISTEMA ASB INDUSTRIAL\n\nUSUÁRIO: {usuario}\nAÇÃO: {acao}\nHORA: {agora}")
            msg['Subject'] = f"LOG ASB: {acao}"
            msg['From'] = remetente
            msg['To'] = destinatario
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(remetente, senha)
                server.sendmail(remetente, destinatario, msg.as_string())
            return True
        except Exception as e:
            st.sidebar.error(f"Falha no envio: {e}")
            return False

# --- 4. CONTROLE DE LOGIN ---
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

    # Diagnóstico de Conexão
    try:
        t_teste = db.reference("sensor/temperatura").get()
        time.sleep(0.2)
        comunicacao_ok = (t_teste is not None)
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
                st.success("LIGAR enviado.")
            if c2.button("DESLIGAR"):
                db.reference("controle/led").set("OFF")
                registrar_acao(st.session_state["user_nome"], "DESLIGOU O EQUIPAMENTO")
                st.warning("DESLIGAR enviado.")

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "🌡️ Medição":
        with conteudo:
            st.header("🌡️ Monitoramento")
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            st.metric("Temperatura", f"{t} °C")
            st.metric("Umidade", f"{u} %")
            time.sleep(3)
            st.rerun()

    # --- TELA 3: RELATÓRIOS (EXIBE AÇÕES NA TELA) ---
    elif menu == "📊 Relatórios":
        with conteudo:
            st.header("📊 Histórico de Ações")
            try:
                dados = db.reference("logs_acoes").get()
                if dados:
                    # Converte os logs do Firebase para uma tabela limpa
                    lista_logs = list(dados.values())
                    df = pd.DataFrame(lista_logs)
                    # Reorganiza as colunas e mostra as mais recentes primeiro
                    df = df[['horario', 'usuario', 'acao']].iloc[::-1]
                    st.table(df.head(15))
                else:
                    st.info("Nenhum registro encontrado.")
            except: st.error("Erro ao carregar logs.")

            if st.button("ENVIAR E-MAIL MANUAL"):
                registrar_acao(st.session_state["user_nome"], "RELATÓRIO MANUAL")

    # --- TELA 4: CADASTRO ---
    elif menu == "👥 Cadastro":
        with conteudo:
            st.header("👥 Usuários")
            st.text_input("Nome do Operador")
            st.button("Salvar")

    # --- TELA 5: DIAGNÓSTICO ---
    elif menu == "🛠️ Diagnóstico":
        with conteudo:
            st.header("🛠️ Diagnóstico")
            if comunicacao_ok:
                st.markdown("<div class='status-online'>COMUNICAÇÃO OK</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-offline'>FALHA DE COMUNICAÇÃO</div>", unsafe_allow_html=True)
            
            if st.button("RESETAR ESP32"):
                db.reference("controle/restart").set(True)
                registrar_acao(st.session_state["user_nome"], "RESET DE HARDWARE")

st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - v3.6")
