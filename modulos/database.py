import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
def inicializar_db():
    if "db" not in st.session_state:
        try:
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            st.session_state.db = firestore.Client(credentials=creds, project="bancowendley")
        except Exception as e:
            st.error(f"Erro de Conexão com Firestore: {e}")
            return None
    return st.session_state.db

# --- USUÁRIOS ---
def carregar_usuarios_firebase():
    db = inicializar_db()
    if not db: return {}
    try:
        users_ref = db.collection("usuarios").stream()
        return {doc.id: doc.to_dict() for doc in users_ref}
    except Exception: return {}

# --- ESFORÇO ---
def carregar_esforco():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("esforco_logs").get()
        return doc.to_dict().get("dados", []) if doc.exists else []
    except: return []

def salvar_esforco(lista_esforco):
    db = inicializar_db()
    if db: db.collection("config").document("esforco_logs").set({"dados": lista_esforco})

# --- PROJETOS (A função que faltava) ---
def carregar_projetos():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("projetos_pqi").get()
        return doc.to_dict().get("dados", []) if doc.exists else []
    except: return []

def salvar_projetos(lista_projetos):
    db = inicializar_db()
    if db: db.collection("config").document("projetos_pqi").set({"dados": lista_projetos})

# --- DIÁRIO ---
def carregar_diario():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("diario_situacoes").get()
        return doc.to_dict().get("dados", []) if doc.exists else []
    except: return []

def salvar_diario(lista_diario):
    db = inicializar_db()
    if db: db.collection("config").document("diario_situacoes").set({"dados": lista_diario})

# --- CONFIGURAÇÕES GERAIS ---
def carregar_motivos():
    db = inicializar_db()
    if not db: return ["PROJETO", "REUNIÃO", "OUTROS"]
    try:
        doc = db.collection("config").document("esforco_motivos").get()
        return doc.to_dict().get("lista", ["PROJETO", "REUNIÃO", "OUTROS"]) if doc.exists else ["PROJETO", "REUNIÃO", "OUTROS"]
    except: return ["PROJETO", "REUNIÃO", "OUTROS"]

def carregar_departamentos():
    db = inicializar_db()
    if not db: return ["GERAL"]
    try:
        doc = db.collection("config").document("departamentos").get()
        return doc.to_dict().get("lista", ["GERAL"]) if doc.exists else ["GERAL"]
    except: return ["GERAL"]
