#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parte 1 — Tela e imagens: carregar PNG flat e desenhar a grade 2×2."""

from __future__ import annotations

from pathlib import Path

import pygame

LARGURA, ALTURA, FPS = 960, 720, 60
FUNDO = (16, 24, 39)
PAINEL = (30, 41, 59)
TEXTO = (248, 250, 252)
TEXTO_ESCURO = (16, 24, 39)
TEXTO_SUAVE = (148, 163, 184)
BORDA = (51, 65, 85)

ELEMENTOS = ("fogo", "agua", "terra", "ar")
CORES_ELEMENTOS = {
    "fogo": (248, 113, 113),
    "agua": (96, 165, 250),
    "terra": (74, 222, 128),
    "ar": (250, 204, 21),
}
ROTULOS = {"fogo": "FOGO", "agua": "ÁGUA", "terra": "TERRA", "ar": "AR"}

# A partir de partes/parte-01-*/main.py → genius-musical/assets/imagens
PASTA_ASSETS = Path(__file__).resolve().parent.parent.parent / "assets" / "imagens"
CAMINHOS_IMAGENS = {e: PASTA_ASSETS / f"{e}.png" for e in ELEMENTOS}

RETANGULOS = {
    "fogo": pygame.Rect(100, 104, 360, 206),
    "agua": pygame.Rect(500, 104, 360, 206),
    "terra": pygame.Rect(100, 334, 360, 206),
    "ar": pygame.Rect(500, 334, 360, 206),
}


def carregar_icones() -> dict[str, pygame.Surface]:
    """Carrega PNGs com transparência, redimensiona e devolve o dicionário."""
    icones: dict[str, pygame.Surface] = {}
    tamanho = (96, 96)
    for elem, caminho in CAMINHOS_IMAGENS.items():
        # image.load + convert_alpha preserva o canal alfa do PNG flat
        img_bruta = pygame.image.load(str(caminho)).convert_alpha()
        # smoothscale evita serrilhado ao reduzir o sprite
        icones[elem] = pygame.transform.smoothscale(img_bruta, tamanho)
    return icones


def desenhar(tela: pygame.Surface, icones: dict[str, pygame.Surface], fonte) -> None:
    tela.fill(FUNDO)
    pygame.draw.rect(tela, PAINEL, pygame.Rect(0, 0, LARGURA, 82))
    titulo = fonte.render("GENIUS MUSICAL — Parte 1: imagens", True, TEXTO)
    tela.blit(titulo, (60, 28))

    for elem in ELEMENTOS:
        rect = RETANGULOS[elem]
        pygame.draw.rect(tela, CORES_ELEMENTOS[elem], rect, border_radius=16)
        pygame.draw.rect(tela, BORDA, rect, 2, border_radius=16)

        icone = icones[elem]
        # blit posiciona o sprite centralizado na metade superior do cartão
        pos = (rect.centerx - icone.get_width() // 2, rect.top + 22)
        tela.blit(icone, pos)

        rotulo = fonte.render(ROTULOS[elem], True, TEXTO_ESCURO)
        tela.blit(rotulo, rotulo.get_rect(center=(rect.centerx, rect.top + 154)))


def main() -> int:
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Genius Musical — Parte 1: tela e imagens")
    fonte = pygame.font.SysFont("dejavusans", 22, bold=True)
    icones = carregar_icones()
    relogio = pygame.time.Clock()
    executando = True
    while executando:
        relogio.tick(FPS)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
        desenhar(tela, icones, fonte)
        pygame.display.flip()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
