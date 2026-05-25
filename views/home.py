import streamlit as st
import pandas as pd
from datetime import datetime
from modulos.utils_tempo import agora_br, agora_iso, parse_dt_safe
from modulos import database as db

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0:
        return "0 min"
    horas = int(minutos // 60)
    mins  = int(minutos % 60)
    return f"{horas}h {mins:02d}min" if horas > 0 else f"{mins} min"


def finalizar_atividade_atual(nome_usuario):
    logs   = db.carregar_esforco()
    mudou  = False
    agora  = agora_br()
    for idx, act in enumerate(logs):
        if act["usuario"] == nome_usuario and act["status"] == "Em andamento":
            logs[idx]["fim"]         = agora.isoformat()
            logs[idx]["status"]      = "Finalizado"
            inicio_dt                = parse_dt_safe(act.get("inicio"))
            duracao                  = (agora - inicio_dt).total_seconds() / 60
            logs[idx]["duracao_min"] = round(duracao, 2)
            mudou = True
    if mudou:
        db.salvar_esforco(logs)


# ─────────────────────────────────────────────
#  CSS GLOBAL  (inspirado no SimpliRoute)
# ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ---------- IMPORTAR FONTE ---------- */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ---------- RESET STREAMLIT ---------- */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ---------- PÁGINA ---------- */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* ---------- HERO HEADER ---------- */
.sr-hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #1d4ed8 60%, #0ea5e9 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 8px 32px rgba(30, 58, 95, 0.35);
}
.sr-hero-left h1 {
    color: #ffffff;
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
}
.sr-hero-left p {
    color: rgba(255,255,255,0.75);
    font-size: 0.85rem;
    margin: 0;
}
.sr-hero-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    backdrop-filter: blur(8px);
    border-radius: 10px;
    padding: 12px 20px;
    text-align: center;
}
.sr-hero-badge .val {
    color: #fff;
    font-size: 1.4rem;
    font-weight: 800;
    display: block;
}
.sr-hero-badge .lbl {
    color: rgba(255,255,255,0.7);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ---------- KPI ROW ---------- */
.sr-kpi-row {
    display: flex;
    gap: 14px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}
.sr-kpi-card {
    flex: 1;
    min-width: 140px;
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-top: 4px solid;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.sr-kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}
.sr-kpi-card .num {
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
}
.sr-kpi-card .lbl {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
.kpi-blue   { border-top-color: #2563eb; }
.kpi-blue   .num { color: #2563eb; }
.kpi-green  { border-top-color: #16a34a; }
.kpi-green  .num { color: #16a34a; }
.kpi-amber  { border-top-color: #d97706; }
.kpi-amber  .num { color: #d97706; }
.kpi-red    { border-top-color: #dc2626; }
.kpi-red    .num { color: #dc2626; }

/* ---------- SECTION TITLE ---------- */
.sr-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin: 0 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #e2e8f0;
}

/* ---------- ACTIVITY CARD (ativa) ---------- */
.sr-active-card {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1px solid #93c5fd;
    border-left: 5px solid #2563eb;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.sr-active-card .act-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 4px;
}
.sr-active-card .act-sub {
    font-size: 0.8rem;
    color: #3b82f6;
}
.sr-active-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-dot 1.5s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(1.4); }
}

/* ---------- HISTORY TABLE ---------- */
.sr-hist-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border-radius: 10px;
    margin-bottom: 6px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    transition: background 0.12s;
}
.sr-hist-row:hover { background: #f1f5f9; }
.sr-hist-time {
    font-size: 0.75rem;
    font-weight: 700;
    color: #94a3b8;
    min-width: 40px;
}
.sr-hist-label {
    flex: 1;
    font-size: 0.85rem;
    font-weight: 600;
    color: #1e293b;
}
.sr-hist-detail {
    font-size: 0.75rem;
    color: #64748b;
    flex: 1;
}
.sr-hist-dur {
    font-size: 0.75rem;
    font-weight: 700;
    color: #2563eb;
    white-space: nowrap;
}

/* ---------- STATUS BADGE ---------- */
.sr-badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 3px 9px;
    border-radius: 20px;
}
.badge-done    { background: #dcfce7; color: #16a34a; }
.badge-pending { background: #fef9c3; color: #92400e; }
.badge-late    { background: #fee2e2; color: #dc2626; }
.badge-today   { background: #eff6ff; color: #2563eb; }

/* ---------- REMINDER CARD ---------- */
.sr-reminder {
    background: #ffffff;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 5px solid;
    transition: box-shadow 0.15s;
}
.sr-reminder:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.12); }
.sr-reminder.late  { border-left-color: #dc2626; }
.sr-reminder.today { border-left-color: #d97706; }
.sr-reminder.diary { border-left-color: #2563eb; }
.sr-reminder .rem-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 3px;
}
.sr-reminder .rem-sub {
    font-size: 0.78rem;
    color: #64748b;
}

/* ---------- AGENDA ROW ---------- */
.sr-agenda-item {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 12px 0;
    border-bottom: 1px solid #f1f5f9;
}
.sr-agenda-date {
    min-width: 56px;
    text-align: center;
    background: #eff6ff;
    border-radius: 10px;
    padding: 8px 4px;
}
.sr-agenda-date .day  { font-size: 1.4rem; font-weight: 800; color: #2563eb; line-height: 1; }
.sr-agenda-date .mon  { font-size: 0.65rem; font-weight: 700; color: #64748b; text-transform: uppercase; }
.sr-agenda-body .title { font-size: 0.88rem; font-weight: 600; color: #1e293b; }
.sr-agenda-body .org   { font-size: 0.75rem; color: #94a3b8; margin-top: 2px; }

/* ---------- FORM PANEL ---------- */
.sr-form-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
}

/* ---------- PROFILE CARD ---------- */
.sr-profile-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #1d4ed8 100%);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    color: #fff;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(30, 58, 95, 0.3);
}
.sr-profile-card .avatar {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
    margin: 0 auto 12px;
    border: 3px solid rgba(255,255,255,0.4);
}
.sr-profile-card .pname { font-size: 1.2rem; font-weight: 800; }
.sr-profile-card .prole { font-size: 0.8rem; opacity: 0.7; margin-top: 2px; }

/* ---------- TABS OVERRIDE ---------- */
[data-baseweb="tab-list"] {
    gap: 4px;
    background: #f1f5f9 !important;
    border-radius: 10px !important;
    padding: 4px !important;
}
[data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #ffffff !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    color: #2563eb !important;
}

/* ---------- BUTTON OVERRIDE ---------- */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.3px !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45) !important;
}

/* ---------- DIVIDER ---------- */
hr { border-color: #e2e8f0 !important; margin: 16px 0 !important; }

/* ---------- EXPANDER ---------- */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
</style>
"""


# ─────────────────────────────────────────────
#  COMPONENTES HTML
# ─────────────────────────────────────────────
def hero(nome: str, data_str: str, total_hoje: str):
    return f"""
    <div class="sr-hero">
        <div class="sr-hero-left">
            <h1>Olá, {nome}! 👋</h1>
            <p>{data_str}</p>
        </div>
        <div class="sr-hero-badge">
            <span class="val">{total_hoje}</span>
            <span class="lbl">Tempo hoje</span>
        </div>
    </div>
    """


def kpi_row(cards: list):
    """cards = [{'num': X, 'lbl': Y, 'cls': 'kpi-blue'}, ...]"""
    html = '<div class="sr-kpi-row">'
    for c in cards:
        html += f"""
        <div class="sr-kpi-card {c['cls']}">
            <div class="num">{c['num']}</div>
            <div class="lbl">{c['lbl']}</div>
        </div>"""
    html += "</div>"
    return html


def section_title(txt: str):
    return f'<p class="sr-section-title">{txt}</p>'


def active_card(motivo: str, hora_inicio: str, decorrido: int):
    return f"""
    <div class="sr-active-card">
        <div class="act-title">
            <span class="sr-active-dot"></span>{motivo}
        </div>
        <div class="act-sub">Iniciado às {hora_inicio} &nbsp;·&nbsp; {decorrido} min decorridos</div>
    </div>
    """


def hist_row(hora: str, motivo: str, detalhe: str, duracao: str, status: str):
    badge = (
        '<span class="sr-badge badge-done">✓ Feito</span>'
        if status == "Finalizado"
        else '<span class="sr-badge badge-pending">● Ativo</span>'
    )
    return f"""
    <div class="sr-hist-row">
        <span class="sr-hist-time">{hora}</span>
        <span class="sr-hist-label">{motivo}</span>
        <span class="sr-hist-detail">{detalhe or "—"}</span>
        <span class="sr-hist-dur">{duracao}</span>
        {badge}
    </div>"""


def reminder_card(tipo: str, titulo: str, texto: str, resp: str = ""):
    cls = "late" if tipo == "atrasado" else ("today" if tipo == "hoje" else "diary")
    badge_html = (
        '<span class="sr-badge badge-late">⚠ Atrasado</span>'
        if tipo == "atrasado"
        else '<span class="sr-badge badge-today">📅 Hoje</span>'
    )
    sub = f"{resp} &nbsp;|&nbsp; " if resp else ""
    return f"""
    <div class="sr-reminder {cls}">
        <div class="rem-title">{titulo}</div>
        <div class="rem-sub">{sub}{texto}</div>
        {badge_html}
    </div>"""


def agenda_item(dia: str, mes: str, titulo: str, origem: str):
    return f"""
    <div class="sr-agenda-item">
        <div class="sr-agenda-date">
            <div class="day">{dia}</div>
            <div class="mon">{mes}</div>
        </div>
        <div class="sr-agenda-body">
            <div class="title">{titulo}</div>
            <div class="org">{origem}</div>
        </div>
    </div>"""


# ─────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL
# ─────────────────────────────────────────────
def exibir(user_info):
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # ── Carregar dados ──────────────────────────────────────
    projs          = db.carregar_projetos()
    diario         = db.carregar_diario()
    atividades_log = db.carregar_esforco()
    motivos_gestao = db.carregar_motivos()
    hoje_dt        = datetime.now().date()
    agora          = agora_br()

    # ── KPIs globais ────────────────────────────────────────
    meu_hist_hoje = [
        a for a in atividades_log
        if a["usuario"] == user_info["nome"]
        and parse_dt_safe(a.get("inicio")) is not None
        and parse_dt_safe(a["inicio"]).date() == hoje_dt
    ]
    total_min_hoje = sum(a.get("duracao_min", 0) or 0 for a in meu_hist_hoje)
    total_hoje_str = formatar_duracao_h_min(total_min_hoje)

    # Pendências
    pend_pqi = sum(
        1 for p in projs for l in p.get("lembretes", [])
        if _parse_date_safe(l.get("data_hora", "")) is not None
        and _parse_date_safe(l["data_hora"]) <= hoje_dt
    )
    pend_diario = sum(
        1 for s in diario
        if s.get("status") == "Pendente"
        and s.get("lembrete", "N/A") != "N/A"
        and _parse_date_safe(s.get("lembrete", "")) is not None
        and _parse_date_safe(s["lembrete"]) <= hoje_dt
    )

    atv_ativa = next(
        (a for a in atividades_log if a["usuario"] == user_info["nome"] and a["status"] == "Em andamento"),
        None,
    )

    # ── HERO ────────────────────────────────────────────────
    data_str = agora.strftime("%A, %d de %B de %Y").capitalize()
    st.markdown(hero(user_info["nome"], data_str, total_hoje_str), unsafe_allow_html=True)

    # ── KPI ROW ─────────────────────────────────────────────
    st.markdown(
        kpi_row([
            {"num": len(meu_hist_hoje), "lbl": "Atividades hoje",  "cls": "kpi-blue"},
            {"num": total_hoje_str,     "lbl": "Tempo registrado", "cls": "kpi-green"},
            {"num": pend_pqi,           "lbl": "PQI pendentes",    "cls": "kpi-amber"},
            {"num": pend_diario,        "lbl": "Diário pendente",  "cls": "kpi-red"},
        ]),
        unsafe_allow_html=True,
    )

    # ── TABS ────────────────────────────────────────────────
    tab_esforco, tab_pendentes, tab_agenda, tab_novo, tab_perfil = st.tabs([
        "⚡ Esforço Hoje",
        "🚀 Pendências",
        "📅 Agenda",
        "➕ Novo",
        "👤 Perfil",
    ])

    # ══════════════════════════════════════════════════════
    #  ABA 1 – ESFORÇO
    # ══════════════════════════════════════════════════════
    with tab_esforco:
        col_status, col_iniciar = st.columns([1, 1.3], gap="large")

        with col_status:
            st.markdown(section_title("STATUS ATUAL"), unsafe_allow_html=True)
            if atv_ativa:
                inicio_dt = parse_dt_safe(atv_ativa.get("inicio"))
                decorrido = int((agora - inicio_dt).total_seconds() // 60) if inicio_dt else 0
                hora_str  = inicio_dt.strftime("%H:%M") if inicio_dt else "--:--"
                st.markdown(active_card(atv_ativa["motivo"], hora_str, decorrido), unsafe_allow_html=True)
                if st.button("🏁 Finalizar tarefa atual", type="secondary", use_container_width=True):
                    finalizar_atividade_atual(user_info["nome"])
                    st.rerun()
            else:
                st.markdown(
                    """
                    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;
                                padding:18px 20px;text-align:center;">
                        <div style="font-size:1.6rem;margin-bottom:6px;">✨</div>
                        <div style="font-weight:700;color:#16a34a;font-size:0.9rem;">Você está livre!</div>
                        <div style="font-size:0.78rem;color:#4ade80;margin-top:3px;">Nenhuma tarefa ativa</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_iniciar:
            st.markdown(section_title("INICIAR ATIVIDADE"), unsafe_allow_html=True)
            with st.container():
                motivo_sel = st.selectbox("Categoria", motivos_gestao, label_visibility="collapsed")
                detalhes   = st.text_input("Observação ou Ticket", placeholder="Ex: CHG-1234 | Reunião de alinhamento...")
                usar_manual = st.checkbox("⏰ Ajustar horário manualmente")
                if usar_manual:
                    ch, cm = st.columns(2)
                    hora_manual = ch.number_input("Hora", 0, 23, value=agora.hour)
                    min_manual  = cm.number_input("Minuto", 0, 59, value=agora.minute)
                if st.button("⚡ Iniciar agora", type="primary", use_container_width=True):
                    finalizar_atividade_atual(user_info["nome"])
                    inicio_ref = (
                        agora.replace(hour=int(hora_manual), minute=int(min_manual), second=0)
                        if usar_manual else agora
                    )
                    atividades_log.append({
                        "usuario":     user_info["nome"],
                        "motivo":      motivo_sel,
                        "detalhes":    detalhes,
                        "inicio":      inicio_ref.isoformat(),
                        "fim":         None,
                        "status":      "Em andamento",
                        "duracao_min": 0,
                    })
                    db.salvar_esforco(atividades_log)
                    st.rerun()

        # ── Histórico do dia ──────────────────────────────
        st.divider()
        st.markdown(section_title("HISTÓRICO DE HOJE"), unsafe_allow_html=True)

        if meu_hist_hoje:
            df = pd.DataFrame(meu_hist_hoje)
            df["inicio_dt"] = df["inicio"].apply(parse_dt_safe)
            df = df[df["inicio_dt"].apply(lambda x: x is not None)].sort_values("inicio_dt", ascending=False)
            html_rows = ""
            for _, row in df.iterrows():
                hora   = row["inicio_dt"].strftime("%H:%M")
                dur    = formatar_duracao_h_min(row.get("duracao_min", 0) or 0)
                html_rows += hist_row(hora, row["motivo"], row.get("detalhes", ""), dur, row["status"])
            st.markdown(html_rows, unsafe_allow_html=True)
        else:
            st.info("Nenhuma atividade registrada hoje.")

    # ══════════════════════════════════════════════════════
    #  ABA 2 – PENDÊNCIAS
    # ══════════════════════════════════════════════════════
    with tab_pendentes:
        tipo_pnd = st.radio("Exibir:", ["Minhas Pendências", "Visão Equipe"], horizontal=True)
        col_pqi, col_dir = st.columns(2, gap="large")

        with col_pqi:
            st.markdown(section_title("📌 PROCESSOS (PQI)"), unsafe_allow_html=True)
            encontrou_pqi = False
            for p_idx, p in enumerate(projs):
                lembretes = p.get("lembretes", [])
                for l_idx in range(len(lembretes) - 1, -1, -1):
                    l = lembretes[l_idx]
                    dt = _parse_date_safe(l.get("data_hora", ""))
                    if dt and dt <= hoje_dt:
                        encontrou_pqi = True
                        tipo = "atrasado" if dt < hoje_dt else "hoje"
                        st.markdown(reminder_card(tipo, p["titulo"], l["texto"]), unsafe_allow_html=True)
                        if st.button("✓ Concluir", key=f"pqi_{p_idx}_{l_idx}", use_container_width=True):
                            p["lembretes"].pop(l_idx)
                            db.salvar_projetos(projs)
                            st.rerun()
            if not encontrou_pqi:
                _empty_state("Nenhuma pendência de PQI para hoje")

        with col_dir:
            st.markdown(section_title("📓 DIÁRIO DE BORDO"), unsafe_allow_html=True)
            encontrou_dir = False
            for idx, sit in enumerate(diario):
                if sit.get("status") != "Pendente" or sit.get("lembrete", "N/A") == "N/A":
                    continue
                if tipo_pnd == "Minhas Pendências" and sit.get("usuario") != user_info["nome"]:
                    continue
                dt = _parse_date_safe(sit.get("lembrete", ""))
                if dt and dt <= hoje_dt:
                    encontrou_dir = True
                    tipo = "atrasado" if dt < hoje_dt else "diary"
                    st.markdown(
                        reminder_card(tipo, f"{sit['depto']}", sit["solicitacao"], sit.get("usuario", "")),
                        unsafe_allow_html=True,
                    )
                    if st.button("✓ Concluir", key=f"dir_{idx}", use_container_width=True):
                        sit["status"] = "Executado"
                        db.salvar_diario(diario)
                        st.rerun()
            if not encontrou_dir:
                _empty_state("Nenhuma situação pendente para hoje")

    # ══════════════════════════════════════════════════════
    #  ABA 3 – AGENDA
    # ══════════════════════════════════════════════════════
    with tab_agenda:
        tipo_age = st.radio(
            "Compromissos de:", ["Apenas Meus", "Toda a Equipe"], horizontal=True
        )
        agenda_raw = []

        for sit in diario:
            if sit.get("status") == "Pendente" and sit.get("lembrete", "N/A") != "N/A":
                dt = _parse_date_safe(sit.get("lembrete", ""))
                dono = sit.get("usuario", "S/I")
                if tipo_age == "Apenas Meus" and dono != user_info["nome"]:
                    continue
                if dt and dt > hoje_dt:
                    agenda_raw.append({"dt": dt, "titulo": sit["solicitacao"],
                                       "origem": f"Diário · {sit['depto']}", "quem": dono})

        for p in projs:
            for l in p.get("lembretes", []):
                dt = _parse_date_safe(l.get("data_hora", ""))
                if dt and dt > hoje_dt:
                    agenda_raw.append({"dt": dt, "titulo": l["texto"],
                                       "origem": f"PQI · {p['titulo']}", "quem": "Equipe"})

        agenda_raw.sort(key=lambda x: x["dt"])

        st.markdown(section_title(f"PRÓXIMOS COMPROMISSOS — {len(agenda_raw)} item(ns)"), unsafe_allow_html=True)
        if agenda_raw:
            html_ag = ""
            for item in agenda_raw:
                html_ag += agenda_item(
                    item["dt"].strftime("%d"),
                    item["dt"].strftime("%b").upper(),
                    item["titulo"],
                    f"{item['origem']} &nbsp;·&nbsp; {item['quem']}",
                )
            st.markdown(html_ag, unsafe_allow_html=True)
        else:
            _empty_state("Nenhum compromisso futuro encontrado")

    # ══════════════════════════════════════════════════════
    #  ABA 4 – NOVO AGENDAMENTO
    # ══════════════════════════════════════════════════════
    with tab_novo:
        st.markdown(section_title("CRIAR NOVO LEMBRETE"), unsafe_allow_html=True)
        st.markdown('<div class="sr-form-panel">', unsafe_allow_html=True)

        with st.form("form_novo_v3", clear_on_submit=True):
            tipo = st.selectbox(
                "Vincular a:",
                ["Situações Diárias (Diário)", "Processos (PQI)"],
            )
            txt_lembrete = st.text_area(
                "O que precisa ser feito?",
                placeholder="Descreva a tarefa com clareza…",
                height=100,
            )
            c1, c2 = st.columns(2)
            d_agendada = c1.date_input("Para quando?", min_value=hoje_dt)
            h_agendada = c2.time_input("Horário", value=datetime.now().time())

            proj_vinc = None
            if tipo == "Processos (PQI)":
                nomes = [p["titulo"] for p in projs]
                proj_vinc = st.selectbox("Projeto PQI:", nomes) if nomes else None

            enviado = st.form_submit_button("🚀 Agendar tarefa", use_container_width=True, type="primary")

        st.markdown("</div>", unsafe_allow_html=True)

        if enviado:
            if not txt_lembrete.strip():
                st.error("Por favor, descreva a tarefa.")
            else:
                data_f = f"{d_agendada.strftime('%d/%m/%Y')} {h_agendada.strftime('%H:%M')}"
                if tipo == "Processos (PQI)" and proj_vinc:
                    for p in projs:
                        if p["titulo"] == proj_vinc:
                            p.setdefault("lembretes", []).append({
                                "id": datetime.now().timestamp(),
                                "data_hora": data_f,
                                "texto": txt_lembrete,
                                "status": "Pendente",
                            })
                    db.salvar_projetos(projs)
                else:
                    diario.append({
                        "usuario":   user_info["nome"],
                        "data_reg":  datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "solicitacao": txt_lembrete,
                        "depto":     "GERAL",
                        "lembrete":  data_f,
                        "status":    "Pendente",
                    })
                    db.salvar_diario(diario)
                st.success(f"✅ Tarefa agendada para **{data_f}**!")
                st.rerun()

    # ══════════════════════════════════════════════════════
    #  ABA 5 – PERFIL
    # ══════════════════════════════════════════════════════
    with tab_perfil:
        col_a, col_b = st.columns([1, 1.8], gap="large")

        with col_a:
            st.markdown(
                f"""
                <div class="sr-profile-card">
                    <div class="avatar">👤</div>
                    <div class="pname">{user_info['nome']}</div>
                    <div class="prole">{user_info.get('cargo', 'Colaborador')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            foto = st.file_uploader("Alterar foto", type=["png", "jpg", "jpeg"])
            if foto:
                import os
                os.makedirs("fotos", exist_ok=True)
                with open(f"fotos/{user_info['nome']}.png", "wb") as f:
                    f.write(foto.getbuffer())
                st.success("Foto salva!")
                st.rerun()

        with col_b:
            st.markdown(section_title("RESUMO DO DIA"), unsafe_allow_html=True)
            categorias = {}
            for a in meu_hist_hoje:
                cat = a.get("motivo", "Outros")
                categorias[cat] = categorias.get(cat, 0) + (a.get("duracao_min", 0) or 0)

            if categorias:
                df_cat = pd.DataFrame(
                    [{"Categoria": k, "Tempo": formatar_duracao_h_min(v), "Minutos": v}
                     for k, v in sorted(categorias.items(), key=lambda x: -x[1])]
                )
                st.dataframe(
                    df_cat[["Categoria", "Tempo"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                _empty_state("Nenhuma atividade registrada hoje")

            st.markdown(section_title("FOTO DE PERFIL ATUAL"), unsafe_allow_html=True)
            try:
                st.image(f"fotos/{user_info['nome']}.png", width=130)
            except Exception:
                st.caption("Nenhuma foto cadastrada.")


# ─────────────────────────────────────────────
#  UTILITÁRIOS PRIVADOS
# ─────────────────────────────────────────────
def _parse_date_safe(valor: str):
    """Retorna um objeto date ou None, sem quebrar."""
    try:
        return datetime.strptime(valor.split(" ")[0], "%d/%m/%Y").date()
    except Exception:
        return None


def _empty_state(msg: str):
    st.markdown(
        f"""
        <div style="text-align:center;padding:28px 16px;color:#94a3b8;">
            <div style="font-size:1.8rem;margin-bottom:8px;">🎉</div>
            <div style="font-size:0.85rem;font-weight:600;">{msg}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
