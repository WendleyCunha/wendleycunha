import streamlit as st
import pandas as pd
from datetime import datetime
from modulos.utils_tempo import agora_br, agora_iso, parse_dt_safe
from modulos import database as db

# ══════════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════
def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0:
        return "0min"
    horas = int(minutos // 60)
    mins  = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"


def finalizar_atividade_atual(nome_usuario):
    logs  = db.carregar_esforco()
    mudou = False
    agora = agora_br()
    for idx, act in enumerate(logs):
        if act['usuario'] == nome_usuario and act['status'] == 'Em andamento':
            logs[idx]['fim']         = agora.isoformat()
            logs[idx]['status']      = 'Finalizado'
            inicio_dt                = parse_dt_safe(act.get('inicio'))
            duracao                  = (agora - inicio_dt).total_seconds() / 60
            logs[idx]['duracao_min'] = round(duracao, 2)
            mudou = True
    if mudou:
        db.salvar_esforco(logs)


# ══════════════════════════════════════════════════════════════════
#  CSS ESPECÍFICO DO HOME
# ══════════════════════════════════════════════════════════════════
HOME_CSS = """
<style>
/* ── Page header ──────────────────────────────────────── */
.page-header {
    background: linear-gradient(135deg, #0a1628 0%, #0d2145 60%, #1a3a6e 100%);
    border-radius: 18px;
    padding: 24px 28px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255,215,0,0.15);
}
.page-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(255,215,0,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header::after {
    content: '';
    position: absolute;
    bottom: -30px; left: 40%;
    width: 100px; height: 100px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.header-greeting {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    z-index: 1;
}
.header-subtitle {
    font-size: 0.85rem;
    color: rgba(200,216,240,0.7);
    margin-top: 4px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    z-index: 1;
}
.header-badge {
    display: inline-block;
    background: rgba(255,215,0,0.15);
    border: 1px solid rgba(255,215,0,0.4);
    color: #FFD700;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 8px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    z-index: 1;
}

/* ── Seção de título ──────────────────────────────────── */
.section-title {
    font-size: 0.7rem;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
    padding-left: 4px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Card de atividade ativa ──────────────────────────── */
.active-task-card {
    background: linear-gradient(135deg, #0a1628, #0d2145);
    border: 1px solid rgba(255,215,0,0.3);
    border-radius: 16px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
}
.active-task-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #FFD700, #FFA500);
    border-radius: 16px 16px 0 0;
}
.active-task-pulse {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse-green 1.5s infinite;
}
@keyframes pulse-green {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.5); }
    50%       { box-shadow: 0 0 0 6px rgba(34,197,94,0); }
}
.active-task-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #FFD700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.active-task-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    margin-top: 6px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.active-task-meta {
    font-size: 0.78rem;
    color: rgba(200,216,240,0.6);
    margin-top: 4px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.time-badge {
    background: rgba(255,215,0,0.12);
    border: 1px solid rgba(255,215,0,0.25);
    color: #FFD700;
    font-size: 1.1rem;
    font-weight: 800;
    padding: 8px 16px;
    border-radius: 10px;
    margin-top: 12px;
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Card livre ───────────────────────────────────────── */
.free-card {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border: 1.5px solid #86efac;
    border-radius: 16px;
    padding: 18px 20px;
    text-align: center;
}
.free-icon { font-size: 2rem; display: block; margin-bottom: 6px; }
.free-text {
    font-size: 0.95rem;
    font-weight: 700;
    color: #15803d;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.free-sub {
    font-size: 0.78rem;
    color: #4ade80;
    margin-top: 3px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Form card ────────────────────────────────────────── */
.form-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* ── Reminder cards ───────────────────────────────────── */
.reminder-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid #ef4444;
    box-shadow: 0 2px 8px rgba(239,68,68,0.08);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.reminder-card:hover {
    transform: translateX(2px);
    box-shadow: 0 4px 12px rgba(239,68,68,0.12);
}
.reminder-card.delayed {
    border-left-color: #dc2626;
    background: #fff8f8;
}
.diary-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 2px 8px rgba(59,130,246,0.08);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.diary-card:hover {
    transform: translateX(2px);
    box-shadow: 0 4px 12px rgba(59,130,246,0.12);
}
.diary-card.delayed {
    border-left-color: #1d4ed8;
    background: #f8faff;
}
.card-tag {
    font-size: 0.67rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 6px;
    display: inline-block;
    margin-bottom: 6px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.card-tag.red   { background:#fef2f2; color:#dc2626; }
.card-tag.orange{ background:#fff7ed; color:#ea580c; }
.card-tag.blue  { background:#eff6ff; color:#1d4ed8; }
.card-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #0f172a;
    font-family: 'Plus Jakarta Sans', sans-serif;
    margin-bottom: 3px;
}
.card-body {
    font-size: 0.82rem;
    color: #475569;
    font-family: 'Plus Jakarta Sans', sans-serif;
    line-height: 1.5;
}
.card-meta {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 5px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Empty state ──────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 32px 20px;
    background: #f8faff;
    border-radius: 14px;
    border: 1.5px dashed #cbd5e1;
}
.empty-icon { font-size: 2.5rem; display: block; margin-bottom: 8px; }
.empty-text {
    font-size: 0.9rem;
    font-weight: 600;
    color: #64748b;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Tabela histórico ─────────────────────────────────── */
.hist-header {
    background: #f8faff;
    border-radius: 12px 12px 0 0;
    padding: 12px 16px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.hist-title {
    font-size: 0.82rem;
    font-weight: 800;
    color: #0a1628;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Agenda row ───────────────────────────────────────── */
.agenda-empty {
    text-align:center; padding:40px;
    background:#f8faff; border-radius:14px;
    border:1.5px dashed #cbd5e1;
}

/* ── Perfil ───────────────────────────────────────────── */
.profile-card {
    background: linear-gradient(135deg, #0a1628, #0d2145);
    border-radius: 18px;
    padding: 28px;
    text-align: center;
    border: 1px solid rgba(255,215,0,0.2);
    position: relative;
    overflow: hidden;
}
.profile-card::before {
    content:'';
    position:absolute; top:-50px; right:-50px;
    width:180px; height:180px;
    background:radial-gradient(circle, rgba(255,215,0,0.08) 0%, transparent 70%);
    border-radius:50%;
}
.profile-avatar {
    width:80px; height:80px;
    background:linear-gradient(135deg,#FFD700,#FFA500);
    border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:2rem; font-weight:900; color:#0a1628;
    margin:0 auto 14px;
    border:3px solid rgba(255,215,0,0.4);
    position:relative; z-index:1;
}
.profile-name {
    font-size:1.2rem; font-weight:800; color:#ffffff;
    font-family:'Plus Jakarta Sans',sans-serif;
    position:relative; z-index:1;
}
.profile-role {
    font-size:0.78rem; font-weight:600; color:#FFD700;
    text-transform:uppercase; letter-spacing:0.08em;
    margin-top:4px;
    font-family:'Plus Jakarta Sans',sans-serif;
    position:relative; z-index:1;
}
.profile-depto {
    font-size:0.82rem; color:rgba(200,216,240,0.6);
    margin-top:6px;
    font-family:'Plus Jakarta Sans',sans-serif;
    position:relative; z-index:1;
}
.profile-info-grid {
    display:grid; grid-template-columns:1fr 1fr;
    gap:10px; margin-top:16px;
}
.profile-info-item {
    background:#ffffff;
    border-radius:12px;
    padding:12px 14px;
    border:1px solid #e2e8f0;
    text-align:left;
}
.profile-info-label {
    font-size:0.68rem; font-weight:700; color:#94a3b8;
    text-transform:uppercase; letter-spacing:0.08em;
    font-family:'Plus Jakarta Sans',sans-serif;
}
.profile-info-value {
    font-size:0.88rem; font-weight:600; color:#0a1628;
    margin-top:3px;
    font-family:'Plus Jakarta Sans',sans-serif;
}
</style>
"""


# ══════════════════════════════════════════════════════════════════
#  FUNÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════
def exibir(user_info):
    st.markdown(HOME_CSS, unsafe_allow_html=True)

    # ── Cabeçalho da página ────────────────────────────────────────────────────
    hora_atual = agora_br()
    saudacao   = (
        "Bom dia" if hora_atual.hour < 12 else
        "Boa tarde" if hora_atual.hour < 18 else
        "Boa noite"
    )
    dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    dia_nome   = dia_semana[hora_atual.weekday()]

    st.markdown(f"""
        <div class="page-header">
            <div class="header-greeting">{saudacao}, {user_info['nome'].split()[0]}! 👋</div>
            <div class="header-subtitle">
                {dia_nome}, {hora_atual.strftime('%d/%m/%Y')} · {hora_atual.strftime('%H:%M')}
            </div>
            <div class="header-badge">
                {user_info.get('role', 'OPERACIONAL')} · {user_info.get('depto', '')}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Carregamento de dados ──────────────────────────────────────────────────
    projs           = db.carregar_projetos()
    diario          = db.carregar_diario()
    atividades_log  = db.carregar_esforco()
    motivos_gestao  = db.carregar_motivos()
    hoje_dt         = datetime.now().date()

    # ── Contadores para badges ─────────────────────────────────────────────────
    def _count_pendencias():
        c = 0
        for p in projs:
            for l in p.get('lembretes', []):
                try:
                    if datetime.strptime(l['data_hora'].split(" ")[0], "%d/%m/%Y").date() <= hoje_dt:
                        c += 1
                except: pass
        for s in diario:
            if s.get('status') == "Pendente" and s.get('lembrete') != "N/A":
                try:
                    if datetime.strptime(s['lembrete'].split(" ")[0], "%d/%m/%Y").date() <= hoje_dt:
                        c += 1
                except: pass
        return c

    n_pend = _count_pendencias()
    badge_pend = f" ({n_pend})" if n_pend > 0 else ""

    # ── Abas ──────────────────────────────────────────────────────────────────
    tab_esforco, tab_pendentes, tab_agenda, tab_novo, tab_perfil = st.tabs([
        "⚡ Esforço",
        f"🚨 Pendências{badge_pend}",
        "📅 Agenda",
        "➕ Agendar",
        "👤 Perfil"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 1 — ESFORÇO
    # ══════════════════════════════════════════════════════════════════════════
    with tab_esforco:
        atv_ativa = next(
            (a for a in atividades_log
             if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'),
            None
        )

        c1, c2 = st.columns([1, 1.3], gap="large")

        # ── Estado atual ───────────────────────────────────────────────────────
        with c1:
            st.markdown('<div class="section-title">STATUS ATUAL</div>', unsafe_allow_html=True)

            if atv_ativa:
                try:
                    inicio_dt = parse_dt_safe(atv_ativa.get('inicio'))
                    decorrido = int((agora_br() - inicio_dt).total_seconds() // 60) if inicio_dt else 0
                    inicio_fmt = inicio_dt.strftime('%H:%M') if inicio_dt else "—"
                except:
                    decorrido, inicio_fmt = 0, "—"

                st.markdown(f"""
                    <div class="active-task-card">
                        <div style="display:flex;align-items:center;">
                            <span class="active-task-pulse"></span>
                            <span class="active-task-label">Em andamento</span>
                        </div>
                        <div class="active-task-name">{atv_ativa['motivo']}</div>
                        {"<div class='active-task-meta'>" + atv_ativa.get('detalhes','') + "</div>" if atv_ativa.get('detalhes') else ""}
                        <div class="active-task-meta" style="margin-top:6px;">
                            Iniciado às {inicio_fmt}
                        </div>
                        <div class="time-badge">⏱ {decorrido} min</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if st.button("🏁 FINALIZAR TAREFA", type="secondary", use_container_width=True, key="btn_finalizar"):
                    finalizar_atividade_atual(user_info['nome'])
                    st.rerun()

            else:
                st.markdown("""
                    <div class="free-card">
                        <span class="free-icon">✨</span>
                        <div class="free-text">Você está livre!</div>
                        <div class="free-sub">Nenhuma tarefa em andamento</div>
                    </div>
                """, unsafe_allow_html=True)

        # ── Iniciar nova ───────────────────────────────────────────────────────
        with c2:
            st.markdown('<div class="section-title">INICIAR ATIVIDADE</div>', unsafe_allow_html=True)
            with st.container():
                motivo_sel = st.selectbox(
                    "Categoria da atividade",
                    motivos_gestao,
                    key="motivo_sel"
                )
                detalhes = st.text_input(
                    "Observação / Ticket",
                    placeholder="Ex: Ticket #1234 ou reunião com cliente...",
                    key="detalhes_input"
                )

                usar_horario_manual = st.checkbox("⏰ Ajustar horário de início manualmente")
                if usar_horario_manual:
                    col_h, col_m = st.columns(2)
                    hora_manual = col_h.number_input("Hora",   0, 23, value=agora_br().hour,   key="hora_man")
                    min_manual  = col_m.number_input("Minuto", 0, 59, value=agora_br().minute, key="min_man")

                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                if st.button("⚡ INICIAR AGORA", type="primary", use_container_width=True, key="btn_iniciar"):
                    finalizar_atividade_atual(user_info['nome'])

                    inicio_ref = (
                        agora_br().replace(hour=int(hora_manual), minute=int(min_manual), second=0)
                        if usar_horario_manual else agora_br()
                    )

                    atividades_log.append({
                        "usuario":     user_info['nome'],
                        "motivo":      motivo_sel,
                        "detalhes":    detalhes,
                        "inicio":      inicio_ref.isoformat(),
                        "fim":         None,
                        "status":      "Em andamento",
                        "duracao_min": 0
                    })
                    db.salvar_esforco(atividades_log)
                    st.rerun()

        # ── Histórico ─────────────────────────────────────────────────────────
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        meu_hist = [a for a in atividades_log if a['usuario'] == user_info['nome']]
        if meu_hist:
            df_meu = pd.DataFrame(meu_hist)
            df_meu['inicio_dt'] = df_meu['inicio'].apply(parse_dt_safe)
            df_meu = df_meu[df_meu['inicio_dt'].apply(
                lambda x: x.date() == hoje_dt if x is not None else False
            )].sort_values('inicio_dt', ascending=False)

            if not df_meu.empty:
                df_meu['🕐 Hora']    = df_meu['inicio_dt'].dt.strftime('%H:%M')
                df_meu['⏱ Tempo']   = df_meu['duracao_min'].apply(formatar_duracao_h_min)
                df_meu['📌 Motivo'] = df_meu['motivo']
                df_meu['📝 Obs']    = df_meu['detalhes']
                df_meu['Status']    = df_meu['status']

                st.markdown("""
                    <div class="hist-header">
                        <span class="hist-title">📋 Histórico de Hoje</span>
                    </div>
                """, unsafe_allow_html=True)
                st.dataframe(
                    df_meu[['🕐 Hora', '📌 Motivo', '📝 Obs', 'Status', '⏱ Tempo']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.markdown("""
                    <div class="empty-state">
                        <span class="empty-icon">📭</span>
                        <div class="empty-text">Nenhuma atividade registrada hoje</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="empty-state">
                    <span class="empty-icon">📭</span>
                    <div class="empty-text">Nenhuma atividade registrada hoje</div>
                </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 2 — PENDÊNCIAS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_pendentes:
        tipo_pnd = st.radio(
            "Filtro:",
            ["Minhas Pendências", "Visão Equipe"],
            horizontal=True,
            key="tipo_pnd"
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        col_pqi, col_dir = st.columns(2, gap="large")

        with col_pqi:
            st.markdown("""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                    <div style="width:4px;height:20px;background:#ef4444;border-radius:2px;"></div>
                    <span style="font-size:0.82rem;font-weight:800;color:#0a1628;
                                 text-transform:uppercase;letter-spacing:0.06em;
                                 font-family:'Plus Jakarta Sans',sans-serif;">
                        Processos (PQI)
                    </span>
                </div>
            """, unsafe_allow_html=True)

            tem_pqi = False
            for p_idx, p in enumerate(projs):
                lembretes = p.get('lembretes', [])
                for l_idx in range(len(lembretes) - 1, -1, -1):
                    l = lembretes[l_idx]
                    try:
                        data_l_dt = datetime.strptime(l['data_hora'].split(" ")[0], "%d/%m/%Y").date()
                        if data_l_dt <= hoje_dt:
                            tem_pqi   = True
                            atrasado  = data_l_dt < hoje_dt
                            tag_class = "red" if atrasado else "orange"
                            tag_label = "⚠️ Atrasada" if atrasado else "⏰ Vence hoje"

                            st.markdown(f"""
                                <div class="reminder-card {'delayed' if atrasado else ''}">
                                    <span class="card-tag {tag_class}">{tag_label}</span>
                                    <div class="card-title">{p['titulo']}</div>
                                    <div class="card-body">{l['texto']}</div>
                                    <div class="card-meta">📅 {l['data_hora']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button(
                                "✓ Concluir",
                                key=f"btn_pqi_{p_idx}_{l_idx}",
                                use_container_width=True
                            ):
                                p['lembretes'].pop(l_idx)
                                db.salvar_projetos(projs)
                                st.rerun()
                    except:
                        continue

            if not tem_pqi:
                st.markdown("""
                    <div class="empty-state">
                        <span class="empty-icon">🎉</span>
                        <div class="empty-text">Nenhuma pendência em processos!</div>
                    </div>
                """, unsafe_allow_html=True)

        with col_dir:
            st.markdown("""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                    <div style="width:4px;height:20px;background:#3b82f6;border-radius:2px;"></div>
                    <span style="font-size:0.82rem;font-weight:800;color:#0a1628;
                                 text-transform:uppercase;letter-spacing:0.06em;
                                 font-family:'Plus Jakarta Sans',sans-serif;">
                        Diário de Bordo
                    </span>
                </div>
            """, unsafe_allow_html=True)

            tem_diario = False
            for idx, sit in enumerate(diario):
                if sit.get('status') == "Pendente" and sit.get('lembrete') != "N/A":
                    if tipo_pnd == "Minhas Pendências" and sit.get('usuario') != user_info['nome']:
                        continue
                    try:
                        data_s_dt = datetime.strptime(sit['lembrete'].split(" ")[0], "%d/%m/%Y").date()
                        if data_s_dt <= hoje_dt:
                            tem_diario = True
                            atrasado   = data_s_dt < hoje_dt
                            tag_class  = "blue"
                            tag_label  = "🚨 Atrasado" if atrasado else "📅 Agendado hoje"

                            st.markdown(f"""
                                <div class="diary-card {'delayed' if atrasado else ''}">
                                    <span class="card-tag {tag_class}">{tag_label}</span>
                                    <div class="card-title">{sit['depto']}</div>
                                    <div class="card-body">{sit['solicitacao']}</div>
                                    <div class="card-meta">👤 {sit.get('usuario','S/I')} · {sit['lembrete']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button(
                                "✓ Concluir",
                                key=f"btn_dir_{idx}",
                                use_container_width=True
                            ):
                                sit['status'] = "Executado"
                                db.salvar_diario(diario)
                                st.rerun()
                    except:
                        continue

            if not tem_diario:
                st.markdown("""
                    <div class="empty-state">
                        <span class="empty-icon">🎉</span>
                        <div class="empty-text">Nenhuma pendência no diário!</div>
                    </div>
                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 3 — AGENDA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_agenda:
        tipo_age = st.radio(
            "Visualizar:",
            ["Apenas Meus", "Toda a Equipe"],
            horizontal=True,
            key="tipo_age"
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        agenda_raw = []

        for sit in diario:
            if sit.get('status') == "Pendente" and sit.get('lembrete', "N/A") != "N/A":
                try:
                    data_dt = datetime.strptime(sit['lembrete'].split(" ")[0], "%d/%m/%Y").date()
                    dono    = sit.get('usuario', 'S/I')
                    if tipo_age == "Apenas Meus" and dono != user_info['nome']:
                        continue
                    if data_dt > hoje_dt:
                        agenda_raw.append({
                            "Data_Ref": data_dt,
                            "📅 Data":   data_dt.strftime("%d/%m/%Y"),
                            "🏷 Origem": f"Diário · {sit['depto']}",
                            "📋 Tarefa": sit['solicitacao'],
                            "👤 Quem":   dono
                        })
                except:
                    continue

        for p in projs:
            for l in p.get('lembretes', []):
                try:
                    data_dt = datetime.strptime(l['data_hora'].split(" ")[0], "%d/%m/%Y").date()
                    if data_dt > hoje_dt:
                        agenda_raw.append({
                            "Data_Ref": data_dt,
                            "📅 Data":   data_dt.strftime("%d/%m/%Y"),
                            "🏷 Origem": f"PQI · {p['titulo']}",
                            "📋 Tarefa": l['texto'],
                            "👤 Quem":   "Equipe"
                        })
                except:
                    continue

        if agenda_raw:
            df_age = pd.DataFrame(agenda_raw).sort_values(by="Data_Ref")
            st.dataframe(
                df_age[["📅 Data", "🏷 Origem", "📋 Tarefa", "👤 Quem"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.markdown("""
                <div class="agenda-empty">
                    <div style="font-size:2.5rem;">🗓️</div>
                    <div style="font-size:0.9rem;font-weight:600;color:#64748b;
                                font-family:'Plus Jakarta Sans',sans-serif;margin-top:8px;">
                        Nenhum compromisso futuro encontrado
                    </div>
                    <div style="font-size:0.8rem;color:#94a3b8;
                                font-family:'Plus Jakarta Sans',sans-serif;margin-top:4px;">
                        Use a aba "Agendar" para criar novos compromissos
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 4 — NOVO AGENDAMENTO
    # ══════════════════════════════════════════════════════════════════════════
    with tab_novo:
        st.markdown('<div class="section-title">CRIAR NOVO LEMBRETE</div>', unsafe_allow_html=True)

        col_form, col_info = st.columns([1.4, 1], gap="large")

        with col_form:
            with st.form("form_novo_v3", clear_on_submit=True):
                tipo = st.selectbox(
                    "Vincular a:",
                    ["Situações Diárias (Diário)", "Processos (PQI)"],
                    key="tipo_agend"
                )
                txt_lembrete = st.text_area(
                    "Descrição da tarefa",
                    placeholder="Descreva detalhadamente o que precisa ser feito...",
                    height=100
                )

                c1, c2 = st.columns(2)
                d_agendada = c1.date_input("📅 Data", min_value=hoje_dt)
                h_agendada = c2.time_input("🕐 Horário", value=datetime.now().time())

                proj_vinc = None
                if tipo == "Processos (PQI)":
                    proj_vinc = st.selectbox(
                        "Selecione o Projeto PQI:",
                        [p['titulo'] for p in projs]
                    )

                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button(
                    "🚀 AGENDAR TAREFA",
                    use_container_width=True,
                    type="primary"
                )

                if submitted:
                    if not txt_lembrete.strip():
                        st.error("Por favor, descreva a tarefa.")
                    else:
                        data_f = f"{d_agendada.strftime('%d/%m/%Y')} {h_agendada.strftime('%H:%M')}"
                        if tipo == "Processos (PQI)":
                            for p in projs:
                                if p['titulo'] == proj_vinc:
                                    p.setdefault('lembretes', []).append({
                                        "id":       datetime.now().timestamp(),
                                        "data_hora": data_f,
                                        "texto":    txt_lembrete,
                                        "status":   "Pendente"
                                    })
                            db.salvar_projetos(projs)
                        else:
                            diario.append({
                                "usuario":    user_info['nome'],
                                "data_reg":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "solicitacao": txt_lembrete,
                                "depto":      "GERAL",
                                "lembrete":   data_f,
                                "status":     "Pendente"
                            })
                            db.salvar_diario(diario)

                        st.success(f"✅ Tarefa agendada para {data_f}!")
                        st.rerun()

        with col_info:
            st.markdown("""
                <div style="background:linear-gradient(135deg,#f8faff,#eef2ff);
                            border:1px solid #c7d2fe;border-radius:16px;padding:20px;">
                    <div style="font-size:0.78rem;font-weight:800;color:#6366f1;
                                text-transform:uppercase;letter-spacing:0.08em;
                                font-family:'Plus Jakarta Sans',sans-serif;margin-bottom:12px;">
                        💡 Como funciona
                    </div>
                    <div style="font-size:0.84rem;color:#334155;
                                font-family:'Plus Jakarta Sans',sans-serif;line-height:1.7;">
                        <strong>Diário de Bordo:</strong> Cria uma pendência pessoal. 
                        Aparecerá nas suas pendências na data agendada.<br><br>
                        <strong>Processos (PQI):</strong> Vincula o lembrete a um 
                        processo existente. Visível para toda a equipe.
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 5 — PERFIL
    # ══════════════════════════════════════════════════════════════════════════
    with tab_perfil:
        col_pf1, col_pf2 = st.columns([1, 1.4], gap="large")

        with col_pf1:
            st.markdown(f"""
                <div class="profile-card">
                    <div class="profile-avatar">
                        {user_info['nome'][0].upper()}
                    </div>
                    <div class="profile-name">{user_info['nome']}</div>
                    <div class="profile-role">{user_info.get('role', 'OPERACIONAL')}</div>
                    <div class="profile-depto">{user_info.get('depto', '')}</div>
                </div>
            """, unsafe_allow_html=True)

        with col_pf2:
            st.markdown('<div class="section-title">INFORMAÇÕES</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="profile-info-grid">
                    <div class="profile-info-item">
                        <div class="profile-info-label">📧 E-mail</div>
                        <div class="profile-info-value">{user_info.get('email', 'Não informado')}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">💼 Função</div>
                        <div class="profile-info-value">{user_info.get('funcao', 'Não informado')}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">🏢 Departamento</div>
                        <div class="profile-info-value">{user_info.get('depto', 'Não informado')}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">🔐 Perfil</div>
                        <div class="profile-info-value">{user_info.get('role', 'OPERACIONAL')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">FOTO DE PERFIL</div>', unsafe_allow_html=True)

            foto = st.file_uploader(
                "Escolha uma imagem",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )
            if foto is not None:
                import os
                os.makedirs("fotos", exist_ok=True)
                caminho = f"fotos/{user_info['nome']}.png"
                with open(caminho, "wb") as f:
                    f.write(foto.getbuffer())
                st.success("✅ Foto atualizada com sucesso!")

            try:
                st.image(f"fotos/{user_info['nome']}.png", width=120)
            except:
                st.markdown("""
                    <div style="background:#f1f5f9;border:1.5px dashed #cbd5e1;
                                border-radius:12px;padding:20px;text-align:center;
                                color:#94a3b8;font-size:0.82rem;
                                font-family:'Plus Jakarta Sans',sans-serif;">
                        📷 Nenhuma foto cadastrada
                    </div>
                """, unsafe_allow_html=True)
