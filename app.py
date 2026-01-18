import streamlit as st
import requests
import time

# --- CONFIGURAÇÃO DA PÁGINA (ESTILO INDUSTRIAL) ---
st.set_page_config(page_title="ASB AUTOMAÇÃO INDUSTRIAL", layout="wide")

URL_FB = "https://projeto-asb-comercial-default-rtdb.firebaseio.com/"

# --- DESIGN PERSONALIZADO ASB ---
st.markdown("""
    <style>
    /* Fundo e Texto Geral */
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* Botões Industriais */
    .stButton>button { 
        width: 100%; 
        border-radius: 5px; 
        height: 3.5em; 
        font-weight: bold; 
        text-transform: uppercase;
        border: 1px solid #4a4a4a;
        background-color: #1f2937;
        color: white;
    }
    .stButton>button:hover { border-color: #00ff00; color: #00ff00; }

    /* Estilo das Métricas */
    [data-testid="stMetricValue"] { color: #00ff00; font-family: 'Courier New', monospace; font-size: 50px !important; }
    [data-testid="stMetricLabel"] { color: #9ca3af; text-transform: uppercase; letter-spacing: 2px; }

    /* Títulos */
    h1, h2, h3 { color: #f3f4f6; font-family: 'Segoe UI', sans-serif; border-bottom: 2px solid #374151; padding-bottom: 10px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #111827; border-right: 2px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def tela_login():
    st.markdown("<h1 style='text-align:center;'>ASB AUTOMAÇÃO INDUSTRIAL</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>Acesso Restrito ao Sistema</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("Login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("ACESSAR SISTEMA")
            
            if entrar:
                # Altere aqui para o seu usuário e senha de preferência
                if usuario == "admin" and senha == "asb123":
                    st.session_state['autenticado'] = True
                    st.success("Acesso Autorizado!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credenciais Inválidas")

# --- FUNÇÕES FIREBASE ---
def fb_get(path, default=None):
    try:
        r = requests.get(f"{URL_FB}{path}.json", timeout=2)
        return r.json() if r.ok else default
    except:
        return default

def fb_set(path, value):
    try:
        requests.put(f"{URL_FB}{path}.json", json=value, timeout=2)
    except:
        pass

# --- CONTEÚDO PRINCIPAL ---
if not st.session_state['autenticado']:
    tela_login()
else:
    # Cabeçalho de Navegação
    st.sidebar.markdown("<h2 style='text-align:center; color:#00ff00;'>ASB V2</h2>", unsafe_allow_html=True)
    st.sidebar.divider()
    aba = st.sidebar.radio("NAVEGAR POR:", ["🕹️ PAINEL DE COMANDO", "📈 MONITORAMENTO TÉRMICO"])
    
    if st.sidebar.button("SAIR DO SISTEMA"):
        st.session_state['autenticado'] = False
        st.rerun()

    # --- FRAGMENTOS DE ATUALIZAÇÃO ---
    @st.fragment(run_every=3)
    def fragmento_status():
        led = fb_get("controle/led", "OFF")
        led_str = str(led).upper()
        cor_led = "🟢" if "ON" in led_str else "🔴"
        st.markdown(f"""
            <div style='text-align: center; border: 2px solid #374151; padding: 30px; border-radius: 10px; background-color: #1f2937;'>
                <p style='color: #9ca3af; margin-bottom: 5px; text-transform: uppercase;'>Status do Equipamento</p>
                <h1 style='margin:0; font-family: monospace;'>{cor_led} {led_str}</h1>
            </div>
        """, unsafe_allow_html=True)

    @st.fragment(run_every=2)
    def fragmento_temperatura():
        temp = fb_get("sensor/temperatura")
        status = fb_get("sensor/status", "ERRO")
        if status == "OK" and isinstance(temp, (int, float)):
            st.metric("LEITURA ATUAL DHT11", f"{temp:.2f} °C")
        else:
            st.error("⚠️ HARDWARE OFFLINE")

    # --- TELAS ---
    if aba == "🕹️ PAINEL DE COMANDO":
        st.title("🕹️ CENTRO DE COMANDO")
        st.write("Gerenciamento de Atuadores em Tempo Real")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Controle Manual")
            if st.button("LIGAR MÁQUINA"):
                fb_set("controle/led", "ON")
                st.toast("Comando ON enviado")
            if st.button("DESLIGAR MÁQUINA"):
                fb_set("controle/led", "OFF")
                st.toast("Comando OFF enviado")
        with c2:
            fragmento_status()

    elif aba == "📈 MONITORAMENTO TÉRMICO":
        st.title("📈 TELEMETRIA DE TEMPERATURA")
        st.write("Dados transmitidos via Protocolo Firebase")
        
        ca, cb = st.columns([1, 2])
        with ca:
            fragmento_temperatura()
        with cb:
            st.info("Painel de Telemetria Industrial - ASB Automação. Verifique a estabilidade do coletor local se a métrica não variar.")
