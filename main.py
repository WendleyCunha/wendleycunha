"""
main.py — Sistema de Rastreio (bancowendley)
Orquestrador enxuto: login + módulo de Rastreio, e só isso. Sem Tickets,
Cartas, Home, Diagnóstico N2 nem Chat — esses não fazem parte deste
sistema (se precisar deles, é o outro projeto, "king"/"portal").
"""
import streamlit as st
from datetime import datetime, timedelta, timezone
import os, time, base64

from database import (
    verificar_login, criar_usuario, listar_usuarios, deletar_usuario,
    redefinir_senha_usuario, alterar_senha_usuario,
    obter_datas_disponiveis_db, pode_exportar,
)

# [Blindagem] Se o mod_rastreio.py (ou qualquer coisa que ele importe)
# falhar ao carregar, o app inteiro não cai — mostra um aviso na tela em
# vez de derrubar até a tela de login.
try:
    from modulo.mod_rastreio import renderizar_rastreio
except Exception as _erro_import_rastreio:
    def renderizar_rastreio(papel, user=None, datas_db=None, pode_exp=False,
                             _erro=_erro_import_rastreio):
        st.error("⚠️ Falha ao carregar o módulo de Rastreio. Detalhe técnico abaixo:")
        st.exception(_erro)
        return False

# [Blindagem] Erros de RUNTIME (cota do Firestore esgotada, índice
# faltando, etc.) também não devem derrubar a página inteira.
from google.api_core.exceptions import ResourceExhausted as _ResourceExhausted

