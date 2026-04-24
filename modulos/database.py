import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL (Motor Original) ---
def inicializar_db():
    if "db" not in st.session_state:
        try:
            # Puxa a chave das Secrets do Streamlit
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            st.session_state.db = firestore.Client(credentials=creds, project="bancowendley")
        except Exception as e:
            st.error(f"Erro de Conexão com Firestore: {e}")
            return None
    return st.session_state.db

# --- GESTÃO DE USUÁRIOS ---
def carregar_usuarios_firebase():
    db = inicializar_db()
    if not db: return {}
    try:
        users_ref = db.collection("usuarios").stream()
        return {doc.id: doc.to_dict() for doc in users_ref}
    except Exception:
        return {}

def salvar_usuario(login, dados):
    db = inicializar_db()
    if db:
        # Garante que o login seja a chave do documento
        db.collection("usuarios").document(login.lower().strip()).set(dados, merge=True)

# --- ESFORÇO (Logs de Atividade) ---
def carregar_esforco():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("esforco_logs").get()
        if doc.exists:
            return doc.to_dict().get("dados", [])
        return []
    except Exception:
        return []

def salvar_esforco(lista_esforco):
    db = inicializar_db()
    if db:
        db.collection("config").document("esforco_logs").set({"dados": lista_esforco})

# --- DIÁRIO DE BORDO ---
def carregar_diario():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("diario_situacoes").get()
        if doc.exists:
            return doc.to_dict().get("dados", [])
        return []
    except Exception:
        return []

def salvar_diario(lista_diario):
    db = inicializar_db()
    if db:
        db.collection("config").document("diario_situacoes").set({"dados": lista_diario})

# --- DEPARTAMENTOS ---
def carregar_departamentos():
    db = inicializar_db()
    if not db: return ["Operação", "Logística", "RH", "TI"]
    try:
        doc = db.collection("config").document("departamentos").get()
        if doc.exists:
            return doc.to_dict().get("lista", ["Operação", "Logística", "RH", "TI"])
        return ["Operação", "Logística", "RH", "TI"]
    except Exception:
        return ["Geral"]

def salvar_departamentos(lista):
    db = inicializar_db()
    if db:
        db.collection("config").document("departamentos").set({"lista": lista})
