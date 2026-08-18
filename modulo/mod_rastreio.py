import sys, os, io, time, re
import html as _h
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import (obter_vinculo_db, salvar_vinculo_db, deletar_rota_db,
                      pode_editar, pode_deletar, obter_tickets_db,
                      criar_usuario, listar_usuarios, deletar_usuario,
                      redefinir_senha_usuario, atualizar_dados_usuario)

# Import isolado: se database_logistica.py tiver qualquer problema, o
# Rastreio inteiro continua funcionando — só a aba de Cadastros/Upload e a
# baixa de entrega com foto ficam indisponíveis, com um aviso.
try:
    from database_logistica import salvar_entregas_db, dar_baixa_entrega_db
    from database import obter_tickets_com_id_db
    _LOGISTICA_OK = True
    _erro_import_logistica_msg = ""
except Exception as _erro_import_logistica:
    _LOGISTICA_OK = False
    _erro_import_logistica_msg = f"{type(_erro_import_logistica).__name__}: {_erro_import_logistica}"
    def salvar_entregas_db(*args, **kwargs):
        raise RuntimeError(f"database_logistica.py não carregou corretamente: {_erro_import_logistica}")
    def dar_baixa_entrega_db(*args, **kwargs):
        return False, "Função de baixa indisponível — atualize o database.py/database_logistica.py."
    def obter_tickets_com_id_db(data_alvo):
        return obter_tickets_db(data_alvo)

# Import isolado: Rastreio ao Vivo (mapa em tempo real). Se qualquer peça
# faltar, a aba "📍 Ao Vivo" avisa, mas o resto do Rastreio (Dashboard,
# Exportar, Cadastros, baixa de entrega) continua 100% funcional.
try:
    from database import (iniciar_rastreio_live_db, obter_config_entrega_live_db,
                          geocodificar_endereco_db, desativar_rastreio_live_db)
    from modulo.mod_rastreio_live import renderizar_mapa_ao_vivo
    _RASTREIO_LIVE_OK = True
    _erro_rastreio_live_msg = ""
except Exception as _erro_rastreio_live:
    _RASTREIO_LIVE_OK = False
    _erro_rastreio_live_msg = f"{type(_erro_rastreio_live).__name__}: {_erro_rastreio_live}"

BRT = timezone(timedelta(hours=-3))

# URL base do motor_api.py no Render — troque pelo domínio real do seu
# serviço (Dashboard do Render → aparece no topo, ex:
# https://bancowendley-motor.onrender.com). É onde vive a página pública
# do CLIENTE (GET /rastreio/{ticket_id}, sem login) e o recebimento de GPS.
URL_BASE_MOTOR_API = "https://bancowendley.onrender.com"

# st.dialog disponível? (popup nativo). Senão, cai no st.popover.
_HAS_DIALOG = bool(getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None))

# Tempo de exibição de mensagens de sucesso/erro antes de recarregar a tela.
_PAUSA_TOAST = 0.5


# ── Helpers ────────────────────────────────────────────────────────
def _html(s: str) -> str:
    return "\n".join(linha.lstrip() for linha in s.splitlines())

def esc(v) -> str:
    return _h.escape(str(v if v is not None else ""))

def get_series(df, col, default=""):
    if col in df.columns: return df[col]
    return pd.Series([default]*len(df))

def formatar_data(v):
    if not v or str(v).strip() in ("","None","null"): return "—"
    try: return datetime.fromisoformat(str(v).strip().replace("+00:00","").replace("Z","")).strftime("%d/%m %H:%M")
    except: return str(v)[:16]

def extrair_chave(rota):
    if not rota: return "SEM_ROTA"
    return rota.split(" - ",1)[1].strip() if " - " in rota else rota.strip()

def _normalizar_placa(s) -> str:
    """Deixa só letras e números maiúsculos — 'PVC-7G92', 'pvc7g92' e
    'PVC 7G92' são reconhecidos como a mesma placa."""
    return re.sub(r'[^A-Z0-9]', '', str(s or '').upper())

def nome_motorista(rota):
    return obter_vinculo_db(extrair_chave(rota))

def garantir_colunas(df):
    if "_notificado" not in df.columns:
        df["_notificado"] = get_series(df,"on_its_way").apply(
            lambda x: bool(x and str(x).strip().lower() not in ("","none","null","false")))
    else:
        df["_notificado"] = df["_notificado"].apply(
            lambda x: x if isinstance(x,bool) else str(x).lower() not in ("false","0","none","null",""))
    df["_status_visual"] = df["_status_visual"].fillna("⏳ Pendente") \
        if "_status_visual" in df.columns else pd.Series(["⏳ Pendente"]*len(df))
    for col, val in {
        "title":"—","address":"—","route":"Rota não identificada",
        "contact_name":"—","contact_phone":"—","contact_email":"—",
        "tracking_id":"—","on_its_way":None,"checkout_time":None,"checkin_time":None,
        "estimated_time_arrival":"—","checkout_observation":"—","checkout_comment":"—",
        "notes":"—","planned_date":"—","order":"—","cliente_codigo":"—",
    }.items():
        if col not in df.columns: df[col] = val
    return df

def aplicar_busca(df, termo):
    if not termo.strip(): return df
    t = termo.strip().lower()
    mask = (
        get_series(df,"title").str.lower().str.contains(t,na=False) |
        get_series(df,"route").str.lower().str.contains(t,na=False) |
        get_series(df,"address").str.lower().str.contains(t,na=False) |
        get_series(df,"contact_name").str.lower().str.contains(t,na=False) |
        get_series(df,"contact_phone").str.lower().str.contains(t,na=False) |
        get_series(df,"tracking_id").str.lower().str.contains(t,na=False)
    )
    nome_mask = get_series(df,"route").apply(nome_motorista).str.lower().str.contains(t,na=False)
    return df[mask | nome_mask]


