import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
def inicializar_db():
    """Conecta ao Firebase usando as Secrets do Streamlit Cloud"""
    if "db" not in st.session_state:
        try:
            # O Streamlit Cloud lerá o JSON que você colará no campo 'textkey' das Secrets
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            # Mantendo o ID do seu projeto conforme solicitado
            st.session_state.db = firestore.Client(credentials=creds, project="bancowendley")
        except Exception as e:
            st.error(f"Erro de conexão com o Banco de Dados: {e}")
            return None
    return st.session_state.db

# --- GESTÃO DE USUÁRIOS ---
def carregar_usuarios_firebase():
    db = inicializar_db()
    if not db: return {}
    try:
        users_ref = db.collection("usuarios").stream()
        return {doc.id: doc.to_dict() for doc in users_ref}
    except: 
        return {}

def salvar_usuario(login, dados):
    db = inicializar_db()
    if db:
        db.collection("usuarios").document(login.lower().strip()).set(dados, merge=True)

def deletar_usuario(login):
    db = inicializar_db()
    if db:
        db.collection("usuarios").document(login).delete()

# --- GESTÃO DE CONFIGURAÇÕES GERAIS (Departamentos, Motivos, Projetos) ---
def carregar_config(documento, chave_dados, default=None):
    """Função genérica para reduzir repetição de código"""
    db = inicializar_db()
    if not db: return default if default is not None else []
    try:
        doc = db.collection("config").document(documento).get()
        if doc.exists:
            return doc.to_dict().get(chave_dados, default if default is not None else [])
        return default if default is not None else []
    except:
        return default if default is not None else []

def salvar_config(documento, chave_dados, lista):
    db = inicializar_db()
    if db:
        try:
            db.collection("config").document(documento).set({chave_dados: lista})
            return True
        except Exception as e:
            st.error(f"Erro ao salvar {documento}: {e}")
            return False
    return False

# --- DEPARTAMENTOS ---
def carregar_departamentos():
    return carregar_config("departamentos", "lista", ["GERAL", "TI", "RH", "OPERAÇÃO"])

def salvar_departamentos(lista):
    return salvar_config("departamentos", "lista", lista)

# --- PROJETOS ---
def carregar_projetos():
    return carregar_config("projetos_pqi", "dados", [])

def salvar_projetos(lista_projetos):
    return salvar_config("projetos_pqi", "dados", lista_projetos)

# --- DIÁRIO E ESFORÇO ---
def carregar_diario():
    return carregar_config("diario_situacoes", "dados", [])

def salvar_diario(lista_diario):
    return salvar_config("diario_situacoes", "dados", lista_diario)

def carregar_esforco():
    return carregar_config("esforco_logs", "dados", [])

def salvar_esforco(lista_esforco):
    return salvar_config("esforco_logs", "dados", lista_esforco)

# --- MÓDULO VEICULAR (SPIN) ---
def carregar_dados_spin():
    return carregar_config("spin_data", "dados", {"km_atual": 138000, "historico": []})

def salvar_dados_spin(dados):
    return salvar_config("spin_data", "dados", dados)

# --- TICKETS E MAILING ---
def carregar_mailing():
    return carregar_config("mailing_tickets", "dados", [])

def salvar_mailing(lista_mailing):
    return salvar_config("mailing_tickets", "dados", lista_mailing)

def carregar_motivos_config():
    return carregar_config("tickets_motivos", "dados", [])

def salvar_motivos_config(lista_motivos):
    return salvar_config("tickets_motivos", "dados", lista_motivos)

# --- GESTÃO DE ARQUIVOS (BLOB) ---
def salvar_arquivo_firestore(nome_arquivo, dados_binarios):
    db = inicializar_db()
    if db:
        try:
            doc_ref = db.collection("arquivos_pqi").document(nome_arquivo)
            doc_ref.set({
                "conteudo": dados_binarios,
                "data_upload": datetime.now()
            })
            return True
        except Exception as e:
            st.error(f"Erro ao salvar arquivo: {e}")
            return False
    return False

def baixar_arquivo_firestore(nome_arquivo):
    db = inicializar_db()
    if not db: return None
    try:
        doc = db.collection("arquivos_pqi").document(nome_arquivo).get()
        if doc.exists:
            return doc.to_dict().get("conteudo")
        return None
    except:
        return None
