import streamlit as st
import pandas as pd
import zipfile
from datetime import datetime
from docx import Document
from io import BytesIO
from modulos import database as db  # Ajustado para sua nova estrutura

# --- FUNÇÕES DE NÚCLEO ---

def gerar_word_memoria(dados):
    try:
        # Busca o template na pasta assets (ajuste o caminho se necessário)
        template_path = "assets/carta_preenchida.docx"
        if not os.path.exists(template_path):
            # Se não houver pasta assets, tenta na raiz (fallback)
            template_path = "carta_preenchida.docx"
            
        doc = Document(template_path)
        for p in doc.paragraphs:
            for k, v in dados.items():
                if f"{{{{{k}}}}}" in p.text: 
                    p.text = p.text.replace(f"{{{{{k}}}}}", str(v))
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for k, v in dados.items():
                            if f"{{{{{k}}}}}" in p.text: 
                                p.text = p.text.replace(f"{{{{{k}}}}}", str(v))
        
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"⚠️ Erro ao processar Word: Verifique se o arquivo 'assets/carta_preenchida.docx' existe.")
        return None

# --- FUNÇÕES DE APOIO ---

def obter_base_colaboradores(fire):
    docs = fire.collection("colaboradores_base").stream()
    return {doc.id: doc.to_dict().get("cpf") for doc in docs}

def salvar_novo_colaborador(fire, nome, cpf):
    fire.collection("colaboradores_base").document(nome.upper().strip()).set({"cpf": str(cpf).strip()})

# --- INTERFACE PRINCIPAL ---

