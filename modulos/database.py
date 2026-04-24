import streamlit as st
import requests
import json

# SUBSTITUA PELA SUA URL REAL DO FIREBASE
FIREBASE_URL = "https://seu-projeto-firebase.firebaseio.com/"

# --- USUÁRIOS ---
def carregar_usuarios_firebase():
    try:
        response = requests.get(f"{FIREBASE_URL}/usuarios.json")
        return response.json() if response.json() else {}
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        return {}

def salvar_usuario(login, dados):
    try:
        requests.put(f"{FIREBASE_URL}/usuarios/{login}.json", json=dados)
    except Exception as e:
        st.error(f"Erro ao salvar usuário: {e}")

# --- ESFORÇO (Logs de Atividade) ---
def carregar_esforco():
    try:
        response = requests.get(f"{FIREBASE_URL}/esforco.json")
        res_json = response.json()
        return res_json if isinstance(res_json, list) else []
    except Exception:
        return []

def salvar_esforco(logs):
    try:
        requests.put(f"{FIREBASE_URL}/esforco.json", json=logs)
    except Exception as e:
        st.error(f"Erro ao salvar esforço: {e}")

# --- DIÁRIO DE BORDO ---
def carregar_diario():
    try:
        response = requests.get(f"{FIREBASE_URL}/diario.json")
        res_json = response.json()
        return res_json if isinstance(res_json, list) else []
    except Exception:
        return []

def salvar_diario(diario):
    try:
        requests.put(f"{FIREBASE_URL}/diario.json", json=diario)
    except Exception as e:
        st.error(f"Erro ao salvar diário: {e}")

# --- CONFIGURAÇÕES GERAIS ---
def carregar_departamentos():
    try:
        response = requests.get(f"{FIREBASE_URL}/configuracoes/departamentos.json")
        res_json = response.json()
        return res_json if res_json else ["Operação", "Logística", "RH", "TI"]
    except Exception:
        return ["Geral"]

def salvar_departamentos(lista):
    try:
        requests.put(f"{FIREBASE_URL}/configuracoes/departamentos.json", json=lista)
    except Exception as e:
        st.error(f"Erro ao salvar departamentos: {e}")
