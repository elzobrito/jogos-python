#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ponto de entrada do Genius Musical.

Inicializa o subsistema de áudio via pre_init, instancia os módulos de lógica,
interface e áudio, e gerencia o loop de eventos e renderização.
"""

from __future__ import annotations

import sys
import pygame

from audio import Audio
from configuracao import (
    ALTURA,
    ELEMENTOS,
    FPS,
    FS,
    LARGURA,
    MAX_DELTA_TIME,
)
from interface import Interface
from jogo import EstadoJogo, Jogo


def main() -> int:
    """Executa o loop principal do Genius Musical."""
    # 1. Configura o mixer com buffer reduzido ANTES do init para baixa latência
    try:
        pygame.mixer.pre_init(FS, -16, 1, 512)
    except Exception as erro:
        print(f"[Aviso] Falha ao pré-inicializar mixer: {erro}")

    # 2. Inicialização dos módulos do Pygame
    pygame.init()

    # 3. Criação da janela lógica
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Genius Musical — Memória Visual e Musical")

    # 4. Instanciação dos subsistemas
    audio = Audio()
    jogo = Jogo(on_tocar_som=audio.tocar)
    interface = Interface(tela, audio=audio)
    relogio = pygame.time.Clock()

    executando = True

    # 5. Game Loop principal
    while executando:
        # Cálculo de delta time seguro (em segundos)
        dt_bruto = relogio.tick(FPS) / 1000.0
        dt = min(dt_bruto, MAX_DELTA_TIME)

        # ---------------------------------------------------------------------
        # Tratamento de Eventos de Entrada
        # ---------------------------------------------------------------------
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

            elif evento.type == pygame.KEYDOWN:
                # Pausa / Retomada
                if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                    jogo.pausar_ou_retomar()

                # Iniciar / Reiniciar / Retomar
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if jogo.estado == EstadoJogo.MENU:
                        jogo.iniciar()
                    elif jogo.estado == EstadoJogo.FIM:
                        jogo.reiniciar()
                    elif jogo.estado == EstadoJogo.PAUSADO:
                        jogo.pausar_ou_retomar()

                # Controle de Som / Mudo
                elif evento.key == pygame.K_m:
                    audio.alternar_mudo()

                # Seleção de Elementos por Teclado (1 a 4)
                elif evento.key in (pygame.K_1, pygame.K_KP1):
                    jogo.selecionar("fogo")
                elif evento.key in (pygame.K_2, pygame.K_KP2):
                    jogo.selecionar("agua")
                elif evento.key in (pygame.K_3, pygame.K_KP3):
                    jogo.selecionar("terra")
                elif evento.key in (pygame.K_4, pygame.K_KP4):
                    jogo.selecionar("ar")

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                alvo = interface.hit_test(evento.pos)
                if alvo in ELEMENTOS:
                    # O clique percorre exatamente a mesma rotina de seleção do teclado
                    jogo.selecionar(alvo)
                elif alvo == "btn_iniciar":
                    if jogo.estado == EstadoJogo.MENU:
                        jogo.iniciar()
                    elif jogo.estado == EstadoJogo.FIM:
                        jogo.reiniciar()
                    elif jogo.estado == EstadoJogo.PAUSADO:
                        jogo.pausar_ou_retomar()
                elif alvo == "btn_pausa":
                    jogo.pausar_ou_retomar()
                elif alvo == "btn_som":
                    audio.alternar_mudo()

        # ---------------------------------------------------------------------
        # Atualização da Lógica do Jogo
        # ---------------------------------------------------------------------
        jogo.atualizar(dt)

        # ---------------------------------------------------------------------
        # Renderização do Quadro
        # ---------------------------------------------------------------------
        interface.desenhar(jogo)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
