import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from datetime import datetime
import time

# --- 1. CONFIGURAÇÕES TÉCNICAS E ESTILO ---
st.set_page_config(page_title="ASB INDUSTRIAL - LOGIN", layout="wide")

# CSS para deixar a tela de login profissional e centralizada
st.markdown("""
    <style>
    .login-box { background-color: #ffffff; padding: 30px; border-radius: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO DO BANCO DE DADOS ---
@st.cache_resource
def conectar_banco():
    if not firebase_admin._apps:
        try:
            # Puxa as credenciais dos Secrets do Streamlit
            cred_data = {
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
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except:
            return False
    return True

# --- 3. CONTROLE DE ACESSO (USUÁRIO E SENHA) ---
# Definimos as credenciais padrão aqui ou buscamos no banco futuramente
USUARIO_SISTEMA = "admin"
SENHA_SISTEMA = "asb2026"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def tela_login():
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito - ASB</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("Login"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("ENTRAR NO SISTEMA")
            
            if entrar:
                if u == USUARIO_SISTEMA and p == SENHA_SISTEMA:
                    st.session_state["autenticado"] = True
                    st.success("Acesso liberado!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

# --- 4. SISTEMA PRINCIPAL (SÓ APARECE SE LOGADO) ---
if not st.session_state["autenticado"]:
    tela_login()
else:
    conectar_banco()
    
    # Barra Lateral com Logout e Navegação
    st.sidebar.title("PAINEL ASB")
    if st.sidebar.button("SAIR / LOGOUT"):
        st.session_state["autenticado"] = False
        st.rerun()
        
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Selecione a Tela", 
        ["Acionamento", "Medição Real", "Relatórios Históricos", "Gestão de Usuários", "Diagnóstico Técnico"])

    # Função Heartbeat para Status
    def check_hw():
        v1 = db.reference("sensor/last_seen").get()
        time.sleep(0.3)
        v2 = db.reference("sensor/last_seen").get()
        return v1 != v2

    # --- TELAS SEPARADAS ---
    if menu == "Acionamento":
        st.header("🕹️ Controle de Acionamento")
        if check_hw(): st.success("Status: EQUIPAMENTO PRONTO")
        else: st.error("Status: EQUIPAMENTO OFFLINE")
        
        c1, c2 = st.columns(2)
        if c1.button("LIGAR"): db.reference("controle/led").set("ON")
        if c2.button("DESLIGAR"): db.reference("controle/led").set("OFF")

    elif menu == "Medição Real":
        st.header("🌡️ Telemetria de Sensores")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura", f"{t} °C")
        col_u.metric("Umidade", f"{u} %")
        time.sleep(3)
        st.rerun()

    elif menu == "Relatórios Históricos":
        st.header("📊 Relatórios de Produção")
        st.write("Histórico de eventos e telemetria.")
        # Exemplo de tabela encorpada
        df_log = pd.DataFrame({
            "Timestamp": [datetime.now().strftime("%H:%M:%S")],
            "Evento": ["Monitoramento Ativo"],
            "Status": ["OK"]
        })
        st.dataframe(df_log, use_container_width=True)

    elif menu == "Gestão de Usuários":
        st.header("👥 Cadastro e Permissões")
        st.text_input("Novo Usuário")
        st.text_input("Nova Senha", type="password")
        st.button("Cadastrar Novo Operador")

    elif menu == "Diagnóstico Técnico":
        st.header("🛠️ Ferramentas de Manutenção")
        st.info("Rede: ASB AUTOMACAO WIFI | Senha: asbconect")
        if st.button("REINICIAR HARDWARE"):
            db.reference("controle/restart").set(True)
            st.warning("Comando de reset enviado com sucesso.")

# Rodapé profissional
st.markdown("---")
st.caption("© 2026 ASB Industrial - Tecnologia em Monitoramento")
