import streamlit as st
from modulos import database as db
import configuracao as config

def exibir(user_role, is_adm):
    if not is_adm:
        st.error("Acesso restrito ao Administrador.")
        return

    st.title("⚙️ Central de Comando")
    
    aba_usuarios, aba_config = st.tabs(["👥 Usuários", "🛠️ Configurações do Sistema"])

    with aba_usuarios:
        usuarios = db.carregar_usuarios_firebase()
        
        # Formulário para criar/editar
        with st.expander("📝 Criar / Editar Usuário"):
            login = st.text_input("Login (ex: wendley)")
            nome = st.text_input("Nome de Exibição")
            senha = st.text_input("Senha", type="password")
            role = st.selectbox("Nível", ["OPERACIONAL", "ADM"])
            
            # Aqui pegamos os IDs internos do configuracao.py
            ids_modulos = list(config.MAPA_MODULOS_MESTRE.values())
            acessos = st.multiselect("Módulos Permitidos", ids_modulos)
            
            if st.button("Salvar Usuário"):
                dados = {
                    "nome": nome,
                    "senha": senha,
                    "role": role,
                    "modulos": acessos
                }
                db.salvar_usuario(login, dados)
                st.success(f"Usuário {login} atualizado!")
                st.rerun()

        # Tabela de visualização
        st.write("### Usuários Ativos")
        st.table(usuarios)

    with aba_config:
        st.subheader("Gestão de Listas")
        # Exemplo: Editar Departamentos
        deps = db.carregar_departamentos()
        novos_deps = st.text_area("Departamentos (um por linha)", value="\n".join(deps))
        if st.button("Atualizar Departamentos"):
            lista_final = [d.strip() for d in novos_deps.split("\n") if d.strip()]
            db.salvar_departamentos(lista_final)
            st.toast("Departamentos atualizados!")
