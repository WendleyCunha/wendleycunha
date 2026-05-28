"""
pwa_inject.py — King Star Portal
═══════════════════════════════════════════════════════════════════════════════
Injeta o PWA (Progressive Web App) no Streamlit via st.markdown.

COMO USAR:
----------
No seu main.py (ou home.py, logo após st.set_page_config):

    from pwa_inject import injetar_pwa
    injetar_pwa()

IMPORTANTE:
-----------
• Chame esta função UMA VEZ, no entry point principal da aplicação.
• O arquivo sw.js deve estar em /static/sw.js (pasta static na raiz do projeto).
• O manifest.json deve estar em /static/manifest.json.
• No Streamlit Community Cloud ou servidor próprio, a pasta /static é servida
  automaticamente se criada na raiz do projeto com o nome correto.

ESTRUTURA DE ARQUIVOS:
----------------------
  seu_projeto/
  ├── main.py              ← chame injetar_pwa() aqui
  ├── pwa_inject.py        ← este arquivo
  ├── static/
  │   ├── manifest.json    ← identidade do app
  │   └── sw.js            ← service worker (cache + offline)
  └── modulos/
      └── ...
"""

import streamlit as st


def injetar_pwa():
    """
    Injeta todas as tags HTML necessárias para transformar o portal
    em um PWA instalável no Android (Chrome) e iOS (Safari).

    Inclui:
    - <link rel="manifest"> apontando para manifest.json
    - <meta name="theme-color"> para colorir a barra de status do celular
    - <meta name="apple-*"> para suporte nativo no iOS
    - Registro do Service Worker via JavaScript
    - Banner de instalação personalizado (substitui o prompt padrão do browser)
    """

    st.markdown(
        """
        <!-- ═══════════════════════════════════════════════════════════
             KING STAR PWA — HEAD TAGS
        ═══════════════════════════════════════════════════════════ -->
        <link rel="manifest" href="/static/manifest.json">

        <!-- Cor da barra de status (Android Chrome + Safari iOS) -->
        <meta name="theme-color" content="#B89647">

        <!-- iOS: comportamento de app nativo ao adicionar à tela inicial -->
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="King Star">

        <!-- Ícone para iOS (usa SVG inline como fallback) -->
        <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><rect width='512' height='512' rx='80' fill='%23B89647'/><text x='50%25' y='54%25' dominant-baseline='middle' text-anchor='middle' font-size='300'>👑</text></svg>">

        <!-- Viewport otimizado para mobile -->
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

        <!-- ═══════════════════════════════════════════════════════════
             BANNER DE INSTALAÇÃO PERSONALIZADO
             Aparece automaticamente quando o browser detecta critérios
             de instalação (HTTPS + manifest + service worker).
        ═══════════════════════════════════════════════════════════ -->
        <style>
          #pwa-install-banner {
            display: none;
            position: fixed;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            background: #ffffff;
            border: 1px solid #B89647;
            border-radius: 16px;
            padding: 14px 20px;
            box-shadow: 0 8px 32px rgba(184,150,71,0.25);
            z-index: 99999;
            max-width: 360px;
            width: calc(100% - 32px);
            font-family: 'DM Sans', sans-serif;
            animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          }
          #pwa-install-banner.show { display: flex; align-items: center; gap: 14px; }

          @keyframes slideUp {
            from { opacity: 0; transform: translateX(-50%) translateY(20px); }
            to   { opacity: 1; transform: translateX(-50%) translateY(0); }
          }

          #pwa-install-banner .pwa-icon {
            width: 48px; height: 48px; border-radius: 12px;
            background: linear-gradient(135deg, #D4B469, #B89647);
            display: flex; align-items: center; justify-content: center;
            font-size: 24px; flex-shrink: 0;
          }

          #pwa-install-banner .pwa-text { flex: 1; }
          #pwa-install-banner .pwa-text strong {
            display: block; font-size: 13px; color: #2D2D2D; font-weight: 700;
          }
          #pwa-install-banner .pwa-text span {
            font-size: 11px; color: #8C867A; margin-top: 2px; display: block;
          }

          #pwa-install-banner .pwa-actions { display: flex; gap: 8px; }
          #pwa-install-banner .btn-instalar {
            background: linear-gradient(135deg, #D4B469, #B89647);
            color: #1A1A1A; border: none; border-radius: 8px;
            padding: 8px 16px; font-size: 12px; font-weight: 700;
            cursor: pointer; white-space: nowrap;
          }
          #pwa-install-banner .btn-dispensar {
            background: transparent; border: 1px solid #E6E2DA;
            color: #8C867A; border-radius: 8px;
            padding: 8px 12px; font-size: 12px; cursor: pointer;
          }

          /* iOS: instrução manual (Safari não tem beforeinstallprompt) */
          #ios-install-tip {
            display: none;
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: #1A1A1A;
            color: #ffffff;
            border-radius: 14px;
            padding: 14px 18px;
            font-size: 12px;
            text-align: center;
            z-index: 99999;
            max-width: 300px;
            width: calc(100% - 32px);
            line-height: 1.6;
            box-shadow: 0 8px 32px rgba(0,0,0,0.35);
            animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          }
          #ios-install-tip.show { display: block; }
          #ios-install-tip .tip-close {
            display: block; margin-top: 10px; color: #B89647;
            font-weight: 700; cursor: pointer; font-size: 13px;
          }
        </style>

        <!-- Banner Android/Chrome -->
        <div id="pwa-install-banner">
          <div class="pwa-icon">👑</div>
          <div class="pwa-text">
            <strong>King Star Portal</strong>
            <span>Instale o app na sua tela inicial</span>
          </div>
          <div class="pwa-actions">
            <button class="btn-instalar" id="btn-instalar">Instalar</button>
            <button class="btn-dispensar" id="btn-dispensar">✕</button>
          </div>
        </div>

        <!-- Dica iOS/Safari -->
        <div id="ios-install-tip">
          <strong style="color:#B89647;">📲 Adicionar à tela inicial</strong><br>
          Toque em <strong>⬆ Compartilhar</strong> e depois em<br>
          <strong>"Adicionar à Tela de Início"</strong>
          <span class="tip-close" id="ios-tip-close">Entendi</span>
        </div>

        <!-- ═══════════════════════════════════════════════════════════
             SERVICE WORKER + LÓGICA DE INSTALAÇÃO
        ═══════════════════════════════════════════════════════════ -->
        <script>
          (function() {
            'use strict';

            // ── 1. Registrar Service Worker ──────────────────────────
            if ('serviceWorker' in navigator) {
              window.addEventListener('load', function() {
                navigator.serviceWorker.register('/static/sw.js', { scope: '/' })
                  .then(function(reg) {
                    console.log('[KS PWA] Service Worker registrado:', reg.scope);
                  })
                  .catch(function(err) {
                    console.warn('[KS PWA] Falha ao registrar SW:', err);
                  });
              });
            }

            // ── 2. Banner de instalação — Android/Chrome ─────────────
            var deferredPrompt = null;
            var banner = document.getElementById('pwa-install-banner');
            var btnInstalar = document.getElementById('btn-instalar');
            var btnDispensar = document.getElementById('btn-dispensar');

            window.addEventListener('beforeinstallprompt', function(e) {
              e.preventDefault();
              deferredPrompt = e;

              // Só mostra se o usuário ainda não instalou / não dispensou
              var dispensado = localStorage.getItem('ks_pwa_dispensado');
              if (!dispensado) {
                setTimeout(function() {
                  banner.classList.add('show');
                }, 2000); // aparece após 2s para não ser intrusivo
              }
            });

            if (btnInstalar) {
              btnInstalar.addEventListener('click', function() {
                if (!deferredPrompt) return;
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(function(result) {
                  if (result.outcome === 'accepted') {
                    console.log('[KS PWA] App instalado!');
                  }
                  deferredPrompt = null;
                  banner.classList.remove('show');
                });
              });
            }

            if (btnDispensar) {
              btnDispensar.addEventListener('click', function() {
                banner.classList.remove('show');
                localStorage.setItem('ks_pwa_dispensado', '1');
              });
            }

            // Remove flag de dispensado quando app é instalado
            window.addEventListener('appinstalled', function() {
              localStorage.removeItem('ks_pwa_dispensado');
              banner.classList.remove('show');
              console.log('[KS PWA] App instalado com sucesso!');
            });

            // ── 3. Dica de instalação — iOS/Safari ───────────────────
            var isIos = /iphone|ipad|ipod/.test(navigator.userAgent.toLowerCase());
            var isInStandaloneMode = ('standalone' in window.navigator) && window.navigator.standalone;
            var iosTip = document.getElementById('ios-install-tip');
            var iosTipClose = document.getElementById('ios-tip-close');

            if (isIos && !isInStandaloneMode) {
              var iosDispensado = localStorage.getItem('ks_ios_dispensado');
              if (!iosDispensado && iosTip) {
                setTimeout(function() {
                  iosTip.classList.add('show');
                }, 3000);
              }
            }

            if (iosTipClose) {
              iosTipClose.addEventListener('click', function() {
                iosTip.classList.remove('show');
                localStorage.setItem('ks_ios_dispensado', '1');
              });
            }

            // ── 4. Modo standalone: remove padding desnecessário ─────
            if (window.matchMedia('(display-mode: standalone)').matches || isInStandaloneMode) {
              document.documentElement.style.setProperty('--safe-area-top', 'env(safe-area-inset-top)');
              console.log('[KS PWA] Rodando em modo standalone (instalado).');
            }

          })();
        </script>
        """,
        unsafe_allow_html=True,
    )