def _injetar_css():
    st.markdown(_html("""
    <style>
    .stApp { background-color: #f4f6f9; }
    div[class*="st-key-mtcard_"] button {
        text-align:left !important; justify-content:flex-start !important;
        background:#fff !important; border:1px solid #e2e8f0 !important;
        border-bottom:none !important; border-left:4px solid #C9A84C !important;
        border-radius:10px 10px 0 0 !important; color:#2c3e50 !important;
        font-weight:700 !important; font-size:0.92rem !important;
        padding:12px 14px 8px !important; margin-bottom:0 !important;
        transition:background .15s, box-shadow .15s; }
    div[class*="st-key-mtcard_"] button:hover {
        background:#eef4ff !important; border-color:#C9A84C !important; }
    .mt-cardbody { background:#fff; border:1px solid #e2e8f0; border-top:none;
        border-left:4px solid #C9A84C; border-radius:0 0 10px 10px;
        padding:4px 14px 12px; margin:-10px 0 12px; }
    .mt-rota { font-size:0.71rem; color:#7f8c8d; margin-bottom:6px; }
    .mt-bar { background:#e8ecf0; border-radius:4px; height:6px; margin:6px 0 3px; }
    .mt-bar > div { background:#2980b9; height:6px; border-radius:4px; }
    .mt-prog { font-size:0.7rem; color:#64778d; margin-bottom:7px; }
    .kpi-card { background:#fff; border-radius:12px; padding:18px 12px;
        text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); }
    .kpi-card.gold  { border-top:4px solid #C9A84C; }
    .kpi-card.green { border-top:4px solid #27ae60; }
    .kpi-card.blue  { border-top:4px solid #2980b9; }
    .kpi-card.red   { border-top:4px solid #e74c3c; }
    .kpi-card.gray  { border-top:4px solid #95a5a6; }
    .kpi-label { color:#64778d; font-size:0.72rem; font-weight:700;
        text-transform:uppercase; letter-spacing:1px; }
    .kpi-value { font-size:2rem; font-weight:800; color:#2c3e50; line-height:1.2; margin:4px 0 2px; }
    .kpi-sub { font-size:0.78rem; font-weight:600; color:#C9A84C; }
    .driver-card { background:#fff; border:1px solid #e2e8f0; border-radius:12px;
        padding:14px; margin-bottom:6px; border-top:4px solid #C9A84C; }
    .tag { display:inline-block; padding:3px 9px; border-radius:10px;
        font-size:0.73rem; font-weight:700; margin:2px; }
    .tg { background:rgba(201,168,76,.12); color:#7a5f1a; }
    .tn { background:rgba(46,204,113,.1);  color:#1e8449; }
    .tb { background:rgba(52,152,219,.1);  color:#2471a3; }
    .tr { background:rgba(231,76,60,.1);   color:#a93226; }
    </style>
    """), unsafe_allow_html=True)


def _stats_rota(df, rota):
    dr   = df[df["route"] == rota]
    tot  = len(dr)
    ok   = int((dr["_status_visual"] == "✅ Sucesso").sum())
    fail = int((dr["_status_visual"] == "❌ Falhou").sum())
    nt   = int(dr["_notificado"].sum())
    pct_n = round(nt/tot*100, 1) if tot else 0
    pct_o = round(ok/tot*100) if tot else 0
    return dr, tot, ok, fail, nt, pct_n, pct_o


def _body_html(rota, tot, ok, fail, nt, pct_n, pct_o):
    return _html(f"""
    <div class="mt-cardbody">
        <div class="mt-rota">{esc(rota)}</div>
        <div class="mt-bar"><div style="width:{pct_o}%;"></div></div>
        <div class="mt-prog">{ok}/{tot} ({pct_o}%)</div>
        <div>
            <span class="tag tn">📱 {nt} ({pct_n}%)</span>
            <span class="tag tg">📦 {tot}</span>
            <span class="tag tb">✅ {ok}</span>
            <span class="tag tr">❌ {fail}</span>
        </div>
    </div>""")


def _conteudo_motorista(rota, df, data_consulta, user):
    dr, tot, ok, fail, nt, pct_n, pct_o = _stats_rota(df, rota)
    nome = nome_motorista(rota)
    ch   = extrair_chave(rota)

    st.markdown(_html(f"""
    <div style="background:#fff;border-left:6px solid #C9A84C;border-radius:10px;
                padding:14px;margin-bottom:12px;border:1px solid #e2e8f0;">
        <h3 style="margin:0;color:#2c3e50;">{esc(nome)}</h3>
        <p style="color:#64778d;font-size:0.8rem;margin:3px 0 10px;">{esc(rota)}</p>
        <span class="tag tg">📦 {tot}</span>
        <span class="tag tn">📱 {nt}</span>
        <span class="tag tb">✅ {ok}</span>
        <span class="tag tr">❌ {fail}</span>
        <div style="background:#e8ecf0;border-radius:4px;height:6px;margin:10px 0 3px;">
            <div style="background:#2980b9;height:6px;border-radius:4px;width:{pct_o}%;"></div>
        </div>
        <span style="font-size:0.73rem;color:#64778d;">{ok}/{tot} concluídas ({pct_o}%)</span>
    </div>"""), unsafe_allow_html=True)

    if pode_editar(user):
        nn = st.text_input("Nome do condutor:", value=nome, key=f"nm_{ch}")
        if st.button("💾 Salvar nome", key=f"svnm_{ch}", type="primary"):
            salvar_vinculo_db(ch, nn.strip())
            st.success("Salvo!"); time.sleep(_PAUSA_TOAST); st.rerun()
    else:
        st.caption("🔒 Edição restrita.")

    if pode_deletar(user):
        if st.checkbox("Liberar exclusão desta rota", key=f"chk_{ch}"):
            if st.button("🗑️ Excluir Rota", key=f"delr_{ch}"):
                try:
                    deletar_rota_db(rota, data_consulta)
                    st.success("Excluído!"); time.sleep(_PAUSA_TOAST); st.rerun()
                except Exception as e:
                    st.error("⚠️ Não consegui excluir. Detalhe técnico abaixo:")
                    st.code(f"{type(e).__name__}: {e}", language="text")
                    st.caption(
                        "Se a mensagem acima mencionar 'requires an index', abra o link "
                        "que vem junto dela, clique em 'Criar índice' no Firebase, espere "
                        "1-2 minutos ficar 'Ativado' e tente excluir de novo."
                    )

    abas = st.tabs(["📋 Fila de Clientes", "⚠️ Ocorrências", "📱 Notificados"])

    with abas[0]:
        st.dataframe(pd.DataFrame({
            "Ordem":    get_series(dr,"order"),
            "Cliente":  get_series(dr,"title"),
            "Endereço": get_series(dr,"address"),
            "Status":   dr["_status_visual"],
            "Notif.":   dr["_notificado"].apply(lambda x:"Sim" if x else "Não"),
            "Check-in": get_series(dr,"checkin_time").apply(formatar_data),
            "Check-out":get_series(dr,"checkout_time").apply(formatar_data),
            "Telefone": get_series(dr,"contact_phone"),
            "Obs":      get_series(dr,"checkout_observation"),
        }), use_container_width=True, hide_index=True)

    with abas[1]:
        df_err = dr[dr["_status_visual"] == "❌ Falhou"]
        if df_err.empty:
            st.success("Nenhuma ocorrência.")
        else:
            st.dataframe(pd.DataFrame({
                "Ordem":  get_series(df_err,"order"),
                "Cliente":get_series(df_err,"title"),
                "Motivo": get_series(df_err,"checkout_observation"),
                "Horário":get_series(df_err,"checkout_time").apply(formatar_data),
            }), use_container_width=True, hide_index=True)

    with abas[2]:
        df_n = dr[dr["_notificado"] == True]
        if df_n.empty:
            st.info("Nenhum notificado ainda.")
        else:
            for _, row in df_n.iterrows():
                st.markdown(
                    f"**#{esc(row.get('order','—'))} · {esc(row.get('title','—'))}**  \n"
                    f"<span style='font-size:0.8rem;color:#64778d;'>📍 {esc(row.get('address','—'))}</span>",
                    unsafe_allow_html=True)
                st.markdown("<hr style='margin:6px 0;border:none;border-top:1px solid #eee;'>",
                            unsafe_allow_html=True)


