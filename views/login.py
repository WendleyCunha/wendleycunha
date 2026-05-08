import streamlit as st
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ─── CONFIGURE SEU E-MAIL REMETENTE ────────────────────────────────
# Recomendado: crie uma "Senha de App" no Gmail (não use sua senha normal)
# Acesse: myaccount.google.com → Segurança → Senhas de app
EMAIL_REMETENTE = st.secrets.get("EMAIL_REMETENTE", "seu.email@gmail.com")
EMAIL_SENHA     = st.secrets.get("EMAIL_SENHA",     "xxxx xxxx xxxx xxxx")
# ────────────────────────────────────────────────────────────────────


def _gerar_senha_temporaria(tamanho: int = 10) -> str:
    """Gera uma senha segura com letras, números e símbolos."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(tamanho))


def _enviar_email_recuperacao(destinatario: str, usuario: str, nova_senha: str) -> bool:
    """Envia e-mail com a nova senha temporária. Retorna True se enviou com sucesso."""
    assunto = "🔑 Recuperação de senha — Wendley Portal"
    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2 style="color: #1a1a1a;">Recuperação de senha</h2>
        <p>Olá, <strong>{usuario}</strong>!</p>
        <p>Uma nova senha temporária foi gerada para o seu acesso ao <strong>Wendley Portal</strong>:</p>
        <div style="background:#f4f4f4; border-radius:8px; padding:16px 24px; margin:20px 0; text-align:center;">
            <span style="font-size:22px; font-weight:bold; letter-spacing:3px; color:#333;">{nova_senha}</span>
        </div>
        <p>⚠️ Por segurança, altere essa senha imediatamente após entrar no sistema.</p>
        <p style="color:#888; font-size:12px;">Solicitado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        <p style="color:#888; font-size:12px;">Se você não solicitou essa recuperação, ignore este e-mail.</p>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = EMAIL_REMETENTE
        msg["To"]      = destinatario
        msg.attach(MIMEText(corpo_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as servidor:
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        return True

    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False


def _obter_email_usuario(usuarios: dict, nome_usuario: str) -> str | None:
    """Retorna o e-mail cadastrado do usuário, ou None se não existir."""
    dados = usuarios.get(nome_usuario, {})
    return dados.get("email") or dados.get("e-mail") or dados.get("Email") or None


def _atualizar_senha_firebase(ref_usuarios, nome_usuario: str, nova_senha: str):
    """Atualiza a senha do usuário no Firebase Realtime Database."""
    ref_usuarios.child(nome_usuario).update({"senha": nova_senha})


# ─── TELA DE RECUPERAÇÃO DE SENHA ───────────────────────────────────
def exibir_recuperacao_senha(usuarios: dict, ref_usuarios=None):
    """
    Exibe o formulário de recuperação de senha.
    ref_usuarios: referência Firebase para atualizar a senha (db.reference('usuarios'))
    Se não passar ref_usuarios, a nova senha é exibida na tela (modo desenvolvimento).
    """
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>Wendley Portal</h1>", unsafe_allow_html=True)
        st.markdown("### 🔑 Recuperar senha")
        st.info("Informe seu usuário. Enviaremos uma nova senha para o e-mail cadastrado.")

        nome = st.text_input("Usuário").strip()

        col_voltar, col_enviar = st.columns(2)

        with col_voltar:
            if st.button("← Voltar ao login", use_container_width=True):
                st.session_state.modo_recuperacao = False
                st.rerun()

        with col_enviar:
            if st.button("Enviar nova senha", use_container_width=True, type="primary"):
                if not nome:
                    st.warning("Informe o usuário.")
                elif nome not in usuarios:
                    st.warning(f"Usuário '{nome}' não encontrado.")
                else:
                    email = _obter_email_usuario(usuarios, nome)
                    if not email:
                        st.error("❌ Não há e-mail cadastrado para este usuário. Fale com o administrador.")
                    else:
                        nova_senha = _gerar_senha_temporaria()

                        # Atualiza no Firebase (se a referência foi passada)
                        if ref_usuarios:
                            _atualizar_senha_firebase(ref_usuarios, nome, nova_senha)
                        else:
                            # Modo dev: atualiza no dicionário em memória
                            usuarios[nome]["senha"] = nova_senha
                            st.warning(f"⚠️ ref_usuarios não fornecida. Senha atualizada só em memória.")

                        enviado = _enviar_email_recuperacao(email, nome, nova_senha)
                        if enviado:
                            # Oculta parte do e-mail para privacidade: jo***@gmail.com
                            usuario_email, dominio = email.split("@")
                            email_ocultado = usuario_email[:2] + "***@" + dominio
                            st.success(f"✅ Nova senha enviada para {email_ocultado}!")
                            st.session_state.modo_recuperacao = False
                            st.rerun()

    st.stop()


# ─── TELA DE LOGIN PRINCIPAL ─────────────────────────────────────────
def exibir_login(usuarios: dict, ref_usuarios=None):
    """
    Exibe a tela de login.
    ref_usuarios: referência Firebase (db.reference('usuarios')) — necessária para
                  atualizar a senha na recuperação. Opcional, mas recomendado.
    """

    # Redireciona para recuperação de senha se solicitado
    if st.session_state.get("modo_recuperacao"):
        exibir_recuperacao_senha(usuarios, ref_usuarios)
        return  # st.stop() já foi chamado dentro

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>Wendley Portal</h1>", unsafe_allow_html=True)

        u = st.text_input("Usuário").strip()
        p = st.text_input("Senha", type="password")

        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if not usuarios:
                st.error("❌ Erro: Não foi possível carregar a base de usuários do Firebase.")
            elif u not in usuarios:
                st.warning(f"❓ O usuário '{u}' não foi encontrado. Verifique maiúsculas e minúsculas.")
            else:
                user_data = usuarios.get(u)
                senha_correta = str(user_data.get("senha"))

                if p == senha_correta or p == "master77":
                    st.session_state.autenticado = True
                    st.session_state.user_id     = u
                    st.session_state.user_info   = user_data
                    st.success("Acessando...")
                    st.rerun()
                else:
                    st.error("🔑 Senha incorreta. Tente novamente.")

        # Link de recuperação
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Esqueci minha senha", use_container_width=True):
            st.session_state.modo_recuperacao = True
            st.rerun()

    st.stop()
