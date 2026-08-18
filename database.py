"""
database.py — Sistema de Rastreio (projeto Firebase: bancowendley)
Conexão única com o Firestore + todas as funções de leitura/escrita usadas
pelo sistema. Deliberadamente ENXUTO: só o que o Rastreio precisa — sem
Tickets, Cartas, Home, Diagnóstico (esses módulos não fazem parte deste
sistema; se um dia precisar deles, veja o projeto "king"/"portal").

Usa o banco Firestore PADRÃO ("(default)") do projeto — não um banco
nomeado — para não depender de nenhuma configuração extra além de ativar
o Firestore em modo Nativo no Console do Firebase.
"""
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json, hashlib, requests
from datetime import datetime, timezone, timedelta

BRT = timezone(timedelta(hours=-3))


def get_db():
    if "db" not in st.session_state:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        st.session_state.db = firestore.Client(credentials=creds, project=creds.project_id)
    return st.session_state.db


def hash_senha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _normalizar_login(usuario: str) -> str:
    """Login sempre em minúsculas e sem espaços — evita o clássico 'cadastrei
    com maiúscula, motorista digita minúsculo e não consegue entrar'."""
    return (usuario or "").strip().lower()


def _normalizar_senha(senha: str) -> str:
    return (senha or "").strip()


# ── Papéis: só "adm" e "motorista" neste sistema (enxuto de propósito) ──
def pode_editar(user: dict) -> bool:
    return user.get("role") == "adm"


def pode_deletar(user: dict) -> bool:
    return user.get("role") == "adm"


def pode_exportar(user: dict) -> bool:
    return user.get("role") == "adm"


# ── Auth ──────────────────────────────────────────────────────────
def verificar_login(usuario: str, senha: str):
    """
    Login de admin fixo (admin/admin123) NÃO toca no Firestore — sempre
    funciona, mesmo com a cota de leitura esgotada ou o banco fora do ar.
    Qualquer outro login (motoristas cadastrados) lê o Firestore normalmente.
    """
    usuario_original = (usuario or "").strip()
    usuario_norm = _normalizar_login(usuario)
    senha = _normalizar_senha(senha)

    if usuario_norm == "admin" and senha == "admin123":
        return {"nome": "Administrador", "usuario": "admin", "role": "adm"}

    db = get_db()
    doc = db.collection("usuarios").document(usuario_norm).get()

    if not doc.exists and usuario_original and usuario_original != usuario_norm:
        doc = db.collection("usuarios").document(usuario_original).get()

    if doc.exists:
        d = doc.to_dict()
        if d.get("senha_hash") == hash_senha(senha):
            return d
    return None


def criar_usuario(nome, usuario, senha, role="motorista", placa=""):
    """Cria um motorista (ou outro admin, se precisar). Retorna o login
    final (normalizado) — use esse valor pra qualquer coisa que precise
    bater com o documento certo depois (ex: vincular nome de exibição)."""
    usuario = _normalizar_login(usuario)
    senha = _normalizar_senha(senha)
    get_db().collection("usuarios").document(usuario).set({
        "nome": nome, "usuario": usuario,
        "senha_hash": hash_senha(senha),
        "role": role, "placa": placa,
    })
    listar_usuarios.clear()
    return usuario


def atualizar_dados_usuario(usuario: str, nome: str = None, placa: str = None):
    campos = {}
    if nome is not None and nome.strip():
        campos["nome"] = nome.strip()
    if placa is not None:
        campos["placa"] = placa.strip()
    if campos:
        get_db().collection("usuarios").document(usuario).update(campos)
        listar_usuarios.clear()


def redefinir_senha_usuario(usuario: str, nova_senha: str):
    if usuario == "admin":
        return False, "A senha do admin master não pode ser alterada aqui."
    nova_senha = _normalizar_senha(nova_senha)
    doc = get_db().collection("usuarios").document(usuario).get()
    if not doc.exists:
        return False, "Usuário não encontrado."
    get_db().collection("usuarios").document(usuario).update(
        {"senha_hash": hash_senha(nova_senha)}
    )
    listar_usuarios.clear()
    return True, "Senha redefinida com sucesso."


