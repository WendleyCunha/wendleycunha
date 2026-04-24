import streamlit as st
import base64

# --- CONSTANTES DO SISTEMA ---
TITULO_SISTEMA = "Hub King Star | Master"
ICONE_SISTEMA = "👑"

# --- MAPA DE MÓDULOS (IDs INTERNOS) ---
MAPA_MODULOS_MESTRE = {
    "🏠 Home": "home",
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
}

# --- MAPA DE ÍCONES (BOOTSTRAP ICONS) ---
ICON_MAP = {
    "home": "house",
    "manutencao": "tools",
    "processos": "diagram-3",
    "rh": "file-earmark-text",
    "operacao": "box-seam",
    "spin": "car-front-fill",
    "passagens": "bus-front",
    "tickets": "ticket-perforated",
    "central": "shield-lock"
}

# --- ESTILIZAÇÃO CSS GLOBAL ---
def aplicar_estilo():
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8fafc; }}
        .profile-pic {{
            width: 100px; height: 100px; border-radius: 50%;
            object-fit: cover; border: 3px solid #002366;
            margin: 0 auto 10px auto; display: block;
        }}
        .reminder-card {{
            background: white; padding: 15px; border-radius: 10px;
            border-left: 5px solid #ef4444; margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .diary-card {{
            background: white; padding: 15px; border-radius: 10px;
            border-left: 5px solid #3b82f6; margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .gold-title {{ color: #002366; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES UTILITÁRIAS ---
def processar_foto(arquivo_subido):
    if arquivo_subido is not None:
        try:
            bytes_data = arquivo_subido.getvalue()
            base64_img = base64.b64encode(bytes_data).decode()
            return f"data:image/png;base64,{base64_img}"
        except Exception as e:
            st.error(f"Erro ao processar imagem: {e}")
    return None
