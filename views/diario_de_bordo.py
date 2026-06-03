"""
diario_de_bordo.py — Módulo de Diário de Trocas — King Star Colchões
Rastreia o ciclo completo: cadastro → conferência → AS (segunda conferência) → efetividade
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from io import BytesIO

# ─── Importação segura do banco de dados ──────────────────────────────────────
try:
    from modulos import database as db
    HAS_DB = True
except ImportError:
    HAS_DB = False


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

CHAVE_TROCAS     = "trocas_diario"
CHAVE_MOTIVOS_T  = "trocas_motivos"
CHAVE_STATUS_RET = "trocas_status_retorno"
CHAVE_DESTINOS   = "trocas_destinos_peca"

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

# "Encaminhado para AS" aciona a 2ª conferência — não remova este valor
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

DESTINO_AS = "Encaminhado para AS (Assistência)"   # gatilho da 2ª conferência


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTÊNCIA
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

def carregar_trocas():       return _carregar(CHAVE_TROCAS,     [])
def salvar_trocas(l):        _salvar(CHAVE_TROCAS,     l)
def carregar_motivos_troca():return _carregar(CHAVE_MOTIVOS_T,  MOTIVOS_PADRAO)
def salvar_motivos_troca(l): _salvar(CHAVE_MOTIVOS_T,  l)
def carregar_status_retorno():return _carregar(CHAVE_STATUS_RET, STATUS_RETORNO_PADRAO)
def salvar_status_retorno(l):_salvar(CHAVE_STATUS_RET, l)
def carregar_destinos():     return _carregar(CHAVE_DESTINOS,   DESTINOS_PECA_PADRAO)
def salvar_destinos(l):      _salvar(CHAVE_DESTINOS,   l)


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def _gerar_id():
    return f"TRO-{int(datetime.now().timestamp()*1000)}"

def _formatar_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return "R$ 0,00"

def _parse_brl(texto):
    try:
        return float(str(texto).replace("R$","").replace(".","").replace(",",".").strip())
    except Exception:
        return 0.0

def _calcular_resultado_financeiro(troca: dict) -> dict:
    """
    resultado = valor_diferenca_paga - (valor_produto_novo - valor_produto_original) - custo_frete
    Positivo = vantajosa; Negativo = prejuízo.
    Só considera "Vantajosa" quando o campo foi marcado na conferência.
    """
    vpo  = _parse_brl(troca.get("valor_produto_original", 0))
    vpn  = _parse_brl(troca.get("valor_produto_novo",     0))
    vdif = _parse_brl(troca.get("valor_diferenca_paga",   0))
    vfrt = _parse_brl(troca.get("custo_frete_logistica",  0))

    custo_liquido = (vpn - vpo) + vfrt - vdif
    resultado     = -custo_liquido

    # Usa avaliação manual da conferência se disponível; caso contrário usa cálculo
    vantajosa_manual = troca.get("vantajosa_conferencia")   # True / False / None
    if vantajosa_manual is None:
        vantajosa = resultado >= 0
    else:
        vantajosa = bool(vantajosa_manual)

    return {"custo_liquido": custo_liquido, "resultado": resultado, "vantajosa": vantajosa}

def _df_para_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Trocas")
    return output.getvalue()

def _importar_planilha(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, dtype=str) if uploaded_file.name.endswith(".csv") \
             else pd.read_excel(uploaded_file, dtype=str)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        col_map = {
            "codigo_cliente":"codigo_cliente","nome_cliente":"nome_cliente",
            "produto_original":"produto_original","produto_novo":"produto_novo",
            "tipo_troca":"tipo_troca","motivo_autorizacao":"motivo_autorizacao",
            "data_troca":"data_troca","valor_produto_original":"valor_produto_original",
            "valor_produto_novo":"valor_produto_novo","valor_diferenca_paga":"valor_diferenca_paga",
            "custo_frete_logistica":"custo_frete_logistica","observacoes":"observacoes",
        }
        registros = []
        for _, row in df.iterrows():
            reg = {
                "id": _gerar_id(), "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "status_retorno_peca":"Pendente","destino_peca":"Pendente",
                "data_retorno_peca":None,"obs_retorno":"",
                "num_carga":"","motorista":"","vantajosa_conferencia":None,
                "as_status":"","as_data":"","as_obs":"","importado_planilha":True,
            }
            for cp, ci in col_map.items():
                reg[ci] = str(row.get(cp,"")).strip() if cp in row.index else ""
            registros.append(reg)
        return registros, None
    except Exception as e:
        return [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — CADASTRO
# ══════════════════════════════════════════════════════════════════════════════

def _tab_cadastro(trocas, motivos, tipos_troca, user_info):
    st.markdown("### ➕ Registrar Nova Troca")

    with st.expander("📂 Importar via Planilha (.xlsx / .csv)", expanded=False):
        st.markdown("""
        **Colunas esperadas:**  
        `codigo_cliente` · `nome_cliente` · `produto_original` · `produto_novo` · `tipo_troca`  
        `motivo_autorizacao` · `data_troca` · `valor_produto_original` · `valor_produto_novo`  
        `valor_diferenca_paga` · `custo_frete_logistica` · `observacoes`
        """)
        template_df = pd.DataFrame(columns=[
            "codigo_cliente","nome_cliente","produto_original","produto_novo",
            "tipo_troca","motivo_autorizacao","data_troca",
            "valor_produto_original","valor_produto_novo",
            "valor_diferenca_paga","custo_frete_logistica","observacoes"
        ])
        st.download_button("⬇️ Baixar Template", data=_df_para_excel(template_df),
            file_name="template_trocas_king_star.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        arq = st.file_uploader("Selecione a planilha:", type=["xlsx","xls","csv"], key="upload_planilha")
        if arq and st.button("📥 Importar Registros", type="primary"):
            novos, erro = _importar_planilha(arq)
            if erro:
                st.error(f"Erro na importação: {erro}")
            else:
                trocas.extend(novos)
                salvar_trocas(trocas)
                st.success(f"✅ {len(novos)} registros importados!")
                st.rerun()

    st.divider()

    with st.form("form_nova_troca", clear_on_submit=True):
        st.markdown("#### 👤 Dados do Cliente")
        c1, c2 = st.columns(2)
        codigo_cliente = c1.text_input("Código do Cliente *", placeholder="Ex: CLI-00123")
        nome_cliente   = c2.text_input("Nome do Cliente *",   placeholder="Nome completo")

        st.markdown("#### 📦 Dados do Produto")
        c3, c4 = st.columns(2)
        produto_original = c3.text_input("Produto Original *",      placeholder="Ex: Colchão Casal Molas")
        produto_novo     = c4.text_input("Produto Novo (após troca)",placeholder="Igual ao original se troca simples")

        c5, c6 = st.columns(2)
        tipo_troca = c5.selectbox("Tipo de Troca *",        tipos_troca)
        motivo     = c6.selectbox("Motivo / Autorização *", motivos)

        st.markdown("#### 📅 Datas e Valores")
        c7, c8, c9 = st.columns(3)
        data_troca     = c7.date_input("Data da Troca *", value=date.today())
        val_original_s = c8.text_input("Valor Produto Original (R$)", value="0,00")
        val_novo_s     = c9.text_input("Valor Produto Novo (R$)",      value="0,00")

        c10, c11 = st.columns(2)
        val_dif_s   = c10.text_input("Diferença Paga pelo Cliente (R$)", value="0,00",
                                     help="Negativo = reembolso ao cliente")
        val_frete_s = c11.text_input("Custo de Frete / Logística (R$)", value="0,00")

        observacoes = st.text_area("Observações / Pedido / Ticket", placeholder="Informações adicionais...")
        operador    = user_info.get("nome","Sistema")
        st.caption(f"Registrado por: **{operador}**")

        if st.form_submit_button("💾 REGISTRAR TROCA", type="primary", use_container_width=True):
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
                    "valor_produto_original": val_original_s.replace(",","."),
                    "valor_produto_novo":     val_novo_s.replace(",","."),
                    "valor_diferenca_paga":   val_dif_s.replace(",","."),
                    "custo_frete_logistica":  val_frete_s.replace(",","."),
                    "observacoes":            observacoes.strip(),
                    "operador_cadastro":      operador,
                    # campos de conferência — preenchidos depois
                    "status_retorno_peca":    "Pendente",
                    "destino_peca":           "Pendente",
                    "data_retorno_peca":      None,
                    "obs_retorno":            "",
                    "num_carga":              "",
                    "motorista":              "",
                    "vantajosa_conferencia":  None,
                    # campos AS — preenchidos se destino = AS
                    "as_status":              "",
                    "as_data":                "",
                    "as_obs":                 "",
                    "importado_planilha":     False,
                }
                trocas.append(novo)
                salvar_trocas(trocas)
                fin = _calcular_resultado_financeiro(novo)
                st.success(f"✅ Troca **{novo['id']}** registrada! Resultado estimado: **{_formatar_brl(fin['resultado'])}**")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — CONFERÊNCIA DE RETORNO  (1ª conferência)
# ══════════════════════════════════════════════════════════════════════════════

def _tab_conferencia(trocas, status_retorno_opts, destinos_opts):
    st.markdown("### 🔄 Conferência de Retorno de Peças")

    pendentes   = [t for t in trocas if t.get("status_retorno_peca") == "Pendente"]
    finalizadas = [t for t in trocas if t.get("status_retorno_peca") != "Pendente"]

    m1, m2, m3 = st.columns(3)
    m1.metric("⏳ Aguardando Conferência", len(pendentes))
    m2.metric("✅ Conferências Concluídas",  len(finalizadas))
    aguardando_as = [t for t in trocas if t.get("destino_peca") == DESTINO_AS and not t.get("as_status")]
    m3.metric("🔧 Aguardando Retorno AS",   len(aguardando_as))

    st.divider()

    if not pendentes:
        st.success("🎉 Nenhuma troca aguardando primeira conferência!")
    else:
        busca = st.text_input("🔍 Buscar (código, nome ou ID):", placeholder="Ex: CLI-00123", key="busca_conf")
        lista = pendentes
        if busca.strip():
            b = busca.strip().lower()
            lista = [t for t in pendentes if
                     b in t.get("codigo_cliente","").lower() or
                     b in t.get("nome_cliente","").lower()   or
                     b in t.get("id","").lower()]
        if not lista:
            st.info("Nenhum resultado para a busca.")
        else:
            for troca in lista:
                idx_real = next((i for i,t in enumerate(trocas) if t["id"]==troca["id"]), None)
                if idx_real is None:
                    continue

                with st.expander(
                    f"📌 **{troca['id']}** — {troca['nome_cliente']} ({troca['codigo_cliente']}) "
                    f"| {troca['produto_original']} → {troca.get('produto_novo','')} "
                    f"| Troca: {troca['data_troca']}",
                    expanded=False
                ):
                    # ── Leitura dos dados cadastrados ────────────────────────
                    st.markdown("#### 📋 Dados Cadastrados")
                    d1, d2, d3, d4 = st.columns(4)
                    d1.info(f"**Tipo:** {troca.get('tipo_troca','—')}")
                    d2.info(f"**Motivo:** {troca.get('motivo_autorizacao','—')}")
                    d3.info(f"**Val. Original:** {_formatar_brl(troca.get('valor_produto_original',0))}")
                    d4.info(f"**Val. Novo:** {_formatar_brl(troca.get('valor_produto_novo',0))}")

                    d5, d6, d7, d8 = st.columns(4)
                    d5.info(f"**Dif. Paga:** {_formatar_brl(troca.get('valor_diferenca_paga',0))}")
                    d6.info(f"**Frete:** {_formatar_brl(troca.get('custo_frete_logistica',0))}")
                    d7.info(f"**Operador:** {troca.get('operador_cadastro','—')}")
                    d8.info(f"**Cadastrado:** {troca.get('data_cadastro','—')}")

                    if troca.get("observacoes"):
                        st.info(f"📝 **Obs. Cadastro:** {troca['observacoes']}")

                    st.markdown("#### ✅ Registrar Conferência")

                    with st.form(key=f"form_conf_{troca['id']}"):
                        # Carga e motorista
                        fc1, fc2 = st.columns(2)
                        num_carga = fc1.text_input("Nº da Carga *", placeholder="Ex: CRG-2024-001",
                                                   key=f"nc_{troca['id']}")
                        motorista = fc2.text_input("Nome do Motorista *", placeholder="Nome completo",
                                                   key=f"mt_{troca['id']}")

                        # Status e destino
                        fs1, fs2 = st.columns(2)
                        status_sel  = fs1.selectbox("Status de Retorno da Peça *",
                                                    status_retorno_opts, key=f"sr_{troca['id']}")
                        destino_sel = fs2.selectbox("Destino da Peça *",
                                                    destinos_opts,       key=f"dp_{troca['id']}")

                        # Data e observação
                        fd1, fd2 = st.columns(2)
                        data_ret = fd1.date_input("Data do Retorno", value=date.today(),
                                                  key=f"dr_{troca['id']}")
                        obs_ret  = fd2.text_input("Observações do Retorno",
                                                  placeholder="Detalhes...", key=f"or_{troca['id']}")

                        # ── Avaliação manual: foi vantajosa? ─────────────────
                        st.markdown("---")
                        st.markdown("##### 💡 Avaliação da Troca")
                        fa1, fa2 = st.columns(2)
                        vantajosa_op = fa1.radio(
                            "Esta troca foi vantajosa para a empresa?",
                            ["Sim ✅", "Não ❌"],
                            horizontal=True,
                            key=f"vt_{troca['id']}"
                        )
                        justificativa = fa2.text_input(
                            "Justificativa (opcional)",
                            placeholder="Ex: Produto voltou sem defeito, revendido.",
                            key=f"jt_{troca['id']}"
                        )

                        if st.form_submit_button("✅ CONFIRMAR CONFERÊNCIA", type="primary",
                                                 use_container_width=True):
                            if not num_carga.strip() or not motorista.strip():
                                st.error("Informe o Nº da Carga e o Nome do Motorista.")
                            else:
                                trocas[idx_real]["status_retorno_peca"]   = status_sel
                                trocas[idx_real]["destino_peca"]          = destino_sel
                                trocas[idx_real]["data_retorno_peca"]     = data_ret.strftime("%d/%m/%Y")
                                trocas[idx_real]["obs_retorno"]           = obs_ret.strip()
                                trocas[idx_real]["num_carga"]             = num_carga.strip().upper()
                                trocas[idx_real]["motorista"]             = motorista.strip()
                                trocas[idx_real]["vantajosa_conferencia"] = (vantajosa_op == "Sim ✅")
                                trocas[idx_real]["justificativa_conf"]    = justificativa.strip()
                                salvar_trocas(trocas)
                                msg = f"Conferência da troca **{troca['id']}** registrada!"
                                if destino_sel == DESTINO_AS:
                                    msg += " ⚠️ Peça encaminhada para AS — aguardando **2ª conferência**."
                                st.success(msg)
                                st.rerun()

    # ── 2ª CONFERÊNCIA — Retorno da AS ──────────────────────────────────────
    st.divider()
    st.markdown("### 🔧 2ª Conferência — Retorno da Assistência Técnica (AS)")

    pendentes_as = [t for t in trocas
                    if t.get("destino_peca") == DESTINO_AS and not t.get("as_status")]

    if not pendentes_as:
        st.success("🎉 Nenhuma peça aguardando retorno da AS.")
    else:
        st.warning(f"⚠️ **{len(pendentes_as)} peça(s)** na AS aguardando resolução.")

        for troca in pendentes_as:
            idx_real = next((i for i,t in enumerate(trocas) if t["id"]==troca["id"]), None)
            if idx_real is None:
                continue

            with st.expander(
                f"🔧 **{troca['id']}** — {troca['nome_cliente']} | {troca['produto_original']} "
                f"| Carga: {troca.get('num_carga','—')} | Motorista: {troca.get('motorista','—')}",
                expanded=False
            ):
                st.markdown("##### 📋 Resumo da 1ª Conferência")
                r1, r2, r3, r4 = st.columns(4)
                r1.info(f"**Status Retorno:** {troca.get('status_retorno_peca','—')}")
                r2.info(f"**Data Retorno:** {troca.get('data_retorno_peca','—')}")
                r3.info(f"**Carga:** {troca.get('num_carga','—')}")
                r4.info(f"**Motorista:** {troca.get('motorista','—')}")
                if troca.get("obs_retorno"):
                    st.info(f"📝 **Obs. Conf.:** {troca['obs_retorno']}")

                st.markdown("##### 🏁 Resultado da Assistência Técnica")

                with st.form(key=f"form_as_{troca['id']}"):
                    a1, a2 = st.columns(2)
                    as_resultado = a1.radio(
                        "Resultado final da peça na AS:",
                        ["Voltou para o Estoque ✅", "PERDA Total ❌"],
                        horizontal=True,
                        key=f"as_res_{troca['id']}"
                    )
                    as_data = a2.date_input("Data do Retorno da AS", value=date.today(),
                                            key=f"as_dt_{troca['id']}")
                    as_obs = st.text_input("Observações da AS", placeholder="Laudo, parecer técnico...",
                                           key=f"as_ob_{troca['id']}")

                    if st.form_submit_button("🏁 CONFIRMAR RETORNO DA AS", type="primary",
                                             use_container_width=True):
                        status_as = "Voltou ao Estoque" if "Estoque" in as_resultado else "PERDA"
                        trocas[idx_real]["as_status"]  = status_as
                        trocas[idx_real]["as_data"]    = as_data.strftime("%d/%m/%Y")
                        trocas[idx_real]["as_obs"]     = as_obs.strip()
                        # Atualiza destino final da peça para refletir no histórico e dashboard
                        if status_as == "Voltou ao Estoque":
                            trocas[idx_real]["destino_peca_final"] = "Voltou ao Estoque (via AS)"
                        else:
                            trocas[idx_real]["destino_peca_final"] = "PERDA (via AS)"
                        salvar_trocas(trocas)
                        st.success(f"✅ Resultado da AS para **{troca['id']}** registrado: **{status_as}**")
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════════

def _tab_historico(trocas):
    st.markdown("### 📋 Histórico de Trocas")

    if not trocas:
        st.info("Nenhuma troca registrada ainda.")
        return

    df = pd.DataFrame(trocas)

    with st.container(border=True):
        st.markdown("##### 🔍 Filtros")
        hc1, hc2, hc3, hc4 = st.columns(4)
        motivos_d  = ["Todos"] + sorted(df["motivo_autorizacao"].dropna().unique().tolist())
        status_d   = ["Todos"] + sorted(df["status_retorno_peca"].dropna().unique().tolist())
        tipos_d    = ["Todos"] + sorted(df["tipo_troca"].dropna().unique().tolist())
        motorista_d= ["Todos"] + sorted([v for v in df.get("motorista", pd.Series()).dropna().unique() if v])
        f_mot  = hc1.selectbox("Motivo",    motivos_d,   key="h_motivo")
        f_sta  = hc2.selectbox("Retorno",   status_d,    key="h_status")
        f_tip  = hc3.selectbox("Tipo",      tipos_d,     key="h_tipo")
        f_moto = hc4.selectbox("Motorista", motorista_d, key="h_moto")
        busca_h = st.text_input("Buscar por nome, código, ID ou carga:", key="h_busca", placeholder="...")

    df_v = df.copy()
    if f_mot  != "Todos": df_v = df_v[df_v["motivo_autorizacao"] == f_mot]
    if f_sta  != "Todos": df_v = df_v[df_v["status_retorno_peca"] == f_sta]
    if f_tip  != "Todos": df_v = df_v[df_v["tipo_troca"] == f_tip]
    if f_moto != "Todos" and "motorista" in df_v.columns:
        df_v = df_v[df_v["motorista"] == f_moto]
    if busca_h.strip():
        b = busca_h.strip().lower()
        mask = (
            df_v["nome_cliente"].str.lower().str.contains(b, na=False) |
            df_v["codigo_cliente"].str.lower().str.contains(b, na=False) |
            df_v["id"].str.lower().str.contains(b, na=False)
        )
        if "num_carga" in df_v.columns:
            mask = mask | df_v["num_carga"].str.lower().str.contains(b, na=False)
        df_v = df_v[mask]

    st.markdown(f"**{len(df_v)} registros encontrados**")

    df_v["resultado_R$"] = df_v.apply(lambda r: _calcular_resultado_financeiro(r)["resultado"], axis=1)
    df_v["vantajosa_label"] = df_v.apply(
        lambda r: ("✅ Sim" if _calcular_resultado_financeiro(r)["vantajosa"] else "❌ Não")
                  if r.get("status_retorno_peca") != "Pendente" else "⏳ Pendente", axis=1)

    cols_exib = [c for c in [
        "id","data_troca","codigo_cliente","nome_cliente","produto_original",
        "motivo_autorizacao","tipo_troca","num_carga","motorista",
        "status_retorno_peca","destino_peca","as_status",
        "valor_diferenca_paga","resultado_R$","vantajosa_label"
    ] if c in df_v.columns]

    st.dataframe(df_v[cols_exib], use_container_width=True, hide_index=True)

    st.download_button("⬇️ Exportar (.xlsx)", data=_df_para_excel(df_v),
        file_name=f"trocas_{date.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Edição / exclusão
    st.divider()
    st.markdown("##### ✏️ Editar ou Excluir Registro")
    ids_disp = ["—"] + df_v["id"].tolist()
    sel_id = st.selectbox("Selecione o ID:", ids_disp, key="sel_edit_id")
    if sel_id != "—":
        idx_real = next((i for i,t in enumerate(trocas) if t["id"]==sel_id), None)
        if idx_real is not None:
            t_sel = trocas[idx_real]
            col_ed, col_del = st.columns([3, 1])
            with col_ed:
                with st.expander("✏️ Editar campos"):
                    with st.form(f"form_edit_{sel_id}"):
                        e1, e2 = st.columns(2)
                        novo_obs     = e1.text_input("Observações Cadastro", value=t_sel.get("observacoes",""))
                        novo_obs_ret = e2.text_input("Obs. Retorno",         value=t_sel.get("obs_retorno",""))
                        e3, e4 = st.columns(2)
                        novo_frete   = e3.text_input("Custo Frete",   value=t_sel.get("custo_frete_logistica","0"))
                        novo_carga   = e4.text_input("Nº Carga",      value=t_sel.get("num_carga",""))
                        novo_moto    = st.text_input("Motorista",     value=t_sel.get("motorista",""))
                        if st.form_submit_button("💾 Salvar"):
                            trocas[idx_real].update({
                                "observacoes":         novo_obs,
                                "obs_retorno":         novo_obs_ret,
                                "custo_frete_logistica": novo_frete,
                                "num_carga":           novo_carga,
                                "motorista":           novo_moto,
                            })
                            salvar_trocas(trocas)
                            st.success("Atualizado!")
                            st.rerun()
            with col_del:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Excluir", type="secondary", use_container_width=True, key=f"del_{sel_id}"):
                    trocas.pop(idx_real)
                    salvar_trocas(trocas)
                    st.warning(f"{sel_id} excluído.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — EFETIVIDADE / DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _tab_dashboard(trocas):
    st.markdown("### 📊 Análise de Efetividade de Trocas")

    if not trocas:
        st.info("Cadastre trocas para ver a análise.")
        return

    df = pd.DataFrame(trocas)

    # ── Cálculo financeiro usando avaliação manual quando disponível ──────────
    fin_df = df.apply(lambda r: pd.Series(_calcular_resultado_financeiro(r)), axis=1)
    df = pd.concat([df, fin_df], axis=1)

    for col in ["valor_produto_original","valor_diferenca_paga","custo_frete_logistica"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",","."), errors="coerce").fillna(0)

    # Apenas trocas com conferência concluída entram no saldo
    df_conf = df[df["status_retorno_peca"] != "Pendente"].copy()

    total_trocas      = len(df)
    total_conferidas  = len(df_conf)
    trocas_vantajosas = int(df_conf["vantajosa"].sum()) if not df_conf.empty else 0
    trocas_prejuizo   = total_conferidas - trocas_vantajosas
    # Saldo = soma dos resultados SOMENTE das trocas conferidas (sem valores fantasmas)
    saldo_total       = df_conf["resultado"].sum() if not df_conf.empty else 0.0
    receita_difs      = df_conf["valor_diferenca_paga"].sum() if not df_conf.empty else 0.0
    pendentes_ret     = int((df["status_retorno_peca"] == "Pendente").sum())
    perdas_as         = int((df.get("as_status","") == "PERDA").sum()) if "as_status" in df.columns else 0

    # KPIs
    k1,k2,k3,k4,k5,k6,k7 = st.columns(7)

    def _kpi(col, label, valor, color="#002366"):
        col.markdown(f"""
        <div style="background:linear-gradient(135deg,#f8faff,#eef2ff);
                    border:1px solid #c7d2fe;border-radius:12px;
                    padding:14px 8px;text-align:center;
                    box-shadow:0 2px 8px rgba(99,102,241,.08);">
            <div style="font-size:9px;color:#6366f1;font-weight:700;
                        text-transform:uppercase;letter-spacing:.05em;">{label}</div>
            <div style="font-size:20px;font-weight:900;color:{color};margin:4px 0;">{valor}</div>
        </div>""", unsafe_allow_html=True)

    _kpi(k1, "Total Trocas",       total_trocas)
    _kpi(k2, "Conferidas",         total_conferidas)
    _kpi(k3, "Vantajosas ✅",      trocas_vantajosas, "#16a34a")
    _kpi(k4, "Prejuízo ❌",        trocas_prejuizo,   "#dc2626")
    _kpi(k5, "Saldo (conferidas)", _formatar_brl(saldo_total),
         "#16a34a" if saldo_total >= 0 else "#dc2626")
    _kpi(k6, "Retornos Pendentes", pendentes_ret, "#d97706")
    _kpi(k7, "Perdas via AS",      perdas_as, "#dc2626" if perdas_as > 0 else "#16a34a")

    st.write("")

    if df_conf.empty:
        st.info("Nenhuma troca conferida ainda. Os gráficos aparecerão após a primeira conferência.")
        return

    # ── Gráficos — linha 1 ────────────────────────────────────────────────────
    g1, g2 = st.columns(2)

    with g1:
        df_mot = df_conf.groupby("motivo_autorizacao").agg(
            Quantidade=("id","count"), Resultado_Medio=("resultado","mean")).reset_index()
        fig = px.bar(df_mot, x="Quantidade", y="motivo_autorizacao", orientation="h",
                     title="📌 Volume e Resultado Médio por Motivo",
                     color="Resultado_Medio",
                     color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                     labels={"motivo_autorizacao":"","Resultado_Medio":"Resultado Médio (R$)"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          height=320, margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        df_van = df_conf.groupby("motivo_autorizacao").agg(
            Total=("id","count"), Vantajosas=("vantajosa","sum")).reset_index()
        df_van["Taxa_%"] = (df_van["Vantajosas"] / df_van["Total"] * 100).round(1)
        fig2 = px.bar(df_van, x="motivo_autorizacao", y="Taxa_%",
                      title="✅ Taxa de Trocas Vantajosas por Motivo (%)",
                      color="Taxa_%",
                      color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                      range_y=[0,110], text="Taxa_%")
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           height=320, margin=dict(l=10,r=10,t=40,b=10),
                           coloraxis_showscale=False, xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Efetividade por Motorista ─────────────────────────────────────────────
    if "motorista" in df_conf.columns and df_conf["motorista"].notna().any():
        df_moto = df_conf[df_conf["motorista"].str.strip() != ""].groupby("motorista").agg(
            Entregas=("id","count"),
            Resultado_Total=("resultado","sum"),
            Vantajosas=("vantajosa","sum"),
        ).reset_index()
        df_moto["Taxa_%"] = (df_moto["Vantajosas"] / df_moto["Entregas"] * 100).round(1)

        st.markdown("#### 🚚 Efetividade por Motorista")
        gm1, gm2 = st.columns(2)

        with gm1:
            fig_m1 = px.bar(df_moto, x="Entregas", y="motorista", orientation="h",
                            title="Entregas por Motorista",
                            color="Resultado_Total",
                            color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                            text="Entregas")
            fig_m1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                 height=300, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig_m1, use_container_width=True)

        with gm2:
            fig_m2 = px.bar(df_moto, x="motorista", y="Taxa_%",
                            title="Taxa de Trocas Vantajosas por Motorista (%)",
                            color="Taxa_%",
                            color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                            range_y=[0,110], text="Taxa_%")
            fig_m2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_m2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                 height=300, margin=dict(l=10,r=10,t=40,b=10),
                                 coloraxis_showscale=False, xaxis_title="")
            st.plotly_chart(fig_m2, use_container_width=True)

        st.dataframe(df_moto, use_container_width=True, hide_index=True)

    # ── Status retorno + Destino ──────────────────────────────────────────────
    g3, g4 = st.columns(2)
    with g3:
        df_ret = df["status_retorno_peca"].value_counts().reset_index()
        df_ret.columns = ["Status","Quantidade"]
        fig3 = px.pie(df_ret, names="Status", values="Quantidade",
                      title="📦 Status de Retorno das Peças", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=300,
                           margin=dict(l=10,r=10,t=40,b=10))
        fig3.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig3, use_container_width=True)

    with g4:
        # inclui resultado AS se disponível
        dest_col = "destino_peca_final" if "destino_peca_final" in df.columns else "destino_peca"
        df_dest = df[df[dest_col] != "Pendente"][dest_col].value_counts().reset_index()
        df_dest.columns = ["Destino","Quantidade"]
        if not df_dest.empty:
            fig4 = px.bar(df_dest, x="Quantidade", y="Destino", orientation="h",
                          title="🏭 Destino Final das Peças",
                          color="Quantidade", color_continuous_scale="Blues")
            fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               height=300, margin=dict(l=10,r=10,t=40,b=10),
                               coloraxis_showscale=False)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Sem peças com destino registrado ainda.")

    # ── Saldo acumulado por motivo ────────────────────────────────────────────
    df_fin = df_conf.groupby("motivo_autorizacao")["resultado"].sum().reset_index()
    df_fin.columns = ["Motivo","Resultado_Total"]
    df_fin = df_fin.sort_values("Resultado_Total")
    fig5 = px.bar(df_fin, x="Resultado_Total", y="Motivo", orientation="h",
                  title="💰 Resultado Financeiro Acumulado por Motivo (R$) — apenas conferidas",
                  color="Resultado_Total",
                  color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                  text="Resultado_Total")
    fig5.update_traces(texttemplate="R$ %{text:,.2f}", textposition="outside")
    fig5.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                       height=350, margin=dict(l=10,r=10,t=50,b=10),
                       coloraxis_showscale=False, xaxis_title="R$")
    st.plotly_chart(fig5, use_container_width=True)

    # ── Sankey ────────────────────────────────────────────────────────────────
    st.markdown("#### 🔀 Fluxo Completo: Motivo → Retorno → Destino Final")
    df_fluxo = df_conf.copy()
    dest_label = "destino_peca_final" if "destino_peca_final" in df_fluxo.columns else "destino_peca"
    df_fluxo = df_fluxo[df_fluxo[dest_label] != "Pendente"]

    if len(df_fluxo) > 0:
        motivos_u  = sorted(df_fluxo["motivo_autorizacao"].unique().tolist())
        status_u   = sorted(df_fluxo["status_retorno_peca"].unique().tolist())
        destinos_u = sorted(df_fluxo[dest_label].unique().tolist())
        todos_nos  = motivos_u + status_u + destinos_u
        idx_map    = {n:i for i,n in enumerate(todos_nos)}
        n_mot = len(motivos_u); n_sta = len(status_u)
        src, tgt, val = [], [], []
        for (m,s), cnt in df_fluxo.groupby(["motivo_autorizacao","status_retorno_peca"]).size().items():
            src.append(idx_map[m]); tgt.append(idx_map[s]); val.append(int(cnt))
        for (s,d), cnt in df_fluxo.groupby(["status_retorno_peca", dest_label]).size().items():
            src.append(idx_map[s]); tgt.append(idx_map[d]); val.append(int(cnt))
        cores = ["#6366f1"]*n_mot + ["#f59e0b"]*n_sta + ["#22c55e"]*len(destinos_u)
        fig_sk = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, line=dict(color="white",width=0.5),
                      label=todos_nos, color=cores),
            link=dict(source=src, target=tgt, value=val)
        ))
        fig_sk.update_layout(title_text="Fluxo de Trocas", font_size=11, height=420,
                             paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sk, use_container_width=True)
    else:
        st.info("Complete o destino de pelo menos uma troca para ver o fluxo Sankey.")

    # ── Resumo por tipo ───────────────────────────────────────────────────────
    st.markdown("#### 📑 Resumo por Tipo de Troca")
    df_tipo = df_conf.groupby("tipo_troca").agg(
        Quantidade=("id","count"),
        Resultado_Total=("resultado","sum"),
        Resultado_Medio=("resultado","mean"),
        Vantajosas=("vantajosa","sum"),
    ).reset_index()
    df_tipo["Taxa_Vantajosa_%"] = (df_tipo["Vantajosas"]/df_tipo["Quantidade"]*100).round(1)
    df_tipo["Resultado_Total"]  = df_tipo["Resultado_Total"].apply(_formatar_brl)
    df_tipo["Resultado_Medio"]  = df_tipo["Resultado_Medio"].apply(_formatar_brl)
    st.dataframe(df_tipo, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA 5 — CONFIGURAÇÕES (ADM)
# ══════════════════════════════════════════════════════════════════════════════

def _tab_config(is_adm):
    if not is_adm:
        st.warning("🔒 Área restrita a administradores.")
        return

    st.markdown("### ⚙️ Configurações do Módulo de Trocas")
    motivos    = carregar_motivos_troca()
    status_ret = carregar_status_retorno()
    destinos   = carregar_destinos()

    for titulo, lista, salvar_fn, key_prefix in [
        ("📌 Motivos / Autorizações", motivos,    salvar_motivos_troca,  "mot"),
        ("📦 Status de Retorno",      status_ret, salvar_status_retorno, "sr"),
        ("🏭 Destinos das Peças",     destinos,   salvar_destinos,       "dp"),
    ]:
        with st.expander(titulo, expanded=(key_prefix=="mot")):
            ca, cb = st.columns([4,1])
            novo = ca.text_input("Novo item:", key=f"nm_{key_prefix}",
                                 label_visibility="collapsed", placeholder="Nome...")
            if cb.button("➕ Adicionar", key=f"btn_{key_prefix}", use_container_width=True):
                if novo.strip() and novo.strip() not in lista:
                    lista.append(novo.strip())
                    salvar_fn(lista)
                    st.success("Adicionado!")
                    st.rerun()
            st.divider()
            for i, item in enumerate(lista):
                c1, c2 = st.columns([5,1])
                c1.markdown(f"▸ **{item}**")
                if c2.button("🗑️", key=f"del_{key_prefix}_{i}", help=f"Remover '{item}'"):
                    lista.pop(i)
                    salvar_fn(lista)
                    st.rerun()

    st.divider()
    st.markdown("#### ⚠️ Zona de Perigo")
    with st.expander("🗑️ Limpar Todos os Registros"):
        st.warning("Irreversível — apaga TODOS os registros de troca.")
        if st.button("🔥 CONFIRMAR LIMPEZA TOTAL", type="primary"):
            salvar_trocas([])
            st.success("Registros apagados.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def exibir(user_info):
    is_adm = user_info.get("role","").upper() in ("ADM","GERÊNCIA")

    st.markdown("""
    <style>
    .troca-badge { display:inline-block; padding:2px 8px;
                   border-radius:20px; font-size:11px; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📓 Diário de Trocas — King Star Colchões")

    trocas      = carregar_trocas()
    motivos     = carregar_motivos_troca()
    status_ret  = carregar_status_retorno()
    destinos    = carregar_destinos()
    tipos_troca = TIPOS_TROCA_PADRAO

    # Alertas rápidos
    pend_conf = sum(1 for t in trocas if t.get("status_retorno_peca") == "Pendente")
    pend_as   = sum(1 for t in trocas if t.get("destino_peca") == DESTINO_AS and not t.get("as_status"))
    if pend_conf:
        st.warning(f"⚠️ **{pend_conf} troca(s)** aguardando 1ª conferência.", icon="⏳")
    if pend_as:
        st.error(f"🔧 **{pend_as} peça(s)** na AS aguardando 2ª conferência.", icon="🔧")

    abas = ["➕ Cadastrar","🔄 Conferência","📋 Histórico","📊 Efetividade"]
    if is_adm:
        abas.append("⚙️ Config")

    tabs = st.tabs(abas)
    with tabs[0]: _tab_cadastro(trocas, motivos, tipos_troca, user_info)
    with tabs[1]: _tab_conferencia(trocas, status_ret, destinos)
    with tabs[2]: _tab_historico(trocas)
    with tabs[3]: _tab_dashboard(trocas)
    if is_adm and len(tabs) == 5:
        with tabs[4]: _tab_config(is_adm)
