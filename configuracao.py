"""
configuracao.py — Configurações globais do sistema King Star
"""
import streamlit as st

# ── Mapa de módulos disponíveis no sistema interno ────────────────────────────
MAPA_MODULOS_MESTRE = {
    "🛏️ Portal Cliente":  "portal_cliente",
    "📋 Processos (PQI)": "processos",
    "📓 Diário de Trocas": "diario_trocas",
    "📄 RH Docs / Cartas": "rh_docs",
}


def configurar_pagina():
    st.set_page_config(
        page_title="King Star — Sistema",
        page_icon="🛏️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def desenhar_sidebar(user_info: dict, menu_options: list) -> str:
    """
    Desenha a sidebar com logo, nome do usuário e menu de navegação.
    Retorna a opção selecionada.
    """
    with st.sidebar:
        # Logo
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px;">
                <div style="background:#C9A227;border-radius:8px;width:38px;height:38px;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:15px;color:#111;flex-shrink:0;">KS</div>
                <div>
                    <div style="font-size:15px;font-weight:700;color:#F0EDE6;">King Star</div>
                    <div style="font-size:10px;color:#aaa;letter-spacing:.05em;">ISO 9001</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Usuário logado
        nome = user_info.get("nome", "Usuário")
        role = user_info.get("role", "")
        initials = "".join(p[0] for p in nome.split()[:2]).upper()
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.06);border-radius:10px;
                        padding:10px 12px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                <div style="background:#C9A227;border-radius:50%;width:34px;height:34px;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:13px;color:#111;flex-shrink:0;">{initials}</div>
                <div>
                    <div style="font-size:13px;font-weight:600;color:#F0EDE6;">{nome}</div>
                    <div style="font-size:11px;color:#aaa;">{role}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        escolha = st.radio(
            "Menu",
            menu_options,
            label_visibility="collapsed",
        )

        # Botão de logout
        st.markdown("<div style='margin-top:auto;padding-top:20px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True, type="secondary"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return escolha
