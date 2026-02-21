import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time
import pytz
import urllib.parse

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="ASB Automação Industrial", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── FUNDO GERAL ── */
.stApp {
    background: #0a0e1a;
    color: #e0e6f0;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #0d1220 !important;
    border-right: 1px solid #1e2d4a;
}
section[data-testid="stSidebar"] * { color: #c8d4e8 !important; }
section[data-testid="stSidebar"] .stRadio label { 
    font-size: 14px !important; 
    padding: 6px 0 !important;
}

/* ── TÍTULOS ── */
.titulo-asb {
    font-family: 'Rajdhani', sans-serif;
    color: #ffffff;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 4px;
    text-align: center;
    padding: 20px 0 4px 0;
    text-transform: uppercase;
}
.subtitulo-asb {
    color: #4a9eff;
    font-size: 13px;
    text-align: center;
    letter-spacing: 6px;
    text-transform: uppercase;
    margin-bottom: 32px;
}
.divider-blue {
    height: 2px;
    background: linear-gradient(90deg, transparent, #4a9eff, transparent);
    margin: 0 auto 32px auto;
    max-width: 400px;
}

/* ── CARDS GENÉRICOS ── */
.asb-card {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 12px;
    padding: 24px;
}

/* ── SEÇÃO: HOME ── */
.home-card {
    background: linear-gradient(135deg, #111827 0%, #0d1a2e 100%);
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 32px 24px;
    text-align: center;
    height: 100%;
    transition: border-color 0.3s ease;
}
.home-card:hover { border-color: #4a9eff; }
.home-icon { font-size: 36px; margin-bottom: 14px; }
.home-card h3 { 
    font-family: 'Rajdhani', sans-serif;
    color: #ffffff; font-size: 20px; font-weight: 600; 
    letter-spacing: 1px; margin-bottom: 10px;
}
.home-card p { color: #6b7fa3; font-size: 14px; line-height: 1.6; }

/* ── SEÇÃO: ACIONAMENTO ── */
.controle-wrap {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-top: 20px;
}
.btn-controle {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 28px 20px;
    border-radius: 14px;
    border: 2px solid;
    cursor: pointer;
    text-align: center;
    transition: all 0.2s ease;
    font-family: 'Rajdhani', sans-serif;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 2px;
}
.btn-ligar { 
    background: rgba(34, 197, 94, 0.1); 
    border-color: #22c55e; 
    color: #22c55e;
}
.btn-repouso { 
    background: rgba(251, 191, 36, 0.1); 
    border-color: #fbbf24; 
    color: #fbbf24;
}
.btn-desligar { 
    background: rgba(239, 68, 68, 0.1); 
    border-color: #ef4444; 
    color: #ef4444;
}
.btn-ativo-ligar { background: rgba(34, 197, 94, 0.25) !important; box-shadow: 0 0 20px rgba(34,197,94,0.4); }
.btn-ativo-repouso { background: rgba(251, 191, 36, 0.25) !important; box-shadow: 0 0 20px rgba(251,191,36,0.4); }
.btn-ativo-desligar { background: rgba(239, 68, 68, 0.25) !important; box-shadow: 0 0 20px rgba(239,68,68,0.4); }

.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    margin-top: 8px;
}
.badge-on { background: rgba(34,197,94,0.2); color: #22c55e; border: 1px solid #22c55e; }
.badge-off { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #ef4444; }
.badge-repouso { background: rgba(251,191,36,0.2); color: #fbbf24; border: 1px solid #fbbf24; }
.badge-inativo { background: rgba(100,116,139,0.2); color: #64748b; border: 1px solid #64748b; }

/* Barra animada */
.barra-wrap { height: 6px; border-radius: 6px; overflow: hidden; margin-top: 12px; background: #1e2d4a; }
.barra-on { height: 100%; background: linear-gradient(90deg, #22c55e, #86efac, #22c55e); background-size: 200%; animation: slide 1.5s linear infinite; }
.barra-repouso { height: 100%; background: linear-gradient(90deg, #fbbf24, #fde68a, #fbbf24); background-size: 200%; animation: slide 2s linear infinite; }
.barra-off { height: 100%; background: #ef4444; }
.barra-inativa { height: 100%; background: #1e2d4a; }
@keyframes slide { 0%{background-position:200% 0} 100%{background-position:0 0} }

/* ── SEÇÃO: MEDIÇÃO ── */
.gauge-card {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
    position: relative;
}
.gauge-label {
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a9eff;
    font-weight: 600;
    margin-bottom: 16px;
}
.gauge-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 72px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 6px;
}
.gauge-unit {
    font-size: 20px;
    color: #6b7fa3;
    margin-bottom: 20px;
}
.gauge-bar-bg { height: 8px; background: #1e2d4a; border-radius: 8px; overflow: hidden; margin-bottom: 16px; }
.gauge-bar-fill { height: 100%; border-radius: 8px; transition: width 0.8s ease; }
.gauge-temp-fill { background: linear-gradient(90deg, #3b82f6, #f59e0b, #ef4444); }
.gauge-umid-fill { background: linear-gradient(90deg, #06b6d4, #3b82f6); }
.gauge-meta { font-size: 12px; color: #4b5563; }
.dado-antigo { 
    background: rgba(239,68,68,0.1); 
    border: 1px solid rgba(239,68,68,0.3); 
    border-radius: 6px; 
    padding: 6px 12px; 
    font-size: 11px; 
    color: #ef4444; 
    margin-top: 8px;
    letter-spacing: 1px;
}
.dado-fresco {
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    color: #22c55e;
    margin-top: 8px;
    letter-spacing: 1px;
}

/* ── SEÇÃO: DIAGNÓSTICO ── */
.diag-status-ok {
    background: rgba(34,197,94,0.08);
    border: 1px solid #22c55e;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    color: #22c55e;
    font-family: 'Rajdhani', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 24px;
}
.diag-status-off {
    background: rgba(239,68,68,0.08);
    border: 1px solid #ef4444;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    color: #ef4444;
    font-family: 'Rajdhani', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 24px;
}
.diag-info-row {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #94a3b8;
}
.diag-info-label { font-weight: 600; color: #e2e8f0; min-width: 160px; }

/* Streamlit button overrides por contexto */
div[data-testid="stButton"] > button {
    width: 100%;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    letter-spacing: 2px !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 14px 20px !important;
    transition: all 0.2s ease !important;
}

/* Botões LIGAR / REPOUSO / DESLIGAR */
.ligar-btn div[data-testid="stButton"] > button { 
    background: linear-gradient(135deg, #166534, #22c55e) !important; 
    color: white !important; 
}
.repouso-btn div[data-testid="stButton"] > button { 
    background: linear-gradient(135deg, #78350f, #f59e0b) !important; 
    color: white !important; 
}
.desligar-btn div[data-testid="stButton"] > button { 
    background: linear-gradient(135deg, #7f1d1d, #ef4444) !important; 
    color: white !important; 
}

/* Botão padrão azul */
div[data-testid="stButton"] > button:not([kind]) {
    background: linear-gradient(135deg, #1e3a5f, #4a9eff) !important;
    color: white !important;
}

/* ── HEADER SEÇÃO ── */
.section-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 3px;
    color: #ffffff;
    text-transform: uppercase;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2d4a;
    margin-bottom: 24px;
}

/* ── CHAT LOGS ── */
.chat-container { 
    background: #0d1220; 
    border: 1px solid #1e2d4a;
    border-radius: 12px; 
    max-height: 420px; 
    overflow-y: auto; 
    padding: 16px;
}
.msg-balao { 
    background: #111827; 
    border-left: 3px solid #4a9eff; 
    border-radius: 8px; 
    padding: 10px 14px; 
    margin-bottom: 8px; 
    font-size: 13px; 
    color: #c8d4e8;
}
.msg-balao b { color: #4a9eff; }
.msg-balao small { color: #4b5563; }

/* ── CARD USUÁRIO ── */
.card-contato {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-left: 4px solid #22c55e;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    color: #c8d4e8;
    font-size: 14px;
}

/* ── MODO AUTO ── */
.auto-info {
    background: rgba(74,158,255,0.07);
    border: 1px solid rgba(74,158,255,0.25);
    border-radius: 12px;
    padding: 20px;
    color: #93c5fd;
    font-size: 15px;
    margin-bottom: 16px;
}

/* ── STATUS PILL ── */
.pill-container {
    display: flex;
    gap: 12px;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
}
.pill {
    padding: 6px 18px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border: 1px solid;
}

/* Inputs */
.stTextInput input, .stNumberInput input {
    background: #111827 !important;
    border: 1px solid #1e2d4a !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
.stRadio label { color: #c8d4e8 !important; }
</style>
""", unsafe_allow_html=True)


# --- 2. FUNÇÕES CORE ---
def obter_hora_brasilia():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

def enviar_email(assunto, mensagem):
    if not st.session_state.get("email_ativo", True): return
    try:
        remetente = st.secrets.get("email_user", "")
        senha = st.secrets.get("email_password", "")
        msg = MIMEText(mensagem)
        msg['Subject'], msg['From'], msg['To'] = assunto, remetente, remetente
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(remetente, senha)
            server.send_message(msg)
    except: pass

@st.cache_resource
def conectar_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["client_email"],
                "token_uri": st.secrets["token_uri"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://projeto-asb-comercial-default-rtdb.firebaseio.com/'})
            return True
        except: return False
    return True

def registrar_evento(acao):
    usuario = st.session_state.get("user_nome", "desconhecido")
    agora_f = obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    try:
        db.reference("historico_acoes").push({"data": agora_f, "usuario": usuario, "acao": acao})
        enviar_email(f"ASB: {acao}", f"Evento: {acao}\nUsuário: {usuario}\nData: {agora_f}")
    except: pass

def checar_dado_fresco(ultimo_pulso_ms, tolerancia_segundos=60):
    """Retorna True se o dado foi atualizado recentemente."""
    if not ultimo_pulso_ms:
        return False
    agora_ms = time.time() * 1000
    return (agora_ms - ultimo_pulso_ms) < (tolerancia_segundos * 1000)


# --- 3. ESTADOS ---
defaults = {
    "logado": False, "is_admin": False, "email_ativo": True,
    "modo_operacao": "MANUAL", "ciclo_ativo": False
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v


# --- 4. LOGIN ---
if not st.session_state["logado"]:
    conectar_firebase()
    st.markdown("<div class='titulo-asb'>ASB Automação Industrial</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-asb'>Plataforma Integrada IoT · 2026</div>", unsafe_allow_html=True)
    st.markdown("<div class='divider-blue'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.container():
            st.markdown("<div class='asb-card'>", unsafe_allow_html=True)
            u = st.text_input("Usuário", placeholder="seu login")
            p = st.text_input("Senha", type="password", placeholder="••••••••")
            if st.button("ACESSAR SISTEMA"):
                # Credenciais hardcoded (via secrets em produção)
                if u == "admin" and p == "asb2026":
                    st.session_state.update({"logado": True, "user_nome": "Admin Master", "is_admin": True})
                    st.rerun()
                elif u == "JM" and p == "123":
                    st.session_state.update({"logado": True, "user_nome": "JM", "is_admin": False})
                    st.rerun()
                else:
                    try:
                        usrs = db.reference("usuarios_autorizados").get()
                        if usrs:
                            for k_u, v_u in usrs.items():
                                if v_u['login'] == u and v_u['senha'] == p:
                                    st.session_state.update({"logado": True, "user_nome": v_u['nome'], "is_admin": False})
                                    st.rerun()
                    except: pass
                    st.error("Credenciais inválidas.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- 5. PAINEL PRINCIPAL ---
else:
    conectar_firebase()
    
    # SIDEBAR
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center; padding: 16px 0 8px 0;'>
            <div style='font-family:Rajdhani,sans-serif; font-size:20px; font-weight:700; 
                        color:#4a9eff; letter-spacing:2px;'>ASB</div>
            <div style='font-size:11px; color:#4b5563; letter-spacing:1px;'>AUTOMAÇÃO INDUSTRIAL</div>
            <div style='margin-top:10px; font-size:13px; color:#94a3b8;'>
                👤 {st.session_state.get("user_nome","")}</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        opts = ["🏠 Home", "🕹️ Acionamento", "🌡️ Medição", "📊 Relatórios", "🛠️ Diagnóstico"]
        if st.session_state["is_admin"]: opts.append("👥 Gestão de Usuários")
        menu = st.radio("Navegação", opts, label_visibility="collapsed")

        st.divider()
        st.session_state["email_ativo"] = st.toggle("📧 Notificações por Email", value=st.session_state["email_ativo"])

        num_wa = st.text_input("WhatsApp Suporte (com DDD)", placeholder="5511999999999")
        if num_wa:
            txt = urllib.parse.quote(f"Olá, sou {st.session_state['user_nome']}. Reportando ocorrência ASB.")
            st.markdown(f'<a href="https://wa.me/{num_wa}?text={txt}" target="_blank" style="color:#4a9eff; font-size:13px;">💬 Abrir Suporte WhatsApp</a>', unsafe_allow_html=True)

        st.divider()
        if st.button("⏻ Encerrar Sessão"):
            st.session_state["logado"] = False
            st.rerun()

    # ─── HOME ───────────────────────────────────────────────────────────────
    if menu == "🏠 Home":
        st.markdown("<div class='titulo-asb'>ASB Automação Industrial</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitulo-asb'>Supervisório IoT · Monitoramento em Tempo Real</div>", unsafe_allow_html=True)
        st.markdown("<div class='divider-blue'></div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3, gap="medium")
        cards = [
            ("🚀", "Supervisão IoT", "Monitoramento contínuo de ativos industriais via nuvem com baixa latência e alta disponibilidade."),
            ("📈", "Análise de Dados", "Gráficos e telemetria em tempo real para tomada de decisão baseada em dados precisos."),
            ("🛡️", "Segurança", "Controle de acesso multiusuário com auditoria completa de todos os acionamentos."),
        ]
        for col, (icon, title, desc) in zip([c1, c2, c3], cards):
            with col:
                st.markdown(f"""
                <div class='home-card'>
                    <div class='home-icon'>{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>""", unsafe_allow_html=True)

    # ─── ACIONAMENTO ────────────────────────────────────────────────────────
    elif menu == "🕹️ Acionamento":
        st.markdown("<div class='section-header'>Controle de Ativos</div>", unsafe_allow_html=True)

        modo = st.radio("Modo de Operação", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        st.session_state["modo_operacao"] = modo
        st.markdown("<br>", unsafe_allow_html=True)

        try:
            status_real = db.reference("controle/led").get() or "OFF"
        except:
            status_real = "DESCONHECIDO"

        if modo == "MANUAL":
            # Status atual no topo
            cor_map = {"ON": "#22c55e", "REPOUSO": "#fbbf24", "OFF": "#ef4444"}
            label_map = {"ON": "● LIGADO", "REPOUSO": "◐ REPOUSO", "OFF": "○ DESLIGADO"}
            cor = cor_map.get(status_real, "#64748b")
            label = label_map.get(status_real, f"? {status_real}")

            st.markdown(f"""
            <div style='text-align:center; margin-bottom:24px;'>
                <span style='background:rgba(0,0,0,0.3); border:1px solid {cor}; 
                    border-radius:30px; padding:8px 24px; font-family:Rajdhani,sans-serif;
                    font-size:16px; font-weight:700; letter-spacing:2px; color:{cor};'>
                    ESTADO ATUAL: {label}
                </span>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3, gap="large")

            with col1:
                ativo = status_real == "ON"
                st.markdown(f"""
                <div style='background:{"rgba(34,197,94,0.15)" if ativo else "rgba(34,197,94,0.05)"};
                    border:{"2px solid #22c55e" if ativo else "1px solid #22c55e40"};
                    border-radius:14px; padding:28px 16px 16px 16px; text-align:center; margin-bottom:12px;'>
                    <div style='font-size:32px; margin-bottom:8px;'>⚡</div>
                    <div style='font-family:Rajdhani,sans-serif; font-size:20px; font-weight:700; 
                        letter-spacing:2px; color:#22c55e;'>LIGAR</div>
                    <div class='barra-wrap' style='margin-top:14px;'>
                        <div class='{"barra-on" if ativo else "barra-inativa"}'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("▶ LIGAR", key="btn_ligar", use_container_width=True):
                    db.reference("controle/led").set("ON")
                    registrar_evento("LIGOU")
                    st.rerun()

            with col2:
                ativo = status_real == "REPOUSO"
                st.markdown(f"""
                <div style='background:{"rgba(251,191,36,0.15)" if ativo else "rgba(251,191,36,0.05)"};
                    border:{"2px solid #fbbf24" if ativo else "1px solid #fbbf2440"};
                    border-radius:14px; padding:28px 16px 16px 16px; text-align:center; margin-bottom:12px;'>
                    <div style='font-size:32px; margin-bottom:8px;'>🌙</div>
                    <div style='font-family:Rajdhani,sans-serif; font-size:20px; font-weight:700;
                        letter-spacing:2px; color:#fbbf24;'>REPOUSO</div>
                    <div class='barra-wrap' style='margin-top:14px;'>
                        <div class='{"barra-repouso" if ativo else "barra-inativa"}'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("⏸ REPOUSO", key="btn_repouso", use_container_width=True):
                    db.reference("controle/led").set("REPOUSO")
                    registrar_evento("REPOUSO")
                    st.rerun()

            with col3:
                ativo = status_real == "OFF"
                st.markdown(f"""
                <div style='background:{"rgba(239,68,68,0.15)" if ativo else "rgba(239,68,68,0.05)"};
                    border:{"2px solid #ef4444" if ativo else "1px solid #ef444440"};
                    border-radius:14px; padding:28px 16px 16px 16px; text-align:center; margin-bottom:12px;'>
                    <div style='font-size:32px; margin-bottom:8px;'>⭕</div>
                    <div style='font-family:Rajdhani,sans-serif; font-size:20px; font-weight:700;
                        letter-spacing:2px; color:#ef4444;'>DESLIGAR</div>
                    <div class='barra-wrap' style='margin-top:14px;'>
                        <div class='{"barra-off" if ativo else "barra-inativa"}'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("⏹ DESLIGAR", key="btn_desligar", use_container_width=True):
                    db.reference("controle/led").set("OFF")
                    registrar_evento("DESLIGOU")
                    st.rerun()

        else:
            st.markdown("<div class='auto-info'>🤖 <b>MODO AUTOMÁTICO ATIVO</b> — Configure os parâmetros do ciclo abaixo.</div>", unsafe_allow_html=True)
            ca1, ca2 = st.columns(2, gap="medium")
            with ca1:
                t_auto = st.number_input("⏱ Tempo de Ciclo (min)", min_value=1, value=5)
            with ca2:
                v_pisca = st.number_input("💡 Velocidade Pisca (seg)", min_value=1, value=2)

            if not st.session_state["ciclo_ativo"]:
                if st.button("▶️ INICIAR CICLO AUTOMÁTICO", use_container_width=True):
                    st.session_state["ciclo_ativo"] = True
                    st.session_state["inicio_ciclo"] = time.time()
                    registrar_evento("INICIOU MODO AUTOMÁTICO")
                    st.rerun()
            else:
                decorrido = (time.time() - st.session_state.get("inicio_ciclo", time.time())) / 60
                restante = t_auto - decorrido
                pct = min(decorrido / t_auto, 1.0) * 100

                st.markdown(f"""
                <div style='background:#111827; border:1px solid #1e2d4a; border-radius:12px; padding:24px; margin-bottom:16px;'>
                    <div style='font-family:Rajdhani,sans-serif; font-size:28px; font-weight:700; 
                        color:#fbbf24; text-align:center;'>{restante:.1f} min restantes</div>
                    <div class='barra-wrap' style='height:10px; margin-top:14px;'>
                        <div style='height:100%; width:{pct}%; background:linear-gradient(90deg,#4a9eff,#22c55e); border-radius:10px; transition:width 1s;'></div>
                    </div>
                    <div style='text-align:right; font-size:12px; color:#4b5563; margin-top:6px;'>{pct:.0f}% concluído</div>
                </div>
                """, unsafe_allow_html=True)

                if restante > 0:
                    fase = int(time.time() % (v_pisca * 2))
                    try:
                        db.reference("controle/led").set("ON" if fase < v_pisca else "OFF")
                    except: pass

                    if st.button("⏹️ PARAR CICLO", use_container_width=True):
                        st.session_state["ciclo_ativo"] = False
                        try: db.reference("controle/led").set("OFF")
                        except: pass
                        st.rerun()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state["ciclo_ativo"] = False
                    try: db.reference("controle/led").set("OFF")
                    except: pass
                    st.success("✅ Ciclo Finalizado!")
                    st.rerun()

    # ─── MEDIÇÃO ────────────────────────────────────────────────────────────
    elif menu == "🌡️ Medição":
        st.markdown("<div class='section-header'>Telemetria Industrial</div>", unsafe_allow_html=True)

        try:
            t = db.reference("sensor/temperatura").get()
            u = db.reference("sensor/umidade").get()
            ultimo_pulso = db.reference("sensor/ultimo_pulso").get()
        except:
            t, u, ultimo_pulso = None, None, None

        # Verificar se dados são frescos (atualizados nos últimos 60 segundos)
        dado_fresco = checar_dado_fresco(ultimo_pulso, tolerancia_segundos=60)

        # Tratar ausência de dados reais
        t_exibir = t if (t is not None and dado_fresco) else None
        u_exibir = u if (u is not None and dado_fresco) else None

        pct_t = min(max(((t or 0) / 60) * 100, 0), 100) if dado_fresco and t is not None else 0
        pct_u = min(max((u or 0), 0), 100) if dado_fresco and u is not None else 0

        if not dado_fresco:
            st.markdown("""
            <div style='background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.4);
                border-radius:10px; padding:14px 20px; margin-bottom:20px; text-align:center;
                color:#ef4444; font-size:14px; font-weight:600; letter-spacing:1px;'>
                ⚠️ ATENÇÃO: Dispositivo sem comunicação — dados podem estar desatualizados.
                Verifique a conexão do ESP32 na aba Diagnóstico.
            </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        with col1:
            valor_t = f"{t_exibir:.1f}" if t_exibir is not None else "—"
            st.markdown(f"""
            <div class='gauge-card'>
                <div class='gauge-label'>Temperatura</div>
                <div class='gauge-value' style='color:{"#f59e0b" if t_exibir and t_exibir > 35 else "#4a9eff"};'>{valor_t}</div>
                <div class='gauge-unit'>°C</div>
                <div class='gauge-bar-bg'>
                    <div class='gauge-bar-fill gauge-temp-fill' style='width:{pct_t}%;'></div>
                </div>
                <div class='gauge-meta'>Faixa: 0 – 60 °C</div>
                <div class='{"dado-fresco" if dado_fresco and t_exibir is not None else "dado-antigo"}'>
                    {"✔ Dado em tempo real" if dado_fresco and t_exibir is not None else "✘ Sem leitura recente"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            valor_u = f"{u_exibir:.1f}" if u_exibir is not None else "—"
            st.markdown(f"""
            <div class='gauge-card'>
                <div class='gauge-label'>Umidade Relativa</div>
                <div class='gauge-value' style='color:#06b6d4;'>{valor_u}</div>
                <div class='gauge-unit'>%</div>
                <div class='gauge-bar-bg'>
                    <div class='gauge-bar-fill gauge-umid-fill' style='width:{pct_u}%;'></div>
                </div>
                <div class='gauge-meta'>Faixa: 0 – 100 %</div>
                <div class='{"dado-fresco" if dado_fresco and u_exibir is not None else "dado-antigo"}'>
                    {"✔ Dado em tempo real" if dado_fresco and u_exibir is not None else "✘ Sem leitura recente"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Última atualização com timestamp
        if ultimo_pulso:
            segundos_atras = int((time.time() * 1000 - ultimo_pulso) / 1000)
            if segundos_atras < 60:
                tempo_str = f"há {segundos_atras}s"
            elif segundos_atras < 3600:
                tempo_str = f"há {segundos_atras//60}min"
            else:
                tempo_str = f"há {segundos_atras//3600}h"
            st.markdown(f"<div style='text-align:center; color:#4b5563; font-size:12px; letter-spacing:1px;'>Último sinal do dispositivo: <b style='color:#94a3b8;'>{tempo_str}</b></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center; color:#ef4444; font-size:12px;'>Nenhum sinal recebido do dispositivo.</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            if st.button("🔄 ATUALIZAR AGORA", use_container_width=True):
                # Só registra no histórico se o dado for fresco
                if dado_fresco and t is not None and u is not None:
                    try:
                        db.reference("historico_sensores").push({
                            "t": t, "u": u, 
                            "data": obter_hora_brasilia().strftime('%H:%M:%S')
                        })
                    except: pass
                st.rerun()

    # ─── RELATÓRIOS ─────────────────────────────────────────────────────────
    elif menu == "📊 Relatórios":
        st.markdown("<div class='section-header'>Histórico de Atividades</div>", unsafe_allow_html=True)

        if st.session_state["is_admin"]:
            col_lixo = st.columns([1, 2, 1])
            with col_lixo[1]:
                if st.button("🗑️ LIMPAR HISTÓRICO", use_container_width=True):
                    try:
                        db.reference("historico_acoes").delete()
                        db.reference("historico_sensores").delete()
                    except: pass
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        try:
            logs = db.reference("historico_acoes").get()
        except:
            logs = None

        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for k in reversed(list(logs.keys())):
                v = logs[k]
                st.markdown(f"""
                <div class='msg-balao'>
                    <b>{v.get("usuario","?")}</b>: {v.get("acao","?")} 
                    <br><small>🕐 {v.get("data","")}</small>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center; color:#4b5563; padding:40px;'>Nenhum registro encontrado.</div>", unsafe_allow_html=True)

    # ─── DIAGNÓSTICO ────────────────────────────────────────────────────────
    elif menu == "🛠️ Diagnóstico":
        st.markdown("<div class='section-header'>Diagnóstico do Sistema</div>", unsafe_allow_html=True)

        try:
            ultimo_p = db.reference("sensor/ultimo_pulso").get()
            status_led = db.reference("controle/led").get() or "—"
        except:
            ultimo_p = None
            status_led = "Erro"

        online = checar_dado_fresco(ultimo_p, tolerancia_segundos=45)

        # Status principal
        if online:
            st.markdown("<div class='diag-status-ok'>✅ SISTEMA ONLINE — Comunicação Ativa</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='diag-status-off'>⚠️ SISTEMA OFFLINE — Sem Comunicação</div>", unsafe_allow_html=True)

        # Informações de diagnóstico
        agora_ms = time.time() * 1000
        if ultimo_p:
            seg_atras = int((agora_ms - ultimo_p) / 1000)
            ultimo_sinal_str = f"{seg_atras}s atrás" if seg_atras < 60 else f"{seg_atras//60}min atrás"
        else:
            ultimo_sinal_str = "Nunca recebido"

        st.markdown(f"""
        <div class='diag-info-row'>
            <span>📡</span>
            <span class='diag-info-label'>Último Heartbeat:</span>
            <span>{ultimo_sinal_str}</span>
        </div>
        <div class='diag-info-row'>
            <span>🔌</span>
            <span class='diag-info-label'>Estado do Ativo:</span>
            <span>{status_led}</span>
        </div>
        <div class='diag-info-row'>
            <span>🕐</span>
            <span class='diag-info-label'>Hora do Servidor:</span>
            <span>{obter_hora_brasilia().strftime('%d/%m/%Y %H:%M:%S')} (Brasília)</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Rajdhani,sans-serif; font-size:16px; font-weight:600; color:#94a3b8; letter-spacing:2px; margin-bottom:14px;'>AÇÕES DE MANUTENÇÃO</div>", unsafe_allow_html=True)

        # Botões alinhados e proporcionais
        d1, d2 = st.columns(2, gap="medium")
        with d1:
            if st.button("🔁 REBOOT ESP32", use_container_width=True):
                try: db.reference("controle/restart").set(True)
                except: pass
                st.success("Comando de reboot enviado.")
        with d2:
            if st.button("📡 RECONFIGURAR WI-FI", use_container_width=True):
                try: db.reference("controle/restart").set(True)
                except: pass
                st.success("Comando de reconfiguração enviado.")

    # ─── GESTÃO DE USUÁRIOS ─────────────────────────────────────────────────
    elif menu == "👥 Gestão de Usuários" and st.session_state["is_admin"]:
        st.markdown("<div class='section-header'>Gerenciamento de Operadores</div>", unsafe_allow_html=True)

        with st.form("cad_u"):
            cf1, cf2, cf3 = st.columns(3, gap="medium")
            with cf1: n = st.text_input("Nome Completo")
            with cf2: l = st.text_input("Login")
            with cf3: s = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR OPERADOR", use_container_width=True):
                if n and l and s:
                    try:
                        db.reference("usuarios_autorizados").push({
                            "nome": n, "login": l, "senha": s,
                            "data": obter_hora_brasilia().strftime('%d/%m/%Y')
                        })
                        st.success(f"Operador '{n}' cadastrado com sucesso.")
                    except: st.error("Erro ao cadastrar.")
                else:
                    st.warning("Preencha todos os campos.")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Rajdhani,sans-serif; font-size:16px; font-weight:600; color:#94a3b8; letter-spacing:2px; margin-bottom:14px;'>OPERADORES CADASTRADOS</div>", unsafe_allow_html=True)

        try:
            usrs = db.reference("usuarios_autorizados").get()
        except:
            usrs = None

        if usrs:
            for k_u, v_u in usrs.items():
                st.markdown(f"""
                <div class='card-contato'>
                    🟢 <b style='color:#e2e8f0;'>{v_u['nome']}</b><br>
                    <span style='color:#94a3b8;'>Usuário:</span> {v_u['login']} &nbsp;|&nbsp;
                    <span style='color:#94a3b8;'>Senha:</span> {v_u['senha']}<br>
                    <small style='color:#4b5563;'>Cadastrado em: {v_u.get('data','—')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#4b5563; padding:20px;'>Nenhum operador cadastrado.</div>", unsafe_allow_html=True)

# ASB AUTOMAÇÃO INDUSTRIAL - v83.0 Professional