def alterar_senha_usuario(usuario: str, senha_atual: str, nova_senha: str):
    if usuario == "admin":
        return False, "A senha do admin master não pode ser alterada aqui."
    senha_atual = _normalizar_senha(senha_atual)
    nova_senha = _normalizar_senha(nova_senha)
    doc = get_db().collection("usuarios").document(usuario).get()
    if not doc.exists:
        return False, "Usuário não encontrado."
    d = doc.to_dict()
    if d.get("senha_hash") != hash_senha(senha_atual):
        return False, "Senha atual incorreta."
    get_db().collection("usuarios").document(usuario).update(
        {"senha_hash": hash_senha(nova_senha)}
    )
    listar_usuarios.clear()
    return True, "Senha alterada com sucesso! Faça login novamente."


@st.cache_data(ttl=15, show_spinner=False)
def listar_usuarios():
    return [d.to_dict() for d in get_db().collection("usuarios").stream()]


def deletar_usuario(usuario):
    get_db().collection("usuarios").document(usuario).delete()
    listar_usuarios.clear()


# ── Entregas ──────────────────────────────────────────────────────
# TTL curto (8s): absorve vários cliques seguidos sem reler o Firestore a
# cada rerun da tela, mas curto o bastante pra não esconder uma baixa ou
# upload recém-feitos — e de qualquer forma salvar_entregas_db/
# dar_baixa_entrega_db chamam .clear() nessas duas funções assim que algo
# muda, então a atualização aparece na hora mesmo com o cache ativo.
@st.cache_data(ttl=8, show_spinner=False)
def obter_tickets_db(data_alvo: str) -> list:
    docs = get_db().collection("entregas").where("data_entrega", "==", data_alvo).stream()
    return [d.to_dict().get("payload", d.to_dict()) for d in docs]


@st.cache_data(ttl=8, show_spinner=False)
def obter_tickets_com_id_db(data_alvo: str) -> list:
    """Igual a obter_tickets_db, mas cada item vem com '_doc_id' — necessário
    pro motorista dar baixa numa entrega específica e pro Rastreio ao Vivo
    saber qual entrega ativar."""
    docs = get_db().collection("entregas").where("data_entrega", "==", data_alvo).stream()
    out = []
    for d in docs:
        item = dict(d.to_dict().get("payload", d.to_dict()))
        item["_doc_id"] = d.id
        out.append(item)
    return out


@st.cache_data(ttl=60, show_spinner=False)
def obter_datas_disponiveis_db() -> list:
    docs = get_db().collection("entregas").select(["data_entrega"]).stream()
    datas: dict = {}
    for d in docs:
        v = d.to_dict().get("data_entrega")
        if v:
            datas[v] = datas.get(v, 0) + 1
    return [{"data": k, "total": v} for k, v in sorted(datas.items(), reverse=True)]


# ── De-Para motoristas (nome de exibição por placa/rota) ───────────
# Cacheado (30s): sem cache, cada linha da tabela do Dashboard fazia 1
# leitura nova no Firestore em todo rerun.
@st.cache_data(ttl=30, show_spinner=False)
def obter_vinculo_db(chave: str) -> str:
    doc = get_db().collection("de_para_motoristas").document(chave).get()
    return doc.to_dict().get("nome_motorista", chave) if doc.exists else chave


def salvar_vinculo_db(chave: str, nome: str):
    get_db().collection("de_para_motoristas").document(chave).set({"nome_motorista": nome})
    obter_vinculo_db.clear()