def _abrir_popup_motorista(rota, df, data_consulta, user):
    deco = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if deco is None:
        return
    titulo = f"🧑 {nome_motorista(rota)}"
    try:
        @deco(titulo, width="large")
        def _p(): _conteudo_motorista(rota, df, data_consulta, user)
        _p()
    except TypeError:
        @deco(titulo)
        def _p2(): _conteudo_motorista(rota, df, data_consulta, user)
        _p2()


def _card_motorista(rota, df, idx, ctx, data_consulta, user):
    dr, tot, ok, fail, nt, pct_n, pct_o = _stats_rota(df, rota)
    nome = nome_motorista(rota)
    body = _body_html(rota, tot, ok, fail, nt, pct_n, pct_o)

    if _HAS_DIALOG:
        if st.button(f"🧑 {nome}", key=f"mtcard_{ctx}_{idx}", use_container_width=True):
            _abrir_popup_motorista(rota, df, data_consulta, user)
        st.markdown(body, unsafe_allow_html=True)
    else:
        st.markdown(_html(f'<div style="font-weight:700;color:#2c3e50;'
                          f'padding:4px 0 2px;">🧑 {esc(nome)}</div>'), unsafe_allow_html=True)
        st.markdown(body, unsafe_allow_html=True)
        with st.popover(f"🔍 Abrir {nome}", use_container_width=True):
            _conteudo_motorista(rota, df, data_consulta, user)


