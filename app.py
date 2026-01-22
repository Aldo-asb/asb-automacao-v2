import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONEXÃO FIREBASE (CONFIGURAÇÃO PELOS SECRETS) ---
def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # Pega as chaves campo a campo dos Secrets (Formato TOML)
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
            return True
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            return False
    return True

# --- 2. CONFIGURAÇÕES DE PÁGINA E DESIGN INDUSTRIAL ---
st.set_page_config(page_title="ASB INDUSTRIAL V3", layout="wide", page_icon="🏭")

# CSS para visual profissional e escuro
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 5px; height: 3.5em; font-weight: bold; 
        background-color: #1f2937; color: white; border: 1px solid #4a4a4a;
        transition: 0.3s;
    }
    .stButton>button:hover { border-color: #00ff00; color: #00ff00; background-color: #111827; }
    .status-container { 
        text-align: center; padding: 30px; background-color: #1f2937; 
        border-radius: 15px; border: 2px solid #374151; margin-top: 10px; 
    }
    .status-text { color: #ffffff !important; font-size: 24px !important; font-weight: bold !important; display: block; margin-top: 10px; }
    .report-card { 
        background-color: #2d3748; padding: 15px; border-radius: 8px; 
        border-left: 5px solid #4ade80; margin-bottom: 10px; color: white; 
    }
    .metric-box { background-color: #1f2937; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE SUPORTE ---
def get_hora_brasil():
    return (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")

def enviar_email_relatorio(destinatario, assunto, corpo):
    try:
        remetente = "asbautomacao@gmail.com"
        senha = "qmvm fnsn afok jejs" # Sua senha de app configurada
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro e-mail: {e}")
        return False

# --- 4. LÓGICA DO SISTEMA ---
if inicializar_firebase():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    # TELA DE LOGIN
    if not st.session_state['autenticado']:
        st.markdown("<h1 style='text-align:center; color:#00ff00;'>ASB AUTOMAÇÃO INDUSTRIAL</h1>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            with st.form("Login"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR SISTEMA"):
                    if u == "admin" and s == "asb123":
                        st.session_state.update({'autenticado':True, 'usuario':"ADMIN", 'role':"admin"})
                        st.rerun()
                    else:
                        usuarios_db = db.reference("config/usuarios").get()
                        if isinstance(usuarios_db, dict):
                            for uid, dados in usuarios_db.items():
                                if dados.get('user') == u and dados.get('pass') == s:
                                    st.session_state.update({'autenticado':True, 'usuario':u, 'role':"cliente"})
                                    st.rerun()
                        st.error("Credenciais inválidas")
    
    # SISTEMA APÓS LOGIN
    else:
        # MENU LATERAL PROFISSIONAL
        st.sidebar.markdown(f"<h2 style='color:#00ff00; text-align:center;'>🏭 ASB INDUSTRIAL</h2>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<p style='text-align:center;'>Operador: <b>{st.session_state['usuario']}</b></p>", unsafe_allow_html=True)
        st.sidebar.divider()
        
        menu = ["🕹️ COMANDO", "📈 TELEMETRIA", "📊 RELATÓRIOS"]
        if st.session_state['role'] == "admin": menu.append("👤 GESTÃO")
        aba = st.sidebar.radio("NAVEGAÇÃO", menu)

        st.sidebar.divider()
        envio_auto = st.sidebar.toggle("E-mail Automático", True)
        email_destino = st.sidebar.text_input("E-mail de Alerta", "asbautomacao@gmail.com")

        if st.sidebar.button("SAIR DO SISTEMA"):
            st.session_state['autenticado'] = False
            st.rerun()

        # --- ABA: COMANDO ---
        if aba == "🕹️ COMANDO":
            st.title("🕹️ CENTRO DE COMANDO")
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown("### Controle de Atuadores")
                if st.button("🚀 LIGAR SISTEMA"):
                    db.reference("controle/led").set("ON")
                    agora = get_hora_brasil()
                    t = db.reference("sensor/temperatura").get() or "0"
                    db.reference("logs/operacao").push({"acao": f"LIGOU", "user": st.session_state['usuario'], "temp": t, "data": agora})
                    if envio_auto:
                        enviar_email_relatorio(email_destino, "ALERTA ASB: SISTEMA LIGADO", f"O sistema foi acionado por {st.session_state['usuario']} às {agora}.\nTemperatura Atual: {t}°C")
                    st.toast("Comando de Ligar enviado!")

                if st.button("🛑 DESLIGAR SISTEMA"):
                    db.reference("controle/led").set("OFF")
                    agora = get_hora_brasil()
                    t = db.reference("sensor/temperatura").get() or "0"
                    db.reference("logs/operacao").push({"acao": f"DESLIGOU", "user": st.session_state['usuario'], "temp": t, "data": agora})
                    if envio_auto:
                        enviar_email_relatorio(email_destino, "ALERTA ASB: SISTEMA DESLIGADO", f"O sistema foi desligado por {st.session_state['usuario']} às {agora}.")
                    st.toast("Comando de Desligar enviado!")

            with c2:
                st.markdown("### Monitor de Estado")
                status_placeholder = st.empty()
                @st.fragment(run_every=2)
                def monitor_led():
                    estado = db.reference("controle/led").get() or "OFF"
                    cor, texto = ("🟢", "EM OPERAÇÃO") if "ON" in str(estado).upper() else ("🔴", "DESATIVADA")
                    status_placeholder.markdown(f"""
                        <div class='status-container'>
                            <span style='font-size:60px;'>{cor}</span>
                            <span class='status-text'>MÁQUINA {texto}</span>
                        </div>
                    """, unsafe_allow_html=True)
                monitor_led()

        # --- ABA: TELEMETRIA ---
        elif aba == "📈 TELEMETRIA":
            st.title("📈 TELEMETRIA EM TEMPO REAL")
            m1, m2 = st.columns(2)
            t_placeholder = m1.empty()
            u_placeholder = m2.empty()
            
            @st.fragment(run_every=3)
            def atualizar_metricas():
                temp = db.reference('sensor/temperatura').get() or '0'
                umid = db.reference('sensor/umidade').get() or '0'
                t_placeholder.metric("🌡️ TEMPERATURA", f"{temp} °
