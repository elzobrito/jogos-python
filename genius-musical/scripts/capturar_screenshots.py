#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para captura automatizada de screenshots do Genius Musical.

Executa em modo headless (SDL_VIDEODRIVER=dummy) e exporta imagens PNG da
interface gráfica em diferentes estados visuais para documentação e validação.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Configura drivers dummy antes da importação do Pygame
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent
if str(DIRETORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_RAIZ))

import pygame

from audio import Audio
from configuracao import ALTURA, LARGURA
from interface import Interface
from jogo import EstadoJogo, Jogo


def main() -> int:
    print("=== Captura de Screenshots Headless do Genius Musical ===")

    pasta_prints = DIRETORIO_RAIZ / "prints"
    pasta_prints.mkdir(parents=True, exist_ok=True)

    try:
        pygame.mixer.pre_init(44100, -16, 1, 512)
    except Exception:
        pass

    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))

    audio = Audio()
    jogo = Jogo(on_tocar_som=audio.tocar)
    interface = Interface(tela, audio=audio)

    # -------------------------------------------------------------------------
    # 1. Captura do Menu Inicial
    # -------------------------------------------------------------------------
    jogo.estado = EstadoJogo.MENU
    interface.desenhar(jogo)
    caminho_menu = pasta_prints / "menu.png"
    pygame.image.save(tela, str(caminho_menu))
    print(f"[OK] Screenshot do Menu salvo em: {caminho_menu}")

    # -------------------------------------------------------------------------
    # 2. Captura da Demonstração Ativa (Elemento Fogo destacado)
    # -------------------------------------------------------------------------
    jogo.pontuacao = 2
    jogo.sequencia = ["fogo", "agua", "terra"]
    jogo.estado = EstadoJogo.DEMONSTRANDO
    jogo.fase_demonstracao = "destaque"
    jogo.indice_demonstracao = 0
    jogo.elemento_demonstrado = "fogo"

    interface.desenhar(jogo)
    caminho_demonstrando = pasta_prints / "demonstrando.png"
    pygame.image.save(tela, str(caminho_demonstrando))
    print(f"[OK] Screenshot de Demonstração salvo em: {caminho_demonstrando}")

    # -------------------------------------------------------------------------
    # 3. Captura opcional de Fim de Jogo para validação completa
    # -------------------------------------------------------------------------
    jogo.pontuacao = 5
    jogo.estado = EstadoJogo.FIM
    jogo.posicao_erro = 6
    jogo.elemento_esperado_erro = "terra"
    jogo.elemento_clicado_erro = "ar"
    jogo.elemento_demonstrado = None
    jogo.elemento_pressionado = None

    interface.desenhar(jogo)
    caminho_fim = pasta_prints / "game_over.png"
    pygame.image.save(tela, str(caminho_fim))
    print(f"[OK] Screenshot de Fim de Jogo salvo em: {caminho_fim}")

    pygame.quit()
    print("Todas as capturas foram concluídas com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
