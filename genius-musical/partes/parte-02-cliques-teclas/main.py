#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parte 2 — Cliques e teclas: hit_test com Rect.collidepoint + teclas 1–4."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pygame

LARGURA, ALTURA, FPS = 960, 720, 60
FUNDO = (16, 24, 39)
PAINEL = (30, 41, 59)
TEXTO = (248, 250, 252)
TEXTO_ESCURO = (16, 24, 39)
TEXTO_SUAVE = (148, 163, 184)
BORDA = (51, 65, 85)
BORDA_DESTAQUE = (255, 255, 255)

ELEMENTOS = ("fogo", "agua", "terra", "ar")
CORES_ELEMENTOS = {
    "fogo": (248, 113, 113),
    "agua": (96, 165, 250),
    "terra": (74, 222, 128),
    "ar": (250, 204, 21),
}
CORES_ATIVAS = {
    "fogo": (254, 180, 180),
    "agua": (175, 215, 254),
    "terra": (160, 245, 195),
    "ar": (255, 235, 140),
}
ROTULOS = {"fogo": "FOGO", "agua": "ÁGUA", "terra": "TERRA", "ar": "AR"}
TECLAS_ROTULO = {"fogo": "1", "agua": "2", "terra": "3", "ar": "4"}
MAPA_TECLAS = {
    pygame.K_1: "fogo",
    pygame.K_KP1: "fogo",
    pygame.K_2: "agua",
    pygame.K_KP2: "agua",
    pygame.K_3: "terra",
    pygame.K_KP3: "terra",
    pygame.K_4: "ar",
    pygame.K_KP4: "ar",
}

PASTA_ASSETS = Path(__file__).resolve().parent.parent.parent / "assets" / "imagens"
CAMINHOS_IMAGENS = {e: PASTA_ASSETS / f"{e}.png" for e in ELEMENTOS}

RETANGULOS = {
    "fogo": pygame.Rect(100, 104, 360, 206),
    "agua": pygame.Rect(500, 104, 360, 206),
    "terra": pygame.Rect(100, 334, 360, 206),
    "ar": pygame.Rect(500, 334, 360, 206),
}


def carregar_icones() -> dict[str, pygame.Surface]:
    icones = {}
    for elem, caminho in CAMINHOS_IMAGENS.items():
        img = pygame.image.load(str(caminho)).convert_alpha()
        icones[elem] = pygame.transform.smoothscale(img, (96, 96))
    return icones


def hit_test(pos: Tuple[int, int]) -> Optional[str]:
    """Retorna o id do cartão sob o ponteiro, ou None."""
    for elem, rect in RETANGULOS.items():
        if rect.collidepoint(pos):
            return elem
    return None


def selecionar(elemento: str, estado: dict) -> None:
    """Mesma rotina para clique e teclado — só destaca o cartão por um instante."""
    if elemento in ELEMENTOS:
        estado["ativo"] = elemento
        estado["timer"] = 0.25  # segundos de destaque visual


def desenhar(tela, icones, fontes, estado) -> None:
    tela.fill(FUNDO)
    pygame.draw.rect(tela, PAINEL, pygame.Rect(0, 0, LARGURA, 82))
    tela.blit(fontes["titulo"].render("Parte 2 — cliques e teclas", True, TEXTO), (60, 18))
    tela.blit(
        fontes["pequena"].render("Clique nos cartões ou use 1–4", True, TEXTO_SUAVE),
        (60, 48),
    )

    for elem in ELEMENTOS:
        rect = RETANGULOS[elem]
        ativo = estado["ativo"] == elem
        cor = CORES_ATIVAS[elem] if ativo else CORES_ELEMENTOS[elem]
        borda = BORDA_DESTAQUE if ativo else BORDA
        pygame.draw.rect(tela, cor, rect, border_radius=16)
        pygame.draw.rect(tela, borda, rect, 4 if ativo else 2, border_radius=16)
        icone = icones[elem]
        tela.blit(icone, (rect.centerx - 48, rect.top + 22))
        rotulo = fontes["card"].render(ROTULOS[elem], True, TEXTO_ESCURO)
        tela.blit(rotulo, rotulo.get_rect(center=(rect.centerx, rect.top + 154)))
        tecla = fontes["tecla"].render(TECLAS_ROTULO[elem], True, TEXTO_ESCURO)
        tela.blit(tecla, (rect.left + 22, rect.top + 18))

    msg = f"Último: {estado['ativo'] or '—'}"
    txt = fontes["status"].render(msg, True, TEXTO)
    tela.blit(txt, txt.get_rect(center=(LARGURA // 2, 578)))


def main() -> int:
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Genius Musical — Parte 2: cliques e teclas")
    fontes = {
        "titulo": pygame.font.SysFont("dejavusans", 22, bold=True),
        "card": pygame.font.SysFont("dejavusans", 21, bold=True),
        "tecla": pygame.font.SysFont("dejavusans", 13, bold=True),
        "status": pygame.font.SysFont("dejavusans", 19, bold=True),
        "pequena": pygame.font.SysFont("dejavusans", 12),
    }
    icones = carregar_icones()
    estado = {"ativo": None, "timer": 0.0}
    relogio = pygame.time.Clock()
    executando = True
    while executando:
        dt = relogio.tick(FPS) / 1000.0
        if estado["timer"] > 0:
            estado["timer"] -= dt
            if estado["timer"] <= 0:
                estado["ativo"] = None

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                alvo = hit_test(evento.pos)
                if alvo is not None:
                    selecionar(alvo, estado)
            elif evento.type == pygame.KEYDOWN and evento.key in MAPA_TECLAS:
                selecionar(MAPA_TECLAS[evento.key], estado)

        desenhar(tela, icones, fontes, estado)
        pygame.display.flip()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