# ── ABA: Cadastros & Upload (só Admin) ──────────────────────────────
def _aba_cadastros(datas_db):
    if not _LOGISTICA_OK:
        st.error(
            "⚠️ O módulo de importação de planilha está indisponível no momento. "
            "O Dashboard e a Exportação continuam funcionando normalmente."
        )
        st.code(str(_erro_import_logistica_msg), language="text")
        return

    try:
        st.markdown("### 📤 Importar Planilha de Entregas")
        st.caption("Envie a planilha já roteirizada (uma linha por entrega, com a coluna do motorista).")

        todos_usuarios = listar_usuarios()
        motoristas = [u for u in todos_usuarios if u.get("role") == "motorista"]

        if not motoristas:
            st.warning("⚠️ Cadastre pelo menos um motorista na seção abaixo antes de importar.")
        else:
            arquivo = st.file_uploader("Planilha (.xlsx ou .csv)", type=["xlsx", "csv"], key="upl_entregas")
            data_entrega = st.date_input(
                "Data das entregas", value=datetime.now(BRT).date(), key="data_upl"
            )

            if arquivo is not None:
                try:
                    df_up = (pd.read_csv(arquivo) if arquivo.name.lower().endswith(".csv")
                              else pd.read_excel(arquivo))
                except Exception as e:
                    st.error(f"Não consegui ler o arquivo: {e}")
                    df_up = None

                if df_up is not None and not df_up.empty:
                    st.dataframe(df_up.head(10), use_container_width=True, hide_index=True)
                    colunas = list(df_up.columns)

                    st.markdown("**Mapeamento de colunas** — diga qual coluna da planilha é qual campo:")
                    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                    col_cliente  = mc1.selectbox("Cliente", colunas, key="map_cliente")
                    col_endereco = mc2.selectbox("Endereço", colunas, key="map_endereco")
                    col_telefone = mc3.selectbox("Telefone (opcional)", ["—"] + colunas, key="map_telefone")
                    col_ordem    = mc4.selectbox("Ordem (opcional)", ["—"] + colunas, key="map_ordem")
                    col_codigo   = mc5.selectbox("Código do cliente (opcional)", ["—"] + colunas, key="map_codigo")

                    opcoes_mot = {f"{m['nome']} ({m['usuario']})": m["usuario"] for m in motoristas}

                    st.markdown("---")
                    modo_atrib = st.radio(
                        "Como identificar o motorista de cada entrega?",
                        ["🚗 Por placa/veículo (a planilha tem várias rotas/motoristas juntos)",
                         "👤 Um único motorista para toda a planilha"],
                        key="modo_atrib_upload",
                    )

                    login_por_linha = None
                    login_unico = None
                    pronto_para_importar = True

                    if modo_atrib.startswith("🚗"):
                        col_placa = st.selectbox("Coluna com a placa/veículo", colunas, key="map_placa")

                        placas_cadastradas = {}
                        for m in motoristas:
                            p = _normalizar_placa(m.get("placa", ""))
                            if p:
                                placas_cadastradas[p] = m["usuario"]

                        placas_planilha = sorted({
                            str(v).strip() for v in df_up[col_placa].dropna().unique() if str(v).strip()
                        })

                        mapa_placa_login = {}
                        nao_identificadas = []

                        for placa_orig in placas_planilha:
                            placa_norm = _normalizar_placa(placa_orig)
                            login_auto = placas_cadastradas.get(placa_norm)
                            if login_auto:
                                mapa_placa_login[placa_norm] = login_auto
                            else:
                                nao_identificadas.append(placa_orig)

                        st.markdown(
                            f"🔎 **{len(placas_planilha)}** placa(s) na planilha · "
                            f"✅ **{len(placas_planilha) - len(nao_identificadas)}** identificada(s) automaticamente · "
                            f"⚠️ **{len(nao_identificadas)}** precisam de atribuição manual"
                        )

                        if mapa_placa_login:
                            with st.expander("✅ Placas identificadas automaticamente", expanded=False):
                                for placa_norm, login in mapa_placa_login.items():
                                    nome_m = next((m["nome"] for m in motoristas if m["usuario"] == login), login)
                                    st.caption(f"`{placa_norm}` → {nome_m} ({login})")

                        if nao_identificadas:
                            st.markdown("**⚠️ Atribua manualmente as placas não identificadas:**")
                            for placa_orig in nao_identificadas:
                                escolha_manual = st.selectbox(
                                    f"Placa `{placa_orig}` pertence a:",
                                    ["— Selecione —"] + list(opcoes_mot.keys()),
                                    key=f"map_placa_manual_{_normalizar_placa(placa_orig)}",
                                )
                                if escolha_manual != "— Selecione —":
                                    mapa_placa_login[_normalizar_placa(placa_orig)] = opcoes_mot[escolha_manual]
                                else:
                                    pronto_para_importar = False

                        login_por_linha = lambda valor_placa: mapa_placa_login.get(_normalizar_placa(valor_placa))

                    else:
                        escolha_mot = st.selectbox(
                            "Todas as linhas desta planilha pertencem a qual motorista?",
                            list(opcoes_mot.keys()), key="map_motorista",
                        )
                        login_unico = opcoes_mot[escolha_mot]

                    if not pronto_para_importar:
                        st.warning("Atribua um motorista para TODAS as placas não identificadas antes de importar.")

                    if st.button("📥 Importar", type="primary", key="btn_importar_planilha",
                                 disabled=not pronto_para_importar):
                        try:
                            data_str = data_entrega.isoformat()
                            entregas = []
                            sem_motorista = 0

                            for i, row in df_up.iterrows():
                                if login_por_linha is not None:
                                    login_linha = login_por_linha(row.get(col_placa, ""))
                                else:
                                    login_linha = login_unico

                                if not login_linha:
                                    sem_motorista += 1
                                    continue

                                entregas.append({
                                    "route": f"Rota - {login_linha}",
                                    "title": str(row.get(col_cliente, "—")),
                                    "address": str(row.get(col_endereco, "—")),
                                    "contact_phone": str(row.get(col_telefone, "—")) if col_telefone != "—" else "—",
                                    "order": row.get(col_ordem, i + 1) if col_ordem != "—" else i + 1,
                                    "cliente_codigo": str(row.get(col_codigo, "—")) if col_codigo != "—" else "—",
                                    "planned_date": data_str,
                                })

                            qtd = salvar_entregas_db(entregas, data_str)
                            msg_extra = f" ({sem_motorista} linha(s) pulada(s) sem motorista)" if sem_motorista else ""
                            st.success(f"✅ {qtd} entregas importadas para {data_str}{msg_extra}.")
                            time.sleep(_PAUSA_TOAST)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Não consegui importar a planilha: {e}")

        st.markdown("---")
        st.markdown("### 🧑‍✈️ Cadastrar Motorista")
        with st.form("form_novo_motorista"):
            c1, c2 = st.columns(2)
            nm_nome  = c1.text_input("Nome completo")
            nm_login = c2.text_input("Login", help="Dica: evite espaços.")
            c3, c4 = st.columns(2)
            nm_senha = c3.text_input("Senha", type="password")
            nm_placa = c4.text_input("Placa do veículo", placeholder="Ex: ABC1D23")
            if st.form_submit_button("Criar motorista"):
                if not (nm_nome and nm_login and nm_senha):
                    st.warning("Preencha nome, login e senha.")
                else:
                    try:
                        login_final = criar_usuario(nm_nome, nm_login, nm_senha, role="motorista", placa=nm_placa)
                        salvar_vinculo_db(login_final, nm_nome)
                        st.success(f"Motorista **{nm_nome}** cadastrado! Login para ele usar: `{login_final}`")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Não consegui cadastrar o motorista: {e}")

        st.markdown("---")
        st.markdown("### 📋 Motoristas Cadastrados")
        motoristas = [u for u in listar_usuarios() if u.get("role") == "motorista"]
        if not motoristas:
            st.caption("Nenhum motorista cadastrado ainda.")
        else:
            for m in motoristas:
                login_m = m.get("usuario", "—")
                exp_key = f"exp_aberto_mot_{login_m}"
                with st.expander(
                    f"🧑‍✈️ **{m.get('nome','—')}** · `{login_m}` · placa {m.get('placa') or '—'}",
                    expanded=st.session_state.get(exp_key, False),
                ):
                    st.markdown("**✏️ Editar dados**")
                    ec1, ec2 = st.columns(2)
                    novo_nome  = ec1.text_input("Nome", value=m.get("nome", ""), key=f"ed_nome_{login_m}")
                    nova_placa = ec2.text_input("Placa", value=m.get("placa", ""), key=f"ed_placa_{login_m}")
                    if st.button("💾 Salvar dados", key=f"ed_salvar_{login_m}"):
                        try:
                            atualizar_dados_usuario(login_m, nome=novo_nome, placa=nova_placa)
                            salvar_vinculo_db(login_m, novo_nome)
                            st.session_state[exp_key] = True
                            st.success("Dados atualizados!")
                            time.sleep(_PAUSA_TOAST)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Não consegui salvar: {e}")

                    st.markdown("---")
                    st.markdown("**🔑 Redefinir senha**")
                    sc1, sc2 = st.columns([3, 1])
                    nova_senha = sc1.text_input(
                        "Nova senha", type="password", key=f"ed_senha_{login_m}",
                        label_visibility="collapsed", placeholder="Nova senha (mín. 6 caracteres)"
                    )
                    if sc2.button("Redefinir", key=f"ed_btn_senha_{login_m}", use_container_width=True):
                        if not nova_senha or len(nova_senha) < 6:
                            st.warning("A senha deve ter pelo menos 6 caracteres.")
                        else:
                            ok, msg = redefinir_senha_usuario(login_m, nova_senha)
                            st.session_state[exp_key] = True
                            (st.success if ok else st.error)(msg)
                            if ok:
                                time.sleep(_PAUSA_TOAST)
                                st.rerun()

                    st.markdown("---")
                    if st.checkbox("Liberar exclusão deste motorista", key=f"ed_chk_del_{login_m}"):
                        if st.button("🗑️ Excluir motorista", key=f"ed_del_{login_m}"):
                            deletar_usuario(login_m)
                            st.session_state.pop(exp_key, None)
                            st.success("Motorista excluído.")
                            time.sleep(_PAUSA_TOAST)
                            st.rerun()

    except Exception as e:
        st.error(f"⚠️ A aba de Cadastros encontrou um erro e foi interrompida, "
                 f"mas o restante do Rastreio continua funcionando. Detalhe: {e}")


