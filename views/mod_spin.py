import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from modulos import database as db
import pytz

def exibir_tamagotchi(user_info):
    fuso_brasil = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_brasil)
    data_hoje_str = agora.strftime("%d/%m/%Y %H:%M")

    if 'dados_spin' not in st.session_state:
        st.session_state.dados_spin = db.carregar_dados_spin()

    km_atual = st.session_state.dados_spin.get('km_atual', 138000)
    historico = st.session_state.dados_spin.get('historico', [])
    inspecoes = st.session_state.dados_spin.get('inspecoes', [])

    REGRAS_MANUTENCAO = {
        "Óleo Motor (5W30)": [5000, 6], 
        "Filtros (Ar/Comb/Óleo)": [10000, 12],
        "Velas e Cabos": [30000, 24],
        "Correia Dentada": [50000, 48],
        "Bomba D'água": [50000, 48],
        "Válvula Termostática": [40000, 36],
        "Bobina de Ignição": [60000, 48],
        "Fluido Câmbio (GF6)": [40000, 24],
        "Arrefecimento (Aditivo Rosa)": [30000, 24],
        "Fluido de Freio": [20000, 12],
        "Pneus (Rodízio)": [10000, 6],
        "Sonda Lambda": [80000, 60]
    }

    CATEGORIAS = {
        "Abastecimento": ["Gasolina", "Etanol", "GNV"],
        "Manutenção Preventiva": list(REGRAS_MANUTENCAO.keys()),
        "Manutenção Corretiva": ["Suspensão", "Freios", "Elétrica", "Ar Condicionado"],
        "Outros": ["IPVA/Seguro", "Estética", "Upgrades"]
    }

    # CSS
    st.markdown(f"""
        <style>
        .main {{ background-color: #f1f5f9; }}
        .relogio {{ background: #0f172a; padding: 15px; border-radius: 12px; text-align: right; color: #38bdf8; font-family: monospace; border: 1px solid #1e293b; margin-bottom: 25px; }}
        .stMetric {{ background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
        .card-saude {{ padding: 15px; border-radius: 15px; background: white; border-left: 6px solid #e2e8f0; margin-bottom: 10px; }}
        @keyframes blinker {{ 50% {{ opacity: 0.4; }} }}
        .critico {{ border-left-color: #ef4444 !important; animation: blinker 2s linear infinite; background: #fef2f2; }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='relogio'>🛰️ SENSOR SPIN ATIVO | {data_hoje_str}</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("🎮 Controle de KM")
        novo_km = st.number_input("Odômetro Atual:", value=km_atual, step=10)
        if novo_km != km_atual:
            st.session_state.dados_spin['km_atual'] = novo_km
            db.salvar_dados_spin(st.session_state.dados_spin)
            st.rerun()
        st.divider()
        st.info("💡 Perito: Na Spin, barulho de 'maquina de costura' pode ser tucho ou comando seco. Atenção ao óleo!")

    tab_dash, tab_registro, tab_saude, tab_inspecao = st.tabs(["📊 DASHBOARD", "📝 LANÇAR", "🩺 SAÚDE VITAL", "🔍 INSPEÇÃO"])

    df_base = pd.DataFrame(historico) if historico else pd.DataFrame()

    with tab_dash:
        if not df_base.empty:
            st.markdown("### 📅 Filtro de Período")
            df_base['Data'] = pd.to_datetime(df_base['Data'])
            hoje = datetime.now().date()
            
            data_inicio_mes = hoje.replace(day=14)
            if data_inicio_mes > hoje:
                mes_anterior = (hoje.month - 2) % 12 + 1
                ano_ajuste = hoje.year if hoje.month > 1 else hoje.year - 1
                data_inicio_mes = data_inicio_mes.replace(month=mes_anterior, year=ano_ajuste)

            opcoes_periodo = {
                "Últimos 7 Dias": hoje - pd.Timedelta(days=7),
                "Último Mês (30 dias)": hoje - pd.Timedelta(days=30),
                f"Ciclo Atual (Desde {data_inicio_mes.strftime('%d/%m')})": data_inicio_mes,
                "Geral (Todo o Histórico)": df_base['Data'].min().date()
            }
            
            selecao = st.radio("Selecione o horizonte:", list(opcoes_periodo.keys()), horizontal=True)
            data_limite = pd.to_datetime(opcoes_periodo[selecao])
            df_dash = df_base[df_base['Data'] >= data_limite].copy()

            df_combustivel = df_dash[df_dash['Litros'] > 0].sort_values('KM')
            media_periodo = 0
            if len(df_combustivel) > 1:
                total_litros = df_combustivel['Litros'].iloc[1:].sum()
                total_km_rodados = df_combustivel['KM'].iloc[-1] - df_combustivel['KM'].iloc[0]
                media_periodo = total_km_rodados / total_litros if total_litros > 0 else 0

            total_gasto = df_dash['Real'].sum()
            km_no_periodo = df_dash['KM'].max() - df_dash['KM'].min() if not df_dash.empty else 0
            custo_por_km = total_gasto / km_no_periodo if km_no_periodo > 0 else 0
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gasto no Período", f"R$ {total_gasto:,.2f}")
            c2.metric("Custo por KM", f"R$ {custo_por_km:,.2f}")
            c3.metric("Média Consumo", f"{media_periodo:.2f} km/l" if media_periodo > 0 else "---")
            c4.metric("Último KM", f"{km_atual:,} KM")

            st.divider()
            col_esq, col_dir = st.columns([1.5, 1])
            with col_esq:
                fig_timeline = px.area(df_dash.sort_values('Data'), x='Data', y='Real', color='Tipo',
                                      title=f"Investimentos: {selecao}", color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                if not df_combustivel.empty:
                    with st.expander("⛽ Detalhes de Abastecimento do Período", expanded=False):
                        df_tec = df_combustivel.copy()
                        df_tec['KM_L'] = df_tec['KM'].diff() / df_tec['Litros'].shift(1)
                        st.dataframe(df_tec[['Data', 'Item', 'Litros', 'KM_L']].sort_values('Data', ascending=False), use_container_width=True)
            
            with col_dir:
                fig_pie = px.sunburst(df_dash, path=['Tipo', 'Item'], values='Real', title="Distribuição de Custos")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.subheader(f"📋 Registros: {selecao}")
            st.dataframe(df_dash.sort_values('Data', ascending=False), use_container_width=True)
        else:
            st.warning("Sem dados para processar o dashboard. Vá em 'Lançar'.")

    with tab_registro:
        st.subheader("Novo Lançamento Financeiro")
        baixa_em_curso = st.session_state.get('baixa_em_curso', None)
        
        if baixa_em_curso:
            st.warning(f"Finalizando pendência: **{baixa_em_curso['item']}**")
        
        tipo_sel = st.selectbox("Categoria do Gasto:", list(CATEGORIAS.keys()))
        
        with st.form("form_registro_perito", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            item_default = baixa_em_curso['item'] if baixa_em_curso else CATEGORIAS[tipo_sel][0]
            item_f = col_a.text_input("Item/Serviço:", value=item_default)
            valor_f = col_b.number_input("Valor Real (R$):", min_value=0.0)
            col_c, col_d = st.columns(2)
            km_f = col_c.number_input("KM no momento:", value=km_atual)
            litros_f = col_d.number_input("Litros (se abastecimento):", min_value=0.0)
            
            if st.form_submit_button("✅ CONFIRMAR REGISTRO"):
                novo_evento = {
                    "Data": agora.strftime("%Y-%m-%d"),
                    "Tipo": tipo_sel,
                    "Item": item_f,
                    "KM": km_f,
                    "Real": float(valor_f),
                    "Litros": float(litros_f)
                }
                st.session_state.dados_spin['historico'].append(novo_evento)
                if baixa_em_curso:
                    st.session_state.dados_spin['inspecoes'].pop(baixa_em_curso['index'])
                    del st.session_state['baixa_em_curso']
                db.salvar_dados_spin(st.session_state.dados_spin)
                st.success("Dados salvos com sucesso!")
                st.rerun()

    with tab_saude:
        st.subheader("Status de Fadiga dos Componentes")
        cols = st.columns(3)
        for idx, (peca, limites) in enumerate(REGRAS_MANUTENCAO.items()):
            km_ref = 127000
            data_ref = datetime(2025, 1, 1, tzinfo=fuso_brasil)
            
            if not df_base.empty and peca in df_base['Item'].values:
                last = df_base[df_base['Item'] == peca].sort_values('KM', ascending=False).iloc[0]
                km_ref = last['KM']
                dt_temp = last['Data']
                if isinstance(dt_temp, str):
                    data_ref = datetime.strptime(dt_temp, "%Y-%m-%d").replace(tzinfo=fuso_brasil)
                elif hasattr(dt_temp, 'to_pydatetime'):
                    data_ref = dt_temp.to_pydatetime().replace(tzinfo=fuso_brasil)
                else:
                    data_ref = dt_temp.replace(tzinfo=fuso_brasil)
            
            vida_km = 100 - ((km_atual - km_ref) / limites[0] * 100)
            vida_tempo = 100 - ((agora - data_ref).days / (limites[1] * 30) * 100)
            saude_final = max(0, int(min(vida_km, vida_tempo)))
            
            cor = "#ef4444" if saude_final <= 20 else "#f59e0b" if saude_final <= 50 else "#10b981"
            classe = "card-saude critico" if saude_final <= 20 else "card-saude"
            
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class='{classe}'>
                        <b style='font-size: 0.85rem; color: #475569;'>{peca.upper()}</b><br>
                        <span style='font-size: 1.8rem; font-weight: bold; color: {cor};'>{saude_final}%</span><br>
                        <small style='color: #94a3b8;'>Próxima: {int(km_ref + limites[0]):,} KM</small>
                    </div>
                """, unsafe_allow_html=True)

    with tab_inspecao:
        st.subheader("Checklist de Campo (Ouvido e Olho)")
        with st.form("f_insp"):
            c1, c2 = st.columns(2)
            i_it = c1.selectbox("Item:", ["Vazamento de Água (Mangueiras)", "Vazamento de Óleo (Junta)", "Barulho na Correia", "Estalo na Direção", "Coxim do Motor"])
            i_st = c2.select_slider("Estado:", options=["🚨 Ruim", "⚠️ Observar", "✅ OK"])
            i_obs = st.text_area("Notas Técnicas do Perito:")
            if st.form_submit_button("Registrar Inspeção"):
                st.session_state.dados_spin['inspecoes'].append({
                    "Data": agora.strftime("%d/%m/%Y"), "Item": i_it, "Status": i_st, "Obs": i_obs, "KM": km_atual
                })
                db.salvar_dados_spin(st.session_state.dados_spin)
                st.rerun()
        
        st.divider()
        for idx, insp in enumerate(reversed(inspecoes)):
            with st.expander(f"{insp['Data']} - {insp['Item']} ({insp['Status']})"):
                st.write(f"**KM:** {insp['KM']}")
                st.write(f"**Notas:** {insp['Obs']}")
                if st.button("💸 Dar Baixa (Gerar Gasto)", key=f"bx_{idx}"):
                    st.session_state['baixa_em_curso'] = {'item': insp['Item'], 'index': len(inspecoes)-1-idx}
                    st.rerun()
