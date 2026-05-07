import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import os
from modulos import database as db

# --- CONFIGURAÇÕES GERAIS ---
UPLOAD_DIR = "anexos_pqi"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

MOTIVOS_PADRAO = [
    "Reunião", "Pedido de Posicionamento",
    "Elaboração de Documentos", "Anotação Interna (Sem Dash)"
]


# --- FUNÇÕES UTILITÁRIAS ---
def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0:
        return "0min"
    horas = int(minutos // 60)
    mins  = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"


def _parse_datas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte a coluna 'inicio' para datetime de forma robusta,
    tratando tanto strings com timezone quanto sem.
    Retorna o df com coluna 'inicio_dt' (tz-naive) e 'data_ref' (date).
    """
    raw = pd.to_datetime(df['inicio'], errors='coerce', utc=True)
    df['inicio_dt'] = raw.dt.tz_localize(None) if raw.dt.tz is None else raw.dt.tz_convert(None)
    df['data_ref']  = df['inicio_dt'].dt.normalize()          # meia-noite, para comparação fácil
    df['duracao_min'] = pd.to_numeric(df.get('duracao_min', 0), errors='coerce').fillna(0)
    return df


def exibir(is_adm):
    if not is_adm:
        st.error("🚫 Acesso restrito aos administradores.")
        return

    # ── ESTILO GLOBAL ──────────────────────────────────────────────────────────
    st.markdown("""
    <style>
        /* Cards de métricas */
        .kpi-card {
            background: linear-gradient(135deg,#f8faff 0%,#eef2ff 100%);
            border: 1px solid #c7d2fe;
            border-radius: 14px;
            padding: 20px 16px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(99,102,241,.08);
        }
        .kpi-value { font-size: 28px; font-weight: 900; color: #002366; margin: 4px 0; }
        .kpi-label { font-size: 11px; color: #6366f1; font-weight: 700;
                     text-transform: uppercase; letter-spacing: .06em; }
        .kpi-sub   { font-size: 12px; color: #64748b; margin-top: 2px; }

        /* Filtros highlight */
        .filter-bar {
            background: #f1f5f9;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 10px;
            border: 1px solid #e2e8f0;
        }

        /* Motivos list */
        .motivo-row {
            display:flex; align-items:center; justify-content:space-between;
            padding: 8px 12px; border-radius: 8px; margin: 4px 0;
            background:#f8faff; border:1px solid #e0e7ff;
        }
        .motivo-nome { font-weight:600; color:#1e293b; font-size:14px; }

        /* Monitor card */
        .monitor-user { font-size:15px; font-weight:700; color:#002366; }
        .monitor-motivo { font-size:13px; color:#475569; }
    </style>
    """, unsafe_allow_html=True)

    # ── CARREGAMENTO ───────────────────────────────────────────────────────────
    usuarios_dict = db.carregar_usuarios_firebase()
    departamentos = db.carregar_departamentos()
    motivos       = db.carregar_motivos()
    logs_esforco  = db.carregar_esforco()

    # ── MENU ───────────────────────────────────────────────────────────────────
    st.title("⚙️ Central de Comando")

    # ✅ FIX 2: PROJETOS PQI removido
    menu = st.segmented_control(
        "Gerenciamento:",
        ["🔴 MONITOR", "📊 DASHBOARD", "👥 USUÁRIOS", "🏢 DEPTOS", "⚙️ MOTIVOS"],
        default="🔴 MONITOR"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # MONITOR
    # ══════════════════════════════════════════════════════════════════════════
    if menu == "🔴 MONITOR":
        st.subheader("Monitoramento em Tempo Real")
        ativos = [a for a in logs_esforco if a.get('status') == 'Em andamento']

        if ativos:
            for atv in ativos:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2.5, 1, 1])
                    c1.markdown(f"<span class='monitor-user'>👤 {atv['usuario']}</span>", unsafe_allow_html=True)
                    c2.markdown(
                        f"<span class='monitor-motivo'>📌 {atv['motivo']}<br>"
                        f"<small>{atv.get('detalhes','')}</small></span>",
                        unsafe_allow_html=True
                    )

                    inicio_dt = None
                    try:
                        inicio_dt = datetime.fromisoformat(atv['inicio']).replace(tzinfo=None)
                        decorrido = (datetime.now() - inicio_dt).seconds // 60
                        c3.metric("⏱ Tempo", f"{decorrido} min")
                    except:
                        c3.write("⏰ N/A")

                    # ✅ FIX 1: encerra apenas a atividade específica (inicio exato + break)
                    key_btn = (
                        f"stop_{atv['usuario']}_{atv['inicio']}"
                        .replace(":", "").replace(".", "").replace("-", "").replace("+", "")
                    )
                    if c4.button("🛑 Encerrar", key=key_btn, type="primary"):
                        if inicio_dt:
                            agora    = datetime.now()
                            duracao  = (agora - inicio_dt).total_seconds() / 60
                            for a in logs_esforco:
                                if (a['usuario'] == atv['usuario']
                                        and a['inicio']  == atv['inicio']
                                        and a['status']  == 'Em andamento'):
                                    a['status']      = 'Finalizado'
                                    a['fim']         = agora.isoformat()
                                    a['duracao_min'] = round(duracao, 2)
                                    break          # ← só esta atividade
                            db.salvar_esforco(logs_esforco)
                            st.success(f"✅ Atividade de **{atv['usuario']}** encerrada.")
                            st.rerun()
                        else:
                            st.error("Início inválido — não foi possível calcular o tempo.")
        else:
            st.info("🟢 Ninguém em atividade no momento.")

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "📊 DASHBOARD":
        st.subheader("📊 BI — Esforço Operacional")

        # ── Validação básica ──────────────────────────────────────────────────
        if not logs_esforco:
            st.info("Nenhum registro de esforço encontrado.")
            return

        df_raw = pd.DataFrame(logs_esforco)
        if df_raw.empty or 'status' not in df_raw.columns:
            st.info("Nenhum registro de esforço encontrado.")
            return

        df_fin = df_raw[df_raw['status'] == 'Finalizado'].copy()
        if df_fin.empty:
            st.info("Nenhuma atividade finalizada ainda.")
            return

        # ── Conversão de datas robusta (suporta tz e sem tz) ─────────────────
        # ✅ CORREÇÃO PRINCIPAL: trata strings com e sem timezone do Firebase
        try:
            raw_dt = pd.to_datetime(df_fin['inicio'], errors='coerce', utc=True)
            df_fin['inicio_dt'] = raw_dt.dt.tz_convert(None)   # sempre tz-naive
        except Exception:
            df_fin['inicio_dt'] = pd.to_datetime(df_fin['inicio'], errors='coerce')

        df_fin = df_fin.dropna(subset=['inicio_dt'])
        if df_fin.empty:
            st.warning("Não foi possível interpretar as datas dos registros.")
            return

        df_fin['data_ref']    = df_fin['inicio_dt'].dt.normalize()
        df_fin['duracao_min'] = pd.to_numeric(df_fin.get('duracao_min', 0), errors='coerce').fillna(0)

        hoje       = pd.Timestamp(date.today())
        data_min   = df_fin['data_ref'].min().date()
        data_max   = df_fin['data_ref'].max().date()

        # ── FILTROS ───────────────────────────────────────────────────────────
        st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
        st.markdown("##### 🔍 Filtros")

        col_p, col_u, col_m = st.columns(3)

        # Filtro de período
        periodo = col_p.selectbox(
            "📅 Período",
            ["Hoje", "Últimos 7 dias", "Este mês", "Personalizado"],
            key="dash_periodo"
        )

        lista_usuarios = ["Todos"] + sorted(df_fin['usuario'].dropna().unique().tolist())
        lista_motivos  = ["Todos"] + sorted(df_fin['motivo'].dropna().unique().tolist())

        user_f   = col_u.selectbox("👤 Operador", lista_usuarios, key="dash_user")
        motivo_f = col_m.selectbox("📌 Motivo",   lista_motivos,  key="dash_motivo")

        # Datas conforme período escolhido
        if periodo == "Hoje":
            de  = date.today()
            ate = date.today()
        elif periodo == "Últimos 7 dias":
            de  = date.today() - timedelta(days=6)
            ate = date.today()
        elif periodo == "Este mês":
            de  = date.today().replace(day=1)
            ate = date.today()
        else:  # Personalizado
            col_de, col_ate = st.columns(2)
            de  = col_de.date_input("De",  value=data_min, min_value=data_min, max_value=data_max, key="dash_de")
            ate = col_ate.date_input("Até", value=data_max, min_value=data_min, max_value=data_max, key="dash_ate")

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Aplica filtros ────────────────────────────────────────────────────
        ts_de  = pd.Timestamp(de)
        ts_ate = pd.Timestamp(ate) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        df_view = df_fin.copy()
        df_view = df_view[(df_view['data_ref'] >= ts_de) & (df_view['data_ref'] <= ts_ate)]
        if user_f   != "Todos": df_view = df_view[df_view['usuario'] == user_f]
        if motivo_f != "Todos": df_view = df_view[df_view['motivo']  == motivo_f]

        st.divider()

        if df_view.empty:
            st.warning("Nenhum dado para os filtros selecionados.")
            return

        # ── KPIs ─────────────────────────────────────────────────────────────
        total_ativ  = len(df_view)
        total_tempo = df_view['duracao_min'].sum()
        media_tempo = df_view['duracao_min'].mean()
        n_operadores = df_view['usuario'].nunique()

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Atividades</div>
                <div class="kpi-value">{total_ativ}</div>
            </div>""", unsafe_allow_html=True)
        k2.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Tempo Total</div>
                <div class="kpi-value">{formatar_duracao_h_min(total_tempo)}</div>
            </div>""", unsafe_allow_html=True)
        k3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Média p/ Atividade</div>
                <div class="kpi-value">{media_tempo:.0f} min</div>
            </div>""", unsafe_allow_html=True)
        k4.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Operadores</div>
                <div class="kpi-value">{n_operadores}</div>
            </div>""", unsafe_allow_html=True)

        st.write("")

        # ── Gráficos — linha 1 ────────────────────────────────────────────────
        g1, g2 = st.columns(2)

        with g1:
            df_bar = (
                df_view.groupby('motivo')['duracao_min']
                .sum().reset_index()
                .sort_values('duracao_min', ascending=True)
            )
            fig_bar = px.bar(
                df_bar, x='duracao_min', y='motivo', orientation='h',
                title="⏱️ Tempo por Motivo",
                labels={'duracao_min': 'Minutos', 'motivo': ''},
                color='duracao_min',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(
                showlegend=False, coloraxis_showscale=False,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=40, b=10), height=300
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with g2:
            fig_pie = px.pie(
                df_view, names='usuario',
                title="👥 Distribuição por Operador",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=40, b=10), height=300,
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        # ── Gráfico — evolução diária ─────────────────────────────────────────
        df_linha = (
            df_view.groupby(df_view['inicio_dt'].dt.date)['duracao_min']
            .sum().reset_index()
        )
        df_linha.columns = ['Data', 'Minutos']

        fig_linha = px.area(
            df_linha, x='Data', y='Minutos',
            title="📈 Evolução Diária de Esforço",
            markers=True,
            color_discrete_sequence=['#6366f1']
        )
        fig_linha.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=40, b=10), height=280
        )
        fig_linha.update_traces(fill='tozeroy', fillcolor='rgba(99,102,241,0.12)')
        st.plotly_chart(fig_linha, use_container_width=True)

        # ── Tabela detalhada ─────────────────────────────────────────────────
        with st.expander("📋 Ver registros detalhados"):
            cols_disp = [c for c in ['usuario', 'motivo', 'detalhes', 'inicio', 'duracao_min'] if c in df_view.columns]
            df_exib = df_view[cols_disp].copy()
            df_exib.columns = ['Usuário', 'Motivo', 'Detalhes', 'Início', 'Duração (min)'][:len(cols_disp)]
            df_exib['Duração (min)'] = df_exib['Duração (min)'].apply(lambda x: f"{x:.1f}")
            st.dataframe(df_exib, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    # USUÁRIOS
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "👥 USUÁRIOS":
        st.subheader("Gestão de Colaboradores")
        with st.expander("➕ Novo Colaborador"):
            with st.form("f_user"):
                u_id    = st.text_input("ID Login")
                u_nome  = st.text_input("Nome Completo")
                u_cargo = st.selectbox("Cargo", ["ADM", "OPERACIONAL", "GERÊNCIA"])
                u_depto = st.selectbox("Departamento", departamentos)
                if st.form_submit_button("💾 Salvar"):
                    db.salvar_usuario(u_id, {
                        "nome": u_nome, "role": u_cargo,
                        "depto": u_depto, "modulos": [], "ativo": True
                    })
                    st.success("Colaborador criado!")
                    st.rerun()

        st.divider()
        for uid, info in usuarios_dict.items():
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                c1.write(f"**{info['nome']}** ({uid}) — {info.get('role','?')} | {info.get('depto','S/D')}")
                if c2.button("🗑️", key=f"del_u_{uid}"):
                    st.info("Exclusão lógica: desative o usuário diretamente no banco.")

    # ══════════════════════════════════════════════════════════════════════════
    # DEPARTAMENTOS
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "🏢 DEPTOS":
        st.subheader("Departamentos")
        col_nd1, col_nd2 = st.columns([4, 1])
        novo_d = col_nd1.text_input("Novo Setor", label_visibility="collapsed", placeholder="Nome do setor...")
        if col_nd2.button("➕ Adicionar", use_container_width=True):
            if novo_d.strip():
                departamentos.append(novo_d.upper().strip())
                db.salvar_departamentos(list(set(departamentos)))
                st.success(f"Setor '{novo_d.upper()}' adicionado!")
                st.rerun()
        st.divider()
        st.write(sorted(departamentos))

    # ══════════════════════════════════════════════════════════════════════════
    # MOTIVOS
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "⚙️ MOTIVOS":
        st.subheader("Motivos Globais")

        with st.container(border=True):
            col_nm1, col_nm2 = st.columns([4, 1])
            novo_m = col_nm1.text_input("Nova categoria", label_visibility="collapsed", placeholder="Nome do motivo...")
            if col_nm2.button("➕ Adicionar", type="primary", use_container_width=True):
                if novo_m.strip():
                    motivos_att = list(set(motivos + [novo_m.upper().strip()]))
                    db.salvar_motivos(motivos_att)
                    st.success(f"Motivo '{novo_m.upper()}' adicionado!")
                    st.rerun()

        st.divider()
        st.markdown("#### 📋 Motivos Cadastrados")

        if motivos:
            # ✅ FIX 4: deletar motivo individualmente
            for idx, motivo in enumerate(sorted(motivos)):
                col_m1, col_m2 = st.columns([5, 1])
                col_m1.markdown(f"▸ **{motivo}**")
                if col_m2.button("🗑️", key=f"del_mot_{idx}_{motivo}", help=f"Remover '{motivo}'"):
                    motivos_att = [m for m in motivos if m != motivo]
                    db.salvar_motivos(motivos_att)
                    st.success(f"Motivo '{motivo}' removido.")
                    st.rerun()
        else:
            st.info("Nenhum motivo cadastrado ainda.")
