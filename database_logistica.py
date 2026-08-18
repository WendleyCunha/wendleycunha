"""
database_logistica.py
Funções de banco exclusivas da logística de entregas (upload de planilha
roteirizada + baixa de entrega com foto). Reaproveita a mesma conexão
Firestore via get_db(), de database.py.
"""

from database import get_db, BRT, obter_tickets_db, obter_tickets_com_id_db
from datetime import datetime


def salvar_entregas_db(entregas: list, data_alvo: str) -> int:
    """
    Salva uma lista de entregas (dicts) na coleção 'entregas' para uma data
    específica. Usada pela importação de planilha na aba "Cadastros".
    Retorna a quantidade de documentos criados.
    """
    db = get_db()
    batch = db.batch()
    count = 0
    for item in entregas:
        doc = dict(item)
        doc["data_entrega"] = data_alvo
        ref = db.collection("entregas").document()
        batch.set(ref, doc)
        count += 1
        if count % 400 == 0:  # limite de 500 ops/batch no Firestore
            batch.commit()
            batch = db.batch()
    batch.commit()

    obter_tickets_db.clear()
    obter_tickets_com_id_db.clear()

    return count


def dar_baixa_entrega_db(doc_id: str, status: str, foto_bytes: bytes = None, observacao: str = ""):
    """
    Registra a baixa de uma entrega feita pelo motorista. Foto OPCIONAL.
    status: "sucesso" ou "falha".
    Retorna (True, msg) ou (False, msg_erro).
    """
    if foto_bytes:
        tamanho_mb = len(foto_bytes) / (1024 * 1024)
        if tamanho_mb > 4.0:
            return False, f"Foto muito grande ({tamanho_mb:.1f}MB) — tire a foto novamente."

    db = get_db()
    ref = db.collection("entregas").document(doc_id)
    doc_atual = ref.get()
    if not doc_atual.exists:
        return False, "Entrega não encontrada."

    agora = datetime.now(BRT)
    status_visual = "✅ Sucesso" if status == "sucesso" else "❌ Falhou"
    campos = {
        "_status_visual": status_visual,
        "checkout_time": agora.isoformat(),
        "checkout_observation": observacao.strip() if observacao and observacao.strip()
                                 else ("Entrega realizada" if status == "sucesso" else "Falha na entrega"),
    }

    dados_doc = doc_atual.to_dict() or {}
    if "payload" in dados_doc:
        campos = {f"payload.{k}": v for k, v in campos.items()}

    ref.update(campos)

    if foto_bytes:
        db.collection("fotos_entrega").document(doc_id).set({
            "entrega_id": doc_id,
            "bin": foto_bytes,
            "status": status,
            "data": agora.strftime("%d/%m/%Y %H:%M"),
        })

    obter_tickets_db.clear()
    obter_tickets_com_id_db.clear()

    return True, "✅ Baixa registrada com sucesso!"


def obter_foto_entrega_db(doc_id: str):
    """Retorna os bytes da foto de uma entrega, ou None se não houver."""
    doc = get_db().collection("fotos_entrega").document(doc_id).get()
    return doc.to_dict().get("bin") if doc.exists else None


def buscar_entregas_por_codigo_db(termo: str, limite: int = 200) -> list:
    """Busca entregas em TODO o histórico cujo código do cliente contenha
    o termo (parcial, case-insensitive). Varre a coleção inteira — ok pro
    volume esperado; revisitar se crescer muito."""
    termo_norm = (termo or "").strip().lower()
    if not termo_norm:
        return []

    db = get_db()
    resultados = []
    for doc in db.collection("entregas").stream():
        dados = doc.to_dict() or {}
        item = dados.get("payload", dados)
        codigo = str(item.get("cliente_codigo", "") or "").strip().lower()
        if termo_norm in codigo:
            resultado = dict(item)
            resultado["_doc_id"] = doc.id
            resultado.setdefault("data_entrega", dados.get("data_entrega", ""))
            resultados.append(resultado)
            if len(resultados) >= limite:
                break
    return resultados
