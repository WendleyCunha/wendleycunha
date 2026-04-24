import streamlit as st
from modulos import database as db
import configuracao as config

def exibir(user_role, is_adm):
    if not is_adm:
        st.error("Acesso negado.")
        return

    st.title("⚙️ Central de Comando")
    
    aba_user, aba_logs = st.tabs(["👥 Gestão de Usuários", "📊 Logs de Esforço"])

    with aba_user:
        st.subheader("Usuários Cadastrados")
        usuarios = db.carregar_usuarios_firebase()
        
        # Formulário para Adicionar/Editar
        with st.expander("➕ Adicionar Novo Usuário"):
            new_u = st.text_input("Username (id)")
            new_n = st.text_input("Nome Completo")
            new_s = st.text_input("Senha", type="password")
            new_r = st.selectbox("Role", ["OPERACIONAL", "ADM"])
            
            # Seleção de módulos baseada no seu MAPA_MODULOS_MESTRE
            opcoes_modulos = list(config.MAPA_MODULOS_MESTRE.values())
            mod_selecionados = st.multiselect("Módulos Permitidos", opcoes_modulos)
            
            if st.button("Cadastrar Usuário"):
                usuarios[new_u] = {
                    "nome": new_n, "senha": new_s, 
                    "role": new_r, "modulos": mod_selecionados
                }
                db.salvar_usuarios_firebase(usuarios)
                st.success("Usuário atualizado!")
                st.rerun()

        st.table(usuarios)

    with aba_logs:
        st.subheader("Relatório de Produtividade")
        esforcos = db.carregar_esforco()
        if esforcos:
            st.dataframe(esforcos)
            if st.button("Limpar Histórico de Logs"):
                db.salvar_esforco([])
                st.rerun()
