# views/central.py
import streamlit as st
from modulos import database as db

def exibir():
    st.title("⚙️ Central de Comando")
    st.subheader("Gestão de Usuários e Acessos")
    
    st.info("Espaço destinado ao administrador para gerenciar permissões.")
    
    # Exemplo de visualização simples
    usuarios = db.carregar_usuarios_firebase()
    if usuarios:
        st.write("Usuários cadastrados:", len(usuarios))
        st.dataframe(usuarios)
