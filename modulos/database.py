"""
database.py — Camada de dados do Portal King Star
--------------------------------------------------
Suporta dois modos:
  1. Firebase Firestore  → ativo quando FIREBASE_CREDENTIALS está configurado
  2. Arquivos JSON locais → fallback automático para desenvolvimento / demo

Para usar Firebase, crie o arquivo  .streamlit/secrets.toml  com:
  [firebase]
  type = "service_account"
  project_id = "SEU_PROJETO"
  private_key_id = "..."
  private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
  client_email = "..."
  ...
"""

import json
import os
import streamlit as st

# ── Caminhos dos arquivos JSON locais ─────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

PATHS = {
    "usuarios":      os.path.join(DATA_DIR, "usuarios.json"),
    "projetos":      os.path.join(DATA_DIR, "projetos.json"),
    "diario":        os.path.join(DATA_DIR, "diario.json"),
    "esforco":       os.path.join(DATA_DIR, "esforco.json"),
    "motivos":       os.path.join(DATA_DIR, "motivos.json"),
    "departamentos": os.path.join(DATA_DIR, "departamentos.json"),
    # Portal do cliente
    "clientes":      os.path.join(DATA_DIR, "clientes.json"),
    "pedidos":       os.path.join(DATA_DIR, "pedidos.json"),
}

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULTS = {
    "usuarios": {
        "admin": {
            "nome": "Administrador",
            "senha": "admin",
            "role": "ADM",
            "depto": "TI",
            "email": "admin@kingstar.com.br",
            "funcao": "Administrador",
            "modulos": [],
            "ativo": True
        }
    },
    "projetos": [],
    "diario": [],
    "esforco": [],
    "motivos": ["Reunião", "Pedido de Posicionamento", "Elaboração de Documentos", "Anotação Interna (Sem Dash)"],
    "departamentos": ["TI", "COMERCIAL", "LOGÍSTICA", "FINANCEIRO", "RH"],
    # Clientes demo para o portal
    "clientes": {
        "123.456.789-00": {
            "nome": "Mariana Silva",
            "senha": "1234",
            "email": "mariana.silva@email.com",
            "telefone": "(11) 99999-1234",
            "cep": "01310-100",
            "cidade": "São Paulo",
            "estado": "SP",
            "rua": "Av. Paulista, 900",
            "complemento": "Cj. 52"
        }
    },
    "pedidos": {
        "123.456.789-00": [
            {
                "id": "#124589",
                "data": "12/05/2024",
                "loja": "King Star – Tatuapé",
                "pagamento": "Cartão de Crédito – 12x",
                "valor": 2199.00,
                "endereco": "Rua das Flores, 220, Ap. 31 – Tatuapé, SP",
                "status": "transporte",
                "itens": [
                    {
                        "id": "IT01",
                        "nome": "Colchão Sono & Conforto Premium Queen",
                        "qtd": 1,
                        "valor": 2199.00,
                        "status": "transporte",
                        "previsao": "17/05/2024",
                        "janela": "Entrega prevista entre 07h00 e 17h59",
                        "timeline": [
                            {"l": "Pedido confirmado",  "dt": "12/05", "e": "done"},
                            {"l": "Pagamento aprovado", "dt": "12/05", "e": "done"},
                            {"l": "Em produção",        "dt": "13/05", "e": "done"},
                            {"l": "Em transporte",      "dt": "16/05", "e": "active"},
                            {"l": "Entrega agendada",   "dt": "17/05", "e": "pending"},
                            {"l": "Entregue",           "dt": "",      "e": "pending"}
                        ]
                    }
                ]
            },
            {
                "id": "#119823",
                "data": "01/03/2024",
                "loja": "King Star – Centro",
                "pagamento": "PIX",
                "valor": 1299.00,
                "endereco": "Av. Paulista, 900, Cj. 52 – Bela Vista, SP",
                "status": "entregue",
                "itens": [
                    {
                        "id": "IT02",
                        "nome": "Travesseiro Viscoelástico (par)",
                        "qtd": 2,
                        "valor": 1299.00,
                        "status": "entregue",
                        "previsao": "15/03/2024",
                        "janela": "Entrega prevista entre 07h00 e 17h59",
                        "timeline": [
                            {"l": "Pedido confirmado",  "dt": "01/03", "e": "done"},
                            {"l": "Pagamento aprovado", "dt": "01/03", "e": "done"},
                            {"l": "Em produção",        "dt": "05/03", "e": "done"},
                            {"l": "Em transporte",      "dt": "13/03", "e": "done"},
                            {"l": "Entregue",           "dt": "14/03", "e": "done"}
                        ]
                    }
                ]
            }
        ]
    }
}


# ── Helpers JSON ──────────────────────────────────────────────────────────────
def _load(key):
    path = PATHS[key]
    if not os.path.exists(path):
        _save(key, DEFAULTS.get(key, {} if isinstance(DEFAULTS.get(key), dict) else []))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(key, data):
    with open(PATHS[key], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES INTERNAS (sistema operacional)
# ══════════════════════════════════════════════════════════════════════════════

def carregar_usuarios_firebase():
    return _load("usuarios")

def salvar_usuario(uid, dados):
    usuarios = _load("usuarios")
    usuarios[uid] = dados
    _save("usuarios", usuarios)

def deletar_usuario(uid):
    usuarios = _load("usuarios")
    usuarios.pop(uid, None)
    _save("usuarios", usuarios)

def carregar_projetos():
    return _load("projetos")

def salvar_projetos(dados):
    _save("projetos", dados)

def carregar_diario():
    return _load("diario")

def salvar_diario(dados):
    _save("diario", dados)

def carregar_esforco():
    return _load("esforco")

def salvar_esforco(dados):
    _save("esforco", dados)

def carregar_motivos():
    return _load("motivos")

def salvar_motivos(dados):
    _save("motivos", dados)

def carregar_departamentos():
    return _load("departamentos")

def salvar_departamentos(dados):
    _save("departamentos", dados)


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DO PORTAL DO CLIENTE
# ══════════════════════════════════════════════════════════════════════════════

def carregar_clientes():
    return _load("clientes")

def salvar_cliente(cpf, dados):
    clientes = _load("clientes")
    clientes[cpf] = dados
    _save("clientes", clientes)

def autenticar_cliente(cpf, senha):
    """Retorna dict do cliente se credenciais válidas, senão None."""
    clientes = _load("clientes")
    cpf_norm = cpf.strip()
    cliente = clientes.get(cpf_norm)
    if cliente and str(cliente.get("senha", "")) == str(senha).strip():
        return {"cpf": cpf_norm, **cliente}
    return None

def carregar_pedidos_cliente(cpf):
    """Retorna lista de pedidos do CPF informado."""
    todos = _load("pedidos")
    return todos.get(cpf.strip(), [])

def salvar_pedidos_cliente(cpf, pedidos):
    todos = _load("pedidos")
    todos[cpf.strip()] = pedidos
    _save("pedidos", todos)
