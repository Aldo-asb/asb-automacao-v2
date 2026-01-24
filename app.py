import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd
import time

# --- 1. CONFIGURAÇÃO VISUAL (PRESERVADA) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

st.markdown("""
    <style>
    .titulo-asb { color: #00458d; font-size: 55px; font-weight: bold; text-align: center; margin-top: 40px; border-bottom: 3px solid #00458d; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; background-color: #00458d; color: white; border-radius: 10px; }
    .card-usuario { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #00458d; }
    .status-ok { color: #28a745; font-weight: bold; padding: 10px; border: 2px solid #28a745; border-radius: 8px; text-align: center; background-color: #e8f5e9; }
    .status-erro { color: #dc3545; font-weight: bold; padding: 10px; border: 2px solid #dc3545; border-radius: 8px; text-align: center; background-color: #ffebee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO FIREBASE ---
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

# --- 3. REGISTRO DE EVENTO E E-MAIL ---
def registrar_evento(acao, manual=False):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
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
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(remetente, senha)
                    server.sendmail(remetente, "asbautomacao@gmail.com", msg.as_string())
    except: pass

# --- 4. FLUXO DE LOGIN ---
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

    # --- TELA 2: MEDIÇÃO ---
    elif menu == "Medição":
        st.header("🌡️ Monitoramento")
        t = db.reference("sensor/temperatura").get() or 0
        u = db.reference("sensor/umidade").get() or 0
        
        col_t, col_u = st.columns(2)
        col_t.metric("Temperatura", f"{t} °C")
        col_u.metric("Umidade", f"{u} %")
        
        st.markdown("---")
        if st.button("🔄 ATUALIZAR LEITURA"):
            st.rerun()

    # --- TELA 3: RELATÓRIOS (ETAPA: LIMPAR HISTÓRICO) ---
    elif menu == "Relatórios":
        st.header("📊 Histórico")
        
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            if st.button("📧 ENVIAR HISTÓRICO POR E-MAIL"):
                registrar_evento("RELATÓRIO MANUAL SOLICITADO", manual=True)
                st.success("E-mail enviado!")
        
        with col_rel2:
            # Botão de limpeza com confirmação simples via checkbox
            confirmar_limpeza = st.checkbox("Confirmar exclusão permanente")
            if st.button("🗑️ LIMPAR TODO O HISTÓRICO"):
                if confirmar_limpeza:
                    db.reference("historico_acoes").delete()
                    registrar_evento("HISTÓRICO LIMPO PELO USUÁRIO")
                    st.success("Histórico removido com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Marque a confirmação acima para limpar.")

        st.markdown("---")
        logs = db.reference("historico_acoes").get()
        if logs:
            df = pd.DataFrame(list(logs.values())).iloc[::-1]
            st.table