def exibir(user_role):
    # CSS ESTILO PREMIUM (Cinza Claro + Dourado)
    st.markdown("""
        <style>
        .metric-card {
            background-color: #F8F9FA;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #D4AF37;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .card-carta {
            background-color: #F8F9FA;
            padding: 20px;
            border-radius: 12px;
            border-top: 5px solid #D4AF37;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            min-height: 180px;
        }
        .loja-header {
            background-color: #495057;
            color: #D4AF37;
            padding: 8px 15px;
            border-radius: 8px;
            margin: 25px 0 15px 0;
            font-weight: bold;
        }
        .label-card { color: #6c757d; font-size: 0.85rem; margin-bottom: 2px; }
        .info-card { font-weight: 600; color: #212529; margin-bottom: 8px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📑 Gestão de Cartas de Débito")
    
    # Inicializa o DB usando sua lógica centralizada
    fire = db.inicializar_db()
    
    # --- CARREGAR DADOS ---
    def obter_cartas():
        docs = fire.collection("cartas_rh").stream()
        return [doc.to_dict() for doc in docs]

    cartas = obter_cartas()
    dict_colab = obter_base_colaboradores(fire)
    lista_nomes = sorted(list(dict_colab.keys()))

    tabs = st.tabs(["🆕 Nova Carta", "📋 Painel de Controle", "📦 Fechamento", "✅ Histórico", "⚙️ Config"])

    # 1. NOVA CARTA
    with tabs[0]:
        st.subheader("Informações do Lançamento")
        escolha_nome = st.selectbox("Busque ou selecione o Colaborador:", ["+ CADASTRAR NOVO"] + lista_nomes)
        
        with st.form("f_premium", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            if escolha_nome == "+ CADASTRAR NOVO":
                nome = c1.text_input("Nome do Colaborador").upper().strip()
                cpf = c2.text_input("CPF")
            else:
                nome = escolha_nome
                cpf = c2.text_input("CPF", value=dict_colab.get(escolha_nome, ""))
            
            cod_cli = c3.text_input("Código do Cliente")
            v1, v2, v3 = st.columns(3)
            valor = v1.number_input("Valor R$", min_value=0.0)
            loja = v2.text_input("Loja Origem").upper()
            data_c = v3.date_input("Data da Ocorrência")
            motivo = st.text_area("Motivo Detalhado").upper()
            
            if st.form_submit_button("✨ Gerar e Registrar"):
                if nome and cpf and cod_cli:
                    if escolha_nome == "+ CADASTRAR NOVO":
                        salvar_novo_colaborador(fire, nome, cpf)
                    
                    id_carta = datetime.now().strftime("%Y%m%d%H%M%S")
                    dados_fb = {
                        "id": id_carta, "NOME": nome, "CPF": cpf, "COD_CLI": cod_cli, 
                        "VALOR": valor, "LOJA": loja, "DATA": data_c.strftime("%d/%m/%Y"), 
                        "MOTIVO": motivo, "status": "Aguardando Assinatura", "anexo_bin": None,
                        "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    fire.collection("cartas_rh").document(id_carta).set(dados_fb)
                    st.success("Carta registrada com sucesso!")
                    st.rerun()

    # 2. PAINEL DE CONTROLE
    with tabs[1]:
        lista_painel = [c for c in cartas if c.get('status') == "Aguardando Assinatura"]
        
        if lista_painel:
            total_valor = sum(c['VALOR'] for c in lista_painel)
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="label-card">Pendentes</div><div style="font-size:1.5rem; font-weight:bold;">{len(lista_painel)} Unidades</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="label-card">Valor Total</div><div style="font-size:1.5rem; font-weight:bold; color:#D4AF37;">R$ {total_valor:,.2f}</div></div>', unsafe_allow_html=True)
            
            st.write("---")
            busca_p = st.text_input("🔍 Buscar no Painel (Nome/Código)")
            if busca_p:
                lista_painel = [c for c in lista_painel if busca_p.upper() in c['NOME'] or busca_p in str(c['COD_CLI'])]

            df_p = pd.DataFrame(lista_painel).sort_values(by="LOJA")
            
            for loja_n, group in df_p.groupby("LOJA"):
                st.markdown(f'<div class="loja-header">📍 {loja_n} ({len(group)} itens)</div>', unsafe_allow_html=True)
                
                cols = st.columns(3)
                for idx, (_, c) in enumerate(group.iterrows()):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        st.markdown(f"""
                            <div class="card-carta">
                                <div class="label-card">COLABORADOR</div>
                                <div class="info-card">{c['NOME']}</div>
                                <div class="label-card">VALOR</div>
                                <div style="font-size: 1.2rem; font-weight: bold; color: #D4AF37;">R$ {c['VALOR']:,.2f}</div>
                                <div class="label-card">DATA: {c['DATA']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Preparação dos dados para o Word
                        dados_w = {
                            "NOME_COLAB": c['NOME'], "CPF": c['CPF'], "CODIGO_CLIENTE": c['COD_CLI'], 
                            "VALOR_DEBITO": f"R$ {c['VALOR']:,.2f}", "LOJA_ORIGEM": c['LOJA'], 
                            "DATA_COMPRA": c['DATA'], "DESC_DEBITO": c['MOTIVO'], 
                            "DATA_LOCAL": f"São Paulo, {datetime.now().strftime('%d/%m/%Y')}"
                        }
                        
                        w_bytes = gerar_word_memoria(dados_w)
                        
                        btn_c1, btn_c2 = st.columns(2)
                        
                        # CORREÇÃO DO ERRO: Só exibe botão se bytes forem válidos
                        if w_bytes:
                            btn_c1.download_button("📂 Baixar", w_bytes, file_name=f"Carta_{c['NOME']}.docx", key=f"w_{c['id']}", use_container_width=True)
                        else:
                            btn_c1.error("DocX Off")

                        if user_role in ["ADM", "GERENTE"]:
                            if btn_c2.button("🗑️", key=f"del_{c['id']}", use_container_width=True, help="Excluir"):
                                fire.collection("cartas_rh").document(c['id']).delete()
                                st.rerun()
                        
                        up = st.file_uploader("Upload Assinada", key=f"up_{c['id']}", label_visibility="collapsed")
                        if up:
                            fire.collection("cartas_rh").document(c['id']).update({
                                "status": "CARTA RECEBIDA", 
                                "anexo_bin": up.getvalue(), 
                                "nome_arquivo": up.name
                            })
                            st.success("Recebida!")
                            st.rerun()
        else:
            st.info("Nenhuma carta aguardando assinatura no momento.")

    # [O restante das abas seguem a mesma lógica de migração e visual]
