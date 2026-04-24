import streamlit as st
from modulos import database as db
import configuracao as config

def exibir(usuarios_firebase, departamentos_lista):
    """
    Exibe a Central de Comando. 
    Recebe os dados carregados no main.py para evitar múltiplas consultas ao banco.
    """
    
    # Validação de segurança: Verifica se o usuário atual é ADM
    user_id_atual = st.session_state.get("user_id")
    user_info_atual = usuarios_firebase.get(user_id_atual, {})
    
    if user_info_atual.get("role") != "ADM":
        st.error("Acesso restrito ao Administrador.")
        st.stop()

    # Título estilizado usando a cor oficial do configuracao.py
    st.markdown(f"""
        <h1 style='color:{config.DOURADO_KING}; text-align:left;'>
            ⚙️ Central de Comando
        </h1>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    aba_usuarios, aba_config = st.tabs(["👥 Gestão de Usuários", "🛠️ Parâmetros do Sistema"])

    # --- ABA 1: GESTÃO DE USUÁRIOS ---
    with aba_usuarios:
        with st.expander("📝 Cadastrar ou Editar Usuário"):
            col1, col2 = st.columns(2)
            with col1:
                id_login = st.text_input("Login (ID único)", placeholder="ex: wendley.cunha").lower().strip()
                nome_exibicao = st.text_input("Nome Completo")
            with col2:
                senha_acesso = st.text_input("Senha", type="password")
                nivel_role = st.selectbox("Nível de Acesso", ["OPERACIONAL", "ADM"])
            
            # Busca os módulos disponíveis dinamicamente do configuracao.py
            modulos_disponiveis = list(config.MAPA_MODULOS_MESTRE.values())
            permissoes_selecionadas = st.multiselect("Módulos Permitidos", modulos_disponiveis)
            
            if st.button("SALVAR ALTERAÇÕES", use_container_width=True):
                if id_login and nome_exibicao and senha_acesso:
                    novos_dados = {
                        "nome": nome_exibicao,
                        "senha": senha_acesso,
                        "role": nivel_role,
                        "modulos": permissoes_selecionadas,
                        "foto": "" # Placeholder para manter a estrutura
                    }
                    db.salvar_usuario(id_login, novos_dados)
                    st.success(f"Dados de '{id_login}' atualizados com sucesso!")
                    st.rerun()
                else:
                    st.warning("Atenção: Login, Nome e Senha são campos obrigatórios.")

        st.subheader("Usuários Cadastrados")
        # Exibe os dados que vieram do parâmetro da função
        st.dataframe(usuarios_firebase, use_container_width=True)

    # --- ABA 2: CONFIGURAÇÕES ---
    with aba_config:
        st.subheader("Listas de Departamentos")
        st.info("Estas opções aparecem nos formulários de todo o sistema.")
        
        # Usa a lista de departamentos que veio do parâmetro da função
        texto_deps = "\n".join(departamentos_lista)
        novos_deps = st.text_area("Um departamento por linha:", value=texto_deps, height=200)
        
        if st.button("ATUALIZAR LISTA DE DEPARTAMENTOS"):
            lista_final = [d.strip() for d in novos_deps.split("\n") if d.strip()]
            db.salvar_departamentos(lista_final)
            st.success("Lista de departamentos atualizada no banco de dados!")
