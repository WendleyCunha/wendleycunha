import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
from datetime import datetime

def inicializar_db():
    if "db" not in st.session_state:
        try:
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            st.session_state.db = firestore.Client(credentials=creds, project="bancowendley")
        except Exception as e:
            st.error(f"Erro no Firebase: {e}")
            return None
    return st.session_state.db

# --- FUNÇÕES DE USUÁRIOS ---

def carregar_usuarios_firebase():
    db = inicializar_db()
    if not db: return {}
    try:
        users_ref = db.collection("usuarios").stream()
        return {doc.id: doc.to_dict() for doc in users_ref}
    except: return {}

def salvar_usuario(uid, dados):
    db = inicializar_db()
    if db:
        db.collection("usuarios").document(uid).set(dados, merge=True)

def deletar_usuario(uid):
    db = inicializar_db()
    if db:
        db.collection("usuarios").document(uid).delete()

# --- FUNÇÕES DE CONFIGURAÇÃO E LOGS ---

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

def carregar_motivos():
    db = inicializar_db()
    if not db: return ["PROJETO", "REUNIÃO", "OUTROS"]
    try:
        doc = db.collection("config").document("esforco_motivos").get()
        return doc.to_dict().get("lista", ["PROJETO", "REUNIÃO", "OUTROS"]) if doc.exists else ["PROJETO", "REUNIÃO", "OUTROS"]
    except: return ["PROJETO", "REUNIÃO", "OUTROS"]

def salvar_motivos(lista):
    db = inicializar_db()
    if db: db.collection("config").document("esforco_motivos").set({"lista": lista})

# --- DEPARTAMENTOS (Ajustado para usar inicializar_db) ---

def carregar_departamentos():
    db = inicializar_db()
    if not db: return ["OPERAÇÃO", "TI", "RH"]
    try:
        # Mantive a coleção 'config' para seguir o padrão das outras funções
        doc = db.collection("config").document("departamentos").get()
        if doc.exists:
            return doc.to_dict().get("lista", ["OPERAÇÃO", "TI", "RH"])
    except:
        pass
    return ["OPERAÇÃO", "TI", "RH"]

def salvar_departamentos(lista):
    db = inicializar_db()
    if db:
        db.collection("config").document("departamentos").set({"lista": lista})

# --- VEÍCULO (SPIN) ---

def carregar_dados_spin():
    db = inicializar_db()
    if not db: return {"km_atual": 138000, "historico": []}
    try:
        doc = db.collection("config").document("spin_data").get()
        return doc.to_dict() if doc.exists else {"km_atual": 138000, "historico": []}
    except: return {"km_atual": 138000, "historico": []}

def salvar_dados_spin(dados):
    db = inicializar_db()
    if db:
        db.collection("config").document("spin_data").set(dados)
