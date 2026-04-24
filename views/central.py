import streamlit as st
import pandas as pd
from datetime import datetime
from modulos import database as db

# Mapa para vincular o nome amigável ao ID do módulo no banco
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
    if 'status' not in df.columns:
        st.warning("Sem dados formatados.")
        return
        
    df_fin = df[df['status'] == 'Finalizado'].copy()
    if df_fin.empty:
        st.warning("Nenhuma atividade finalizada.")
        return

    # Filtros simples
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
    departamentos = db.carregar_departamentos()

    menu = st.segmented_control("Gerenciamento:", 
                               ["🔴 MONITOR", "📊 DASHBOARD", "👥 USUÁRIOS", "🏢 DEPTOS", "⚙️ MOTIVOS"], 
                               default="🔴 MONITOR")

    # --- 1. MONITORAMENTO EM TEMPO REAL ---
    if menu == "🔴 MONITOR":
        st.subheader("Monitoramento em Tempo Real")
        logs = db.carregar_esforco()
        ativos = [a for a in logs if a.get('status') == 'Em andamento']
        
        if ativos:
            for atv in ativos:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                    c1.write(f"👤 **{atv['usuario']}**")
                    c2.write(f"📌 {atv['motivo']}")
                    c3.write(f"⏰ {atv['inicio'][11:16]}") # Mostra apenas HH:MM
                    
                    # KEY ÚNICA: Nome + Início para evitar DuplicateKeyError
                    key_btn = f"stop_{atv['usuario']}_{atv['inicio']}".replace(":", "")
                    if c4.button("🛑", key=key_btn, help="Encerrar atividade"):
                        # Lógica de encerramento forçado pelo ADM
                        agora = datetime.now()
                        inicio = datetime.fromisoformat(atv['inicio'])
                        duracao = (agora - inicio).total_seconds() / 60
                        
                        novos_logs = []
                        for a in logs:
                            if a == atv:
                                a['status'] = 'Finalizado'
                                a['fim'] = agora.isoformat()
                                a['duracao_min'] = round(duracao, 2)
                                a['obs_adm'] = "Encerrado pela Central de Comando"
                            novos_logs.append(a)
                        
                        db.salvar_esforco(novos_logs)
                        st.success(f"Atividade de {atv['usuario']} encerrada!")
                        st.rerun()
        else:
            st.info("Ninguém online no momento.")

    # --- 2. DASHBOARD ---
    elif menu == "📊 DASHBOARD":
        exibir_dashboard_encerradas()

    # --- 3. GESTÃO DE USUÁRIOS ---
    elif menu == "👥 USUÁRIOS":
        st.subheader("Gestão de Acessos")
        
        with st.expander("➕ Cadastrar Novo Usuário"):
            with st.form("form_novo_user"):
                new_id = st.text_input("ID Usuário (Ex: wendley.cunha)")
                new_nome = st.text_input("Nome Completo")
                new_role = st.selectbox("Cargo", ["ADM", "OPERACIONAL"])
                new_depto = st.selectbox("Departamento", departamentos)
                
                st.write("---")
                st.write("Permissões de Módulo:")
                selecionados = []
                cols = st.columns(2)
                for i, (label, mod_id) in enumerate(MAPA_MODULOS.items()):
                    if cols[i % 2].checkbox(label, key=f"check_{mod_id}"):
                        selecionados.append(mod_id)
                
                if st.form_submit_button("Salvar Usuário"):
                    if new_id and new_nome:
                        dados_user = {
                            "nome": new_nome,
                            "role": new_role,
                            "depto": new_depto,
                            "modulos": selecionados,
                            "ativo": True
                        }
                        db.salvar_usuario(new_id, dados_user)
                        st.success("Usuário cadastrado!")
                        st.rerun()
                    else:
                        st.error("Preencha ID e Nome.")

        st.write("---")
        # Tabela simples de usuários
        df_users = pd.DataFrame.from_dict(usuarios, orient='index').reset_index()
        if not df_users.empty:
            st.dataframe(df_users[['index', 'nome', 'role', 'depto']], use_container_width=True)

    # --- 4. DEPARTAMENTOS ---
    elif menu == "🏢 DEPTOS":
        st.subheader("Configuração de Departamentos")
        
        c1, c2 = st.columns([3, 1])
        novo_depto = c1.text_input("Nome do Departamento")
        if c2.button("Adicionar"):
            if novo_depto:
                departamentos.append(novo_depto.upper())
                db.salvar_departamentos(list(set(departamentos))) # list(set()) remove duplicados
                st.rerun()
        
        st.write("Atuais:")
        for d in departamentos:
            st.code(d)

    # --- 5. MOTIVOS ---
    elif menu == "⚙️ MOTIVOS":
        st.subheader("Motivos de Esforço")
        motivos = db.carregar_motivos()
        
        novo_m = st.text_input("Novo Motivo")
        if st.button("Salvar Motivo"):
            if novo_m:
                motivos.append(novo_m.upper())
                db.salvar_motivos(list(set(motivos)))
                st.rerun()
        
        st.write(motivos)