# ── ABA: Rastreio ao Vivo ────────────────────────────────────────────
def _aba_rastreio_ao_vivo(df_dia, data_consulta, user):
    if not _RASTREIO_LIVE_OK:
        st.error(
            "⚠️ O Rastreio ao Vivo está indisponível no momento — faltam as "
            "funções novas no seu database.py ou o arquivo modulo/mod_rastreio_live.py."
        )
        with st.expander("Detalhe técnico"):
            st.code(_erro_rastreio_live_msg, language="text")
        return

    motoristas = [u for u in listar_usuarios() if u.get("role") == "motorista"]

    if pode_editar(user):
        sem_entregas = df_dia is None or df_dia.empty
        with st.expander("🧪 Criar entrega de teste", expanded=sem_entregas):
            st.caption(
                "Cria uma entrega avulsa na data selecionada, só pra você testar o "
                "rastreio ao vivo sem precisar montar planilha nenhuma."
            )
            if not motoristas:
                st.warning("⚠️ Cadastre pelo menos um motorista na aba **🧑‍✈️ Cadastros** antes.")
            elif not _LOGISTICA_OK:
                st.warning("⚠️ A criação de entregas depende do database_logistica.py, indisponível agora.")
            else:
                with st.form("form_entrega_teste"):
                    tc1, tc2 = st.columns(2)
                    opcoes_mot = {f"{m['nome']} ({m['usuario']})": m["usuario"] for m in motoristas}
                    escolha_mot = tc1.selectbox("Motorista", list(opcoes_mot.keys()), key="teste_live_motorista")
                    teste_cliente = tc2.text_input("Nome do cliente", value="Cliente Teste", key="teste_live_cliente")
                    teste_endereco = st.text_input(
                        "Endereço completo (rua, número, bairro, cidade)",
                        placeholder="Ex: Avenida Paulista 1000, Bela Vista, São Paulo, SP",
                        key="teste_live_endereco",
                    )
                    teste_telefone = st.text_input(
                        "Telefone do cliente (com DDI, ex: +5511999998888)", key="teste_live_telefone",
                    )
                    if st.form_submit_button("Criar entrega de teste", type="primary"):
                        if not teste_endereco.strip():
                            st.warning("Informe um endereço — é a partir dele que o destino é localizado no mapa.")
                        else:
                            login_mot = opcoes_mot[escolha_mot]
                            entrega_teste = [{
                                "route": f"Rota - {login_mot}",
                                "title": teste_cliente.strip() or "Cliente Teste",
                                "address": teste_endereco.strip(),
                                "contact_phone": teste_telefone.strip() or "—",
                                "order": 1,
                                "cliente_codigo": "TESTE",
                                "planned_date": data_consulta,
                            }]
                            try:
                                salvar_entregas_db(entrega_teste, data_consulta)
                                st.success("✅ Entrega de teste criada! Selecione-a abaixo para ativar o rastreio.")
                                time.sleep(_PAUSA_TOAST)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Não consegui criar a entrega de teste: {e}")

    st.markdown("---")

    if df_dia is None or df_dia.empty or "_doc_id" not in df_dia.columns:
        st.info(
            "⏳ Nenhuma entrega com identificador disponível para rastrear ainda. "
            "Crie uma entrega de teste acima, ou importe uma planilha em 🧑‍✈️ Cadastros."
        )
        return

    candidatas = df_dia[df_dia["_doc_id"].notna() & (df_dia["_doc_id"] != "")]
    if candidatas.empty:
        st.info("⏳ Nenhuma entrega com identificador disponível para rastrear ainda.")
        return

    opcoes = {
        f"#{row.get('order','—')} · {row.get('title','—')} · {nome_motorista(row.get('route',''))}": row.get("_doc_id")
        for _, row in candidatas.iterrows()
    }
    escolha_label = st.selectbox("📦 Selecione a entrega para acompanhar", list(opcoes.keys()), key="sel_live_global")
    ticket_id = opcoes[escolha_label]
    linha = candidatas[candidatas["_doc_id"] == ticket_id].iloc[0]

    config = obter_config_entrega_live_db(ticket_id)

    if config:
        renderizar_mapa_ao_vivo(ticket_id)

        link_cliente = f"{URL_BASE_MOTOR_API}/rastreio/{ticket_id}"
        st.caption("📍 Link EXCLUSIVO para o CLIENTE acompanhar esta entrega (sem login, mande por WhatsApp):")
        st.code(link_cliente, language=None)

        if pode_editar(user):
            if st.button("🛑 Encerrar rastreio ao vivo desta entrega", key=f"desativar_live_{ticket_id}"):
                desativar_rastreio_live_db(ticket_id)
                st.success("Rastreio ao vivo encerrado.")
                time.sleep(_PAUSA_TOAST)
                st.rerun()
        return

    if not pode_editar(user):
        st.info("Esta entrega ainda não tem rastreio ao vivo ativado. Peça ao admin para ativar.")
        return

    endereco = str(linha.get("address", "") or "")
    telefone = str(linha.get("contact_phone", "") or "")
    st.caption(f"Endereço da entrega: {endereco or '—'}")

    usar_manual_key = f"live_manual_{ticket_id}"
    if st.button("📍 Ativar rastreio ao vivo", key=f"ativar_live_{ticket_id}"):
        lat, lng = geocodificar_endereco_db(endereco)
        if lat is None:
            st.session_state[usar_manual_key] = True
        else:
            iniciar_rastreio_live_db(ticket_id, lat, lng, telefone)
            st.success("Rastreio ao vivo ativado! O link do cliente já aparece acima.")
            time.sleep(_PAUSA_TOAST)
            st.rerun()

    if st.session_state.get(usar_manual_key):
        st.warning("Não consegui localizar esse endereço automaticamente. Informe lat/lng manualmente:")
        mc1, mc2 = st.columns(2)
        lat_manual = mc1.number_input("Latitude", format="%.6f", key=f"lat_manual_{ticket_id}")
        lng_manual = mc2.number_input("Longitude", format="%.6f", key=f"lng_manual_{ticket_id}")
        if st.button("Confirmar coordenadas e ativar", key=f"confirmar_manual_{ticket_id}"):
            if lat_manual == 0 and lng_manual == 0:
                st.warning("Informe coordenadas válidas antes de confirmar.")
            else:
                iniciar_rastreio_live_db(ticket_id, lat_manual, lng_manual, telefone)
                st.session_state.pop(usar_manual_key, None)
                st.success("Rastreio ao vivo ativado com coordenadas manuais!")
                time.sleep(_PAUSA_TOAST)
                st.rerun()


