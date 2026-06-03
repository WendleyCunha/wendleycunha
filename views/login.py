"""
views/login.py — Tela de login para usuários internos do sistema.
"""
import streamlit as st

def exibir_login(usuarios: dict):
    """Exibe formulário de login e autentica o usuário no session_state."""

    st.markdown(
        """
        <style>
        .login-wrap {
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; min-height:80vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:28px;">
                <div style="background:#C9A227;border-radius:14px;width:60px;height:60px;
                            display:inline-flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:22px;color:#111;margin-bottom:12px;">KS</div>
                <h2 style="font-size:22px;font-weight:700;color:#1A1A1A;margin:0;">King Star — Sistema</h2>
                <p style="color:#888;font-size:13px;margin-top:4px;">Acesso restrito a colaboradores</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_login_interno", clear_on_submit=False):
            login_id = st.text_input("Login", placeholder="Seu ID de acesso")
            senha    = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar   = st.form_submit_button("Entrar", use_container_width=True, type="primary")
       
        if entrar:
            # Cria um dicionário auxiliar onde as chaves estão em minúsculo
            # Isso permite encontrar o usuário independente de como ele foi digitado
            usuarios_case_insensitive = {k.lower(): v for k, v in usuarios.items()}
            
            login_input = login_id.strip().lower()
            user = usuarios_case_insensitive.get(login_input)
            
            if user and user.get("ativo", True) and str(user.get("senha", "")) == senha.strip():
                st.session_state.autenticado = True
                st.session_state.user_id     = login_id.strip() # Mantém a grafia original do login
                st.session_state.user_info   = user
                st.rerun()
            else:
                st.error("Login ou senha incorretos.")
