import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pandas as pd

# --- 1. IDENTIDADE VISUAL ASB (DESTAQUE MÁXIMO) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb {
        color: #00458d;
        font-size: 55px;
        font-weight: bold;
        text-align: center;
        margin-top: 40px;
        font-family: 'Arial Black', sans-serif;
        border-bottom: 3px solid #00458d;
    }
    .stButton>button { width: 100%; height: 3.8em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .stMetric { background-color: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #dcdcdc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO FIREBASE (PRESERVADA) ---
@st.cache_resource
def conectar_firebase():
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

# --- 3. FUNÇÃO DE LOG POR E-MAIL (ACIONAMENTO E ALERTAS) ---
def registrar_evento_email(usuario, acao_detalhada):
    try:
        # Usa as credenciais configuradas nos Secrets do Streamlit
        remetente = st.secrets["email_user"]
        senha_app = st.secrets["email_password"]
        destinatario = "asbautomacao@gmail.com"
        
        hora_exata = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        corpo_msg = f"""
        RELATÓRIO DE EVENTO - ASB AUTOMAÇÃO INDUSTRIAL
        ----------------------------------------------
        USUÁRIO RESPONSÁVEL: {usuario}
        HORÁRIO DA AÇÃO: {hora_exata}
        DESCRIÇÃO DA AÇÃO: {acao_detalhada}
        STATUS DO SISTEMA: Registrado via Supervisório v3.0
        ----------------------------------------------
        """
        
        msg = MIMEText(corpo_msg)
        msg['Subject'] = f"LOG ASB: {acao_detalhada}"
        msg['From'] = remetente
        msg['To'] = destinatario
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remetente, senha_app)
            server.sendmail(remetente, destinatario, msg.as_string())
        return True
    except:
        return False

# --- 4. FLUXO DE ACESSO (LOGIN) ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    st.write("")
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("Acesso"):
            user = st.text_input("Usuário Identificado")
            pw = st.text_input("Senha de Segurança", type="password")
            if st.form_submit_button("VALIDAR ACESSO"):
                if user == "admin" and pw == "asb2026":
                    st.session_state["logado"] = True
                    st.session_state["usuario_nome"] = user
                    st.rerun()
                else:
                    st.error("Credenciais Negadas.")
else:
    conectar_firebase()
    
    # --- 5. NAVEGAÇÃO LATERAL (ESTRUTURA ORIGINAL PRESERVADA) ---
    st.sidebar.title("PAINEL INDUSTRIAL")
    st.sidebar.info(f"Operador: {st.session_state['usuario_nome']}")
    
    menu = st.sidebar.radio("Selecione a Tela:", 
        ["Acionamento Individual", "Medição de Sensores", "Relatórios e E-mail", "Cadastro de Usuários", "Diagnóstico de Conexão"])

    # LOGICA DE WATCHDOG (AVISO DE FALHA REAL)
    ref_check = db.reference("sensor/temperatura")
    val_a = ref_check.get() or 0
    time.sleep(0.4)
    val_b = ref_check.get() or 0
    is_online = (val_a != val_b)

    if st.sidebar.button("FINALIZAR SESSÃO (LOGOUT)"):
        st.session_state["logado"] = False
        st.rerun()

    # --- TELA 1: ACIONAMENTO (COM ENVIO DE E-MAIL AUTOMÁTICO) ---
    if menu == "Acionamento Individual":
        st.header("🕹️ Painel de Acionamento")
        if not is_online:
            st.error("⚠️ ERRO DE COMUNICAÇÃO: O EQUIPAMENTO NÃO RESPONDE.")
        
        c_on, c_off = st.columns(2)
        if c_on.button("LIGAR MÁQUINA"):
            db.reference("controle/led").set("ON")
            registrar_evento_email(st.session_state["usuario_nome"], "LIGOU O EQUIPAMENTO")
            st.success("Comando executado e e-mail enviado para asbautomacao@gmail.com")
            
        if c_off.button("DESLIGAR MÁQUINA"):
            db.reference("controle/led").set("OFF")
            registrar_evento_email(st.session_state["usuario_nome"], "DESLIGOU O EQUIPAMENTO")
            st.warning("Comando executado e e-mail enviado para asbautomacao@gmail.com")

    # --- TELA 2: MEDIÇÃO DE SENSORES ---
    elif menu == "Medição de Sensores":
        st.header("🌡️ Telemetria em Tempo Real")
        t = db.reference("sensor/temperatura").get() or 0.0
        u = db.reference("sensor/umidade").get() or 0.0
        
        st.metric("Temperatura de Processo", f"{t} °C")
        st.metric("Umidade Relativa", f"{u} %")
        
        if t > 50:
            st.error("⚠️ ALERTA DE ALTA TEMPERATURA!")
            # Opcional: registrar_evento_email("SISTEMA", "ALERTA AUTOMÁTICO: TEMPERATURA ACIMA DE 50C")
            
        time.sleep(2)
        st.rerun()

    # --- TELA 3: RELATÓRIOS E E-MAIL ---
    elif menu == "Relatórios e E-mail":
        st.header("📊 Relatórios e Logs")
        st.write(f"Histórico destinado a: **asbautomacao@gmail.com**")
        
        if st.button("GERAR E ENVIAR RELATÓRIO DE STATUS AGORA"):
            t_r = db.reference("sensor/temperatura").get()
            info = f"Solicitação Manual de Relatório\nTemp: {t_r}C\nStatus: Online"
            if registrar_evento_email(st.session_state["usuario_nome"], info):
                st.success("Relatório enviado com sucesso!")

    # --- TELA 4: CADASTRO DE USUÁRIOS ---
    elif menu == "Cadastro de Usuários":
        st.header("👥 Gestão de Acessos")
        st.text_input("Novo Usuário")
        st.selectbox("Perfil", ["Operador", "Manutenção", "Gerência"])
        st.button("Cadastrar")

    # --- TELA 5: DIAGNÓSTICO DE CONEXÃO ---
    elif menu == "Diagnóstico de Conexão":
        st.header("🛠️ Diagnóstico do Hardware")
        st.info("Rede Operacional: **ASB AUTOMACAO WIFI**")
        if st.button("REINICIAR ESP32 REMOTAMENTE"):
            db.reference("controle/restart").set(True)
            registrar_evento_email(st.session_state["usuario_nome"], "SOLICITOU RESET DO HARDWARE")
            st.warning("Reset enviado.")

st.markdown("---")
st.caption("ASB AUTOMAÇÃO INDUSTRIAL - Sistema de Gestão V3.1")
