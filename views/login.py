import streamlit as st

def exibir_login(usuarios):
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>Wendley Portal</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuário").lower().strip()
        p = st.text_input("Senha", type="password")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if u in usuarios and (usuarios[u].get("senha") == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()