# ── VISÃO EXCLUSIVA DO MOTORISTA ─────────────────────────────────────
def _visualizacao_motorista(user):
    hoje = datetime.now(BRT).date().isoformat()
    minha_chave = user.get("usuario", "")

    tickets_raw = obter_tickets_com_id_db(hoje) if _LOGISTICA_OK else obter_tickets_db(hoje)
    df = pd.DataFrame(tickets_raw) if tickets_raw else pd.DataFrame()

    if df.empty:
        st.info("⏳ Nenhuma entrega para hoje.")
        return

    df = garantir_colunas(df.copy())
    if "route" in df.columns:
        df = df[df["route"].apply(extrair_chave) == minha_chave]

    if df.empty:
        st.info("⏳ Nenhuma entrega atribuída a você hoje.")
        return

    total  = len(df)
    concl  = int((df["_status_visual"] == "✅ Sucesso").sum())
    falhas = int((df["_status_visual"] == "❌ Falhou").sum())
    pend   = total - concl - falhas

    if "motorista_kpi_filtro" not in st.session_state:
        st.session_state.motorista_kpi_filtro = "todos"
    filtro = st.session_state.motorista_kpi_filtro

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        if st.button(f"📦 Total\n{total}", key="kpi_mot_total", use_container_width=True,
                     type="primary" if filtro == "todos" else "secondary"):
            st.session_state.motorista_kpi_filtro = "todos"; st.rerun()
    with k2:
        if st.button(f"✅ Feitas\n{concl}", key="kpi_mot_feitas", use_container_width=True,
                     type="primary" if filtro == "feitas" else "secondary"):
            st.session_state.motorista_kpi_filtro = "feitas"; st.rerun()
    with k3:
        if st.button(f"⏳ Pendentes\n{pend}", key="kpi_mot_pendentes", use_container_width=True,
                     type="primary" if filtro == "pendentes" else "secondary"):
            st.session_state.motorista_kpi_filtro = "pendentes"; st.rerun()
    with k4:
        if st.button(f"❌ Falhas\n{falhas}", key="kpi_mot_falhas", use_container_width=True,
                     type="primary" if filtro == "falhas" else "secondary"):
            st.session_state.motorista_kpi_filtro = "falhas"; st.rerun()

    if not _LOGISTICA_OK:
        st.warning("⚠️ A confirmação de entrega com foto está indisponível no momento.")

    if filtro == "feitas":
        df_lista = df[df["_status_visual"] == "✅ Sucesso"]
    elif filtro == "pendentes":
        df_lista = df[df["_status_visual"] == "⏳ Pendente"]
    elif filtro == "falhas":
        df_lista = df[df["_status_visual"] == "❌ Falhou"]
    else:
        df_lista = df

    try:
        df_lista = df_lista.sort_values(by="order", key=lambda s: pd.to_numeric(s, errors="coerce"))
    except Exception:
        pass

    if df_lista.empty:
        st.info("Nenhuma entrega nesse filtro.")

    for _, row in df_lista.iterrows():
        status = row.get("_status_visual", "⏳ Pendente")
        cor = {"✅ Sucesso": "tb", "❌ Falhou": "tr"}.get(status, "tg")
        doc_id = row.get("_doc_id")

        st.markdown(_html(f"""
        <div class="driver-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
                <div style="font-weight:700;color:#2c3e50;">#{esc(row.get('order','—'))} · {esc(row.get('title','—'))}</div>
                <span class="tag {cor}">{esc(status)}</span>
            </div>
            <div style="font-size:0.82rem;color:#64778d;margin-top:4px;">📍 {esc(row.get('address','—'))}</div>
            <div style="font-size:0.82rem;color:#64778d;">📞 {esc(row.get('contact_phone','—'))}</div>
        </div>
        """), unsafe_allow_html=True)

        if status == "⏳ Pendente":
            if not (_LOGISTICA_OK and doc_id):
                st.caption("⚠️ Não é possível dar baixa nesta entrega agora.")
            else:
                with st.popover(f"📸 Dar baixa — #{row.get('order','—')}", use_container_width=True):
                    st.caption("A foto é opcional — se quiser, tire uma no ato da entrega.")
                    foto = st.camera_input("Tirar foto (opcional)", key=f"foto_{doc_id}")
                    resultado = st.radio(
                        "Resultado da entrega", ["✅ Sucesso", "❌ Falha"],
                        key=f"result_{doc_id}", horizontal=True,
                    )
                    motivo = ""
                    if resultado == "❌ Falha":
                        motivo = st.text_input(
                            "Motivo da falha *", key=f"motivo_{doc_id}",
                            placeholder="Ex: Cliente ausente, endereço não encontrado...",
                        )
                    if st.button("Confirmar baixa", key=f"confirmar_{doc_id}",
                                 type="primary", use_container_width=True):
                        if resultado == "❌ Falha" and not motivo.strip():
                            st.warning("Descreva o motivo da falha antes de confirmar.")
                        else:
                            status_db = "sucesso" if resultado == "✅ Sucesso" else "falha"
                            foto_bytes = foto.getvalue() if foto is not None else None
                            ok, msg = dar_baixa_entrega_db(doc_id, status_db, foto_bytes, motivo)
                            (st.success if ok else st.error)(msg)
                            if ok:
                                if _RASTREIO_LIVE_OK and doc_id:
                                    try:
                                        desativar_rastreio_live_db(doc_id)
                                    except Exception:
                                        pass
                                time.sleep(_PAUSA_TOAST)
                                st.rerun()


