import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import os
from modulos import database as db

# --- CONFIGURAÇÕES GERAIS ---
UPLOAD_DIR = "anexos_pqi"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

MOTIVOS_PADRAO = ["Reunião", "Pedido de Posicionamento", "Elaboração de Documentos", "Anotação Interna (Sem Dash)"]


# --- FUNÇÕES UTILITÁRIAS ---
def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0:
        return "0min"
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"


def exibir(is_adm):
    if not is_adm:
        st.error("🚫 Acesso restrito aos administradores.")
        return

    # --- ESTILO CSS ---
    st.markdown("""
    <style>
        .metric-card {
            background-color: #ffffff; padding: 15px; border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #ececec; text-align: center;
        }
        .metric-value { font-size: 24px; font-weight: 800; color: #002366; }
        .metric-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

    # --- CARREGAMENTO DE DADOS ---
    usuarios_dict = db.carregar_usuarios_firebase()
    departamentos = db.carregar_departamentos()
    motivos = db.carregar_motivos()
    logs_esforco = db.carregar_esforco()

    # --- MENU PRINCIPAL ---
    st.title("⚙️ Central de Comando")

    # ✅ FIX 2: Aba "PROJETOS PQI" removida
    menu = st.segmented_control(
        "Gerenciamento:",
        ["🔴 MONITOR", "📊 DASHBOARD", "👥 USUÁRIOS", "🏢 DEPTOS", "⚙️ MOTIVOS"],
        default="🔴 MONITOR"
    )

    # =========================================================
    # SEÇÃO 1: MONITOR
    # =========================================================
    if menu == "🔴 MONITOR":
        st.subheader("Monitoramento em Tempo Real")
        ativos = [a for a in logs_esforco if a.get('status') == 'Em andamento']

        if ativos:
            for atv in ativos:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.markdown(f"👤 **{atv['usuario']}**")
                    c2.markdown(
                        f"📌 {atv['motivo']}<br><small>{atv.get('detalhes', '')}</small>",
                        unsafe_allow_html=True
                    )

                    inicio_dt = None
                    try:
                        inicio_dt = datetime.fromisoformat(atv['inicio']).replace(tzinfo=None)
                        decorrido = (datetime.now() - inicio_dt).seconds // 60
                        c3.metric("Tempo", f"{decorrido} min")
                    except:
                        c3.write("⏰ N/A")

                    # ✅ FIX 1: Encerra APENAS a atividade específica (usuario + inicio exato + break)
                    key_btn = (
                        f"adm_stop_{atv['usuario']}_{atv['inicio']}"
                        .replace(":", "").replace(".", "").replace("-", "")
                    )
                    if c4.button("🛑 Encerrar", key=key_btn):
                        if inicio_dt:
                            agora = datetime.now()
                            duracao = (agora - inicio_dt).total_seconds() / 60
                            for a in logs_esforco:
                                if (a['usuario'] == atv['usuario']
                                        and a['inicio'] == atv['inicio']
                                        and a['status'] == 'Em andamento'):
                                    a['status'] = 'Finalizado'
                                    a['fim'] = agora.isoformat()
                                    a['duracao_min'] = round(duracao, 2)
                                    break  # ✅ Para após fechar apenas esta atividade
                            db.salvar_esforco(logs_esforco)
                            st.success(f"✅ Atividade de **{atv['usuario']}** encerrada.")
                            st.rerun()
                        else:
                            st.error("Não foi possível calcular o tempo. Início inválido.")
        else:
            st.info("Ninguém online no momento.")

    # =========================================================
    # SEÇÃO 2: DASHBOARD BI
    # =========================================================
    elif menu == "📊 DASHBOARD":
        st.subheader("📊 BI - Esforço Operacional")

        # Validações de segurança antes de qualquer operação
        if not logs_esforco:
            st.warning("Sem dados de esforço registrados.")
            return

        df = pd.DataFrame(logs_esforco)

        if df.empty or 'status' not in df.columns:
            st.warning("Sem dados de esforço registrados.")
            return

        df_fin = df[df['status'] == 'Finalizado'].copy()

        if df_fin.empty:
            st.warning("Nenhuma atividade finalizada encontrada.")
            return

        # ✅ Conversão segura de datas
        df_fin['inicio_dt'] = pd.to_datetime(df_fin['inicio'], errors='coerce')
        df_fin = df_fin.dropna(subset=['inicio_dt'])

        if df_fin.empty:
            st.warning("Nenhuma atividade com data de início válida.")
            return

        df_fin['data_ref'] = df_fin['inicio_dt'].dt.date
        df_fin['duracao_min'] = pd.to_numeric(df_fin['duracao_min'], errors='coerce').fillna(0)

        # ✅ FIX 3: Filtros por USUÁRIO, MOTIVO e DATA
        st.markdown("#### 🔍 Filtros")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        lista_usuarios = ["Todos"] + sorted(df_fin['usuario'].dropna().unique().tolist())
        lista_motivos  = ["Todos"] + sorted(df_fin['motivo'].dropna().unique().tolist())
        data_min_val   = df_fin['data_ref'].min()
        data_max_val   = df_fin['data_ref'].max()

        user_f   = col_f1.selectbox("👤 Usuário", lista_usuarios, key="dash_user")
        motivo_f = col_f2.selectbox("📌 Motivo",  lista_motivos,  key="dash_motivo")
        data_ini = col_f3.date_input("📅 De",  value=data_min_val,
                                     min_value=data_min_val, max_value=data_max_val, key="dash_de")
        data_fim = col_f4.date_input("📅 Até", value=data_max_val,
                                     min_value=data_min_val, max_value=data_max_val, key="dash_ate")

        # Aplica filtros
        df_view = df_fin.copy()
        if user_f != "Todos":
            df_view = df_view[df_view['usuario'] == user_f]
        if motivo_f != "Todos":
            df_view = df_view[df_view['motivo'] == motivo_f]
        df_view = df_view[
            (df_view['data_ref'] >= data_ini) &
            (df_view['data_ref'] <= data_fim)
        ]

        st.divider()

        if df_view.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            return

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-card"><div class="metric-label">Atividades</div><div class="metric-value">{len(df_view)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-label">Tempo Total</div><div class="metric-value">{formatar_duracao_h_min(df_view["duracao_min"].sum())}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-label">Média por Atividade</div><div class="metric-value">{df_view["duracao_min"].mean():.1f} min</div></div>', unsafe_allow_html=True)

        st.write("")

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            df_bar = df_view.groupby('motivo')['duracao_min'].sum().reset_index()
            st.plotly_chart(
                px.bar(df_bar, x='motivo', y='duracao_min',
                       title="⏱️ Tempo por Motivo",
                       labels={'duracao_min': 'Minutos', 'motivo': 'Motivo'}),
                use_container_width=True
            )
        with g2:
            st.plotly_chart(
                px.pie(df_view, names='usuario', title="👥 Distribuição por Usuário"),
                use_container_width=True
            )

        # Evolução diária
        df_linha = df_view.groupby('data_ref')['duracao_min'].sum().reset_index()
        df_linha.columns = ['Data', 'Minutos']
        st.plotly_chart(
            px.line(df_linha, x='Data', y='Minutos',
                    title="📈 Evolução Diária de Esforço", markers=True),
            use_container_width=True
        )

        # Tabela detalhada
        st.markdown("#### 📋 Registros Detalhados")
        colunas_disp = [c for c in ['usuario', 'motivo', 'detalhes', 'inicio', 'duracao_min'] if c in df_view.columns]
        df_exib = df_view[colunas_disp].copy()
        df_exib.columns = ['Usuário', 'Motivo', 'Detalhes', 'Início', 'Duração (min)'][:len(colunas_disp)]
        st.dataframe(df_exib, use_container_width=True, hide_index=True)

    # =========================================================
    # SEÇÃO 3: USUÁRIOS
    # =========================================================
    elif menu == "👥 USUÁRIOS":
        st.subheader("Gestão de Colaboradores")
        with st.expander("➕ Novo Colaborador"):
            with st.form("f_user"):
                u_id    = st.text_input("ID Login")
                u_nome  = st.text_input("Nome")
                u_cargo = st.selectbox("Cargo", ["ADM", "OPERACIONAL", "GERÊNCIA"])
                u_depto = st.selectbox("Departamento", departamentos)
                if st.form_submit_button("Salvar"):
                    db.salvar_usuario(u_id, {
                        "nome": u_nome, "role": u_cargo,
                        "depto": u_depto, "modulos": [], "ativo": True
                    })
                    st.success("Colaborador criado!")
                    st.rerun()

        st.divider()
        for uid, info in usuarios_dict.items():
            with st.container(border=True):
                c_u1, c_u2 = st.columns([4, 1])
                c_u1.write(f"**{info['nome']}** ({uid}) — {info['role']} | {info.get('depto', 'S/D')}")
                if c_u2.button("🗑️", key=f"del_u_{uid}"):
                    st.info("Exclusão lógica: Desative no banco.")

    # =========================================================
    # SEÇÃO 4: DEPARTAMENTOS
    # =========================================================
    elif menu == "🏢 DEPTOS":
        st.subheader("Departamentos")
        novo_d = st.text_input("Novo Setor")
        if st.button("Adicionar"):
            if novo_d.strip():
                departamentos.append(novo_d.upper().strip())
                db.salvar_departamentos(list(set(departamentos)))
                st.success(f"Setor '{novo_d.upper()}' adicionado!")
                st.rerun()
        st.divider()
        st.write(sorted(departamentos))

    # =========================================================
    # SEÇÃO 5: MOTIVOS
    # =========================================================
    elif menu == "⚙️ MOTIVOS":
        st.subheader("Motivos Globais")

        with st.container(border=True):
            novo_m = st.text_input("Nova Categoria de Motivo")
            if st.button("➕ Salvar Motivo", type="primary"):
                if novo_m.strip():
                    motivos_atualizados = list(set(motivos + [novo_m.upper().strip()]))
                    db.salvar_motivos(motivos_atualizados)
                    st.success(f"Motivo '{novo_m.upper()}' adicionado!")
                    st.rerun()

        st.divider()
        st.markdown("#### 📋 Motivos Cadastrados")

        if motivos:
            # ✅ FIX 4: Botão de deletar ao lado de cada motivo
            for idx, motivo in enumerate(sorted(motivos)):
                col_m1, col_m2 = st.columns([5, 1])
                col_m1.markdown(f"▸ **{motivo}**")
                if col_m2.button("🗑️", key=f"del_mot_{idx}_{motivo}"):
                    motivos_atualizados = [m for m in motivos if m != motivo]
                    db.salvar_motivos(motivos_atualizados)
                    st.success(f"Motivo '{motivo}' removido.")
                    st.rerun()
        else:
            st.info("Nenhum motivo cadastrado ainda.")
