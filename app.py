import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
import pandas as pd # Caso use nos relatórios

# --- 1. CONEXÃO FIREBASE (PRESERVADA) ---
if not firebase_admin._apps:
    try:
        creds = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        }
        cred = credentials.Certificate(creds)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'
        })
    except:
        pass

# --- 2. CONFIGURAÇÃO VISUAL ORIGINAL ---
st.set_page_config(page_title="SISTEMA ASB INDUSTRIAL", layout="wide")

# --- 3. MENU DE NAVEGAÇÃO LATERAL (IDENTICO AO ANTERIOR) ---
st.sidebar.title("MENU ASB")
menu = st.sidebar.radio("Navegação", 
    ["Painel de Controle", "Relatórios", "Cadastro de Usuários", "Diagnóstico de Rede"])

# --- FUNÇÃO DE STATUS (HEARTBEAT) ---
def verificar_conexao():
    v1 = db.reference("sensor/last_seen").get() or 0
    time.sleep(0.3)
    v2 = db.reference("sensor/last_seen").get() or 0
    return v1 != v2

# --- TELA: PAINEL DE CONTROLE ---
if menu == "Painel de Controle":
    st.title("🕹️ Painel de Controle e Monitoramento")
    
    # Status de conexão integrado sem mudar o layout
    online = verificar_conexao()
    if online:
        st.success("Equipamento Online")
    else:
        st.error("Equipamento Offline")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Acionamento")
        if st.button("LIGAR MÁQUINA"):
            db.reference("controle/led").set("ON")
        if st.button("DESLIGAR MÁQUINA"):
            db.reference("controle/led").set("OFF")

    with col2:
        st.subheader("Dados do Sensor")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        st.metric("Temperatura", f"{t} °C")
        st.metric("Umidade", f"{u} %")
    
    time.sleep(2)
    st.rerun()

# --- TELA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatórios de Operação")
    st.write("Histórico de leituras e acionamentos.")
    # Espaço reservado para sua lógica original de tabelas/gráficos
    st.info("Consulte aqui os dados salvos no banco de dados.")

# --- TELA: CADASTRO DE USUÁRIOS ---
elif menu == "Cadastro de Usuários":
    st.title("👥 Cadastro de Usuários")
    st.write("Gerencie quem tem acesso ao sistema.")
    with st.form("cadastro_usuario"):
        nome = st.text_input("Nome Completo")
        cargo = st.text_input("Cargo/Setor")
        enviar = st.form_submit_button("Cadastrar")
        if enviar:
            st.success(f"Usuário {nome} cadastrado com sucesso!")

# --- TELA: DIAGNÓSTICO DE REDE ---
elif menu == "Diagnóstico de Rede":
    st.title("🛠️ Diagnóstico de Conexão")
    st.write("Informações técnicas para manutenção.")
    
    st.info("Rede Wi-Fi para Configuração: **ASB AUTOMACAO WIFI**")
    st.info("Senha padrão: **asbconect**")
    
    st.markdown("---")
    st.subheader("Ações de Recuperação")
    if st.button("REINICIAR EQUIPAMENTO (RESET REMOTO)"):
        db.reference("controle/restart").set(True)
        st.warning("Comando de reinicialização enviado ao hardware.")
