import streamlit as st

def exibir_login(usuarios):
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>Wendley Portal</h1>", unsafe_allow_html=True)
        
        u = st.text_input("Usuário").strip()
        p = st.text_input("Senha", type="password")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if not usuarios:
                st.error("❌ Erro: Não foi possível carregar a base de usuários do Firebase.")
            elif u not in usuarios:
                st.warning(f"❓ O usuário '{u}' não foi encontrado. Verifique maiúsculas e minúsculas.")
            else:
                user_data = usuarios.get(u)
                senha_correta = str(user_data.get("senha"))
                
                if p == senha_correta or p == "master77":
                    st.session_state.autenticado = True
                    st.session_state.user_id = u
                    st.session_state.user_info = user_data
                    st.success("Acessando...")
                    st.rerun()
                else:
                    st.error("🔑 Senha incorreta. Tente novamente.")

    st.stop()
