"""
mod_diario_de_bordo.py — Módulo de Diário de Trocas — King Star Colchões
Rastreia o ciclo completo: cadastro → execução → retorno da peça → análise de rentabilidade
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from io import BytesIO
import json

# ─── Importação segura do banco de dados ──────────────────────────────────────
try:
    from modulos import database as db
    HAS_DB = True
except ImportError:
    HAS_DB = False


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES E CONFIGURAÇÕES PADRÃO
# ══════════════════════════════════════════════════════════════════════════════

CHAVE_TROCAS      = "trocas_diario"
CHAVE_MOTIVOS_T   = "trocas_motivos"
CHAVE_STATUS_RET  = "trocas_status_retorno"
CHAVE_DESTINOS    = "trocas_destinos_peca"

MOTIVOS_PADRAO = [
    "Adaptação",
    "Qualidade CD",
    "CX (Atendimento ao Cliente)",
    "Logística",
    "Defeito de Fabricação",
    "Arrependimento de Compra",
    "Produto Errado Entregue",
]

STATUS_RETORNO_PADRAO = [
    "Sem Defeito Aparente",
    "Defeito Pequeno / Cosmético",
    "Defeito Grave / Estrutural",
    "Peça Não Retornou",
    "Retorno Parcial",
]

DESTINOS_PECA_PADRAO = [
    "Voltou ao Estoque",
    "Encaminhado para AS (Assistência)",
    "Descartado / Inutilizado",
    "Devolvido ao Fornecedor",
    "Em Análise",
]

TIPOS_TROCA_PADRAO = [
    "Troca por Produto Igual",
    "Troca por Produto Superior (Up)",
    "Troca por Produto Inferior (Down)",
    "Troca por Reparo / Conserto",
    "Devolução com Reembolso",
]

PRODUTOS_PADRAO = [
    "Colchão Casal",
    "Colchão Solteiro",
    "Colchão Queen",
    "Colchão King",
    "Box Casal",
    "Box Solteiro",
    "Travesseiro",
    "Cama Box Completa",
]


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTÊNCIA — Firebase ou Session State como fallback
# ══════════════════════════════════════════════════════════════════════════════

def _init_session(chave, default):
    if chave not in st.session_state:
        st.session_state[chave] = default

def _carregar(chave, default):
    if HAS_DB:
        try:
            firebase_db = db.inicializar_db()
            if firebase_db:
                doc = firebase_db.collection("config").document(chave).get()
                if doc.exists:
                    return doc.to_dict().get("dados", default)
        except Exception:
            pass
    _init_session(chave, default)
    return st.session_state.get(chave, default)

def _salvar(chave, dados):
    if HAS_DB:
        try:
            firebase_db = db.inicializar_db()
            if firebase_db:
                firebase_db.collection("config").document(chave).set({"dados": dados})
                return
        except Exception:
            pass
    st.session_state[chave] = dados


def carregar_trocas():
    return _carregar(CHAVE_TROCAS, [])

def salvar_trocas(lista):
    _salvar(CHAVE_TROCAS, lista)

def carregar_motivos_troca():
    return _carregar(CHAVE_MOTIVOS_T, MOTIVOS_PADRAO)

def salvar_motivos_troca(lista):
    _salvar(CHAVE_MOTIVOS_T, lista)

def carregar_status_retorno():
    return _carregar(CHAVE_STATUS_RET, STATUS_RETORNO_PADRAO)

def salvar_status_retorno(lista):
    _salvar(CHAVE_STATUS_RET, lista)

def carregar_destinos():
    return _carregar(CHAVE_DESTINOS, DESTINOS_PECA_PADRAO)

def salvar_destinos(lista):
    _salvar(CHAVE_DESTINOS, lista)


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def _gerar_id():
    return f"TRO-{int(datetime.now().timestamp()*1000)}"

def _formatar_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def _parse_brl(texto):
    try:
        return float(str(texto).replace("R$", "").replace(".", "").replace(",", ".").strip())
    except Exception:
        return 0.0

def _calcular_resultado_financeiro(troca: dict) -> dict:
    """
    Retorna dict com análise financeira de uma troca individual.
    Lógica:
      - valor_produto_original: custo do produto que saiu
      - valor_diferenca_paga:   valor recebido do cliente (positivo = cliente pagou; negativo = reembolso)
      - valor_produto_novo:     custo do novo produto enviado ao cliente
      - custo_frete_logistica:  custo estimado da operação logística
      - resultado = valor_diferenca_paga - (valor_produto_novo - valor_produto_original) - custo_frete_logistica
    """
    vpo  = _parse_brl(troca.get("valor_produto_original", 0))
    vpn  = _parse_brl(troca.get("valor_produto_novo", 0))
    vdif = _parse_brl(troca.get("valor_diferenca_paga", 0))
    vfrt = _parse_brl(troca.get("custo_frete_logistica", 0))

    custo_liquido = (vpn - vpo) + vfrt - vdif
    resultado     = -custo_liquido  # positivo = lucro / ganho; negativo = prejuízo

    return {
        "custo_liquido": custo_liquido,
        "resultado":     resultado,
        "vantajosa":     resultado >= 0,
    }


def _df_para_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Trocas")
    return output.getvalue()


def _importar_planilha(uploaded_file) -> list:
    """
    Lê planilha (.xlsx ou .csv) e retorna lista de dicts no formato interno.
    Colunas esperadas (case-insensitive, espaços tolerados):
      codigo_cliente, nome_cliente, produto_original, produto_novo, tipo_troca,
      motivo_autorizacao, data_troca, valor_produto_original, valor_produto_novo,
      valor_diferenca_paga, custo_frete_logistica, observacoes
    """
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        col_map = {
            "codigo_cliente":         "codigo_cliente",
            "nome_cliente":           "nome_cliente",
            "produto_original":       "produto_original",
            "produto_novo":           "produto_novo",
            "tipo_troca":             "tipo_troca",
            "motivo_autorizacao":     "motivo_autorizacao",
            "data_troca":             "data_troca",
            "valor_produto_original": "valor_produto_original",
            "valor_produto_novo":     "valor_produto_novo",
            "valor_diferenca_paga":   "valor_diferenca_paga",
            "custo_frete_logistica":  "custo_frete_logistica",
            "observacoes":            "observacoes",
        }

        registros = []
        for _, row in df.iterrows():
            reg = {
                "id":                     _gerar_id(),
                "data_cadastro":          datetime.now().strftime("%d/%m/%Y %H:%M"),
                "status_retorno_peca":    "Pendente",
                "destino_peca":           "Pendente",
                "data_retorno_peca":      None,
                "obs_retorno":            "",
                "importado_planilha":     True,
            }
            for col_planilha, col_interno in col_map.items():
                reg[col_interno] = str(row.get(col_planilha, "")).strip() if col_planilha in row.index else ""
            registros.append(reg)
        return registros, None
    except Exception as e:
        return [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
# FORMULÁRIO DE CADASTRO
# ══════════════════════════════════════════════════════════════════════════════

def _tab_cadastro(trocas, motivos, tipos_troca, user_info):
    st.markdown("### ➕ Registrar Nova Troca")

    # Upload de planilha
    with st.expander("📂 Importar via Planilha (.xlsx / .csv)", expanded=False):
        st.markdown("""
        **Colunas esperadas na planilha:**  
        `codigo_cliente` · `nome_cliente` · `produto_original` · `produto_novo` · `tipo_troca`  
        `motivo_autorizacao` · `data_troca` · `valor_produto_original` · `valor_produto_novo`  
        `valor_diferenca_paga` · `custo_frete_logistica` · `observacoes`
        """)

        # Download do template
        template_df = pd.DataFrame(columns=[
            "codigo_cliente", "nome_cliente", "produto_original", "produto_novo",
            "tipo_troca", "motivo_autorizacao", "data_troca",
            "valor_produto_original", "valor_produto_novo",
            "valor_diferenca_paga", "custo_frete_logistica", "observacoes"
        ])
        st.download_button(
            "⬇️ Baixar Template",
            data=_df_para_excel(template_df),
            file_name="template_trocas_king_star.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        arquivo = st.file_uploader("Selecione a planilha:", type=["xlsx", "xls", "csv"], key="upload_planilha")
        if arquivo and st.button("📥 Importar Registros", type="primary"):
            novos, erro = _importar_planilha(arquivo)
            if erro:
                st.error(f"Erro na importação: {erro}")
            else:
                trocas.extend(novos)
                salvar_trocas(trocas)
                st.success(f"✅ {len(novos)} registros importados com sucesso!")
                st.rerun()

    st.divider()

    # Formulário manual
    with st.form("form_nova_troca", clear_on_submit=True):
        st.markdown("#### 👤 Dados do Cliente")
        c1, c2 = st.columns(2)
        codigo_cliente = c1.text_input("Código do Cliente *", placeholder="Ex: CLI-00123")
        nome_cliente   = c2.text_input("Nome do Cliente *", placeholder="Nome completo")

        st.markdown("#### 📦 Dados do Produto")
        c3, c4 = st.columns(2)
        produto_original = c3.text_input("Produto Original *", placeholder="Ex: Colchão Casal Molas")
        produto_novo     = c4.text_input("Produto Novo (após troca)", placeholder="Igual ao original se troca simples")

        c5, c6 = st.columns(2)
        tipo_troca = c5.selectbox("Tipo de Troca *", tipos_troca)
        motivo     = c6.selectbox("Motivo / Autorização *", motivos)

        st.markdown("#### 📅 Datas e Valores")
        c7, c8, c9 = st.columns(3)
        data_troca      = c7.date_input("Data da Troca *", value=date.today())
        val_original_s  = c8.text_input("Valor Produto Original (R$)", value="0,00", placeholder="0,00")
        val_novo_s      = c9.text_input("Valor Produto Novo (R$)", value="0,00", placeholder="0,00")

        c10, c11 = st.columns(2)
        val_dif_s   = c10.text_input("Valor de Diferença Paga pelo Cliente (R$)", value="0,00",
                                     help="Use valor negativo se houve reembolso ao cliente")
        val_frete_s = c11.text_input("Custo de Frete / Logística (R$)", value="0,00")

        observacoes = st.text_area("Observações / Número do Pedido / Ticket", placeholder="Informações adicionais...")

        operador = user_info.get("nome", "Sistema")
        st.caption(f"Registrado por: **{operador}**")

        submitted = st.form_submit_button("💾 REGISTRAR TROCA", type="primary", use_container_width=True)

        if submitted:
            if not codigo_cliente.strip() or not nome_cliente.strip() or not produto_original.strip():
                st.error("Preencha os campos obrigatórios: Código, Nome e Produto Original.")
            else:
                novo = {
                    "id":                     _gerar_id(),
                    "data_cadastro":          datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "codigo_cliente":         codigo_cliente.strip().upper(),
                    "nome_cliente":           nome_cliente.strip(),
                    "produto_original":       produto_original.strip(),
                    "produto_novo":           produto_novo.strip() or produto_original.strip(),
                    "tipo_troca":             tipo_troca,
                    "motivo_autorizacao":     motivo,
                    "data_troca":             data_troca.strftime("%d/%m/%Y"),
                    "valor_produto_original": val_original_s.replace(",", "."),
                    "valor_produto_novo":     val_novo_s.replace(",", "."),
                    "valor_diferenca_paga":   val_dif_s.replace(",", "."),
                    "custo_frete_logistica":  val_frete_s.replace(",", "."),
                    "observacoes":            observacoes.strip(),
                    "status_retorno_peca":    "Pendente",
                    "destino_peca":           "Pendente",
                    "data_retorno_peca":      None,
                    "obs_retorno":            "",
                    "operador_cadastro":      operador,
                    "importado_planilha":     False,
                }
                trocas.append(novo)
                salvar_trocas(trocas)
                fin = _calcular_resultado_financeiro(novo)
                st.success(f"✅ Troca **{novo['id']}** registrada! Resultado estimado: **{_formatar_brl(fin['resultado'])}**")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CONFERÊNCIA DE RETORNO
# ══════════════════════════════════════════════════════════════════════════════

def _tab_conferencia(trocas, status_retorno_opts, destinos_opts):
    st.markdown("### 🔄 Conferência de Retorno de Peças")

    pendentes = [t for t in trocas if t.get("status_retorno_peca") == "Pendente"]
    finalizadas = [t for t in trocas if t.get("status_retorno_peca") != "Pendente"]

    c_p, c_f = st.columns(2)
    c_p.metric("⏳ Aguardando Retorno", len(pendentes))
    c_f.metric("✅ Retornos Registrados", len(finalizadas))

    st.divider()

    if not pendentes:
        st.success("🎉 Todas as trocas já possuem retorno registrado!")
        return

    # Busca rápida
    busca = st.text_input("🔍 Buscar por código do cliente, nome ou ID da troca:", placeholder="Ex: CLI-00123")
    lista_filtrada = pendentes
    if busca.strip():
        b = busca.strip().lower()
        lista_filtrada = [
            t for t in pendentes
            if b in t.get("codigo_cliente", "").lower()
            or b in t.get("nome_cliente", "").lower()
            or b in t.get("id", "").lower()
        ]

    if not lista_filtrada:
        st.info("Nenhum resultado para a busca.")
        return

    for idx_t, troca in enumerate(lista_filtrada):
        idx_real = next((i for i, t in enumerate(trocas) if t["id"] == troca["id"]), None)
        if idx_real is None:
            continue

        with st.expander(
            f"📌 **{troca['id']}** — {troca['nome_cliente']} ({troca['codigo_cliente']}) "
            f"| {troca['produto_original']} → {troca.get('produto_novo','')} "
            f"| Troca: {troca['data_troca']}",
            expanded=False
        ):
            with st.form(key=f"form_retorno_{troca['id']}"):
                r1, r2 = st.columns(2)
                status_sel  = r1.selectbox("Status de Retorno da Peça *", status_retorno_opts, key=f"sr_{troca['id']}")
                destino_sel = r2.selectbox("Destino da Peça *",           destinos_opts,       key=f"dp_{troca['id']}")

                r3, r4 = st.columns(2)
                data_ret = r3.date_input("Data do Retorno", value=date.today(), key=f"dr_{troca['id']}")
                obs_ret  = r4.text_input("Observações do Retorno", placeholder="Detalhes...", key=f"or_{troca['id']}")

                if st.form_submit_button("✅ CONFIRMAR RETORNO", type="primary", use_container_width=True):
                    trocas[idx_real]["status_retorno_peca"] = status_sel
                    trocas[idx_real]["destino_peca"]        = destino_sel
                    trocas[idx_real]["data_retorno_peca"]   = data_ret.strftime("%d/%m/%Y")
                    trocas[idx_real]["obs_retorno"]         = obs_ret.strip()
                    salvar_trocas(trocas)
                    st.success(f"Retorno da troca **{troca['id']}** registrado!")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO / CONSULTA
# ══════════════════════════════════════════════════════════════════════════════

def _tab_historico(trocas):
    st.markdown("### 📋 Histórico de Trocas")

    if not trocas:
        st.info("Nenhuma troca registrada ainda.")
        return

    df = pd.DataFrame(trocas)

    # ── Filtros ───────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("##### 🔍 Filtros")
        hc1, hc2, hc3, hc4 = st.columns(4)

        motivos_disp  = ["Todos"] + sorted(df["motivo_autorizacao"].dropna().unique().tolist())
        status_disp   = ["Todos"] + sorted(df["status_retorno_peca"].dropna().unique().tolist())
        tipos_disp    = ["Todos"] + sorted(df["tipo_troca"].dropna().unique().tolist())
        produtos_disp = ["Todos"] + sorted(df["produto_original"].dropna().unique().tolist())

        f_motivo  = hc1.selectbox("Motivo",   motivos_disp,  key="h_motivo")
        f_status  = hc2.selectbox("Retorno",  status_disp,   key="h_status")
        f_tipo    = hc3.selectbox("Tipo",     tipos_disp,    key="h_tipo")
        f_produto = hc4.selectbox("Produto",  produtos_disp, key="h_produto")

        busca_h = st.text_input("Buscar por nome, código ou ID:", key="h_busca", placeholder="...")

    df_v = df.copy()
    if f_motivo  != "Todos": df_v = df_v[df_v["motivo_autorizacao"] == f_motivo]
    if f_status  != "Todos": df_v = df_v[df_v["status_retorno_peca"] == f_status]
    if f_tipo    != "Todos": df_v = df_v[df_v["tipo_troca"] == f_tipo]
    if f_produto != "Todos": df_v = df_v[df_v["produto_original"] == f_produto]
    if busca_h.strip():
        b = busca_h.strip().lower()
        df_v = df_v[
            df_v["nome_cliente"].str.lower().str.contains(b, na=False) |
            df_v["codigo_cliente"].str.lower().str.contains(b, na=False) |
            df_v["id"].str.lower().str.contains(b, na=False)
        ]

    st.markdown(f"**{len(df_v)} registros encontrados**")

    # Cálculo do resultado financeiro para cada linha
    df_v["resultado_R$"] = df_v.apply(
        lambda r: _calcular_resultado_financeiro(r)["resultado"], axis=1
    )
    df_v["vantajosa"] = df_v["resultado_R$"].apply(lambda x: "✅ Sim" if x >= 0 else "❌ Não")

    cols_exib = [
        "id", "data_troca", "codigo_cliente", "nome_cliente",
        "produto_original", "motivo_autorizacao", "tipo_troca",
        "status_retorno_peca", "destino_peca",
        "valor_diferenca_paga", "resultado_R$", "vantajosa"
    ]
    cols_exib = [c for c in cols_exib if c in df_v.columns]

    st.dataframe(df_v[cols_exib], use_container_width=True, hide_index=True)

    # Export
    excel_data = _df_para_excel(df_v)
    st.download_button(
        "⬇️ Exportar Filtrado (.xlsx)",
        data=excel_data,
        file_name=f"trocas_export_{date.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Edição / Exclusão
    st.divider()
    st.markdown("##### ✏️ Editar ou Excluir Registro")
    ids_disp = ["—"] + df_v["id"].tolist()
    sel_id = st.selectbox("Selecione o ID da troca:", ids_disp, key="sel_edit_id")

    if sel_id != "—":
        idx_real = next((i for i, t in enumerate(trocas) if t["id"] == sel_id), None)
        if idx_real is not None:
            t_sel = trocas[idx_real]
            col_ed, col_del = st.columns([3, 1])
            with col_ed:
                with st.expander("✏️ Editar campos básicos"):
                    with st.form(f"form_edit_{sel_id}"):
                        e1, e2 = st.columns(2)
                        novo_obs = e1.text_input("Observações", value=t_sel.get("observacoes", ""))
                        novo_obs_ret = e2.text_input("Obs. Retorno", value=t_sel.get("obs_retorno", ""))
                        novo_frete = st.text_input("Custo Frete/Log.", value=t_sel.get("custo_frete_logistica", "0"))
                        if st.form_submit_button("💾 Salvar Edição"):
                            trocas[idx_real]["observacoes"]         = novo_obs
                            trocas[idx_real]["obs_retorno"]         = novo_obs_ret
                            trocas[idx_real]["custo_frete_logistica"] = novo_frete
                            salvar_trocas(trocas)
                            st.success("Registro atualizado!")
                            st.rerun()

            with col_del:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Excluir Registro", type="secondary", use_container_width=True, key=f"del_{sel_id}"):
                    trocas.pop(idx_real)
                    salvar_trocas(trocas)
                    st.warning(f"Registro {sel_id} excluído.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD DE EFETIVIDADE
# ══════════════════════════════════════════════════════════════════════════════

def _tab_dashboard(trocas):
    st.markdown("### 📊 Análise de Efetividade de Trocas")

    if len(trocas) < 1:
        st.info("Cadastre trocas para ver a análise.")
        return

    df = pd.DataFrame(trocas)

    # Cálculo financeiro
    fin = df.apply(lambda r: pd.Series(_calcular_resultado_financeiro(r)), axis=1)
    df  = pd.concat([df, fin], axis=1)

    df["valor_produto_original"]   = pd.to_numeric(df["valor_produto_original"].str.replace(",", "."), errors="coerce").fillna(0)
    df["valor_diferenca_paga"]     = pd.to_numeric(df["valor_diferenca_paga"].str.replace(",", "."), errors="coerce").fillna(0)
    df["custo_frete_logistica"]    = pd.to_numeric(df["custo_frete_logistica"].str.replace(",", "."), errors="coerce").fillna(0)

    # ── KPIs principais ───────────────────────────────────────────────────────
    total_trocas      = len(df)
    trocas_vantajosas = int(df["vantajosa"].sum()) if "vantajosa" in df.columns else 0
    trocas_prejuizo   = total_trocas - trocas_vantajosas
    saldo_total       = df["resultado"].sum()
    receita_difs      = df["valor_diferenca_paga"].sum()
    custo_fretes      = df["custo_frete_logistica"].sum()
    pendentes_ret     = int((df["status_retorno_peca"] == "Pendente").sum())

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    def _kpi(col, label, valor, color="#002366"):
        col.markdown(f"""
        <div style="background:linear-gradient(135deg,#f8faff,#eef2ff);
                    border:1px solid #c7d2fe;border-radius:12px;
                    padding:16px 10px;text-align:center;
                    box-shadow:0 2px 8px rgba(99,102,241,.08);">
            <div style="font-size:10px;color:#6366f1;font-weight:700;
                        text-transform:uppercase;letter-spacing:.05em;">{label}</div>
            <div style="font-size:22px;font-weight:900;color:{color};margin:4px 0;">{valor}</div>
        </div>""", unsafe_allow_html=True)

    _kpi(k1, "Total Trocas",     total_trocas)
    _kpi(k2, "Vantajosas ✅",    trocas_vantajosas, "#16a34a")
    _kpi(k3, "Prejuízo ❌",      trocas_prejuizo,   "#dc2626")
    _kpi(k4, "Saldo Total",      _formatar_brl(saldo_total),  "#16a34a" if saldo_total >= 0 else "#dc2626")
    _kpi(k5, "Receita Diferenças", _formatar_brl(receita_difs))
    _kpi(k6, "Retornos Pendentes", pendentes_ret, "#d97706")

    st.write("")

    # ── Gráficos — Linha 1 ────────────────────────────────────────────────────
    g1, g2 = st.columns(2)

    with g1:
        # Trocas por motivo + resultado médio
        df_mot = df.groupby("motivo_autorizacao").agg(
            Quantidade=("id", "count"),
            Resultado_Medio=("resultado", "mean")
        ).reset_index()
        fig_mot = px.bar(
            df_mot, x="Quantidade", y="motivo_autorizacao", orientation="h",
            title="📌 Volume e Resultado Médio por Motivo",
            color="Resultado_Medio",
            color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
            labels={"motivo_autorizacao": "", "Resultado_Medio": "Resultado Médio (R$)"},
        )
        fig_mot.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=320, margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_colorbar=dict(title="R$")
        )
        st.plotly_chart(fig_mot, use_container_width=True)

    with g2:
        # Taxa de vantajosidade por motivo
        df_van = df.groupby("motivo_autorizacao").agg(
            Total=("id", "count"),
            Vantajosas=("vantajosa", "sum")
        ).reset_index()
        df_van["Taxa_%"] = (df_van["Vantajosas"] / df_van["Total"] * 100).round(1)
        fig_van = px.bar(
            df_van, x="motivo_autorizacao", y="Taxa_%",
            title="✅ Taxa de Trocas Vantajosas por Motivo (%)",
            color="Taxa_%",
            color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
            range_y=[0, 110],
            text="Taxa_%",
        )
        fig_van.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_van.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=320, margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_showscale=False, xaxis_title="",
        )
        st.plotly_chart(fig_van, use_container_width=True)

    # ── Gráficos — Linha 2 ────────────────────────────────────────────────────
    g3, g4 = st.columns(2)

    with g3:
        # Status de retorno das peças
        df_ret = df["status_retorno_peca"].value_counts().reset_index()
        df_ret.columns = ["Status", "Quantidade"]
        fig_ret = px.pie(
            df_ret, names="Status", values="Quantidade",
            title="📦 Status de Retorno das Peças",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_ret.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", height=300,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig_ret.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_ret, use_container_width=True)

    with g4:
        # Destino das peças retornadas
        df_dest = df[df["destino_peca"] != "Pendente"]["destino_peca"].value_counts().reset_index()
        df_dest.columns = ["Destino", "Quantidade"]
        if not df_dest.empty:
            fig_dest = px.bar(
                df_dest, x="Quantidade", y="Destino", orientation="h",
                title="🏭 Destino das Peças Retornadas",
                color="Quantidade",
                color_continuous_scale="Blues",
            )
            fig_dest.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                height=300, margin=dict(l=10, r=10, t=40, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_dest, use_container_width=True)
        else:
            st.info("Sem peças com destino registrado ainda.")

    # ── Resultado financeiro acumulado por motivo ──────────────────────────────
    df_fin_mot = df.groupby("motivo_autorizacao")["resultado"].sum().reset_index()
    df_fin_mot.columns = ["Motivo", "Resultado_Total"]
    df_fin_mot = df_fin_mot.sort_values("Resultado_Total")

    fig_fin = px.bar(
        df_fin_mot, x="Resultado_Total", y="Motivo", orientation="h",
        title="💰 Resultado Financeiro Acumulado por Motivo de Troca (R$)",
        color="Resultado_Total",
        color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
        text="Resultado_Total",
    )
    fig_fin.update_traces(texttemplate="R$ %{text:,.2f}", textposition="outside")
    fig_fin.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=350, margin=dict(l=10, r=10, t=50, b=10),
        coloraxis_showscale=False, xaxis_title="R$",
    )
    st.plotly_chart(fig_fin, use_container_width=True)

    # ── Sankey: Motivo → Status Retorno → Destino ─────────────────────────────
    st.markdown("#### 🔀 Fluxo Completo: Motivo → Retorno → Destino")
    df_fluxo = df[df["status_retorno_peca"] != "Pendente"].copy()

    if len(df_fluxo) > 0:
        # Gera nós únicos
        motivos_u   = sorted(df_fluxo["motivo_autorizacao"].unique().tolist())
        status_u    = sorted(df_fluxo["status_retorno_peca"].unique().tolist())
        destinos_u  = sorted(df_fluxo["destino_peca"].unique().tolist())

        todos_nos = motivos_u + status_u + destinos_u
        idx_map   = {n: i for i, n in enumerate(todos_nos)}
        n_mot  = len(motivos_u)
        n_sta  = len(status_u)

        source_list, target_list, value_list = [], [], []

        # Motivo → Status
        for (m, s), cnt in df_fluxo.groupby(["motivo_autorizacao", "status_retorno_peca"]).size().items():
            source_list.append(idx_map[m])
            target_list.append(idx_map[s])
            value_list.append(int(cnt))

        # Status → Destino
        for (s, d), cnt in df_fluxo.groupby(["status_retorno_peca", "destino_peca"]).size().items():
            source_list.append(idx_map[s])
            target_list.append(idx_map[d])
            value_list.append(int(cnt))

        cores = (
            ["#6366f1"] * n_mot +
            ["#f59e0b"] * n_sta +
            ["#22c55e"] * len(destinos_u)
        )

        fig_sankey = go.Figure(go.Sankey(
            node=dict(
                pad=15, thickness=20,
                line=dict(color="white", width=0.5),
                label=todos_nos,
                color=cores,
            ),
            link=dict(
                source=source_list,
                target=target_list,
                value=value_list,
            )
        ))
        fig_sankey.update_layout(
            title_text="Fluxo de Trocas — Motivo → Status → Destino",
            font_size=11, height=420,
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.info("Complete o retorno de pelo menos uma troca para ver o fluxo Sankey.")

    # ── Resumo por Tipo de Troca ───────────────────────────────────────────────
    st.markdown("#### 📑 Resumo por Tipo de Troca")
    df_tipo = df.groupby("tipo_troca").agg(
        Quantidade=("id", "count"),
        Resultado_Total=("resultado", "sum"),
        Resultado_Medio=("resultado", "mean"),
        Vantajosas=("vantajosa", "sum"),
    ).reset_index()
    df_tipo["Taxa_Vantajosa_%"] = (df_tipo["Vantajosas"] / df_tipo["Quantidade"] * 100).round(1)
    df_tipo["Resultado_Total"]  = df_tipo["Resultado_Total"].apply(_formatar_brl)
    df_tipo["Resultado_Medio"]  = df_tipo["Resultado_Medio"].apply(_formatar_brl)
    st.dataframe(df_tipo, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES (motivos, status, destinos dinâmicos)
# ══════════════════════════════════════════════════════════════════════════════

def _tab_config(is_adm):
    if not is_adm:
        st.warning("🔒 Área restrita a administradores.")
        return

    st.markdown("### ⚙️ Configurações do Módulo de Trocas")

    motivos    = carregar_motivos_troca()
    status_ret = carregar_status_retorno()
    destinos   = carregar_destinos()

    # ── Motivos de Autorização ─────────────────────────────────────────────────
    with st.expander("📌 Motivos / Autorizações de Troca", expanded=True):
        col_a, col_b = st.columns([4, 1])
        novo_m = col_a.text_input("Novo motivo:", key="nm_mot", label_visibility="collapsed", placeholder="Ex: Gerência Comercial")
        if col_b.button("➕ Adicionar", key="btn_mot", use_container_width=True):
            if novo_m.strip() and novo_m.strip() not in motivos:
                motivos.append(novo_m.strip())
                salvar_motivos_troca(motivos)
                st.success("Motivo adicionado!")
                st.rerun()
        st.divider()
        for i, m in enumerate(motivos):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"▸ **{m}**")
            if c2.button("🗑️", key=f"del_mot_{i}", help=f"Remover '{m}'"):
                motivos.pop(i)
                salvar_motivos_troca(motivos)
                st.rerun()

    # ── Status de Retorno ──────────────────────────────────────────────────────
    with st.expander("📦 Status de Retorno da Peça"):
        col_a2, col_b2 = st.columns([4, 1])
        novo_s = col_a2.text_input("Novo status:", key="nm_sr", label_visibility="collapsed", placeholder="Ex: Retornou Embalado")
        if col_b2.button("➕ Adicionar", key="btn_sr", use_container_width=True):
            if novo_s.strip() and novo_s.strip() not in status_ret:
                status_ret.append(novo_s.strip())
                salvar_status_retorno(status_ret)
                st.success("Status adicionado!")
                st.rerun()
        st.divider()
        for i, s in enumerate(status_ret):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"▸ **{s}**")
            if c2.button("🗑️", key=f"del_sr_{i}", help=f"Remover '{s}'"):
                status_ret.pop(i)
                salvar_status_retorno(status_ret)
                st.rerun()

    # ── Destinos de Peças ──────────────────────────────────────────────────────
    with st.expander("🏭 Destinos das Peças"):
        col_a3, col_b3 = st.columns([4, 1])
        novo_d = col_a3.text_input("Novo destino:", key="nm_dp", label_visibility="collapsed", placeholder="Ex: Reciclagem")
        if col_b3.button("➕ Adicionar", key="btn_dp", use_container_width=True):
            if novo_d.strip() and novo_d.strip() not in destinos:
                destinos.append(novo_d.strip())
                salvar_destinos(destinos)
                st.success("Destino adicionado!")
                st.rerun()
        st.divider()
        for i, d in enumerate(destinos):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"▸ **{d}**")
            if c2.button("🗑️", key=f"del_dp_{i}", help=f"Remover '{d}'"):
                destinos.pop(i)
                salvar_destinos(destinos)
                st.rerun()

    st.divider()
    st.markdown("#### ⚠️ Zona de Perigo")
    with st.expander("🗑️ Limpar Todos os Registros de Troca"):
        st.warning("Esta ação é irreversível e apagará TODOS os registros do diário de trocas.")
        if st.button("🔥 CONFIRMAR LIMPEZA TOTAL", type="primary"):
            salvar_trocas([])
            st.success("Todos os registros foram apagados.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA — chamado pelo main.py
# ══════════════════════════════════════════════════════════════════════════════

def exibir(user_info):
    """
    Função principal do módulo. Chamada pelo main.py com user_info dict.
    user_info deve conter: nome, role (ADM | OPERACIONAL | GERÊNCIA | SUPERVISOR)
    """
    is_adm = user_info.get("role", "").upper() in ("ADM", "GERÊNCIA")

    # ── Estilo global do módulo ────────────────────────────────────────────────
    st.markdown("""
    <style>
    .troca-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📓 Diário de Trocas — King Star Colchões")

    # ── Carregamento de dados ──────────────────────────────────────────────────
    trocas       = carregar_trocas()
    motivos      = carregar_motivos_troca()
    status_ret   = carregar_status_retorno()
    destinos     = carregar_destinos()
    tipos_troca  = TIPOS_TROCA_PADRAO  # fixo por ora; pode ser tornado dinâmico

    # ── Alerta de pendências na tela principal ─────────────────────────────────
    pendentes_count = sum(1 for t in trocas if t.get("status_retorno_peca") == "Pendente")
    if pendentes_count > 0:
        st.warning(f"⚠️ **{pendentes_count} troca(s)** aguardando conferência de retorno.", icon="⏳")

    # ── Abas ──────────────────────────────────────────────────────────────────
    abas = ["➕ Cadastrar", "🔄 Conferência", "📋 Histórico", "📊 Efetividade"]
    if is_adm:
        abas.append("⚙️ Config")

    tabs = st.tabs(abas)

    with tabs[0]:
        _tab_cadastro(trocas, motivos, tipos_troca, user_info)

    with tabs[1]:
        _tab_conferencia(trocas, status_ret, destinos)

    with tabs[2]:
        _tab_historico(trocas)

    with tabs[3]:
        _tab_dashboard(trocas)

    if is_adm and len(tabs) == 5:
        with tabs[4]:
            _tab_config(is_adm)
