#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parte 3 — Sequência e estados: máquina MENU→DEMONSTRANDO→ENTRADA→FEEDBACK→FIM."""

from __future__ import annotations

import random
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple

import pygame

LARGURA, ALTURA, FPS = 960, 720, 60
MAX_DELTA_TIME = 0.033
FUNDO = (16, 24, 39)
PAINEL = (30, 41, 59)
TEXTO = (248, 250, 252)
TEXTO_ESCURO = (16, 24, 39)
TEXTO_SUAVE = (148, 163, 184)
BORDA = (51, 65, 85)
BORDA_DESTAQUE = (255, 255, 255)
FOGO = (248, 113, 113)
TERRA = (74, 222, 128)
AR = (250, 204, 21)

ELEMENTOS = ("fogo", "agua", "terra", "ar")
CORES_ELEMENTOS = {
    "fogo": FOGO, "agua": (96, 165, 250), "terra": TERRA, "ar": AR,
}
CORES_ATIVAS = {
    "fogo": (254, 180, 180), "agua": (175, 215, 254),
    "terra": (160, 245, 195), "ar": (255, 235, 140),
}
CORES_INDISPONIVEIS = {
    "fogo": (160, 75, 75), "agua": (65, 110, 165),
    "terra": (50, 145, 85), "ar": (165, 135, 20),
}
ROTULOS = {"fogo": "FOGO", "agua": "ÁGUA", "terra": "TERRA", "ar": "AR"}
TECLAS_ROTULO = {"fogo": "1", "agua": "2", "terra": "3", "ar": "4"}

TEMPO_DESTAQUE_S = 0.450
INTERVALO_ENTRE_NOTAS_S = 0.200
FEEDBACK_TOQUE_S = 0.180
INTERVALO_PROXIMA_RODADA_S = 0.800

PASTA_ASSETS = Path(__file__).resolve().parent.parent.parent / "assets" / "imagens"
CAMINHOS_IMAGENS = {e: PASTA_ASSETS / f"{e}.png" for e in ELEMENTOS}

RETANGULOS = {
    "fogo": pygame.Rect(100, 104, 360, 206),
    "agua": pygame.Rect(500, 104, 360, 206),
    "terra": pygame.Rect(100, 334, 360, 206),
    "ar": pygame.Rect(500, 334, 360, 206),
}


class EstadoJogo(Enum):
    MENU = auto()
    DEMONSTRANDO = auto()
    ENTRADA = auto()
    FEEDBACK = auto()
    FIM = auto()
    PAUSADO = auto()


class Jogo:
    """Lógica pura: sequência acumulativa e timers com dt (sem time.sleep)."""

    def __init__(self) -> None:
        self.estado = EstadoJogo.MENU
        self.sequencia: List[str] = []
        self.pontuacao = 0
        self.indice_demonstracao = 0
        self.fase_demonstracao = "destaque"
        self.elemento_demonstrado: Optional[str] = None
        self.temporizador = 0.0
        self.indice_jogador = 0
        self.elemento_pressionado: Optional[str] = None
        self.temporizador_toque = 0.0
        self.temporizador_feedback = 0.0
        self.posicao_erro: Optional[int] = None
        self.rng = random.Random()

    @property
    def rodada(self) -> int:
        return self.pontuacao + 1

    @property
    def elemento_ativo(self) -> Optional[str]:
        if self.estado == EstadoJogo.DEMONSTRANDO:
            return self.elemento_demonstrado
        if self.estado in (EstadoJogo.ENTRADA, EstadoJogo.FEEDBACK):
            return self.elemento_pressionado
        return None

    @property
    def mensagem_status(self) -> str:
        if self.estado == EstadoJogo.MENU:
            return "Pressione Enter para iniciar"
        if self.estado == EstadoJogo.DEMONSTRANDO:
            return "Observe a sequência"
        if self.estado == EstadoJogo.ENTRADA:
            return f"Sua vez — {self.indice_jogador} de {len(self.sequencia)}"
        if self.estado == EstadoJogo.FEEDBACK:
            return "Sequência correta!"
        if self.estado == EstadoJogo.FIM:
            return f"Você errou na posição {self.posicao_erro}! Enter reinicia"
        return ""

    def iniciar(self) -> None:
        self.pontuacao = 0
        self.sequencia = [self.rng.choice(ELEMENTOS)]
        self.posicao_erro = None
        self._iniciar_demonstracao()

    def reiniciar(self) -> None:
        self.iniciar()

    def selecionar(self, elemento: str) -> bool:
        if self.estado != EstadoJogo.ENTRADA or elemento not in ELEMENTOS:
            return False
        self.elemento_pressionado = elemento
        self.temporizador_toque = FEEDBACK_TOQUE_S
        esperado = self.sequencia[self.indice_jogador]
        if elemento == esperado:
            self.indice_jogador += 1
            if self.indice_jogador == len(self.sequencia):
                self.estado = EstadoJogo.FEEDBACK
                self.temporizador_feedback = INTERVALO_PROXIMA_RODADA_S
            return True
        self.posicao_erro = self.indice_jogador + 1
        self.estado = EstadoJogo.FIM
        return False

    def atualizar(self, dt: float) -> None:
        if self.temporizador_toque > 0:
            self.temporizador_toque -= dt
            if self.temporizador_toque <= 0:
                self.elemento_pressionado = None
        if self.estado == EstadoJogo.DEMONSTRANDO:
            self._atualizar_demonstracao(dt)
        elif self.estado == EstadoJogo.FEEDBACK:
            self.temporizador_feedback -= dt
            if self.temporizador_feedback <= 0:
                self.pontuacao += 1
                self.sequencia.append(self.rng.choice(ELEMENTOS))
                self._iniciar_demonstracao()

    def _iniciar_demonstracao(self) -> None:
        self.estado = EstadoJogo.DEMONSTRANDO
        self.indice_demonstracao = 0
        self.fase_demonstracao = "destaque"
        self.temporizador = 0.0
        self.elemento_demonstrado = self.sequencia[0]

    def _atualizar_demonstracao(self, dt: float) -> None:
        self.temporizador += dt
        if self.fase_demonstracao == "destaque":
            if self.temporizador >= TEMPO_DESTAQUE_S:
                self.elemento_demonstrado = None
                self.temporizador = 0.0
                if self.indice_demonstracao < len(self.sequencia) - 1:
                    self.fase_demonstracao = "pausa"
                else:
                    self.estado = EstadoJogo.ENTRADA
                    self.indice_jogador = 0
        elif self.fase_demonstracao == "pausa":
            if self.temporizador >= INTERVALO_ENTRE_NOTAS_S:
                self.temporizador = 0.0
                self.indice_demonstracao += 1
                self.fase_demonstracao = "destaque"
                self.elemento_demonstrado = self.sequencia[self.indice_demonstracao]


