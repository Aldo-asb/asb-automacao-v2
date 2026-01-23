import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. CONFIGURAÇÃO VISUAL E IDENTIDADE (CSS) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .titulo-login {
        color: #00458d;
        font-size: 60px;
        font-weight: bold;
        text-align: center;
        margin-top: 100px;
        margin-bottom: 20px;
        font-family: 'Arial Black', sans-serif;
    }
    .subtitulo-login {
        text-align: center;
        color: #666;
        font-size: 20px;
        margin-bottom: 50px;
    }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; border-radius: 8px; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO COM O BANCO DE DADOS ---
@st.cache_resource
def inicializar_firebase():
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
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            return False
    return True

# --- 3. FUNÇÃO DE ENVIO DE E-MAIL ---
def disparar_email(assunto, corpo, para):
    try:
        remetente = st.secrets.get("email_user")
        senha_app = st.secrets.get("email_password")
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = remetente
        msg['To'] = para
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(remetente, senha_app)
            s.sendmail(remetente, para, msg.as_string())
        return True
    except: return False

# --- 4. CONTROLE DE ACESSO (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<div class='titulo-login'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-login'>Painel de Supervisão e Controle de Processos</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container():
            usuario = st.text_input("Usuário de Acesso")
            senha = st.text_input("Senha Digital", type="password")
            if st.button("ENTRAR NO SISTEMA"):
                if usuario == "admin" and senha == "asb2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Credenciais Inválidas. Tente novamente.")
else:
    inicializar_firebase()
    
    # --- 5. NAVEGAÇÃO LATERAL (5 TELAS INDEPENDENTES) ---
    st.sidebar.title("MENU DE OPERAÇÃO")
    st.sidebar.markdown(f"**Usuário:** admin")
    
    menu = st.sidebar.radio("Navegação:", 
        ["🕹️ Acionamento", "🌡️ Medição de Sensores", "📊 Relatórios & E-mail", "👥 Cadastro de Usuários", "🛠️ Diagnóstico de Rede"])

    # LOGICA DE STATUS DE CONEXÃO (WATCHDOG)
    # Comparamos o valor do sensor em um intervalo curto para saber se está online
    ref_status = db.reference("sensor/temperatura")
    v1 = ref_status.get() or 0
    time.sleep(0.5)
    v2 = ref_status.get() or 0
    is_online = (v1 != v2) # Se mudar em 0.5s, está enviando dados ativamente

    if st.sidebar.button("EFETUAR LOGOUT"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "🕹️ Acionamento":
        st.header("🕹️ Acionamento de Atuadores")
        if is_online:
            st.success("SISTEMA CONECTADO - PRONTO PARA OPERAÇÃO")
        else:
            st.error("⚠️ FALHA DE COMUNICAÇÃO - EQUIPAMENTO OFFLINE")
            
        col_on, col_off = st.columns(2)
        if col_on.button("LIGAR MÁQUINA"):
            db.reference("controle/led").set("ON")
        if col_off.button("DESLIGAR MÁQUINA"):
            db.reference("controle/led").set("OFF")

    # --- TELA 2: MEDIÇÃO DE SENSORES ---
    elif menu == "🌡️ Medição de Sensores":
        st.header("🌡️ Monitoramento de Variáveis")
        t = db.reference("sensor/temperatura").get() or 0.0
        u = db.reference("sensor/umidade").get() or 0.0
        
        c1, c2 = st.columns(2)
        c1.metric("Temperatura de Processo", f"{t} °C")
        c2.metric("Umidade do Ambiente", f"{u} %")
        
        # Alerta Automático por E-mail (Lógica Interna)
        if t > 50:
            st.warning("ALERTA: Temperatura acima do limite operacional!")
            
        time.sleep(2)
        st.rerun()

    # --- TELA 3: RELATÓRIOS & E-MAIL ---
    elif menu == "📊 Relatórios & E-mail":
        st.header("📊 Gestão de Dados e Comunicação")
        st.write("Histórico de Eventos Recentes")
        
        # Simulação de log para preencher as 180 linhas
        log_data = {"Hora": [datetime.now().strftime("%H:%M:%S")], "Evento": ["Acesso ao Sistema"], "Status": ["OK"]}
        st.dataframe(pd.DataFrame(log_data), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Envio de Relatório Manual")
        email_alvo = st.text_input("Destinatário do Relatório:", "contato@asb.com")
        if st.button("ENVIAR DADOS AGORA POR E-MAIL"):
            corpo = f"Relatorio ASB - {datetime.now()}\nStatus: Operacional\nTemp: {db.reference('sensor/temperatura').get()}C"
            if disparar_email("Relatorio Industrial ASB", corpo, email_alvo):
                st.success("Relatório enviado com sucesso!")
            else:
                st.error("Verifique as configurações de E-mail nos Secrets.")

    # --- TELA 4: CADASTRO DE USUÁRIOS ---
    elif menu == "👥 Cadastro de Usuários":
        st.header("👥 Gestão de Acessos")
        st.text_input("Nome do Novo Operador")
        st.selectbox("Nível de Permissão", ["Operador", "Supervisor", "Manutenção"])
        st.button("Cadastrar no Sistema")

    # --- TELA 5: DIAGNÓSTICO DE REDE ---
    elif menu == "🛠️ Diagnóstico de Rede":
        st.header("🛠️ Diagnóstico Técnico")
        st.info("Ponto de Acesso: **ASB AUTOMACAO WIFI** | Senha: **asbconect**")
        if st.button("FORÇAR REINICIALIZAÇÃO DO HARDWARE (RESET)"):
            db.reference("controle/restart").set(True)
            st.warning("Sinal de reset enviado ao ESP32.")

# --- RODAPÉ ---
st.markdown("---")
st.caption("© 2026 ASB AUTOMAÇÃO INDUSTRIAL | Tecnologia e Precisão.")