def _executar_protegido(nome_modulo: str, func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except _ResourceExhausted:
        st.error(
            f"🚫 **{nome_modulo}** não pôde carregar agora: a cota diária gratuita "
            "de leituras do Firestore foi esgotada (limite do plano Spark)."
        )
        st.info(
            "**Como resolver:** espere o reset automático (meia-noite horário do "
            "Pacífico, ≈ 4h-5h da manhã em Brasília), ou migre o projeto no Firebase "
            "para o plano **Blaze** (console.firebase.google.com → ⚙️ → Uso e "
            "faturamento → Modificar plano) — as primeiras 50k leituras/dia continuam "
            "grátis, o erro some assim que o plano muda."
        )
        return None
    except Exception as e:
        st.error(f"⚠️ **{nome_modulo}** encontrou um erro e não pôde carregar agora.")
        st.exception(e)
        return None


st.set_page_config(
    page_title="Rastreio · BancoWendley",
    layout="wide", page_icon="🚚",
    initial_sidebar_state="collapsed",
)

BRT = timezone(timedelta(hours=-3))
def agora_brt(): return datetime.now(BRT).strftime("%H:%M:%S")

def get_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #f4f6f9; }
.block-container { padding-top: 2rem !important; }
.ks-header {
    background:#ffffff; border-left:5px solid #C9A84C;
    border-radius:12px; padding:16px 24px; margin-bottom:20px;
    box-shadow:0 2px 8px rgba(0,0,0,0.05);
    display:flex; align-items:center; gap:18px;
}
.ks-title { font-size:1.4rem; font-weight:800; color:#2c3e50; margin:0; }
.ks-sub { font-size:0.8rem; color:#64778d; margin-top:3px; }
[data-testid="stMain"] [data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #3d1f10, #6b3a22) !important;
  border: none !important; color: white !important;
}
div[role="dialog"] { width: 95vw !important; max-width: 900px !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSÃO ────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ── LOGIN ─────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        lb = get_logo()
        if lb:
            st.markdown(
                f'<div style="text-align:center;margin-bottom:20px;">'
                f'<img src="data:image/png;base64,{lb}" style="height:80px;"></div>',
                unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align:center;color:#2c3e50;margin-bottom:20px;'>🚚 Rastreio · Login</h2>",
            unsafe_allow_html=True)
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            u = None
            banco_indisponivel = False
            try:
                u = verificar_login(usuario, senha)
            except _ResourceExhausted:
                banco_indisponivel = True
                st.error(
                    "🚫 O sistema está temporariamente indisponível "
                    "(banco de dados fora do ar). Tente novamente em alguns minutos."
                )
            except Exception:
                banco_indisponivel = True
                st.error("🚫 O sistema está temporariamente indisponível. Tente novamente.")

            if u:
                st.session_state.user = u
                st.rerun()
            elif not banco_indisponivel:
                st.error("Credenciais inválidas.")
        st.caption("Admin padrão: `admin` / `admin123` (troque depois, se quiser criar outro admin).")
    st.stop()

# ── USUÁRIO CONFIRMADO ────────────────────────────────────────────
user = st.session_state.user
papel = user.get("role", "motorista")

# ══════════════════════════════════════════════════════════════════
# VISÃO DO MOTORISTA — direto no Rastreio, sem cabeçalho de admin
# ══════════════════════════════════════════════════════════════════
if papel == "motorista":
    lb = get_logo()
    if lb:
        st.markdown(
            f'<div style="text-align:center;padding:6px 0 10px;">'
            f'<img src="data:image/png;base64,{lb}" style="height:44px;"></div>',
            unsafe_allow_html=True)

    _executar_protegido("Rastreio", renderizar_rastreio, papel, user, datas_db=[], pode_exp=False)

    if st.button("🔄 Atualizar entregas", use_container_width=True):
        st.rerun()

    st.markdown("<hr style='margin:20px 0 14px;border:none;border-top:1px solid #eee;'>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:center;color:#64778d;font-size:0.85rem;margin-bottom:8px;'>"
        f"{user['nome']}</div>", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        st.session_state.user = None
        st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════
# VISÃO DO ADMIN
# ══════════════════════════════════════════════════════════════════
lb = get_logo()
logo_html = (f'<img src="data:image/png;base64,{lb}" style="height:50px;margin-right:18px;">' if lb else "")

hc1, hc2 = st.columns([9, 1])
with hc1:
    st.markdown(f"""
    <div class="ks-header">
        {logo_html}
        <div style="flex:1;">
            <div class="ks-title">🚚 Sistema de Rastreio</div>
            <div class="ks-sub">{user['nome']} · {agora_brt()}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with hc2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# ── Datas disponíveis (protegido contra falha de Firestore) ───────
def _obter_datas_protegido():
    try:
        return obter_datas_disponiveis_db()
    except _ResourceExhausted:
        st.warning(
            "⚠️ Não foi possível carregar o histórico de dias (cota do Firestore "
            "esgotada). Mostrando só o dia de hoje."
        )
        return []
    except Exception:
        st.warning("⚠️ Não foi possível carregar o histórico de dias agora.")
        return []

datas_db = _obter_datas_protegido()

is_hoje = _executar_protegido(
    "Rastreio", renderizar_rastreio, papel, user,
    datas_db=datas_db, pode_exp=pode_exportar(user)
)
if is_hoje:
    if st.button("🔄 Atualizar rastreio", key="btn_refresh_rastreio"):
        st.rerun()

# ── Rodapé simples: trocar senha do próprio usuário ────────────────
with st.expander("👤 Minha conta"):
    st.markdown(f"**Nome:** {user['nome']} | **Login:** `{user.get('usuario','')}` | **Nível:** {papel.upper()}")
    with st.form("form_senha"):
        s_atual = st.text_input("Senha atual", type="password")
        s_nova = st.text_input("Nova senha", type="password")
        s_conf = st.text_input("Confirmar nova senha", type="password")
        if st.form_submit_button("Alterar Senha"):
            if not s_atual or not s_nova or not s_conf:
                st.warning("Preencha todos os campos.")
            elif s_nova != s_conf:
                st.error("As senhas não coincidem.")
            elif len(s_nova) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                ok, msg = alterar_senha_usuario(user.get("usuario", ""), s_atual, s_nova)
                if ok:
                    st.success(msg)
                    time.sleep(1)
                    st.session_state.user = None
                    st.rerun()
                else:
                    st.error(msg)
