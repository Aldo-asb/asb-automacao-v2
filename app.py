import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd
import time
import pytz
import urllib.parse 

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 10px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 10px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; }
    
    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: sans-serif; position: relative; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
    .msg-admin { align-self: flex-end; background-color: #dcf8c6; border-top-right-radius: 0; }
    .msg-user { align-self: flex-start; background-color: #ffffff; border-top-left-radius: 0; }
    .msg-info { font-size: 12px; color: #555; font-weight: bold; }
    .msg-hora { font-size: 10px; color: #888; text-align: right; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES AUXILIARES ---
def obter_hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso)

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

def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
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
                server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(remetente, senha)
                server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string()); server.quit()
    except: pass

# --- 3. FLUXO DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "email_ativo" not in st.session_state: st.session_state["email_ativo"] = True
if "click_status" not in st.session_state: st.session_state["click_status"] = None

if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB AUTOMAÇÃO INDUSTRIAL</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u_input = st.text_input("Usuário")
        p_input = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if u_input == "admin" and p_input == "asb2026":
                st.session_state["logado"], st.session_state["user_nome"], st.session_state["is_admin"] = True, "Admin Master", True
                st.rerun()
            else:
                conectar_firebase()
                usuarios_db = db.reference("usuarios_autorizados").get()
                if usuarios_db:
                    for key, user_data in usuarios_db.items():
                        if user_data['login'] == u_input and user_data['senha'] == p_input:
                            st.session_state["logado"], st.session_state["user_nome"], st.session_state["is_admin"] = True, user_data['nome'], False
                            st.rerun()
                st.error("Dados incorretos.")
else:
    conectar_firebase()
    menu = st.sidebar.radio("Navegação:", ["Acionamento", "Medição", "Relatórios", "Diagnóstico"] + (["Gestão de Usuários"] if st.session_state["is_admin"] else []))
    st.session_state["email_ativo"] = st.sidebar.toggle("E-mail Automático", value=st.session_state["email_ativo"])
    if st.sidebar.button("SAIR"): st.session_state["logado"] = False; st.rerun()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "Acionamento":
        st.header("🕹️ Controle Operacional")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"LIGAR {'🟢' if st.session_state['click_status'] == 'ON' else '⚪'}"):
                db.reference("controle/led").set("ON"); st.session_state["click_status"] = "ON"; registrar_evento("LIGOU EQUIPAMENTO"); st.rerun()
        with c2:
            if st.button(f"DESLIGAR {'🔴' if st.session_state['click_status'] == 'OFF' else '⚪'}"):
                db.reference("controle/led").set("OFF"); st.session_state["click_status"] = "OFF"; registrar_evento("DESLIGOU EQUIPAMENTO"); st.rerun()

    # --- TELA 2: MEDIÇÃO (REFRESH ADICIONADO) ---
    elif menu == "Medição":
        st.header("🌡️ Monitoramento")
        t, u = db.reference("sensor/temperatura").get() or 0, db.reference("sensor/umidade").get() or 0
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura", f"{t} °C"); col_u.metric("Umidade", f"{u} %")
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1: st.subheader("🌡️ Temperatura"); st.bar_chart(pd.DataFrame({"°C": [t]}, index=["Atual"]), color="#dc3545")
        with g2: st.subheader("💧 Umidade"); st.bar_chart(pd.DataFrame({"%": [u]}, index=["Atual"]), color="#00458d")
        if st.button("🔄 ATUALIZAR LEITURA"): st.rerun()

    # --- TELA 3: RELATÓRIOS (WHATSAPP PADRÃO) ---
    elif menu == "Relatórios":
        st.header("💬 Central de Mensagens")
        
        with st.expander("📲 Enviar Notificação WhatsApp", expanded=True):
            # Substitua pelo seu número padrão no formato: 55 + DDD + Numero (Sem espaços)
            tel_padrao = "62996732859" 
            tel = st.text_input("Número do Gestor (DDD + Número)", value=tel_padrao)
            msg_zap = st.text_area("Mensagem de Alerta", "Aviso do Sistema ASB: Por favor, verifique o painel.")
            if st.button("GERAR LINK DE ENVIO"):
                if tel and msg_zap:
                    texto_url = urllib.parse.quote(msg_zap)
                    link = f"https://wa.me/{tel}?text={texto_url}"
                    st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold; font-size:18px;">👉 CLIQUE AQUI PARA ENVIAR NO WHATSAPP</div></a>', unsafe_allow_html=True)
                    registrar_evento(f"ALERTA WHATSAPP GERADO PARA {tel}")
                else: st.warning("Dados incompletos.")

        st.markdown("---")
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for key in logs:
                val = logs[key]
                user, acao, data = val.get("usuario", "Sistema"), val.get("acao", ""), val.get("data", "")
                classe = "msg-admin" if user == "Admin Master" else "msg-user"
                st.markdown(f'<div class="msg-balao {classe}"><div class="msg-info">{user}</div><div>{acao}</div><div class="msg-hora">{data}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🗑️ LIMPAR HISTÓRICO"):
            db.reference("historico_acoes").delete(); st.rerun()

    # --- TELA 4: DIAGNÓSTICO ---
    elif menu == "Diagnóstico":
        st.header("🛠️ Status")
        if db.reference("sensor/temperatura").get() is not None:
            st.markdown("<div class='status-ok'>SISTEMA ONLINE</div>", unsafe_allow_html=True)
        else: st.markdown("<div class='status-erro'>SISTEMA OFFLINE</div>", unsafe_allow_html=True)
        if st.button("RESETAR HARDWARE"): db.reference("controle/restart").set(True); registrar_evento("RESET REMOTO")

# ASB AUTOMAÇÃO INDUSTRIAL - v7.8
