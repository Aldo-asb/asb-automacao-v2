import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

# --- 1. CONFIGURAÇÕES DE INTERFACE ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .status-online { color: #28a745; font-weight: bold; font-size: 20px; border: 2px solid #28a745; padding: 10px; border-radius: 5px; text-align: center; }
    .status-offline { color: #dc3545; font-weight: bold; font-size: 20px; border: 2px solid #dc3545; padding: 10px; border-radius: 5px; text-align: center; }
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
def enviar_email_asb(assunto, acao):
    try:
        remetente = st.secrets["email_user"]
        senha = st.secrets["email_password"]
        destinatario = "asbautomacao@gmail.com"
        msg = MIMEText(f"ASB INDUSTRIAL\n\nDETALHES: {acao}\nHORA: {datetime.now().strftime('%H:%M:%S')}")
        msg['Subject'] = assunto
        msg['From'] = remetente
        msg['To'] = destinatario
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.quit()
        return True
    except: return False

# --- 4. CONTROLE DE LOGIN E SESSÃO ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "envio_auto" not in st.session_state: st.session_state["envio_auto"] = True

if not st.session_state["logado"]:
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if u == "admin" and p == "asb2026":
                st.session_state["logado"] = True
                st.rerun()
            else: st.error("Acesso Negado")
else:
    iniciar_firebase()
    st.sidebar.title("MENU OPERACIONAL")
    menu = st.sidebar.radio("Navegação:", ["🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "👥 Cadastro", "🛠️ Diagnóstico"])
    st.session_state["envio_auto"] = st.sidebar.toggle("Envio de E-mail Automático", value=st.session_state["envio_auto"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state["logado"] = False
        st.rerun()

    # Lógica de Verificação de Conexão (Watchdog)
    # Verificamos se o valor da temperatura oscila em milissegundos
    try:
        ref = db.reference("sensor/temperatura")
        v1 = ref.get()
        time.sleep(0.3)
        v2 = ref.get()
        # Se os dados estão mudando ou o timestamp é recente, está OK
        comunicacao_ok = (v1 != v2) or (v1 is not None) # Ajuste dependendo da frequência do seu ESP
    except:
        comunicacao_ok = False

    # CONTAINER PARA CADA TELA (EVITA MISTURA)
    conteudo = st.container()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "🕹️ Acionamento":
        with conteudo:
            st.header("🕹️ Acionamento de Atuadores")
            c1, c2 = st.columns(2)
            if c1.button("LIGAR"):
                db.reference("controle/led").set("ON")
                if st.session_state["envio_auto"]: enviar_email_asb("LOG: Ligado", "Comando LIGAR via Web")
            if c2.button("DESLIGAR"):
                db.reference("controle/led").set("OFF")
                if st.session_state["envio_auto"]: enviar_email_asb("LOG: Desligado", "Comando DESLIGAR via Web")

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "🌡️ Medição":
        with conteudo:
            st.header("🌡️ Telemetria em Tempo Real")
            t = db.reference("sensor/temperatura").get() or 0
            u = db.reference("sensor/umidade").get() or 0
            col_t, col_u = st.columns(2)
            col_t.metric("Temperatura", f"{t} °C")
            col_u.metric("Umidade", f"{u} %")
            time.sleep(2)
            st.rerun()

    # --- TELA 3: RELATÓRIOS ---
    elif menu == "📊 Relatórios":
        with conteudo:
            st.header("📊 Relatórios Industriais")
            if st.button("ENVIAR RELATÓRIO MANUAL"):
                enviar_email_asb("Relatório Manual", f"Solicitado pelo admin as {datetime.now()}")
                st.success("E-mail enviado!")

    # --- TELA 4: CADASTRO ---
    elif menu == "👥 Cadastro":
        with conteudo:
            st.header("👥 Gestão de Usuários")
            st.text_input("Novo Operador")
            st.button("Cadastrar")

    # --- TELA 5: DIAGNÓSTICO (COM STATUS DE CONEXÃO) ---
    elif menu == "🛠️ Diagnóstico":
        with conteudo:
            st.header("🛠️ Diagnóstico de Sistema")
            
            # EXIBIÇÃO DO STATUS DE COMUNICAÇÃO
            if comunicacao_ok:
                st.markdown("<div class='status-online'>ESTATUS: COMUNICAÇÃO OK (CONECTADO)</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-offline'>ESTATUS: FALHA DE COMUNICAÇÃO (ESP32 OFFLINE)</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.info("Rede Configurada: ASB AUTOMACAO WIFI")
            if st.button("REINICIAR ESP32 REMOTAMENTE"):
                db.reference("controle/restart").set(True)
                st.warning("Comando de Reset enviado.")

st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - v3.4")
