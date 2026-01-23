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
    .status-box { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; }
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

# --- 3. FUNÇÃO DE E-MAIL (CORRIGIDA PARA NÃO CAIR NO SPAM) ---
def enviar_email_asb(assunto, acao):
    try:
        remetente = st.secrets["email_user"]
        senha = st.secrets["email_password"]
        destinatario = "asbautomacao@gmail.com"
        
        msg = MIMEText(f"SISTEMA ASB INDUSTRIAL\n\nDETALHES: {acao}\nHORA: {datetime.now().strftime('%H:%M:%S')}\nOPERADOR: admin")
        msg['Subject'] = assunto
        msg['From'] = remetente
        msg['To'] = destinatario
        
        # Uso de SMTP padrão com STARTTLS (mais aceite pelo Gmail)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.sidebar.error(f"Falha no Servidor de E-mail: {e}")
        return False

# --- 4. CONTROLE DE SESSÃO E LOGIN ---
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
                st.rerun()
            else: st.error("Acesso Negado")
else:
    iniciar_firebase()
    
    # --- 5. MENU LATERAL ---
    st.sidebar.title("PAINEL DE CONTROLO")
    menu = st.sidebar.radio("Navegação:", ["🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "👥 Cadastro", "🛠️ Diagnóstico"])
    
    st.sidebar.markdown("---")
    # BOTÃO PARA ATIVAR/DESATIVAR ENVIO AUTOMÁTICO (RECUPERADO)
    st.session_state["envio_auto"] = st.sidebar.toggle("Envio Automático de E-mail", value=st.session_state["envio_auto"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state["logado"] = False
        st.rerun()

    # --- LÓGICA DAS TELAS (ISOLADAS PARA NÃO MISTURAR) ---
    conteudo = st.empty()

    if menu == "🕹️ Acionamento":
        with conteudo.container():
            st.header("🕹️ Controlo de Acionamento")
            c1, c2 = st.columns(2)
            
            if c1.button("LIGAR EQUIPAMENTO"):
                db.reference("controle/led").set("ON")
                if st.session_state["envio_auto"]:
                    enviar_email_asb("ALERTA: Equipamento Ligado", "O operador acionou o comando LIGAR.")
                st.success("Comando enviado!")

            if c2.button("DESLIGAR EQUIPAMENTO"):
                db.reference("controle/led").set("OFF")
                if st.session_state["envio_auto"]:
                    enviar_email_asb("ALERTA: Equipamento Desligado", "O operador acionou o comando DESLIGAR.")
                st.warning("Comando enviado!")

    elif menu == "🌡️ Medição":
        with conteudo.container():
            st.header("🌡️ Telemetria em Tempo Real")
            temp = db.reference("sensor/temperatura").get() or 0
            umid = db.reference("sensor/umidade").get() or 0
            
            col_t, col_u = st.columns(2)
            col_t.metric("Temperatura", f"{temp} °C")
            col_u.metric("Umidade", f"{umid} %")
            
            # Alerta automático por temperatura (se ativo)
            if temp > 45 and st.session_state["envio_auto"]:
                enviar_email_asb("CRÍTICO: Temperatura Alta", f"Atenção: {temp}°C detectados!")
            
            time.sleep(2)
            st.rerun()

    elif menu == "📊 Relatórios":
        with conteudo.container():
            st.header("📊 Relatórios e Envio Manual")
            st.write("Configuração atual de e-mail: **asbautomacao@gmail.com**")
            
            if st.button("ENVIAR RELATÓRIO MANUAL AGORA"):
                t_atual = db.reference("sensor/temperatura").get()
                if enviar_email_asb("Relatório Manual ASB", f"Status OK. Temperatura atual: {t_atual}°C"):
                    st.success("E-mail manual enviado com sucesso!")
                else:
                    st.error("Erro no envio. Verifique a barra lateral.")

    elif menu == "👥 Cadastro":
        with conteudo.container():
            st.header("👥 Gestão de Operadores")
            st.text_input("Novo Usuário")
            st.button("Gravar no Banco")

    elif menu == "🛠️ Diagnóstico":
        with conteudo.container():
            st.header("🛠️ Diagnóstico do Sistema")
            if st.button("REINICIAR HARDWARE"):
                db.reference("controle/restart").set(True)
                if st.session_state["envio_auto"]:
                    enviar_email_asb("LOG: Sistema Reiniciado", "Comando de Reset enviado via web.")
