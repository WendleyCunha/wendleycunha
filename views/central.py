import streamlit as st
import pandas as pd
from datetime import datetime
from modulos import database as db

# Importamos o mapa aqui para o formulário de cadastro
MAPA_MODULOS = {
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
}

def exibir_dashboard_encerradas():
    st.subheader("📊 Business Intelligence - Esforço")
    logs = db.carregar_esforco()
    if not logs:
        st.info("Nenhum registro encontrado.")
        return

    df = pd.DataFrame(logs)
    df_fin = df[df['status'] == 'Finalizado'].copy()
    if df_fin.empty:
        st.warning("Nenhuma atividade finalizada.")
        return

    # Filtros simples (Ajuste conforme sua necessidade de BI)
    user_f = st.selectbox("Filtrar Usuário", ["Todos"] + sorted(df_fin['usuario'].unique().tolist()))
    if user_f != "Todos":
        df_fin = df_fin[df_fin['usuario'] == user_f]
    
    st.dataframe(df_fin, use_container_width=True)

def exibir(is_adm):
    if not is_adm:
        st.error("Acesso negado.")
        return

    st.title("⚙️ Central de Comando")
    
    # Carregamento de dados
    usuarios = db.carregar_usuarios_firebase()
    # Usamos get() para evitar erro caso a função não exista no db
    try:
        departamentos = db.carregar_departamentos()
    except:
        departamentos = ["GERAL"] 

    menu = st.segmented_control("Gerenciamento:", 
                               ["🔴 MONITOR", "📊 DASHBOARD", "👥 USUÁRIOS", "🏢 DEPTOS", "⚙️ MOTIVOS"], 
                               default="🔴 MONITOR")

    if menu == "🔴 MONITOR":
        st.subheader("Monitoramento em Tempo Real")
        logs = db.carregar_esforco()
        ativos = [a for a in logs if a['status'] == 'Em andamento']
        if ativos:
            for atv in ativos:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"👤 **{atv['usuario']}**")
                    c2.write(f"📌 {atv['motivo']}")
                    if c3.button("Encerrar", key=f"stop_{atv['usuario']}"):
                        # Lógica de encerramento ADM aqui
                        pass 
        else:
            st.info("Ninguém online.")

    elif menu == "📊 DASHBOARD":
        exibir_dashboard_encerradas()

    elif menu == "👥 USUÁRIOS":
        st.subheader("Gestão de Acessos")
        # Aqui você coloca a lógica de st.expander de cadastro e a lista de usuários
        st.write("Lista de usuários cadastrados:")
        st.json(list(usuarios.keys())) # Exemplo simplificado

    elif menu == "🏢 DEPTOS":
        st.subheader("Departamentos")
        novo_depto = st.text_input("Novo Departamento")
        if st.button("Salvar Depto"):
            departamentos.append(novo_depto.upper())
            db.salvar_departamentos(departamentos)
            st.rerun()