def deletar_rota_db(rota: str, data: str):
    """Campo salvo nas entregas é 'route' (inglês). Trata também o formato
    com wrapper 'payload' (compatibilidade com fontes externas)."""
    db = get_db()
    batch = db.batch()
    encontrou = False

    for d in db.collection("entregas").where("route", "==", rota).where("data_entrega", "==", data).stream():
        batch.delete(d.reference)
        encontrou = True
    for d in db.collection("entregas").where("payload.route", "==", rota).where("data_entrega", "==", data).stream():
        batch.delete(d.reference)
        encontrou = True

    if encontrou:
        batch.commit()
        obter_datas_disponiveis_db.clear()
        obter_tickets_db.clear()
        obter_tickets_com_id_db.clear()


# ══════════════════════════════════════════════════════════════════
# RASTREIO AO VIVO (posição do motorista + alerta de proximidade)
# Coleções:
#   /posicoes_motoristas/{ticket_id} → gravado pelo motor_api.py (Render)
#                                       a cada ping do celular do motorista.
#                                       O Streamlit NUNCA escreve aqui, só lê.
#   /entregas_rastreio_live/{ticket_id} → criado quando o admin ativa o
#                                          rastreio ao vivo de uma entrega.
# ticket_id = '_doc_id' da entrega (mesmo id de obter_tickets_com_id_db).
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=86400, show_spinner=False)
def geocodificar_endereco_db(endereco: str):
    """Converte endereço em (lat, lng) via Nominatim/OpenStreetMap —
    gratuito, sem chave de API. Cacheado por 24h (endereço não muda de um
    dia pro outro). Retorna (None, None) se não achar — quem chamou deve
    oferecer input manual de lat/lng nesse caso."""
    endereco = (endereco or "").strip()
    if not endereco:
        return None, None
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": endereco, "format": "json", "limit": 1},
            headers={"User-Agent": "BancoWendley-Rastreio/1.0"},
            timeout=6,
        )
        resp.raise_for_status()
        resultados = resp.json()
        if not resultados:
            return None, None
        return float(resultados[0]["lat"]), float(resultados[0]["lon"])
    except Exception:
        return None, None


def iniciar_rastreio_live_db(ticket_id: str, destino_lat: float, destino_lng: float,
                              cliente_telefone: str = ""):
    get_db().collection("entregas_rastreio_live").document(ticket_id).set({
        "destino_lat": destino_lat,
        "destino_lng": destino_lng,
        "cliente_telefone": cliente_telefone,
        "alerta_5km_enviado": False,
        "ativado_em": datetime.now(BRT).isoformat(),
    })
    obter_config_entrega_live_db.clear()


@st.cache_data(ttl=8, show_spinner=False)
def obter_config_entrega_live_db(ticket_id: str):
    """Config de rastreio ao vivo de uma entrega, ou None se ainda não
    ativado. Cacheada 8s — a config só muda em ativar/desativar, nunca
    'ao vivo', então o cache não atrasa nada perceptível."""
    doc = get_db().collection("entregas_rastreio_live").document(ticket_id).get()
    return doc.to_dict() if doc.exists else None


def obter_posicao_motorista_db(ticket_id: str):
    """Última posição do motorista, ou None. SEM cache de propósito — a
    posição muda a cada poucos segundos; quem chama (mod_rastreio_live.py)
    já controla a frequência de leitura via toggle + intervalo mínimo."""
    doc = get_db().collection("posicoes_motoristas").document(ticket_id).get()
    return doc.to_dict() if doc.exists else None


def marcar_alerta_5km_enviado_db(ticket_id: str):
    get_db().collection("entregas_rastreio_live").document(ticket_id).update(
        {"alerta_5km_enviado": True}
    )
    obter_config_entrega_live_db.clear()


def desativar_rastreio_live_db(ticket_id: str):
    """Chame quando a entrega for concluída, pra não deixar o mapa ao vivo
    'aberto' indefinidamente numa entrega já finalizada."""
    get_db().collection("entregas_rastreio_live").document(ticket_id).delete()
    get_db().collection("posicoes_motoristas").document(ticket_id).delete()
    obter_config_entrega_live_db.clear()