# ── FUNÇÃO PRINCIPAL ──────────────────────────────────────────────
def renderizar_rastreio(papel: str, user: dict = None,
                        datas_db: list = None, pode_exp: bool = False):
    if user is None: user = {"role": papel}
    if datas_db is None: datas_db = []

    _injetar_css()

    if papel == "motorista":
        _visualizacao_motorista(user)
        return True

    hoje  = datetime.now(BRT).date().isoformat()
    ontem = (datetime.now(BRT).date() - timedelta(days=1)).isoformat()
    datas_disp = [d["data"] for d in datas_db]

    fc1, fc2, fc3, fc4 = st.columns([2, 2, 1.5, 1.5])
    with fc1:
        opcoes = []
        if hoje in datas_disp or not datas_disp: opcoes.append(f"Hoje ({hoje})")
        if ontem in datas_disp: opcoes.append(f"Ontem ({ontem})")
        for item in datas_db:
            if item["data"] not in (hoje, ontem):
                try:    opcoes.append(f"{datetime.strptime(item['data'],'%Y-%m-%d').strftime('%d/%m/%Y')} — {item['total']}")
                except: opcoes.append(item["data"])
        if not opcoes: opcoes = [f"Hoje ({hoje})"]
        data_sel = st.selectbox("📅 Período", opcoes, label_visibility="visible", key="data_sel_rastreio")

    with fc2:
        termo = st.text_input("🔍 Buscar", placeholder="Placa, motorista, cliente, telefone...",
                              label_visibility="visible", key="busca_rastreio")
    with fc3:
        f_st = st.selectbox("Status", ["Todos","✅ Sucesso","❌ Falhou","📱 Notificado","⏳ Pendente"],
                            label_visibility="visible", key="f_status")
    with fc4:
        f_nt = st.selectbox("Notificação", ["Todas","Sim","Não"],
                            label_visibility="visible", key="f_notif")

    if   "Hoje"  in data_sel: data_consulta = hoje
    elif "Ontem" in data_sel: data_consulta = ontem
    else:
        try:    data_consulta = datetime.strptime(data_sel.split("—")[0].strip(),"%d/%m/%Y").strftime("%Y-%m-%d")
        except: data_consulta = hoje
    is_hoje = (data_consulta == hoje)

    tickets_raw = obter_tickets_com_id_db(data_consulta) if _LOGISTICA_OK else obter_tickets_db(data_consulta)
    df = pd.DataFrame(tickets_raw) if tickets_raw else pd.DataFrame()
    sem_dados_no_dia = df.empty

    if not sem_dados_no_dia:
        df = garantir_colunas(df.copy())
        df_f = aplicar_busca(df, termo)
        if f_st != "Todos":  df_f = df_f[df_f["_status_visual"] == f_st]
        if f_nt == "Sim":    df_f = df_f[df_f["_notificado"] == True]
        elif f_nt == "Não":  df_f = df_f[df_f["_notificado"] == False]
        if termo and df_f.empty:
            st.warning(f"Nenhum resultado para **{termo}**."); return is_hoje
    else:
        df_f = df

    abas_nomes = ["🏠 Dashboard"]
    if pode_exp: abas_nomes.append("📥 Exportar")
    abas_nomes.append("📍 Ao Vivo")
    idx_ao_vivo = len(abas_nomes) - 1
    mostra_cadastros = pode_editar(user)
    if mostra_cadastros:
        abas_nomes.append("🧑‍✈️ Cadastros")
    abas = st.tabs(abas_nomes)

    with abas[0]:
        if sem_dados_no_dia:
            st.info("⏳ Nenhum dado de entrega para o dia selecionado.")
            st.caption("Use a aba **📍 Ao Vivo** para criar uma entrega de teste, "
                       "ou a aba **🧑‍✈️ Cadastros** para importar uma planilha real.")
        else:
            total    = len(df)
            notif    = int(df["_notificado"].sum())
            sucesso  = int((df["_status_visual"]=="✅ Sucesso").sum())
            falhou   = int((df["_status_visual"]=="❌ Falhou").sum())
            pendente = total - sucesso - falhou
            motores  = len([r for r in df["route"].unique()
                            if r and "não identificada" not in str(r).lower()])

            k1,k2,k3,k4,k5,k6 = st.columns(6)
            k1.markdown(f'<div class="kpi-card gold"><div class="kpi-label">📦 Total</div><div class="kpi-value">{total}</div><div class="kpi-sub">Carga do dia</div></div>',unsafe_allow_html=True)
            k2.markdown(f'<div class="kpi-card green"><div class="kpi-label">📱 Notificados</div><div class="kpi-value">{notif}</div><div class="kpi-sub">{round(notif/total*100,1) if total else 0}%</div></div>',unsafe_allow_html=True)
            k3.markdown(f'<div class="kpi-card blue"><div class="kpi-label">✅ Sucessos</div><div class="kpi-value">{sucesso}</div><div class="kpi-sub">{round(sucesso/total*100,1) if total else 0}%</div></div>',unsafe_allow_html=True)
            k4.markdown(f'<div class="kpi-card red"><div class="kpi-label">❌ Falhas</div><div class="kpi-value">{falhou}</div><div class="kpi-sub">{round(falhou/total*100,1) if total else 0}%</div></div>',unsafe_allow_html=True)
            k5.markdown(f'<div class="kpi-card gray"><div class="kpi-label">⏳ Pendentes</div><div class="kpi-value">{pendente}</div><div class="kpi-sub">Na rua</div></div>',unsafe_allow_html=True)
            k6.markdown(f'<div class="kpi-card gold"><div class="kpi-label">🧑 Motoristas</div><div class="kpi-value">{motores}</div><div class="kpi-sub">Em operação</div></div>',unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if termo: st.info(f"🔍 {len(df_f)} resultado(s) para **{termo}**")

            rotas = [r for r in sorted(df_f["route"].unique())
                     if r and "não identificada" not in str(r).lower()] if "route" in df_f.columns else []
            if rotas:
                st.markdown("### 🧑 Motoristas em Operação")
                st.caption("Clique no nome do motorista para abrir os detalhes.")
                cols = st.columns(min(len(rotas), 4))
                for idx, rota in enumerate(rotas):
                    with cols[idx % 4]:
                        _card_motorista(rota, df_f, idx, "dash", data_consulta, user)

            st.markdown("---")
            st.markdown(f"**{len(df_f)} entregas**")
            st.dataframe(pd.DataFrame({
                "Ordem":    get_series(df_f,"order"),
                "Motorista":get_series(df_f,"route").apply(nome_motorista),
                "Cliente":  get_series(df_f,"title"),
                "Endereço": get_series(df_f,"address"),
                "Status":   df_f["_status_visual"],
                "Notif.":   df_f["_notificado"].apply(lambda x:"Sim" if x else "Não"),
                "Check-out":get_series(df_f,"checkout_time").apply(formatar_data),
                "Telefone": get_series(df_f,"contact_phone"),
            }), use_container_width=True, hide_index=True)

    if pode_exp:
        with abas[1]:
            if sem_dados_no_dia:
                st.info("⏳ Nenhum dado de entrega para exportar neste dia.")
            else:
                st.markdown("### 💾 Exportação de Dados")

                def montar(df_src):
                    return pd.DataFrame({
                        "Ordem":      get_series(df_src,"order"),
                        "Motorista":  get_series(df_src,"route").apply(nome_motorista),
                        "Cliente":    get_series(df_src,"title"),
                        "Endereço":   get_series(df_src,"address"),
                        "Status":     get_series(df_src,"_status_visual","⏳ Pendente"),
                        "Notificado": get_series(df_src,"_notificado").apply(lambda x:"Sim" if x else "Não"),
                        "Check-in":   get_series(df_src,"checkin_time").apply(formatar_data),
                        "Check-out":  get_series(df_src,"checkout_time").apply(formatar_data),
                        "Obs":        get_series(df_src,"checkout_observation"),
                    })

                ec1, ec2 = st.columns(2)
                with ec1:
                    st.markdown(f"#### 📅 Dia: `{data_consulta}`")
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine="openpyxl") as w: montar(df).to_excel(w, index=False)
                    st.download_button(f"📥 Baixar {data_consulta}", out.getvalue(),
                        f"Entregas_{data_consulta}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary", use_container_width=True)
                with ec2:
                    mes     = datetime.strptime(data_consulta,"%Y-%m-%d").strftime("%Y-%m")
                    mes_lbl = datetime.strptime(data_consulta,"%Y-%m-%d").strftime("%B/%Y")
                    st.markdown(f"#### 🗓️ Mês: `{mes_lbl}`")
                    if st.button(f"Carregar {mes_lbl}", use_container_width=True):
                        datas_mes = [d["data"] for d in datas_db if d["data"].startswith(mes)]
                        frames=[]; prog=st.progress(0)
                        for i, dt in enumerate(sorted(datas_mes)):
                            t = obter_tickets_db(dt)
                            if t: frames.append(pd.DataFrame(t))
                            prog.progress((i+1)/max(len(datas_mes),1))
                        prog.empty()
                        if frames:
                            df_mes = pd.concat(frames, ignore_index=True)
                            out2   = io.BytesIO()
                            with pd.ExcelWriter(out2,engine="openpyxl") as w: montar(df_mes).to_excel(w,index=False)
                            st.download_button(f"📥 {mes_lbl} ({len(df_mes)} entregas)", out2.getvalue(),
                                f"Entregas_{mes}.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary", use_container_width=True)

    with abas[idx_ao_vivo]:
        _aba_rastreio_ao_vivo(df_f if not sem_dados_no_dia else pd.DataFrame(), data_consulta, user)

    if mostra_cadastros:
        with abas[-1]:
            _aba_cadastros(datas_db)

    return is_hoje
