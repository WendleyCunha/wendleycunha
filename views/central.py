import streamlit as st
import database as db
import configuracao as config

def exibir(is_adm): # Ajustado para bater com a chamada do main.py
    if not is_adm:
        st.error("Acesso restrito ao Administrador.")
        return

    st.markdown("<h1 class='gold-title'>⚙️ Central de Comando</h1>", unsafe_allow_html=True)
    
    aba_usuarios, aba_config = st.tabs(["👥 Gestão de Usuários", "🛠️ Configurações"])

    with aba_usuarios:
        usuarios = db.carregar_usuarios_firebase()
        
        with st.expander("📝 Criar / Editar Usuário"):
            col1, col2 = st.columns(2)
            with col1:
                login = st.text_input("Login (id único)", placeholder="ex: wendley.cunha").lower().strip()
                nome = st.text_input("Nome de Exibição")
            with col2:
                senha = st.text_input("Senha", type="password")
                role = st.selectbox("Nível de Acesso", ["OPERACIONAL", "ADM"])
            
            # Puxa os módulos automáticos do seu arquivo de configuração
            ids_modulos = list(config.MAPA_MODULOS_MESTRE.values())
            acessos = st.multiselect("Módulos Permitidos", ids_modulos)
            
            if st.button("Confirmar Cadastro / Alteração", use_container_width=True):
                if login and nome and senha:
                    dados = {
                        "nome": nome,
                        "senha": senha,
                        "role": role,
                        "modulos": acessos,
                        "foto": "" # Placeholder para foto
                    }
                    db.salvar_usuario(login, dados)
                    st.success(f"Usuário {login} processado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha Login, Nome e Senha.")

        st.write("### Painel de Acessos")
        # Mostra de forma mais limpa que st.table
        st.dataframe(usuarios, use_container_width=True)

    with aba_config:
        st.subheader("Parâmetros do Sistema")
        deps = db.carregar_departamentos()
        novos_deps = st.text_area("Departamentos da King Star (um por linha)", value="\n".join(deps))
        
        if st.button("Atualizar Listas Internas"):
            lista_final = [d.strip() for d in novos_deps.split("\n") if d.strip()]
            db.salvar_departamentos(lista_final)
            st.success("Listas atualizadas!")
