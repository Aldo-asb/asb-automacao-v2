import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd
import time
import pytz

# --- 1. CONFIGURAÇÃO VISUAL (PRESERVADA v7.5) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 10px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 10px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; }
    
    .chat-container { display: flex; flex-direction: column; gap: 10px; background-color: #e5ddd5; padding: 20px; border-radius: 15px; max-height: 500px; overflow-y: auto; }
    .msg-balao { max-width: 70%; padding: 10px 15px; border-radius: 15px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; position: relative; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
    .msg-admin { align-self: flex-end; background-color: #dcf8c6; border-top-right-radius: 0; }
    .msg-user { align-self: flex-start; background-color: #ffffff; border-top-left-radius: 0; }
    .msg-info { font-size: 12px; color: #555; margin-bottom: 3px; font-weight: bold; }
    .msg-texto { font-size: 16px; color: #000; }
    .msg-hora { font-size: 10px; color: #888; text-align: right; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÃO PARA HORÁRIO DE BRASÍLIA ---
def obter_hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso)

# --- 3. CONEXÃO FIREBASE ---
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

# --- 4. REGISTRO DE EVENTO E E-MAIL (REVISADO E BLINDADO) ---
def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    
    # 1. Sempre registra no Firebase primeiro
    try:
        db.reference("historico_acoes").push({"data": agora, "usuario": usuario, "acao": acao})
    except:
        st.error("Erro ao gravar no banco de dados.")

    # 2. Envio de E-mail
    if st.session_state.get("email_ativo", True) or manual:
        try:
            remetente = st.secrets.get("email_user")
            senha = st.secrets.get("email_password")
            destinatario = "asbautomacao@gmail.com"
            
            if remetente and senha:
                msg = MIMEText(f"LOG ASB INDUSTRIAL\n\nUsuário: {usuario}\nAção: {acao}\nData/Hora: {agora}\nStatus: Sistema Operacional")
                msg['Subject'] = f"SISTEMA ASB: {acao}"
                msg['From'] = remetente
                msg['To'] = destinatario
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(remetente, senha)
                server.sendmail(remetente, destinatario, msg.as_string())
                server.quit()
            else:
                st.warning("Configurações de e-mail ausentes nos Secrets.")
        except Exception as e:
            # Mostra o erro apenas se for um envio manual para não poluir a tela
            if manual: st.error(f"Erro no envio de e-mail: {e}")

# --- 5. FLUXO DE LOGIN ---
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
                st.session_state["logado"] = True
                st.session_state["user_nome"] = "Admin Master"
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                conectar_firebase()
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
        st.session_state["is_admin"] = False
        st.session_state["click_status"] = None
        st.rerun()

    # --- TELA 1: ACIONAMENTO ---
    if menu == "Acionamento":
        st.header("🕹️ Controle Operacional")
        c1, c2 = st.columns(2)
        status_sessao = st.session_state["click_status"]
        with c1:
            label_ligar = f"LIGAR {'🟢' if status_sessao == 'ON' else '⚪'}"
            if st.button(label_ligar):
                db.reference("controle/led").set("ON")
                st.session_state["click_status"] = "ON"
                registrar_evento("LIGOU EQUIPAMENTO")
                st.rerun()
        with c2:
            label_desligar = f"DESLIGAR {'🔴' if status_sessao == 'OFF' else '⚪'}"
            if st.button(label_desligar):
                db.reference("controle/led").set("OFF")
                st.session_state["click_status"] = "OFF"
                registrar_evento("DESLIGOU EQUIPAMENTO")
                st.rerun()

    # --- TELA 2: MEDIÇÃO (GRÁFICOS SEPARADOS) ---
    elif menu == "Medição":
        st.header("🌡️ Monitoramento")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura", f"{t} °C")
        col_u.metric("Umidade", f"{u} %")
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🌡️ Nível de Temperatura")
            st.bar_chart(pd.DataFrame({"°C": [t]}, index=["Atual"]), color="#dc3545")
        with g2:
            st.subheader("💧 Nível de Umidade")
            st.bar_chart(pd.DataFrame({"%": [u]}, index=["Atual"]), color="#00458d")
        
        if st.button("🔄 REFRESH (ATUALIZAR LEITURA)"):
            st.rerun()

    # --- TELA 3: RELATÓRIOS (ESTILO WHATSAPP) ---
    elif menu == "Relatórios":
        st.header("💬 Diário de Operações")
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            if st.button("📧 ENVIAR LOG POR E-MAIL"):
                registrar_evento("RELATÓRIO MANUAL SOLICITADO", manual=True)
                st.success("Tentativa de envio processada!")
        with col_rel2:
            confirmar_limpeza = st.checkbox("Confirmar exclusão de mensagens")
            if st.button("🗑️ LIMPAR HISTÓRICO"):
                if confirmar_limpeza:
                    db.reference("historico_acoes").delete()
                    registrar_evento("SISTEMA RESETADO PELO ADMIN")
                    st.rerun()
        
        st.markdown("---")
        logs = db.reference("historico_acoes").get()
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for key in logs:
                val = logs[key]
                user = val.get("usuario", "Sistema")
                acao = val.get("acao", "")
                data_hora = val.get("data", "")
                classe_balao = "msg-admin" if user == "Admin Master" else "msg-user"
                st.markdown(f'<div class="msg-balao {classe_balao}"><div class="msg-info">{user}</div><div class="msg-texto">{acao}</div><div class="msg-hora">{data_hora}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else: st.info("Nenhuma mensagem no histórico.")

    # --- TELA 4: DIAGNÓSTICO ---
    elif menu == "Diagnóstico":
        st.header("🛠️ Status de Comunicação")
        check_sensor = db.reference("sensor/temperatura").get()
        if check_sensor is not None:
            st.markdown(f"<div class='status-ok'>SISTEMA ONLINE</div>", unsafe_allow_html=True)
        else: st.markdown("<div class='status-erro'>SISTEMA OFFLINE</div>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🔄 ATUALIZAR STATUS"):
            st.rerun()
        if st.button("RESETAR HARDWARE"):
            db.reference("controle/restart").set(True)
            registrar_evento("RESET REMOTO")

    # --- TELA 5: GESTÃO DE USUÁRIOS ---
    elif menu == "Gestão de Usuários":
        if st.session_state["is_admin"]:
            st.header("👥 Cadastro de Operadores")
            with st.form("form_cadastro"):
                nome_novo = st.text_input("Nome Completo")
                login_novo = st.text_input("Login")
                senha_nova = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    if nome_novo and login_novo and senha_nova:
                        db.reference("usuarios_autorizados").push({
                            "nome": nome_novo, "login": login_novo, "senha": senha_nova,
                            "data_criacao": obter_hora_brasilia().strftime('%d/%m/%Y')
                        })
                        st.success(f"Operador {nome_novo} cadastrado!")
            lista_users = db.reference("usuarios_autorizados").get()
            if lista_users:
                for key, val in lista_users.items():
                    st.markdown(f"<div class='card-usuario'><b>Nome:</b> {val.get('nome')} | <b>Login:</b> {val.get('login')}</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v7.6
