import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modulos import database as db

# Configurações de Módulos (Identico ao seu mapeamento)
MAPA_MODULOS = {
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
}

def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0: return "0min"
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"

def exibir(is_adm):
    if not is_adm:
        st.error("🚫 Acesso restrito aos administradores.")
        return

    st.title("⚙️ Central de Comando")
    
    # Carregamento de dados globais
    usuarios_dict = db.carregar_usuarios_firebase()
    departamentos = db.carregar_departamentos()
    motivos = db.carregar_motivos()
    logs = db.carregar_esforco()

    menu = st.segmented_control(
        "Gerenciamento:", 
        ["🔴 MONITOR", "📊 DASHBOARD", "👥 USUÁRIOS", "🏢 DEPTOS", "⚙️ MOTIVOS"], 
        default="🔴 MONITOR"
    )

    # --- 1. MONITORAMENTO EM TEMPO REAL ---
    if menu == "🔴 MONITOR":
        st.subheader("Monitoramento em Tempo Real")
        ativos = [a for a in logs if a.get('status') == 'Em andamento']
        
        if ativos:
            for atv in ativos:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.markdown(f"👤 **{atv['usuario']}**")
                    c2.markdown(f"📌 {atv['motivo']}\n<small>{atv.get('detalhes', '')}</small>", unsafe_allow_html=True)
                    
                    # Cálculo de tempo decorrido
                    try:
                        inicio_dt = datetime.fromisoformat(atv['inicio']).replace(tzinfo=None)
                        decorrido = (datetime.now() - inicio_dt).seconds // 60
                        c3.metric("Tempo", f"{decorrido} min")
                    except: c3.write("⏰ N/A")
                    
                    key_btn = f"adm_stop_{atv['usuario']}_{atv['inicio']}".replace(":", "")
                    if c4.button("🛑 Encerrar", key=key_btn):
                        agora = datetime.now()
                        duracao = (agora - inicio_dt).total_seconds() / 60
                        
                        for a in logs:
                            if a['usuario'] == atv['usuario'] and a['status'] == 'Em andamento':
                                a['status'] = 'Finalizado'
                                a['fim'] = agora.isoformat()
                                a['duracao_min'] = round(duracao, 2)
                        
                        db.salvar_esforco(logs)
                        st.success(f"Finalizado: {atv['usuario']}")
                        st.rerun()
        else:
            st.info("Ninguém online no momento.")

    # --- 2. DASHBOARD (BI IDENTICO AO ANTIGO) ---
    elif menu == "📊 DASHBOARD":
        st.subheader("📊 Business Intelligence - Esforço")
        df = pd.DataFrame(logs)
        
        if not df.empty and 'status' in df.columns:
            df_fin = df[df['status'] == 'Finalizado'].copy()
            if not df_fin.empty:
                # Filtros
                col_f1, col_f2 = st.columns(2)
                user_f = col_f1.selectbox("Filtrar Usuário", ["Todos"] + sorted(df_fin['usuario'].unique().tolist()))
                mot_f = col_f2.selectbox("Filtrar Motivo", ["Todos"] + sorted(df_fin['motivo'].unique().tolist()))
                
                if user_f != "Todos": df_fin = df_fin[df_fin['usuario'] == user_f]
                if mot_f != "Todos": df_fin = df_fin[df_fin['motivo'] == mot_f]

                # Métricas em destaque
                m1, m2, m3 = st.columns(3)
                m1.metric("Atividades", len(df_fin))
                m2.metric("Tempo Total", formatar_duracao_h_min(df_fin['duracao_min'].sum()))
                m3.metric("Média/Atividade", f"{df_fin['duracao_min'].mean():.1f} min")

                # Gráficos
                g1, g2 = st.columns(2)
                with g1:
                    fig_mot = px.bar(df_fin.groupby('motivo')['duracao_min'].sum().reset_index(), 
                                   x='motivo', y='duracao_min', title="Minutos por Motivo", color='motivo')
                    st.plotly_chart(fig_mot, use_container_width=True)
                with g2:
                    fig_user = px.pie(df_fin, names='usuario', title="Distribuição de Esforço", hole=0.3)
                    st.plotly_chart(fig_user, use_container_width=True)
            else:
                st.warning("Sem dados finalizados para gerar gráficos.")

    # --- 3. GESTÃO DE USUÁRIOS (COM EDIÇÃO E EXCLUSÃO) ---
    elif menu == "👥 USUÁRIOS":
        st.subheader("Gestão de Acessos King Star")
        
        # Formulário de Cadastro
        with st.expander("➕ Cadastrar Novo Colaborador", expanded=False):
            with st.form("novo_user"):
                c1, c2 = st.columns(2)
                u_id = c1.text_input("ID Login (ex: wendley.cunha)")
                u_nome = c2.text_input("Nome Completo")
                u_cargo = c1.selectbox("Cargo", ["ADM", "OPERACIONAL", "GERÊNCIA"])
                u_depto = c2.selectbox("Departamento Principal", departamentos)
                
                st.write("**Permissões de Módulos:**")
                mods_cols = st.columns(3)
                mods_sel = []
                for idx, (label, mid) in enumerate(MAPA_MODULOS.items()):
                    if mods_cols[idx % 3].checkbox(label, key=f"new_mod_{mid}"):
                        mods_sel.append(mid)
                
                if st.form_submit_button("Salvar Colaborador"):
                    if u_id and u_nome:
                        dados = {"nome": u_nome, "role": u_cargo, "depto": u_depto, "modulos": mods_sel, "ativo": True}
                        db.salvar_usuario(u_id, dados)
                        st.success("Usuário criado!")
                        st.rerun()

        # Lista de Usuários com Ações
        st.divider()
        for uid, info in usuarios_dict.items():
            with st.container(border=True):
                col_u1, col_u2, col_u3 = st.columns([3, 2, 1])
                col_u1.write(f"**{info['nome']}** ({uid})")
                col_u2.caption(f"Cargo: {info['role']} | Depto: {info['depto']}")
                
                if col_u3.button("🗑️", key=f"del_{uid}"):
                    st.warning("Funcionalidade de exclusão pendente no banco.")

    # --- 4. DEPARTAMENTOS ---
    elif menu == "🏢 DEPTOS":
        st.subheader("Departamentos")
        novo_d = st.text_input("Nome do Setor")
        if st.button("Adicionar Setor"):
            if novo_d:
                departamentos.append(novo_d.upper())
                db.salvar_departamentos(list(set(departamentos)))
                st.rerun()
        
        st.write("Setores Ativos:")
        cols_d = st.columns(4)
        for i, d in enumerate(sorted(departamentos)):
            cols_d[i % 4].code(d)

    # --- 5. MOTIVOS ---
    elif menu == "⚙️ MOTIVOS":
        st.subheader("Motivos de Atividade")
        novo_m = st.text_input("Descrição do Motivo")
        if st.button("Adicionar Motivo"):
            if novo_m:
                motivos.append(novo_m.upper())
                db.salvar_motivos(list(set(motivos)))
                st.rerun()
        
        st.table(pd.DataFrame({"Motivos Habilitados": motivos}))
