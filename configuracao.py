import streamlit as st

# 1. CONFIGURAÇÃO DE PÁGINA
def configurar_pagina():
    st.set_page_config(
        page_title="Hub King Star | Master",
        layout="wide",
        page_icon="👑"
    )

# 2. ESTILO CSS PREMIUM (Unificado e Atualizado)
CSS_PREMIUM = """
    <style>
    /* Estilo Geral da App */
    .stApp { background-color: #f8fafc; }
    
    /* Títulos e Cabeçalhos */
    .gold-title {
        color: #002366;
        text-align: center;
        font-weight: bold;
        letter-spacing: 2px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Perfil do Usuário na Sidebar */
    .profile-pic {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #D4AF37; /* Borda Dourada */
        margin: 0 auto 10px auto;
        display: block;
    }

    /* Card de Usuário na Central de Comando */
    .user-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    
    /* Badges de Role (Alçada) */
    .role-badge {
        background-color: #002366;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
        margin-top: 5px;
    }

    /* Cards da Home (Lembretes e Diário) */
    .reminder-card {
        background: white; 
        padding: 15px; 
        border-radius: 10px;
        border-left: 5px solid #ef4444; 
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .diary-card {
        background: white; 
        padding: 15px; 
        border-radius: 10px;
        border-left: 5px solid #3b82f6; 
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Estilo do Monitor Online */
    .status-online { 
        color: #10b981; 
        font-size: 12px; 
        font-weight: bold; 
    }
    </style>
"""

# 3. MAPA DE MÓDULOS (IDs que batem com as permissões do Firebase)
MAPA_MODULOS_MESTRE = {
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets"
}

# 4. MAPA DE ÍCONES (Para garantir a identidade visual do option_menu)
ICON_MAP = {
    "🏠 Home": "house",
    "🏗️ Manutenção": "tools",
    "🎯 Processos": "diagram-3",
    "📄 RH Docs": "file-earmark-text",
    "📊 Operação": "box-seam",
    "🚗 Minha Spin": "car-front-fill",
    "🚌 Passagens": "bus-front",
    "🎫 Tickets": "ticket-perforated",
    "⚙️ Central de Comando": "shield-lock"
}
