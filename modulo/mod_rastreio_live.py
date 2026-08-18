"""
modulo/mod_rastreio_live.py
Mapa ao vivo (visão do Admin) da posição do motorista para UMA entrega.
Usa Leaflet + OpenStreetMap (grátis, sem chave de API), embutido via
st.components.v1.html.

Lê (nunca escreve) as coleções gravadas pelo motor_api.py:
  /posicoes_motoristas/{motorista_login} -> posição atual do motorista
  /entregas_rastreio_live/{ticket_id}    -> destino + config da entrega

Ponto de entrada usado por modulo/mod_rastreio.py: renderizar_mapa_ao_vivo(ticket_id)

[ATUALIZADO] Atualização automática SEMPRE ligada -- sem toggle, sem botão
manual de "atualizar posição". A cada _INTERVALO_AUTO_REFRESH segundos, o
mapa se redesenha sozinho com a posição mais recente, o tempo todo que a
tela estiver aberta. Isso consome cota do Firestore continuamente
enquanto alguém estiver olhando esta tela -- é a troca consciente pedida
(GPS "full time", sem passos manuais).
"""
import streamlit as st
import streamlit.components.v1 as components

from database import obter_posicao_motorista_db, obter_config_entrega_live_db

_INTERVALO_AUTO_REFRESH = 10  # segundos -- atualização contínua, sem botão

_FRAGMENT_DECORATOR = getattr(st, "fragment", None) or getattr(st, "experimental_fragment", None)
_TEM_FRAGMENT = _FRAGMENT_DECORATOR is not None


def _desenhar_mapa(ticket_id, posicao, config):
    lat_m = posicao.get("lat")
    lng_m = posicao.get("lng")
    lat_d = config.get("destino_lat")
    lng_d = config.get("destino_lng")

    if lat_m is None or lng_m is None or lat_d is None or lng_d is None:
        st.warning("Dados de posição/destino incompletos — não foi possível desenhar o mapa.")
        return

    html = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <div id="mapa_live_{ticket_id}" style="height:420px;border-radius:10px;overflow:hidden;"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
      var mapa = L.map('mapa_live_{ticket_id}');
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; OpenStreetMap contributors'
      }}).addTo(mapa);

      var iconeMotorista = L.divIcon({{ html: '<div style="font-size:26px;">🚚</div>', className: '', iconSize: [26, 26] }});
      var iconeDestino   = L.divIcon({{ html: '<div style="font-size:26px;">📍</div>', className: '', iconSize: [26, 26] }});

      L.marker([{lat_m}, {lng_m}], {{ icon: iconeMotorista }}).addTo(mapa);
      L.marker([{lat_d}, {lng_d}], {{ icon: iconeDestino }}).addTo(mapa);
      mapa.fitBounds([[{lat_m}, {lng_m}], [{lat_d}, {lng_d}]], {{ padding: [30, 30] }});
    </script>
    """
    components.html(html, height=440)

    col1, col2, col3 = st.columns(3)
    vel = posicao.get("velocidade_kmh")
    precisao = posicao.get("precisao_m")
    col1.metric("🚚 Velocidade", f"{vel:.0f} km/h" if vel else "—")
    col2.metric("🎯 Precisão do GPS", f"{precisao:.0f} m" if precisao else "—")
    col3.metric("🚨 Alerta 5km", "✅ Já enviado" if config.get("alerta_5km_enviado") else "⏳ Ainda não")
    st.caption(f"📡 Atualizando automaticamente a cada {_INTERVALO_AUTO_REFRESH}s · última posição: {posicao.get('atualizado_em', '—')}")


def _renderizar_conteudo(ticket_id: str):
    config = obter_config_entrega_live_db(ticket_id)
    if not config:
        st.info("Rastreio ao vivo ainda não foi ativado para esta entrega.")
        return

    # A posição é gravada por MOTORISTA (login), não por ticket_id de uma
    # entrega -- resolve o login vinculado a esta entrega (gravado quando o
    # rastreio foi ativado) e busca a posição dele.
    motorista_login = config.get("motorista_login", "")
    posicao = obter_posicao_motorista_db(motorista_login) if motorista_login else None
    if not posicao:
        st.info(
            "⏳ Aguardando o motorista iniciar o compartilhamento de localização "
            "(ele precisa abrir o link e permitir acesso ao GPS no celular)."
        )
        return

    _desenhar_mapa(ticket_id, posicao, config)


def renderizar_mapa_ao_vivo(ticket_id: str):
    """
    [ATUALIZADO] Sem toggle, sem botão -- atualiza sozinho o tempo todo,
    via st.fragment, enquanto esta tela estiver aberta. Se a versão do
    Streamlit não suportar st.fragment (< 1.35.0), cai para uma única
    renderização estática com um aviso pra atualizar a versão.
    """
    if _TEM_FRAGMENT:
        _FRAGMENT_DECORATOR(run_every=_INTERVALO_AUTO_REFRESH)(_renderizar_conteudo)(ticket_id)
    else:
        st.warning(
            "⚠️ Sua versão do Streamlit não suporta atualização automática "
            "(`st.fragment`). Atualize `streamlit>=1.35.0` no requirements.txt "
            "para a atualização contínua funcionar."
        )
        _renderizar_conteudo(ticket_id)
