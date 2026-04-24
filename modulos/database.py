import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import time
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
def inicializar_db():
    """Inicializa e persiste a conexão com o Firebase no session_state."""
    if "db" not in st.session_state:
        try:
            if "textkey" not in st.secrets:
                st.error("Chave 'textkey' não encontrada no st.secrets.")
                return None
                
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            st.session_state.db = firestore.Client(credentials=creds, project="bancowendley")
        except Exception as e:
            st.error(f"Erro crítico na inicialização do Firebase: {e}")
            return None
    return st.session_state.db

# --- FUNÇÕES DE USUÁRIOS ---

def carregar_usuarios_firebase():
    """Carrega usuários com sistema de retentativa para evitar quedas de login."""
    db = inicializar_db()
    if not db: return {}
    
    for tentativa in range(3):
        try:
            users_ref = db.collection("usuarios").stream()
            return {doc.id: doc.to_dict() for doc in users_ref}
        except Exception as e:
            if tentativa < 2:
                time.sleep(1)
                continue
            print(f"Erro ao carregar usuários (Tentativa {tentativa+1}): {e}")
            return {}

def salvar_usuario(uid, dados):
    db = inicializar_db()
    if db:
        # Remove espaços acidentais que impedem o login
        db.collection("usuarios").document(uid.strip()).set(dados, merge=True)

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
    if db: 
        db.collection("config").document("projetos_pqi").set({"dados": lista_projetos})

def carregar_diario():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("diario_situacoes").get()
        return doc.to_dict().get("dados", []) if doc.exists else []
    except: return []

def salvar_diario(lista_diario):
    db = inicializar_db()
    if db: 
        db.collection("config").document("diario_situacoes").set({"dados": lista_diario})

# --- GESTÃO DE ESFORÇO E MOTIVOS ---

def carregar_esforco():
    db = inicializar_db()
    if not db: return []
    try:
        doc = db.collection("config").document("esforco_logs").get()
        return doc.to_dict().get("dados", []) if doc.exists else []
    except: return []

def salvar_esforco(lista_esforco):
    db = inicializar_db()
    if db: 
        db.collection("config").document("esforco_logs").set({"dados": lista_esforco})

def carregar_motivos():
    db = inicializar_db()
    padrao = ["PROJETO", "REUNIÃO", "OUTROS"]
    if not db: return padrao
    try:
        doc = db.collection("config").document("esforco_motivos").get()
        return doc.to_dict().get("lista", padrao) if doc.exists else padrao
    except: return padrao

def salvar_motivos(lista):
    db = inicializar_db()
    if db: 
        db.collection("config").document("esforco_motivos").set({"lista": lista})

# --- DEPARTAMENTOS ---

def carregar_departamentos():
    db = inicializar_db()
    padrao = ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA", "CX"]
    if not db: return padrao
    try:
        doc = db.collection("config").document("departamentos").get()
        if doc.exists:
            return doc.to_dict().get("lista", padrao)
    except: pass
    return padrao

def salvar_departamentos(lista):
    db = inicializar_db()
    if db:
        db.collection("config").document("departamentos").set({"lista": lista})

# --- VEÍCULO (SPIN) ---

def carregar_dados_spin():
    db = inicializar_db()
    default_spin = {"km_atual": 138000, "historico": []}
    if not db: return default_spin
    try:
        doc = db.collection("config").document("spin_data").get()
        return doc.to_dict() if doc.exists else default_spin
    except: return default_spin

def salvar_dados_spin(dados):
    db = inicializar_db()
    if db:
        db.collection("config").document("spin_data").set(dados)