def carregar_icones():
    icones = {}
    for e, c in CAMINHOS_IMAGENS.items():
        icones[e] = pygame.transform.smoothscale(
            pygame.image.load(str(c)).convert_alpha(), (96, 96)
        )
    return icones


def hit_test(pos: Tuple[int, int]) -> Optional[str]:
    for elem, rect in RETANGULOS.items():
        if rect.collidepoint(pos):
            return elem
    return None


def desenhar(tela, icones, fontes, jogo: Jogo) -> None:
    tela.fill(FUNDO)
    pygame.draw.rect(tela, PAINEL, pygame.Rect(0, 0, LARGURA, 82))
    tela.blit(fontes["titulo"].render("Parte 3 — sequência e estados", True, TEXTO), (60, 18))
    tela.blit(
        fontes["pequena"].render(f"RODADA {jogo.rodada:02d}  ·  PONTOS {jogo.pontuacao}", True, TEXTO_SUAVE),
        (LARGURA - 260, 28),
    )
    ativo = jogo.elemento_ativo
    for elem in ELEMENTOS:
        rect = RETANGULOS[elem]
        esta_ativo = ativo == elem
        indisponivel = jogo.estado == EstadoJogo.DEMONSTRANDO and not esta_ativo
        if esta_ativo:
            cor, borda, lw = CORES_ATIVAS[elem], BORDA_DESTAQUE, 4
        elif indisponivel:
            cor, borda, lw = CORES_INDISPONIVEIS[elem], BORDA, 2
        else:
            cor, borda, lw = CORES_ELEMENTOS[elem], BORDA, 2
        pygame.draw.rect(tela, cor, rect, border_radius=16)
        pygame.draw.rect(tela, borda, rect, lw, border_radius=16)
        tela.blit(icones[elem], (rect.centerx - 48, rect.top + 22))
        rotulo = fontes["card"].render(ROTULOS[elem], True, TEXTO_ESCURO)
        tela.blit(rotulo, rotulo.get_rect(center=(rect.centerx, rect.top + 154)))
        tela.blit(fontes["tecla"].render(TECLAS_ROTULO[elem], True, TEXTO_ESCURO), (rect.left + 22, rect.top + 18))

    cor_msg = TERRA if jogo.estado == EstadoJogo.FEEDBACK else (FOGO if jogo.estado == EstadoJogo.FIM else TEXTO)
    msg = fontes["status"].render(jogo.mensagem_status, True, cor_msg)
    tela.blit(msg, msg.get_rect(center=(LARGURA // 2, 578)))


def main() -> int:
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Genius Musical — Parte 3: sequência e estados")
    fontes = {
        "titulo": pygame.font.SysFont("dejavusans", 22, bold=True),
        "card": pygame.font.SysFont("dejavusans", 21, bold=True),
        "tecla": pygame.font.SysFont("dejavusans", 13, bold=True),
        "status": pygame.font.SysFont("dejavusans", 19, bold=True),
        "pequena": pygame.font.SysFont("dejavusans", 12),
    }
    icones = carregar_icones()
    jogo = Jogo()
    mapa = {pygame.K_1: "fogo", pygame.K_2: "agua", pygame.K_3: "terra", pygame.K_4: "ar",
            pygame.K_KP1: "fogo", pygame.K_KP2: "agua", pygame.K_KP3: "terra", pygame.K_KP4: "ar"}
    relogio = pygame.time.Clock()
    executando = True
    while executando:
        dt = min(relogio.tick(FPS) / 1000.0, MAX_DELTA_TIME)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if jogo.estado == EstadoJogo.MENU:
                        jogo.iniciar()
                    elif jogo.estado == EstadoJogo.FIM:
                        jogo.reiniciar()
                elif evento.key in mapa:
                    jogo.selecionar(mapa[evento.key])
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                alvo = hit_test(evento.pos)
                if alvo is not None:
                    jogo.selecionar(alvo)
        jogo.atualizar(dt)
        desenhar(tela, icones, fontes, jogo)
        pygame.display.flip()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
